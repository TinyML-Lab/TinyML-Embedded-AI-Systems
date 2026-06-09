#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../" && pwd)"
COLLECTOR="$ROOT_DIR/project_01_human_activity_recognition/tools/collect_imu_dataset.py"
OUTPUT_DIR="$ROOT_DIR/project_01_human_activity_recognition/data/raw/final"
SAMPLES=1200

collect_class() {
    local label="$1"
    local instruction="$2"

    echo
    echo "============================================================"
    echo "LABEL: $label"
    echo "$instruction"
    echo "Samples: $SAMPLES"
    echo "Important: keep sensor still for the first 6 seconds for calibration."
    echo "Press ENTER when you are ready..."
    read -r

    "$COLLECTOR" \
        --label "$label" \
        --samples "$SAMPLES" \
        --output-dir "$OUTPUT_DIR"
}

collect_class "idle" "Keep the board completely still on the table."
collect_class "shake" "Shake the board repeatedly with different speeds."
collect_class "left_tilt" "Tilt the board left, return, repeat slow/normal/fast."
collect_class "right_tilt" "Tilt the board right, return, repeat slow/normal/fast."
collect_class "forward_motion" "Move the board forward then back to start, repeat."
collect_class "backward_motion" "Move the board backward then back to start, repeat."
collect_class "circular_motion" "Move the board in circular motion, repeat both small and wide circles."
collect_class "fall_detection" "Simulate fall: hold board upright, drop/tilt quickly to horizontal on soft surface, repeat safely."
collect_class "gesture_recognition" "Use one fixed custom gesture, e.g. draw Z-shape in air, repeat consistently."

echo
echo "Dataset collection finished."
echo "Output directory: $OUTPUT_DIR"
