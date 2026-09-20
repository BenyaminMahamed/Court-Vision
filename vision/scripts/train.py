"""
Fine-tune a pretrained YOLOv8n model on the labeled basketball/rim/backboard
dataset exported from Roboflow.

Usage:
    python scripts/train.py
"""

import os
from ultralytics import YOLO

DATASET_YAML = os.path.join(os.path.dirname(__file__), "..", "data", "dataset", "data.yaml")

def main():
    model = YOLO("yolov8n.pt")

    results = model.train(
        data=DATASET_YAML,
        epochs=50,
        imgsz=640,
        batch=4,        # drastically reduced to test for GPU memory issue
        name="basketball_v1",
        patience=10,
        workers=0,
        amp=False,
    )

    print("\nTraining complete.")
    print(f"Best weights saved to: {results.save_dir}/weights/best.pt")

if __name__ == "__main__":
    main()
