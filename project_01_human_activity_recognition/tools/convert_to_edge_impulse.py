#!/usr/bin/env python3
"""Convert per-class IMU CSV files into Edge Impulse CSV format with timestamp."""

import os
from pathlib import Path

import pandas as pd

DATA_DIR = Path("data/raw/final")
OUTPUT_DIR = Path("data/edge_impulse_windows")
WINDOW_SIZE = 50
STRIDE = 10
SAMPLE_INTERVAL_MS = 20  # 50 Hz

EI_COLUMNS = ["timestamp", "accX", "accY", "accZ", "gyroX", "gyroY", "gyroZ"]

SOURCE_MAP = {
    "acc_x_g": "accX",
    "acc_y_g": "accY",
    "acc_z_g": "accZ",
    "gyro_x_dps": "gyroX",
    "gyro_y_dps": "gyroY",
    "gyro_z_dps": "gyroZ",
}

# Clean output dir
if OUTPUT_DIR.exists():
    import shutil
    shutil.rmtree(OUTPUT_DIR)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

total = 0
for csv_path in sorted(DATA_DIR.glob("*.csv")):
    label = csv_path.name.split("_2026")[0]
    label_dir = OUTPUT_DIR / label
    label_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)
    df = df.rename(columns=SOURCE_MAP)

    count = 0
    for start in range(0, len(df) - WINDOW_SIZE + 1, STRIDE):
        window = df.iloc[start:start + WINDOW_SIZE][["accX", "accY", "accZ", "gyroX", "gyroY", "gyroZ"]].copy()
        window.insert(0, "timestamp", [i * SAMPLE_INTERVAL_MS for i in range(WINDOW_SIZE)])
        out_file = label_dir / f"{label}_{count:04d}.csv"
        window.to_csv(out_file, index=False)
        count += 1

    total += count
    print(f"{label}: {count} windows")

print(f"\nTotal: {total} windows saved to {OUTPUT_DIR}/")
print("Format: timestamp,accX,accY,accZ,gyroX,gyroY,gyroZ (50 rows @ 50Hz per file)")
