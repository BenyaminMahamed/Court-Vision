"""
Baseline test: run a pretrained COCO YOLOv8 model against sample frames
from each clip in data/clips/, to see what it detects out of the box
(person, sports ball) before we do any custom training.

Usage:
    python scripts/baseline_test.py

Expects clips in vision/data/clips/*.mov (or .mp4)
Writes annotated frames + a summary to vision/data/frames/baseline/
"""

import os
import glob
import cv2
from ultralytics import YOLO

CLIPS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "clips")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "frames", "baseline")
FRAMES_PER_CLIP = 5  # evenly spaced sample frames per clip

os.makedirs(OUT_DIR, exist_ok=True)

# yolov8n.pt auto-downloads on first run (~6MB)
model = YOLO("yolov8n.pt")

clip_paths = sorted(
    glob.glob(os.path.join(CLIPS_DIR, "*.mov")) +
    glob.glob(os.path.join(CLIPS_DIR, "*.mp4"))
)

if not clip_paths:
    print(f"No clips found in {CLIPS_DIR} -- check the folder and file extensions.")
    raise SystemExit(1)

summary = []

for clip_path in clip_paths:
    clip_name = os.path.splitext(os.path.basename(clip_path))[0]
    cap = cv2.VideoCapture(clip_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames <= 0:
        print(f"Could not read frame count for {clip_name}, skipping.")
        cap.release()
        continue

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

        detections = []
        for box in results.boxes:
            cls_name = model.names[int(box.cls)]
            conf = float(box.conf)
            detections.append(f"{cls_name}:{conf:.2f}")

        summary.append((clip_name, idx, detections))
        print(f"{clip_name} frame {idx}: {detections if detections else 'nothing detected'}")

    cap.release()

print(f"\nAnnotated frames written to {OUT_DIR}")
print(f"Total frames processed: {len(summary)}")
