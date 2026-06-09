#!/usr/bin/env python3

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split


def main():
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent

    features_path = project_dir / "data" / "processed" / "imu_statistical_features.csv"
    results_dir = project_dir / "results"
    models_dir = project_dir / "models" / "saved_models"

    results_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(features_path)

    drop_columns = [
        "label",
        "label_id",
        "source_file",
        "window_start",
        "window_end",
    ]

    X = df.drop(columns=drop_columns)
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)
    labels = sorted(y.unique())

    cm = confusion_matrix(y_test, y_pred, labels=labels)

    model_path = models_dir / "random_forest_model.joblib"
    joblib.dump(model, model_path)

    metrics = {
        "model": "RandomForestClassifier",
        "features_file": str(features_path),
        "num_total_windows": int(len(df)),
        "num_train_windows": int(len(X_train)),
        "num_test_windows": int(len(X_test)),
        "accuracy": float(accuracy),
        "labels": labels,
        "classification_report": report,
        "model_path": str(model_path),
    }

    metrics_path = results_dir / "random_forest_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=4)

    cm_df = pd.DataFrame(cm, index=labels, columns=labels)
    cm_csv_path = results_dir / "random_forest_confusion_matrix.csv"
    cm_df.to_csv(cm_csv_path)

    plt.figure(figsize=(10, 8))
    plt.imshow(cm)
    plt.title("Random Forest Confusion Matrix")
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")
    plt.xticks(range(len(labels)), labels, rotation=45, ha="right")
    plt.yticks(range(len(labels)), labels)

    for i in range(len(labels)):
        for j in range(len(labels)):
            plt.text(j, i, cm[i, j], ha="center", va="center")

    plt.tight_layout()
    cm_png_path = results_dir / "random_forest_confusion_matrix.png"
    plt.savefig(cm_png_path, dpi=150)

    print("Random Forest training done.")
    print(f"Total windows: {len(df)}")
    print(f"Train windows: {len(X_train)}")
    print(f"Test windows: {len(X_test)}")
    print(f"Accuracy: {accuracy:.4f}")
    print()
    print("Saved files:")
    print(f"  {model_path}")
    print(f"  {metrics_path}")
    print(f"  {cm_csv_path}")
    print(f"  {cm_png_path}")


if __name__ == "__main__":
    main()
