import usb.core
import time

VENDOR = 0x0451
PRODUCT = 0xE022

SERVICE_STREAM = 0x04


def open_device():
    dev = usb.core.find(idVendor=VENDOR, idProduct=PRODUCT)
    if dev is None:
        raise Exception("Calculator not found")

    dev.set_configuration()
    return dev


def read_raw(dev):
    try:
        return bytes(dev.read(0x81, 512, timeout=2000))
    except:
        return None


def extract_payload(raw):
    if not raw or len(raw) < 12:
        return None

    service = raw[1]
    payload = raw[12:]

    return service, payload


def main():
    dev = open_device()

    buffer = b""

    print("Listening...")

    while True:
        raw = read_raw(dev)
        msg = extract_payload(raw)

        if not msg:
            continue

        service, payload = msg

        if service == SERVICE_STREAM:
            text = payload.decode(errors="ignore")
            print("STREAM:", text)


if __name__ == "__main__":
    main()