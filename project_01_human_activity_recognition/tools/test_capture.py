#!/usr/bin/env python3
"""Capture ESP32 serial output for a fixed duration to test predictions."""

import argparse
import serial
import time
import sys

PORT = "/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_48:CA:43:AF:8B:BC-if00"
BAUD = 115200

def main():
    parser = argparse.ArgumentParser(description="Capture ESP32 serial output.")
    parser.add_argument("--seconds", type=int, default=8, help="Capture duration")
    parser.add_argument("--port", default=PORT)
    args = parser.parse_args()

    print(f"Capturing {args.seconds}s from {args.port}...")
    print("Perform your movement NOW!\n")

    try:
        ser = serial.Serial(args.port, BAUD, timeout=1)
        start = time.time()

        while time.time() - start < args.seconds:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if line:
                print(line)

        ser.close()
    except serial.SerialException as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print("\n--- Capture done ---")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
