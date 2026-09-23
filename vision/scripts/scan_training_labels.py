"""
Scans YOLO label files for 'basketball' class boxes sitting suspiciously
close to the image border -- checking whether a training-label mistake
(e.g. from the Roboflow SAM3 auto-labeler) taught the model to associate
the frame's own corner/edge with "basketball", which would explain a
stable, high-confidence false positive that shows up at the same screen
position across completely different clips.

YOLO label format per line: <class_id> <x_center> <y_center> <width> <height>
all normalized 0-1. A box is "near the border" if any edge sits within
BORDER_MARGIN of the image boundary.

Usage:
    python scripts\scan_training_labels.py
"""

from pathlib import Path

DATASET_DIR = Path(r"C:\Users\datbo\Court-Vision\vision\data\dataset")
DATA_YAML = DATASET_DIR / "data.yaml"
BORDER_MARGIN = 0.03  # within 3% of any edge counts as "near the border"


def load_class_names():
    """Read class names from data.yaml (avoids hardcoding class index)."""
    import re
    text = DATA_YAML.read_text(encoding="utf-8")
    match = re.search(r"names:\s*\[(.*?)\]", text, re.DOTALL)
    if not match:
        raise RuntimeError(f"Couldn't parse class names from {DATA_YAML}")
    names = [n.strip().strip("'\"") for n in match.group(1).split(",")]
    return {i: name for i, name in enumerate(names)}


def is_near_border(x_center, y_center, w, h, margin=BORDER_MARGIN):
    x1, y1 = x_center - w / 2, y_center - h / 2
    x2, y2 = x_center + w / 2, y_center + h / 2
    return x1 < margin or y1 < margin or x2 > (1 - margin) or y2 > (1 - margin)


def main():
    class_names = load_class_names()
    basketball_id = next((i for i, n in class_names.items() if n == "basketball"), None)
    if basketball_id is None:
        print(f"No 'basketball' class in data.yaml. Classes found: {class_names}")
        return

    print(f"Classes: {class_names}")
    print(f"Scanning for 'basketball' (class {basketball_id}) labels within {BORDER_MARGIN*100:.0f}% of image border...\n")

    hits = 0
    total_basketball_labels = 0

    for split in ["train", "valid", "test"]:
        labels_dir = DATASET_DIR / split / "labels"
        if not labels_dir.exists():
            continue

        for label_file in sorted(labels_dir.glob("*.txt")):
            lines = label_file.read_text(encoding="utf-8").strip().splitlines()
            for line in lines:
                parts = line.split()
                if not parts:
                    continue
                cls_id = int(parts[0])
                if cls_id != basketball_id:
                    continue
                total_basketball_labels += 1
                x, y, w, h = map(float, parts[1:5])
                if is_near_border(x, y, w, h):
                    hits += 1
                    print(f"  BORDER LABEL  [{split}] {label_file.name}  "
                          f"center=({x:.3f},{y:.3f}) size=({w:.3f}x{h:.3f})")

    print(f"\n--- Summary ---")
    print(f"Total 'basketball' labels across dataset: {total_basketball_labels}")
    print(f"Labels sitting near the image border:      {hits}")
    if hits:
        print("\nThis strongly suggests at least one training example taught the model")
        print("to associate the frame border/corner with 'basketball'. Open the flagged")
        print("image(s) in Roboflow (or the matching image in data/dataset/<split>/images/)")
        print("to confirm, then delete/relabel and retrain.")
    else:
        print("\nNo border-adjacent training labels found -- the corner artifact likely")
        print("has a different cause (worth checking NMS settings or reviewing a few")
        print("training images near the border by eye instead).")


if __name__ == "__main__":
    main()
