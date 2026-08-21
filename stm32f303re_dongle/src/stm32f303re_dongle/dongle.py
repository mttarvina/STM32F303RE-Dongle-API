import time
from dataclasses import dataclass
from enum import IntEnum, StrEnum

import serial

CMD_ARGUMENT_SIZE = 4


class CMD_Action(IntEnum):
    CMD_READ = 48
    CMD_WRITE = 49
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


class GPIO_Ports(StrEnum):
    GPIOA = "0"
    GPIOB = "1"
    GPIOC = "2"
    GPIOD = "3"
    GPIOE = "4"
    GPIOF = "5"


class GPIO_Modes(StrEnum):
    INPUT = "0"
    OUTPUT = "1"
    ALTERNATE = "2"
    ANALOG = "3"


class GPIO_Speeds(StrEnum):
    LOW = "0"
    MEDIUM = "1"
    HIGH = "2"


class GPIO_OutputTypes(StrEnum):
    PUSH_PULL = "0"
    OPEN_DRAIN = "1"


class GPIO_PullModes(StrEnum):
    NONE = "0"
    PULL_UP = "1"
    PULL_DOWN = "2"


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
        # print(f"[SENT]:\t{payload}")
        self.send(payload=payload)
        time.sleep(0.01)
        resp = self.dev.read_until(b"\r\n")
        # print(f"[RESP]:\t{resp}")
        return resp.decode("utf-8")

    def gpio_config(
        self,
        port: GPIO_Ports,
        pins: int,
        mode: GPIO_Modes,
        speed: GPIO_Speeds,
        output_type: GPIO_OutputTypes,
        pull_mode: GPIO_PullModes,
    ):
        cmd = CMD_Frame(
            CMD_Action.CMD_CONFIG,
            CMD_Subject.CMD_GPIO,
            port,
            f"{pins:04X}",
            (mode + speed + output_type + pull_mode),
        )
        self.send_receive(payload=cmd.format())

    def gpio_write(self, port: GPIO_Ports, pins: int, level: int):
        cmd = CMD_Frame(
            CMD_Action.CMD_WRITE,
            CMD_Subject.CMD_GPIO,
            port,
            f"{pins:04X}",
            f"{level:01X}000",
        )
        self.send(payload=cmd.format())

    def gpio_toggle(self, port: GPIO_Ports, pins: int):
        cmd = CMD_Frame(
            CMD_Action.CMD_TOGGLE,
            CMD_Subject.CMD_GPIO,
            port,
            f"{pins:04X}",
            "0000",
        )
        self.send(payload=cmd.format())

    def gpio_read(self, port: GPIO_Ports, pins: int) -> int:
        cmd = CMD_Frame(
            CMD_Action.CMD_READ,
            CMD_Subject.CMD_GPIO,
            port,
            f"{pins:04X}",
            "0000",
        )
        try:
            pin_states = int(self.send_receive(payload=cmd.format()))
        except ValueError:
            pin_states = 0
        return pin_states
