#!/usr/bin/env python3

import argparse
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import serial


CSV_HEADER = [
    "timestamp_ms",
    "acc_x_g",
    "acc_y_g",
    "acc_z_g",
    "gyro_x_dps",
    "gyro_y_dps",
    "gyro_z_dps",
    "label",
]


DEFAULT_PORT = "/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_48:CA:43:AF:8B:BC-if00"


def parse_args():
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent
    default_output_dir = project_dir / "data" / "raw"

    parser = argparse.ArgumentParser(
        description="Collect calibrated IMU CSV data from ESP32-S3 serial output."
    )

    parser.add_argument("--port", default=DEFAULT_PORT, help="Serial port path")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate")
    parser.add_argument("--label", required=True, help="Activity label")
    parser.add_argument("--samples", type=int, default=1000, help="Number of samples to collect")
    parser.add_argument("--duration-sec", type=float, default=None, help="Optional collection duration in seconds")
    parser.add_argument("--output-dir", default=str(default_output_dir), help="Output directory")

    return parser.parse_args()


def is_valid_csv_row(row):
    if len(row) != len(CSV_HEADER):
        return False

    try:
        int(row[0])
        for value in row[1:7]:
            float(value)
    except ValueError:
        return False

    return True


def main():
    args = parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"{args.label}_{timestamp}.csv"

    print(f"Port: {args.port}")
    print(f"Label: {args.label}")
    print(f"Target samples: {args.samples}")
    print(f"Output: {output_file}")
    print("Keep the sensor still during ESP32 startup calibration...")

    collected = 0
    start_time = None

    try:
        with serial.Serial(args.port, args.baud, timeout=2) as ser:
            time.sleep(6)
            ser.reset_input_buffer()

            ser.write(f"label={args.label}\n".encode("utf-8"))
            time.sleep(0.5)

            with open(output_file, "w", newline="") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(CSV_HEADER)

                start_time = time.time()

                while collected < args.samples:
                    if args.duration_sec is not None:
                        if time.time() - start_time >= args.duration_sec:
                            break

                    line = ser.readline().decode("utf-8", errors="ignore").strip()

                    if not line:
                        continue

                    if line.startswith("#"):
                        print(line)
                        continue

                    if line.startswith("timestamp_ms"):
                        continue

                    row = line.split(",")

                    if not is_valid_csv_row(row):
                        print(f"Skipping invalid line: {line}")
                        continue

                    row[-1] = args.label
                    writer.writerow(row)

                    collected += 1

                    if collected % 50 == 0:
                        print(f"Collected {collected}/{args.samples}")

    except serial.SerialException as error:
        print(f"Serial error: {error}", file=sys.stderr)
        return 1

    print(f"Done. Saved {collected} samples to {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
