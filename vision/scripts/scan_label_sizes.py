"""
Separates genuine ball-sized 'basketball' labels from apparent full-frame
labeling contamination -- a box covering most of the image is not a
basketball, and if this shows up in a large fraction of files it's almost
certainly a Roboflow auto-labeler fallback artifact that slipped through
unreviewed, not a real annotation.

Usage:
    python scripts\scan_label_sizes.py
"""

import re
from pathlib import Path
from collections import Counter

DATASET_DIR = Path(r"C:\Users\datbo\Court-Vision\vision\data\dataset")
DATA_YAML = DATASET_DIR / "data.yaml"

FULL_FRAME_AREA_THRESHOLD = 0.50   # box covering >50% of the image = almost certainly not a ball
PLAUSIBLE_BALL_AREA_MAX = 0.02     # a ball realistically covers well under 2% of frame area


def load_class_names():
    text = DATA_YAML.read_text(encoding="utf-8")
    match = re.search(r"names:\s*\[(.*?)\]", text, re.DOTALL)
    names = [n.strip().strip("'\"") for n in match.group(1).split(",")]
    return {i: name for i, name in enumerate(names)}


def main():
    class_names = load_class_names()
    basketball_id = next((i for i, n in class_names.items() if n == "basketball"), None)
    if basketball_id is None:
        print(f"No 'basketball' class in data.yaml. Classes found: {class_names}")
        return

    total = 0
    full_frame = 0
    plausible = 0
    other = 0
    files_with_full_frame = 0
    files_scanned = 0
    full_frame_examples = []

    for split in ["train", "valid", "test"]:
        labels_dir = DATASET_DIR / split / "labels"
        if not labels_dir.exists():
            continue

        for label_file in sorted(labels_dir.glob("*.txt")):
            files_scanned += 1
            has_full_frame_here = False
            lines = label_file.read_text(encoding="utf-8").strip().splitlines()
            for line in lines:
                parts = line.split()
                if not parts:
                    continue
                cls_id = int(parts[0])
                if cls_id != basketball_id:
                    continue
                total += 1
                w, h = float(parts[3]), float(parts[4])
                area = w * h
                if area >= FULL_FRAME_AREA_THRESHOLD:
                    full_frame += 1
                    has_full_frame_here = True
                    if len(full_frame_examples) < 5:
                        full_frame_examples.append((split, label_file.name, area))
                elif area <= PLAUSIBLE_BALL_AREA_MAX:
                    plausible += 1
                else:
                    other += 1
            if has_full_frame_here:
                files_with_full_frame += 1

    print(f"Classes: {class_names}\n")
    print(f"Label files scanned:                    {files_scanned}")
    print(f"Total 'basketball' labels:               {total}")
    print(f"  Full-frame contamination (area>={FULL_FRAME_AREA_THRESHOLD}):  {full_frame}")
    print(f"  Plausible ball-sized (area<={PLAUSIBLE_BALL_AREA_MAX}):    {plausible}")
    print(f"  Other (in between):                    {other}")
    print(f"\nFiles containing at least one full-frame 'basketball' label: {files_with_full_frame} / {files_scanned}")
    print(f"({100*files_with_full_frame/files_scanned:.1f}% of all label files affected)")

    if full_frame_examples:
        print("\nExample full-frame contaminated files:")
        for split, name, area in full_frame_examples:
            print(f"  [{split}] {name}  (box covers {area*100:.1f}% of image)")

    if files_with_full_frame > files_scanned * 0.1:
        print("\nThis is a widespread, systemic labeling defect -- not an isolated mistake.")
        print("Training on these would teach the model that a basketball fills the whole")
        print("frame in most images, which plausibly explains weak precision/recall on")
        print("its own, separate from the small corner-artifact false positive.")


if __name__ == "__main__":
    main()
