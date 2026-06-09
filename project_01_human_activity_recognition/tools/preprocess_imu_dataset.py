#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


SENSOR_COLUMNS = [
    "acc_x_g",
    "acc_y_g",
    "acc_z_g",
    "gyro_x_dps",
    "gyro_y_dps",
    "gyro_z_dps",
]


def parse_args():
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent

    parser = argparse.ArgumentParser(
        description="Preprocess IMU CSV files into sliding windows and statistical features."
    )

    parser.add_argument("--data-dir", default=str(project_dir / "data" / "raw" / "final"))
    parser.add_argument("--output-dir", default=str(project_dir / "data" / "processed"))
    parser.add_argument("--window-size", type=int, default=50)
    parser.add_argument("--stride", type=int, default=10)

    return parser.parse_args()


def extract_features(window):
    features = {}

    for column in SENSOR_COLUMNS:
        values = window[column].to_numpy(dtype=np.float32)

        features[f"{column}_mean"] = np.mean(values)
        features[f"{column}_std"] = np.std(values)
        features[f"{column}_var"] = np.var(values)
        features[f"{column}_min"] = np.min(values)
        features[f"{column}_max"] = np.max(values)
        features[f"{column}_rms"] = np.sqrt(np.mean(values ** 2))
        features[f"{column}_energy"] = np.sum(values ** 2)

    acc_mag = np.sqrt(
        window["acc_x_g"] ** 2 +
        window["acc_y_g"] ** 2 +
        window["acc_z_g"] ** 2
    )

    gyro_mag = np.sqrt(
        window["gyro_x_dps"] ** 2 +
        window["gyro_y_dps"] ** 2 +
        window["gyro_z_dps"] ** 2
    )

    features["acc_mag_mean"] = np.mean(acc_mag)
    features["acc_mag_std"] = np.std(acc_mag)
    features["acc_mag_max"] = np.max(acc_mag)
    features["gyro_mag_mean"] = np.mean(gyro_mag)
    features["gyro_mag_std"] = np.std(gyro_mag)
    features["gyro_mag_max"] = np.max(gyro_mag)

    return features


def main():
    args = parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(data_dir.glob("*.csv"))

    if not csv_files:
        print(f"No CSV files found in: {data_dir}")
        return 1

    labels = sorted({path.name.split("_2026")[0] for path in csv_files})
    label_to_id = {label: idx for idx, label in enumerate(labels)}

    raw_windows = []
    label_ids = []
    feature_rows = []

    windows_per_label = {label: 0 for label in labels}

    for csv_path in csv_files:
        df = pd.read_csv(csv_path)

        label = df["label"].iloc[0]
        label_id = label_to_id[label]

        for start in range(0, len(df) - args.window_size + 1, args.stride):
            end = start + args.window_size
            window = df.iloc[start:end]

            raw_window = window[SENSOR_COLUMNS].to_numpy(dtype=np.float32)
            raw_windows.append(raw_window)
            label_ids.append(label_id)

            features = extract_features(window)
            features["label"] = label
            features["label_id"] = label_id
            features["source_file"] = csv_path.name
            features["window_start"] = start
            features["window_end"] = end
            feature_rows.append(features)

            windows_per_label[label] += 1

    raw_windows = np.asarray(raw_windows, dtype=np.float32)
    label_ids = np.asarray(label_ids, dtype=np.int64)

    np.savez(
        output_dir / "imu_raw_windows.npz",
        X=raw_windows,
        y=label_ids,
        labels=np.asarray(labels),
    )

    features_df = pd.DataFrame(feature_rows)
    features_df.to_csv(output_dir / "imu_statistical_features.csv", index=False)

    with open(output_dir / "label_mapping.json", "w") as f:
        json.dump(label_to_id, f, indent=4)

    summary = {
        "window_size": args.window_size,
        "stride": args.stride,
        "sensor_columns": SENSOR_COLUMNS,
        "num_classes": len(labels),
        "total_windows": int(len(label_ids)),
        "windows_per_label": windows_per_label,
        "raw_windows_shape": list(raw_windows.shape),
    }

    with open(output_dir / "preprocessing_summary.json", "w") as f:
        json.dump(summary, f, indent=4)

    print("Preprocessing done.")
    print(f"Classes: {len(labels)}")
    print(f"Total windows: {len(label_ids)}")
    print(f"Raw windows shape: {raw_windows.shape}")
    print()
    print("Windows per label:")
    for label, count in windows_per_label.items():
        print(f"  {label}: {count}")

    print()
    print(f"Saved: {output_dir / 'imu_raw_windows.npz'}")
    print(f"Saved: {output_dir / 'imu_statistical_features.csv'}")
    print(f"Saved: {output_dir / 'label_mapping.json'}")
    print(f"Saved: {output_dir / 'preprocessing_summary.json'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
