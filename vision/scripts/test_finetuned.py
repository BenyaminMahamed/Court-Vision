"""
Test the fine-tuned basketball/rim/backboard model against sample frames
from the original clips, to see real-world performance vs. the raw
COCO baseline test from earlier.

Usage:
    python scripts/test_finetuned.py
"""

import os
import glob
import cv2
from ultralytics import YOLO

CLIPS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "clips")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "frames", "finetuned_test")
WEIGHTS = os.path.join(os.path.dirname(__file__), "..", "..", "runs", "detect", "basketball_v1-10", "weights", "best.pt")
FRAMES_PER_CLIP = 8

os.makedirs(OUT_DIR, exist_ok=True)

model = YOLO(WEIGHTS)

clip_paths = sorted(
    glob.glob(os.path.join(CLIPS_DIR, "*.mov")) +
    glob.glob(os.path.join(CLIPS_DIR, "*.mp4"))
)

for clip_path in clip_paths:
    clip_name = os.path.splitext(os.path.basename(clip_path))[0]
    cap = cv2.VideoCapture(clip_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    frame_indices = [
        int(total_frames * (i + 1) / (FRAMES_PER_CLIP + 1))
        for i in range(FRAMES_PER_CLIP)
    ]

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            continue

        results = model(frame, verbose=False)[0]
        annotated = results.plot()

        out_path = os.path.join(OUT_DIR, f"{clip_name}_f{idx}.jpg")
        cv2.imwrite(out_path, annotated)

        detections = [f"{model.names[int(b.cls)]}:{float(b.conf):.2f}" for b in results.boxes]
        print(f"{clip_name} frame {idx}: {detections if detections else 'nothing detected'}")

    cap.release()

print(f"\nAnnotated frames written to {OUT_DIR}")
