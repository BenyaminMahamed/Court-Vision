"""
Scans a wide set of frames at a low confidence threshold to relocate exactly
which frame(s) trigger the recurring top-left false-positive basketball
detection. Once found, point ab_test_letterbox.py's FRAMES_DIR at the
fp_candidates folder this script creates to run the actual A/B comparison.

Usage:
    python scripts\scan_false_positives.py
"""

import shutil
import cv2
from pathlib import Path
from ultralytics import YOLO

WEIGHTS = r"C:\Users\datbo\Court-Vision\runs\detect\basketball_v2-3\weights\best.pt"
SCAN_DIR = Path(r"C:\Users\datbo\Court-Vision\vision\data\frames\raw")
CANDIDATES_DIR = Path(r"C:\Users\datbo\Court-Vision\vision\data\frames\fp_candidates")
CONF_THRESHOLD = 0.15  # deliberately very low -- we want to catch the FP even if
                        # its confidence varies frame to frame, not just at 0.55-0.66

# Slightly wider than the AB script's default, to be safe while relocating.
FP_REGION_X_FRAC = 0.25
FP_REGION_Y_FRAC = 0.25


def is_top_left(box_xyxy, img_w, img_h):
    x1, y1, x2, y2 = box_xyxy
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    return cx < img_w * FP_REGION_X_FRAC and cy < img_h * FP_REGION_Y_FRAC


def main():
    model = YOLO(WEIGHTS)
    basketball_idx = [i for i, name in model.names.items() if name == "basketball"][0]

    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)

    frame_paths = sorted(SCAN_DIR.glob("*.jpg")) + sorted(SCAN_DIR.glob("*.png"))
    if not frame_paths:
        print(f"No frames found in {SCAN_DIR}")
        return

    print(f"Scanning {len(frame_paths)} frames from {SCAN_DIR} at conf >= {CONF_THRESHOLD}\n")

    found = 0
    for path in frame_paths:
        img = cv2.imread(str(path))
        if img is None:
            continue
        h, w = img.shape[:2]

        result = model.predict(source=img, imgsz=640, conf=CONF_THRESHOLD, verbose=False)[0]

        for box in result.boxes:
            if int(box.cls[0]) != basketball_idx:
                continue
            conf = float(box.conf[0])
            xyxy = box.xyxy[0].tolist()
            if is_top_left(xyxy, w, h):
                found += 1
                print(f"  FOUND  {path.name}  conf={conf:.2f}  box={[round(v) for v in xyxy]}")
                shutil.copy(path, CANDIDATES_DIR / path.name)
                annotated = result.plot()
                cv2.imwrite(str(CANDIDATES_DIR / f"annotated_{path.name}"), annotated)
                break  # one flag per frame is enough to relocate it

    print(f"\nDone. {found} candidate frame(s) found out of {len(frame_paths)} scanned.")
    print(f"Copied to: {CANDIDATES_DIR}")
    if found:
        print("\nNext step: point ab_test_letterbox.py's FRAMES_DIR at fp_candidates and re-run it.")
    else:
        print("\nNo hits at this threshold/region in this folder. Consider lowering CONF_THRESHOLD")
        print("further, widening FP_REGION_X_FRAC/Y_FRAC, or scanning a different clip's frames.")


if __name__ == "__main__":
    main()
