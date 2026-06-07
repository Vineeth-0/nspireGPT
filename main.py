import usb.core
import usb.util

VENDOR = 0x0451
PRODUCT = 0xE022
EP_IN = 0x81


def open_device():
    dev = usb.core.find(idVendor=VENDOR, idProduct=PRODUCT)
    if dev is None:
        raise Exception("Calculator not found")

    dev.set_configuration()

    try:
        usb.util.claim_interface(dev, 0)
    except:
        pass

    return dev


def main():
    dev = open_device()

    print("Listening for stream...")

    buffer = ""

    while True:
        try:
            data = dev.read(EP_IN, 2048, timeout=5000)
            text = bytes(data).decode(errors="ignore")

            buffer += text

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()

                if line:
                    print("STREAM:", line)

        except Exception:
            continue


if __name__ == "__main__":
    main()