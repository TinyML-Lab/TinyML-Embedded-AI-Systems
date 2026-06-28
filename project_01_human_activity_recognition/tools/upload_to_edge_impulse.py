#!/usr/bin/env python3
"""Upload per-window CSV files to Edge Impulse, one label at a time."""

import os
import sys
from pathlib import Path

from edgeimpulse.experimental.data import upload_directory

DATA_DIR = Path("data/edge_impulse_windows")

if not os.environ.get("EI_API_KEY"):
    print("ERROR: Set EI_API_KEY environment variable first:")
    print("  export EI_API_KEY='ei-your-key-here'")
    sys.exit(1)

labels = sorted([d.name for d in DATA_DIR.iterdir() if d.is_dir()])
print(f"Found {len(labels)} labels: {labels}\n")

for label in labels:
    label_dir = DATA_DIR / label
    n_files = len(list(label_dir.glob("*.csv")))
    print(f"Uploading '{label}' ({n_files} files)...")

    resp = upload_directory(
        directory=str(label_dir),
        category="training",
        label=label,
        show_progress=True,
        allow_duplicates=True,
    )
    print(f"  -> {resp}\n")

print("Done! Next steps in EI Studio:")
print("  1. Dashboard -> Rebalance data (80/20 train/test)")
print("  2. Create impulse: Input = Time series (6 axes) + Spectral features + Classifier")
print("  3. Set sampling frequency to 50 Hz")
print("  4. Train -> Deploy -> C++ Library")
