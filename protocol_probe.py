#!/usr/bin/env python3
"""
TI-Nspire USB Protocol Probe
Attempts to reverse-engineer the communication protocol
"""

import usb.core
import usb.util
import time

VID = 0x0451
PID = 0xe022

def probe_device():
    dev = usb.core.find(idVendor=VID, idProduct=PID)
    if not dev:
        print("Device not found")
        return
    
    print("=" * 60)
    print("TI-Nspire CX II USB Probe")
    print("=" * 60)
    
    dev.set_configuration()
    cfg = dev.get_active_configuration()
    intf = cfg[(0, 0)]
    
    # Get endpoints
    ep_out = usb.util.find_descriptor(
        intf,
        custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
    )
    ep_in = usb.util.find_descriptor(
        intf,
        custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
    )
    
    print(f"\nEndpoints:")
    print(f"  OUT: {hex(ep_out.bEndpointAddress)} (max {ep_out.wMaxPacketSize} bytes)")
    print(f"  IN:  {hex(ep_in.bEndpointAddress)} (max {ep_in.wMaxPacketSize} bytes)")
    
    usb.util.claim_interface(dev, 0)
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("""
1. On the calculator, check if there's a USB file transfer mode:
   - Try: Press [DOC] or [HOME] → look for "USB" or "Connect" option
   - Try: Check Settings → Connectivity → USB Transfer Mode
   
2. If the calculator has a "Connect to Computer" mode, enable it

3. Run this script again to see if the device responds

4. Alternatively, use Wireshark to capture TI-Nspire<->Computer USB traffic:
   - Install Wireshark: sudo apt install wireshark
   - Capture USB traffic while using official TI software
   - Analyze the packets to reverse-engineer the protocol

5. Check if there's a usblib or similar on the calculator itself
   that defines the protocol in documentation form
""")

if __name__ == '__main__':
    probe_device()
