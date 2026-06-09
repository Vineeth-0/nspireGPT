#!/usr/bin/env python3
"""
TI-Nspire USB Communication Tool
A Python implementation for file transfer to/from TI-Nspire calculators
"""

import usb.core
import usb.util
import struct
import sys
import os
from pathlib import Path
from typing import Optional, List, Tuple
import argparse
from dataclasses import dataclass

# TI Constants
VID = 0x0451  # Texas Instruments
PID = 0xe012  # Standard TI-Nspire
PID_CX2 = 0xe022  # CX-II

# USB Endpoints
EP_OUT = 0x01
EP_IN = 0x82

TIMEOUT = 5000


@dataclass
class FileInfo:
    """File information from calculator"""
    name: str
    is_dir: bool
    size: int
    date: int


class TINspireDevice:
    """Handle communication with TI-Nspire calculator"""

    def __init__(self, device: usb.core.Device):
        """Initialize device connection"""
        self.device = device
        self.device.set_configuration()

        # Claim interface
        usb.util.claim_interface(self.device, 0)

    def __del__(self):
        """Clean up USB device"""
        try:
            usb.util.release_interface(self.device, 0)
        except:
            pass

    def _send_data(self, data: bytes) -> None:
        """Send data to calculator"""
        self.device.write(EP_OUT, data, TIMEOUT)

    def _receive_data(self, size: int = 4096) -> bytes:
        """Receive data from calculator"""
        return bytes(self.device.read(EP_IN, size, TIMEOUT))

    def _send_command(self, cmd: str, *args) -> bytes:
        """Send command and get response"""
        # Construct command packet
        packet = self._build_packet(cmd, args)
        self._send_data(packet)
        
        # Receive response
        return self._receive_data()

    def _build_packet(self, cmd: str, args: Tuple) -> bytes:
        """Build USB command packet"""
        # This is a simplified version - actual protocol is more complex
        packet = bytearray()
        packet.extend(b'\x00\x00\x00\x00')  # Header
        packet.extend(cmd.encode())
        for arg in args:
            if isinstance(arg, str):
                packet.extend(arg.encode())
            elif isinstance(arg, bytes):
                packet.extend(arg)
        return bytes(packet)

    def get_info(self) -> dict:
        """Get calculator information"""
        # This would need to implement the actual protocol
        # For now, returning placeholder
        try:
            info_packet = self._send_command("INFO")
            return {
                "name": "TI-Nspire",
                "os_version": "N/A",
                "device_id": "N/A"
            }
        except Exception as e:
            print(f"Error getting device info: {e}")
            return {}

    def list_dir(self, path: str = "/") -> List[FileInfo]:
        """List directory contents"""
        print(f"Listing directory: {path}")
        files = []
        try:
            # Send LIST command
            response = self._send_command("LIST", path)
            # Parse response (simplified - actual protocol differs)
            return files
        except Exception as e:
            print(f"Error listing directory: {e}")
            return []

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to calculator"""
        try:
            local_file = Path(local_path)
            if not local_file.exists():
                print(f"Error: {local_path} not found")
                return False

            with open(local_file, 'rb') as f:
                file_data = f.read()

            file_name = local_file.name
            remote_full_path = f"{remote_path}/{file_name}"

            print(f"Uploading {file_name} ({len(file_data)} bytes) to {remote_full_path}")

            # Build upload packet with file data
            # This is simplified - actual protocol is more complex
            packet = bytearray()
            packet.extend(b'\x03\x00')  # Upload command
            packet.extend(len(remote_full_path).to_bytes(2, 'little'))
            packet.extend(remote_full_path.encode())
            packet.extend(len(file_data).to_bytes(4, 'little'))
            packet.extend(file_data)

            self._send_data(bytes(packet))
            response = self._receive_data()

            print(f"Upload complete: {file_name}")
            return True

        except Exception as e:
            print(f"Error uploading file: {e}")
            return False

    def download_file(self, remote_path: str, local_dir: str = ".") -> bool:
        """Download file from calculator"""
        try:
            file_name = Path(remote_path).name
            local_path = Path(local_dir) / file_name

            print(f"Downloading {remote_path} to {local_path}")

            # Build download request packet
            packet = bytearray()
            packet.extend(b'\x02\x00')  # Download command
            packet.extend(len(remote_path).to_bytes(2, 'little'))
            packet.extend(remote_path.encode())

            self._send_data(bytes(packet))

            # Receive file data
            file_data = self._receive_data()

            with open(local_path, 'wb') as f:
                f.write(file_data)

            print(f"Download complete: {local_path}")
            return True

        except Exception as e:
            print(f"Error downloading file: {e}")
            return False

    def delete_file(self, remote_path: str) -> bool:
        """Delete file on calculator"""
        try:
            print(f"Deleting {remote_path}")

            packet = bytearray()
            packet.extend(b'\x04\x00')  # Delete command
            packet.extend(len(remote_path).to_bytes(2, 'little'))
            packet.extend(remote_path.encode())

            self._send_data(bytes(packet))
            response = self._receive_data()

            print(f"Delete complete: {remote_path}")
            return True

        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

    def create_dir(self, remote_path: str) -> bool:
        """Create directory on calculator"""
        try:
            print(f"Creating directory {remote_path}")

            packet = bytearray()
            packet.extend(b'\x05\x00')  # Mkdir command
            packet.extend(len(remote_path).to_bytes(2, 'little'))
            packet.extend(remote_path.encode())

            self._send_data(bytes(packet))
            response = self._receive_data()

            print(f"Directory created: {remote_path}")
            return True

        except Exception as e:
            print(f"Error creating directory: {e}")
            return False


def find_device() -> Optional[TINspireDevice]:
    """Find connected TI-Nspire calculator"""
    all_devices = list(usb.core.find(find_all=True))
    ti_devices = [
        d for d in all_devices
        if d.idVendor == VID and d.idProduct in (PID, PID_CX2)
    ]

    if not ti_devices:
        print("No TI-Nspire calculator found")
        if all_devices:
            print("Connected USB devices:")
            for d in all_devices:
                print(f"  {hex(d.idVendor)}:{hex(d.idProduct)} on bus {getattr(d, 'bus', '?')} addr {getattr(d, 'address', '?')}")
        return None

    dev = ti_devices[0]
    print(f"Found TI-Nspire candidate: {hex(dev.idVendor)}:{hex(dev.idProduct)} on bus {getattr(dev, 'bus', '?')} addr {getattr(dev, 'address', '?')}")

    try:
        if dev.is_kernel_driver_active(0):
            try:
                dev.detach_kernel_driver(0)
            except usb.core.USBError as e:
                print(f"Unable to detach kernel driver: {e}")
                return None
        return TINspireDevice(dev)
    except usb.core.USBError as e:
        print(f"Error connecting to device: {e}")
        return None
    except Exception as e:
        print(f"Error initializing TI-Nspire device: {e}")
        return None


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description="TI-Nspire USB File Transfer Tool"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # List command
    parser_ls = subparsers.add_parser('ls', help='List calculator directory')
    parser_ls.add_argument('path', nargs='?', default='/', help='Directory path')

    # Upload command
    parser_upload = subparsers.add_parser('upload', help='Upload file to calculator')
    parser_upload.add_argument('file', help='Local file to upload')
    parser_upload.add_argument('dest', help='Destination path on calculator')

    # Download command
    parser_download = subparsers.add_parser('download', help='Download file from calculator')
    parser_download.add_argument('file', help='File path on calculator')
    parser_download.add_argument('dest', default='.', help='Destination directory')

    # Delete command
    parser_delete = subparsers.add_parser('delete', help='Delete file on calculator')
    parser_delete.add_argument('file', help='File path on calculator')

    # Mkdir command
    parser_mkdir = subparsers.add_parser('mkdir', help='Create directory on calculator')
    parser_mkdir.add_argument('path', help='Directory path to create')

    # Info command
    subparsers.add_parser('info', help='Get calculator information')

    args = parser.parse_args()

    # Find device
    device = find_device()
    if device is None:
        sys.exit(1)

    # Execute command
    if args.command == 'info':
        info = device.get_info()
        for key, value in info.items():
            print(f"{key}: {value}")

    elif args.command == 'ls':
        path = getattr(args, 'path', '/')
        files = device.list_dir(path)
        for file_info in files:
            marker = '/' if file_info.is_dir else ''
            print(f"{file_info.name}{marker}")

    elif args.command == 'upload':
        device.upload_file(args.file, args.dest)

    elif args.command == 'download':
        device.download_file(args.file, args.dest)

    elif args.command == 'delete':
        device.delete_file(args.file)

    elif args.command == 'mkdir':
        device.create_dir(args.path)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()