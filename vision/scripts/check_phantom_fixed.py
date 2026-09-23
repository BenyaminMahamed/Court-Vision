"""
Checks all three known-affected frames for BOTH detections we found
visually: the real ball (further from the frame edge) and the phantom
(clipped right against the top edge, near y=0). Reports every basketball
detection per frame so we can see directly whether the edge-hugging
phantom is gone in v2, rather than just re-finding the real ball again.

Usage:
    python scripts\check_phantom_fixed.py
"""

import cv2
from pathlib import Path
from ultralytics import YOLO

WEIGHTS = r"C:\Users\datbo\Court-Vision\runs\detect\basketball_v2-3\weights\best.pt"
FRAMES = [
    r"C:\Users\datbo\Court-Vision\vision\data\frames\raw\ScreenRecording_03-10-2026 16-02-37_1_f00300.jpg",
    r"C:\Users\datbo\Court-Vision\vision\data\frames\raw\ScreenRecording_03-10-2026 16-02-37_1_f00305.jpg",
    r"C:\Users\datbo\Court-Vision\vision\data\frames\raw\ScreenRecording_04-08-2026 21-16-43_1_f00550.jpg",
]
CONF_THRESHOLD = 0.10  # very low, so we see the phantom even if its confidence dropped a lot

EDGE_PIXELS = 15  # a box within this many pixels of y=0 counts as "edge-clipped" (the phantom's signature)


def main():
    model = YOLO(WEIGHTS)
    basketball_idx = [i for i, name in model.names.items() if name == "basketball"][0]

    for path_str in FRAMES:
        path = Path(path_str)
        img = cv2.imread(str(path))
        if img is None:
            print(f"Couldn't read {path}")
            continue

        result = model.predict(source=img, imgsz=640, conf=CONF_THRESHOLD, verbose=False)[0]

        print(f"\n{path.name}")
        found_any = False
        for box in result.boxes:
            if int(box.cls[0]) != basketball_idx:
                continue
            found_any = True
            conf = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            edge_clipped = y1 <= EDGE_PIXELS
            tag = "PHANTOM (edge-clipped, y1<={})".format(EDGE_PIXELS) if edge_clipped else "real-ball-position"
            print(f"  conf={conf:.2f}  box=[{x1:.0f},{y1:.0f},{x2:.0f},{y2:.0f}]  -> {tag}")

        if not found_any:
            print("  no basketball detections at all")


if __name__ == "__main__":
    main()
