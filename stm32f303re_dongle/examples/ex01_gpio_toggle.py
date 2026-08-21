import time

from stm32f303re_dongle import (
    GPIO_Modes,
    GPIO_OutputTypes,
    GPIO_Ports,
    GPIO_PullModes,
    GPIO_Speeds,
    STM32F303RE_Dongle,
    scan_stlink,
)


def main():
    com_port = scan_stlink()
    if com_port is None:
        raise RuntimeError("No STM32/STLINK found!")

    test_pins = (0x1 << 5) | (0x1 << 6)  # GPIOA, pins 5 & 6

    dongle = STM32F303RE_Dongle(port=com_port)
    dongle.gpio_config(
        port=GPIO_Ports.GPIOA,
        pins=test_pins,
        mode=GPIO_Modes.OUTPUT,
        speed=GPIO_Speeds.HIGH,
        output_type=GPIO_OutputTypes.PUSH_PULL,
        pull_mode=GPIO_PullModes.NONE,
    )
    try:
        while True:
            dongle.gpio_toggle(port=GPIO_Ports.GPIOA, pins=test_pins)
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nExiting...")
        exit(1)


if __name__ == "__main__":
    main()
