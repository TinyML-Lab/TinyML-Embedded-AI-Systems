#!/usr/bin/env python3

import argparse
import csv
from collections import defaultdict
from pathlib import Path


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


def parse_args():
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent
    default_data_dir = project_dir / "data" / "raw"

    parser = argparse.ArgumentParser(
        description="Validate collected IMU dataset CSV files."
    )

    parser.add_argument("--data-dir", default=str(default_data_dir))
    parser.add_argument("--min-samples", type=int, default=500)

    return parser.parse_args()


def validate_file(csv_path):
    valid_rows = 0
    invalid_rows = 0
    labels_count = defaultdict(int)

    with open(csv_path, "r", newline="") as csv_file:
        reader = csv.reader(csv_file)

        try:
            header = next(reader)
        except StopIteration:
            return False, 0, 0, labels_count, "empty file"

        if header != CSV_HEADER:
            return False, 0, 0, labels_count, "invalid header"

        for row in reader:
            if len(row) != len(CSV_HEADER):
                invalid_rows += 1
                continue

            try:
                int(row[0])
                for value in row[1:7]:
                    float(value)
            except ValueError:
                invalid_rows += 1
                continue

            label = row[-1].strip()

            if not label:
                invalid_rows += 1
                continue

            labels_count[label] += 1
            valid_rows += 1

    return True, valid_rows, invalid_rows, labels_count, ""


def main():
    args = parse_args()

    data_dir = Path(args.data_dir)

    if not data_dir.exists():
        print(f"Dataset directory does not exist: {data_dir}")
        return 1

    csv_files = sorted(data_dir.glob("*.csv"))

    if not csv_files:
        print(f"No CSV files found in: {data_dir}")
        return 1

    total_labels = defaultdict(int)
    failed = False

    print(f"Validating dataset directory: {data_dir}")
    print()

    for csv_path in csv_files:
        is_valid, valid_rows, invalid_rows, labels_count, error = validate_file(csv_path)

        if not is_valid:
            print(f"[FAIL] {csv_path.name}: {error}")
            failed = True
            continue

        status = "PASS" if invalid_rows == 0 else "WARN"

        print(f"[{status}] {csv_path.name}")
        print(f"  valid rows:   {valid_rows}")
        print(f"  invalid rows: {invalid_rows}")

        for label, count in labels_count.items():
            print(f"  label: {label} -> {count}")
            total_labels[label] += count

        if invalid_rows > 0:
            failed = True

        print()

    print("Summary:")
    for label, count in sorted(total_labels.items()):
        status = "OK" if count >= args.min_samples else "LOW"
        print(f"  {label}: {count} samples [{status}]")

        if count < args.min_samples:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
