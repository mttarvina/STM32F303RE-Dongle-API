import serial.tools.list_ports as list_com_ports


def scan_stlink() -> str | None:
    stlink_port = None
    ports = list_com_ports.comports()
    for port in ports:
        if "stm32" in port.description.casefold():
            stlink_port = port.device
            break
    return stlink_port


# Test ---------------------------------------------------------------------------------------------
if __name__ == "__main__":
    print(scan_stlink())
