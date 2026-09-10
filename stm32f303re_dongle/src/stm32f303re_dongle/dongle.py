import struct
import time
from dataclasses import dataclass
from enum import IntEnum, StrEnum

import serial

CMD_ARGUMENT_SIZE = 4


class CMD_Action(IntEnum):
    CMD_READ = 48
    CMD_WRITE = 49
    CMD_APPEND = 50
    CMD_TOGGLE = 51
    CMD_START = 52
    CMD_STOP = 53
    CMD_CAPTURE = 54
    CMD_CONFIG = 55
    CMD_INIT = 56
    CMD_RESET = 57


class CMD_Subject(IntEnum):
    CMD_GPIO = 48
    CMD_ADC = 49
    CMD_I2C = 50
    CMD_SPI = 51
    CMD_BUFFER = 52
    CMD_TIMER = 53
    CMD_PWM = 54


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


class SPI_DataWidth(StrEnum):
    WIDTH_4 = "3"
    WIDTH_5 = "4"
    WIDTH_6 = "5"
    WIDTH_7 = "6"
    WIDTH_8 = "7"
    WIDTH_9 = "8"
    WIDTH_10 = "9"
    WIDTH_11 = "A"
    WIDTH_12 = "B"
    WIDTH_13 = "C"
    WIDTH_14 = "D"
    WIDTH_15 = "E"
    WIDTH_16 = "F"


class SPI_FirstBit(StrEnum):
    MSB = "0"
    LSB = "1"


class SPI_ClkFreq(StrEnum):
    CLK_18MHZ = "0"
    CLK_9MHZ = "1"
    CLK_4P5MHZ = "2"
    CLK_2P25MHZ = "3"
    CLK_1P125MHZ = "4"
    CLK_562P5KHZ = "5"
    CLK_281P25KHZ = "6"


class SPI_ClkPolarity(StrEnum):
    IDLE_LOW = "0"
    IDLE_HIGH = "1"


class SPI_ClkPhase(StrEnum):
    FIRST_EDGE = "1"
    SECOND_EDGE = "2"


class SPI_CSNPolarity(StrEnum):
    ACTIVE_LOW = "0"
    ACTIVE_HIGH = "1"


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
    def __init__(self, port, baud_rate: int = 1500000):
        self.dev = serial.Serial(port=port, baudrate=baud_rate, timeout=2.0)

    def send(self, payload: bytes):
        # print(f"[SENT]:\t{payload}")
        if len(payload) != 14:
            raise RuntimeError("Invalid number of command bytes!")
        self.dev.write(payload)
        self.dev.flush()

    def send_receive(self, payload: bytes):
        self.send(payload=payload)
        resp = self.dev.read_until(b"\r\n")
        # print(f"[RESP]:\t{resp.decode('utf-8')}")
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

    def spi_init(
        self,
        data_width: SPI_DataWidth,
        first_bit: SPI_FirstBit,
        freq: SPI_ClkFreq,
        clk_polarity: SPI_ClkPolarity,
        clk_phase: SPI_ClkPhase,
        sample_rate: int,
        transmit_delay: float,
        csn_pulse_width: float,
        csn_polarity: SPI_CSNPolarity,
    ):
        if sample_rate > 800_000:
            raise ValueError(
                f"SPI sample rate ({sample_rate}) should not exceed 800kHz!"
            )

        if transmit_delay > 56.875e-6:
            raise ValueError(
                f"SPI transmit delay ({transmit_delay}) should not exceed 56.875us!"
            )

        if csn_pulse_width < (1 / 72_000_000.0):
            raise ValueError(
                f"SPI CSN pulse width ({csn_pulse_width}) should not be less than 13.8889ns!"
            )

        # configure SPI
        transmit_delay_count = int(transmit_delay * 72_000_000.0)
        cmd = CMD_Frame(
            CMD_Action.CMD_CONFIG,
            CMD_Subject.CMD_SPI,
            "0",
            f"{data_width}{first_bit}{freq}{clk_polarity}",
            f"{clk_phase}{transmit_delay_count:03X}",
        )
        self.send(payload=cmd.format())
        time.sleep(0.01)

        # configure SPI CS
        csn_pulse_width_count = int(csn_pulse_width * 72_000_000.0)
        cmd = CMD_Frame(
            CMD_Action.CMD_CONFIG,
            CMD_Subject.CMD_SPI,
            "1",
            f"{csn_pulse_width_count:04X}",
            f"{csn_polarity}000",
        )
        self.send(payload=cmd.format())
        time.sleep(0.01)

        # configure SPI sample rate
        sample_rate_khz = int(sample_rate / 1000)
        cmd = CMD_Frame(
            CMD_Action.CMD_CONFIG,
            CMD_Subject.CMD_SPI,
            "2",
            f"{sample_rate_khz:04X}",
            "0000",
        )
        self.send(payload=cmd.format())
        time.sleep(0.01)

        # initialize SPI
        cmd = CMD_Frame(
            CMD_Action.CMD_INIT,
            CMD_Subject.CMD_SPI,
            "0",
            "0000",
            "0000",
        )
        self.send(payload=cmd.format())
        time.sleep(0.01)

    def spi_transmit(self, tx_command: list[int], frame_size: int, increment: bool):
        self.buffer_reset_tx()
        self.buffer_append_to_tx(data=tx_command)
        if increment:
            cmd = CMD_Frame(
                CMD_Action.CMD_WRITE,
                CMD_Subject.CMD_SPI,
                "0",
                f"{frame_size:04X}",
                "0001",
            )
        else:
            cmd = CMD_Frame(
                CMD_Action.CMD_WRITE,
                CMD_Subject.CMD_SPI,
                "0",
                f"{frame_size:04X}",
                "0000",
            )
        self.send(payload=cmd.format())

    def buffer_append_to_tx(self, data: list[int]):
        for i in data:
            cmd = CMD_Frame(
                CMD_Action.CMD_APPEND,
                CMD_Subject.CMD_BUFFER,
                "1",
                f"{i:04X}",
                "0000",
            )
            self.send(payload=cmd.format())

    def buffer_read_rx(self, frame_size: int) -> list[int]:
        cmd = CMD_Frame(
            CMD_Action.CMD_READ,
            CMD_Subject.CMD_BUFFER,
            "0",
            f"{frame_size:04X}",
            "0000",
        )
        self.dev.reset_input_buffer()
        self.send(payload=cmd.format())
        bytes_to_read = 2 * frame_size
        data_frame = b""
        while len(data_frame) < bytes_to_read:
            buf = self.dev.read(bytes_to_read - len(data_frame))
            if not buf:
                raise TimeoutError(
                    f"Failed to read data! Only captured {len(data_frame)} bytes"
                )
            data_frame += buf
        # print(f"Read bytes: {len(data_frame)}")
        return list(struct.unpack(f"<{frame_size}H", data_frame))

    def buffer_reset_rx(self):
        cmd = CMD_Frame(
            CMD_Action.CMD_RESET,
            CMD_Subject.CMD_BUFFER,
            "0",
            "0000",
            "0000",
        )
        self.send(payload=cmd.format())

    def buffer_reset_tx(self):
        cmd = CMD_Frame(
            CMD_Action.CMD_RESET,
            CMD_Subject.CMD_BUFFER,
            "1",
            "0000",
            "0000",
        )
        self.send(payload=cmd.format())
