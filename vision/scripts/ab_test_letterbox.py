"""
A/B test: does letterbox padding cause the recurring false-positive
basketball detection?

Condition A (letterbox): the frame is passed to the model as-is. Ultralytics
applies its own default letterbox padding internally to reach 640x640.

Condition B (stretched): we pre-resize the frame to exactly 640x640 with a
plain stretch (no padding) before handing it to the model, bypassing the
internal letterbox step entirely.

If the false positive disappears in Condition B but not A, that's strong
confirmation of the letterbox theory. If it persists in both, letterbox
padding isn't the (sole) cause.

Usage:
    python scripts\ab_test_letterbox.py
"""

import cv2
from pathlib import Path
from ultralytics import YOLO

WEIGHTS = r"C:\Users\datbo\Court-Vision\runs\detect\basketball_v2-3\weights\best.pt"
FRAMES_DIR = Path(r"C:\Users\datbo\Court-Vision\vision\data\frames\finetuned_test")
OUTPUT_DIR = Path(r"C:\Users\datbo\Court-Vision\vision\data\frames\ab_test_results")
CONF_THRESHOLD = 0.3  # deliberately low so we SEE the false positive if it's still there,
                       # rather than filtering it out before we can compare

# Roughly where the known false positive has shown up -- top-left corner region.
# Adjust these fractions if your own observations put it somewhere slightly different.
FP_REGION_X_FRAC = 0.20
FP_REGION_Y_FRAC = 0.20


def is_top_left(box_xyxy, img_w, img_h):
    x1, y1, x2, y2 = box_xyxy
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    return cx < img_w * FP_REGION_X_FRAC and cy < img_h * FP_REGION_Y_FRAC


def basketball_detections(result, model):
    """Yield (confidence, box_xyxy) for every 'basketball' class detection."""
    basketball_idx = [i for i, name in model.names.items() if name == "basketball"]
    if not basketball_idx:
        raise RuntimeError(f"No 'basketball' class found in model.names: {model.names}")
    basketball_idx = basketball_idx[0]

    for box in result.boxes:
        if int(box.cls[0]) == basketball_idx:
            yield float(box.conf[0]), box.xyxy[0].tolist()


def main():
    model = YOLO(WEIGHTS)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    frame_paths = sorted(FRAMES_DIR.glob("*.jpg")) + sorted(FRAMES_DIR.glob("*.png"))
    if not frame_paths:
        print(f"No frames found in {FRAMES_DIR}")
        return

    print(f"Testing {len(frame_paths)} frames from {FRAMES_DIR}\n")
    print(f"{'frame':<55} {'letterbox FP':<14} {'stretched FP':<14} {'lb conf':<10} {'str conf':<10}")
    print("-" * 105)

    summary = {"lb_fp": 0, "str_fp": 0, "both": 0, "neither": 0, "lb_only": 0, "str_only": 0}

    for path in frame_paths:
        img = cv2.imread(str(path))
        if img is None:
            print(f"  (skipped, couldn't read) {path.name}")
            continue
        h, w = img.shape[:2]

        # --- Condition A: letterbox (default ultralytics behavior) ---
        result_lb = model.predict(source=img, imgsz=640, conf=CONF_THRESHOLD, verbose=False)[0]
        lb_dets = list(basketball_detections(result_lb, model))
        lb_fp = [d for d in lb_dets if is_top_left(d[1], w, h)]

        # --- Condition B: pre-stretched to 640x640, no padding ---
        stretched = cv2.resize(img, (640, 640), interpolation=cv2.INTER_LINEAR)
        result_str = model.predict(source=stretched, imgsz=640, conf=CONF_THRESHOLD, verbose=False)[0]
        str_dets = list(basketball_detections(result_str, model))
        str_fp = [d for d in str_dets if is_top_left(d[1], 640, 640)]

        lb_fp_conf = f"{max(d[0] for d in lb_fp):.2f}" if lb_fp else "-"
        str_fp_conf = f"{max(d[0] for d in str_fp):.2f}" if str_fp else "-"

        print(f"{path.name:<55} {'YES' if lb_fp else 'no':<14} {'YES' if str_fp else 'no':<14} {lb_fp_conf:<10} {str_fp_conf:<10}")

        if lb_fp:
            summary["lb_fp"] += 1
        if str_fp:
            summary["str_fp"] += 1
        if lb_fp and str_fp:
            summary["both"] += 1
        elif lb_fp and not str_fp:
            summary["lb_only"] += 1
        elif str_fp and not lb_fp:
            summary["str_only"] += 1
        else:
            summary["neither"] += 1

        # Save annotated versions side-by-side for visual spot-checking
        annotated_lb = result_lb.plot()
        annotated_str = result_str.plot()
        combined = cv2.hconcat([annotated_lb, cv2.resize(annotated_str, (annotated_lb.shape[1], annotated_lb.shape[0]))])
        cv2.imwrite(str(OUTPUT_DIR / f"compare_{path.stem}.jpg"), combined)

    print("\n--- Summary ---")
    print(f"Total frames tested:            {len(frame_paths)}")
    print(f"False positive under letterbox: {summary['lb_fp']}")
    print(f"False positive under stretched: {summary['str_fp']}")
    print(f"  Both conditions:              {summary['both']}")
    print(f"  Letterbox only (theory HOLDS for these): {summary['lb_only']}")
    print(f"  Stretched only (unexpected):  {summary['str_only']}")
    print(f"  Neither:                      {summary['neither']}")
    print(f"\nAnnotated side-by-side comparisons saved to: {OUTPUT_DIR}")
    print("(left = letterbox condition, right = stretched condition)")


if __name__ == "__main__":
    main()
