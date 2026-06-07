#include <os.h>

static const unsigned int usb_send_addrs[] = { 0x103E4A8C };

#define os_usb_send SYSCALL_CUSTOM(usb_send_addrs, void, void *, int)

void send_packet_to_pc(const char *data_payload, int size) {
    char usb_packet[64]; 
    
    if (size > 64) return;
    
    memcpy(usb_packet, data_payload, size);
    
    os_usb_send(usb_packet, size);
}

int main(void) {
    const char *msg = "HELLO_PC";
    send_packet_to_pc(msg, 8);
    return 0;
}
