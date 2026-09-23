"""
Fine-tune a pretrained YOLOv8n model on the CLEANED basketball/rim/backboard
dataset (with the 212 full-frame 'basketball' label contamination removed).

Usage:
    python scripts/train_v2.py
"""

import os
from ultralytics import YOLO

DATASET_YAML = os.path.join(os.path.dirname(__file__), "..", "data", "dataset_cleaned", "data.yaml")

def main():
    model = YOLO("yolov8n.pt")

    results = model.train(
        data=DATASET_YAML,
        epochs=50,
        imgsz=640,
        batch=4,
        name="basketball_v2",
        patience=10,
        workers=0,
        amp=False,
    )

    print("\nTraining complete.")
    print(f"Best weights saved to: {results.save_dir}/weights/best.pt")

if __name__ == "__main__":
    main()
