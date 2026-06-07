import usb.core
import struct
import time


def open_device():
    dev = usb.core.find(idVendor=0x0451, idProduct=0xE022)
    if dev is None:
        raise Exception("Calculator not found")

    if dev.is_kernel_driver_active(0):
        dev.detach_kernel_driver(0)

    dev.set_configuration()
    return dev

# constants

ADDR_ME   = 0xFE
ADDR_CALC = 0x01

SERVICE_ADDR_REQ = 0x01
SERVICE_TIME     = 0x02
SERVICE_STREAM   = 0x04
SERVICE_UNKNOWN   = 0x08
ACK_FLAG         = 0x80

seqno = [0]

# checksum stuff

def compute_checksum(data: bytes) -> int:
    acc = 0
    n = len(data)

    for i in range(0, n - 1, 2):
        acc += (data[i] << 8) | data[i + 1]

    if n & 1:
        acc += data[-1] << 8

    while acc >> 16:
        acc = (acc >> 16) + (acc & 0xFFFF)

    return acc & 0xFFFF


def verify_checksum(data: bytes) -> bool:
    return (compute_checksum(data) ^ 0xFFFF) == 0

#packet creation

def make_packet(service, src, dest,
                payload=b'',
                req_ack=0,
                unknown=0,
                misc=0,
                seq=None):

    if seq is None:
        seq = seqno[0]
        seqno[0] += 1

    length = 12 + len(payload)

    header = struct.pack('>BBBBBBHH',
        misc,
        service,
        src,
        dest,
        unknown,
        req_ack,
        length,
        seq
    )

    packet = header + b'\x00\x00' + payload
    csum = compute_checksum(packet) ^ 0xFFFF

    return header + struct.pack('>H', csum) + payload

# read packets

def read_nnse(dev, timeout=5000):
    try:
        raw = bytes(dev.read(0x81, 1500, timeout=timeout))
    except usb.core.USBTimeoutError:
        return None

    if len(raw) < 12:
        return None

    misc    = raw[0]
    service = raw[1]
    src     = raw[2]
    dest    = raw[3]
    unknown = raw[4]
    req_ack = raw[5]
    length  = (raw[6] << 8) | raw[7]
    seq     = (raw[8] << 8) | raw[9]
    payload = raw[12:length]

    ok = verify_checksum(raw)

    print(
        f"IN  svc={service:02x} src={src:02x} dst={dest:02x} "
        f"len={length} seq={seq} chk={ok} "
        f"payload={payload.hex()}"
    )

    return misc, service, src, dest, unknown, req_ack, seq, payload


# respond to calc ack reqs

def send_ack(dev, msg):
    misc, service, src, dest, unknown, req_ack, seq, payload = msg

    ack = make_packet(
        service | ACK_FLAG,
        dest,
        src,
        payload=b'',
        req_ack=req_ack & ~1,
        unknown=unknown,
        misc=misc,
        seq=seq
    )

    print("OUT ACK")
    dev.write(0x01, ack, timeout=3000)

# address requests

def handle_addr_request(dev, msg):
    misc, service, src, dest, unknown, req_ack, seq, payload = msg

    if len(payload) >= 8:
        prefix = payload[:4]
        mode   = payload[4:8]
    else:
        prefix = b"\x00\x00\x00\x00"
        mode   = b"\x00\x00\x00\x02"

    resp_payload = prefix + mode

    resp = make_packet(
        SERVICE_ADDR_REQ,
        ADDR_ME,
        src,
        payload=resp_payload,
        misc=misc,
        unknown=unknown
    )

    print(f"OUT ADDR resp {resp_payload.hex()}")
    dev.write(0x01, resp, timeout=3000)



dev = open_device()
dev.reset()
time.sleep(1)
dev = open_device()

print("Waiting for packets...")

for i in range(100):

    msg = read_nnse(dev, timeout=1000)
    if msg is None:
        continue

    misc, service, src, dest, unknown, req_ack, seq, payload = msg

    if req_ack & 1:
        send_ack(dev, msg)

    svc = service & ~ACK_FLAG


    if svc == SERVICE_ADDR_REQ and not (service & ACK_FLAG):
        print("ADDR request")
        handle_addr_request(dev, msg)


    elif svc == SERVICE_TIME and not (service & ACK_FLAG):
        print("TIME request")

        t = int(time.time())

        resp_payload = (
            bytes([0x80]) +
            struct.pack('>I', t) +
            b'\x00' * 12
        )

        resp = make_packet(
            SERVICE_TIME,
            ADDR_ME,
            src,
            payload=resp_payload,
            misc=misc,
            unknown=unknown
        )

        dev.write(0x01, resp, timeout=3000)

        print("HANDSHAKE COMPLETE")
        break


    elif svc == SERVICE_UNKNOWN and not (service & ACK_FLAG):
        print("UNKNOWN service")

        resp = make_packet(
            SERVICE_UNKNOWN,
            ADDR_ME,
            src,
            payload=bytes([0x81, 0x03]),
            misc=misc,
            unknown=unknown
        )

        dev.write(0x01, resp, timeout=3000)


print("stream mode :)")

while True:
    msg = read_nnse(dev, timeout=5000)
    if msg is None:
        continue

    misc, service, src, dest, unknown, req_ack, seq, payload = msg

    if req_ack & 1:
        send_ack(dev, msg)

    svc = service & ~ACK_FLAG

    if svc == SERVICE_STREAM:
        print("STREAM:", payload.hex())

    elif svc == SERVICE_UNKNOWN:
        print("UNKNOWN:", payload.hex())