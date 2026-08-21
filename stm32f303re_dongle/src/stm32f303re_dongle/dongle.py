import time
from dataclasses import dataclass
from enum import IntEnum

import serial

CMD_ARGUMENT_SIZE = 4


class CMD_Action(IntEnum):
    CMD_GET = 48
    CMD_SET = 49
    CMD_TOGGLE = 50
    CMD_START = 51
    CMD_STOP = 52
    CMD_CAPTURE = 53
    CMD_CONFIG = 54


class CMD_Subject(IntEnum):
    CMD_GPIO = 48
    CMD_ADC = 49
    CMD_I2C = 50
    CMD_SPI = 51
    CMD_TIMER = 52
    CMD_PWM = 53


@dataclass(order=True)
class CMD_Frame:
    action: CMD_Action
    subject: CMD_Subject
    param: str
    argA: str
    argB: str

    def format(self) -> bytes:
        cmd: bytes = b""
        cmd += bytes([self.action])
        cmd += bytes([self.subject])
        cmd += bytes(self.param, encoding="utf-8")
        cmd += bytes(self.argA, encoding="utf-8")
        cmd += bytes(self.argB, encoding="utf-8")
        cmd += bytes("!\r\n", encoding="utf-8")
        return cmd


class STM32F303RE_Dongle:
    def __init__(self, port, baud_rate: int = 230400, time_out: float = 1.0):
        self.dev = serial.Serial(port=port, baudrate=baud_rate, timeout=time_out)

    def send(self, payload: bytes):
        if len(payload) != 14:
            raise RuntimeError("Invalid number of command bytes!")
        self.dev.write(payload)
        self.dev.flush()

    def send_receive(self, payload: bytes):
        self.send(payload=payload)
        time.sleep(0.01)
        resp = self.dev.readline()
        return resp


if __name__ == "__main__":
    from stm32f303re_dongle import utils

    com_port = utils.scan_stlink()
    if com_port is None:
        raise RuntimeError("No STM32/STLINK found!")

    dongle = STM32F303RE_Dongle(port=com_port)
    cmd = CMD_Frame(CMD_Action.CMD_TOGGLE, CMD_Subject.CMD_GPIO, "0", "0020", "0000")
    cmd_bytes = CMD_Frame.format(cmd)
    print(cmd_bytes)
    try:
        while True:
            dongle.send(payload=cmd_bytes)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting...")
        exit(1)
