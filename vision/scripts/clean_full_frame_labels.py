"""
Removes full-frame 'basketball' label contamination (area >= 50% of image),
writing cleaned labels to a NEW dataset folder rather than modifying the
original in place. Images are copied unchanged; only label .txt files with
the bad line removed (or, rarely, made empty if that was the only label
for the whole image) go into the cleaned folder.

Usage:
    python scripts\clean_full_frame_labels.py
"""

import shutil
import re
from pathlib import Path

DATASET_DIR = Path(r"C:\Users\datbo\Court-Vision\vision\data\dataset")
CLEANED_DIR = Path(r"C:\Users\datbo\Court-Vision\vision\data\dataset_cleaned")
DATA_YAML = DATASET_DIR / "data.yaml"

FULL_FRAME_AREA_THRESHOLD = 0.50


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

    if CLEANED_DIR.exists():
        print(f"{CLEANED_DIR} already exists -- delete it first if you want a fresh run.")
        return

    total_removed = 0
    files_changed = 0
    files_emptied = 0

    for split in ["train", "valid", "test"]:
        src_images = DATASET_DIR / split / "images"
        src_labels = DATASET_DIR / split / "labels"
        if not src_labels.exists():
            continue

        dst_images = CLEANED_DIR / split / "images"
        dst_labels = CLEANED_DIR / split / "labels"
        dst_images.mkdir(parents=True, exist_ok=True)
        dst_labels.mkdir(parents=True, exist_ok=True)

        for label_file in sorted(src_labels.glob("*.txt")):
            lines = label_file.read_text(encoding="utf-8").strip().splitlines()
            kept_lines = []
            removed_here = 0

            for line in lines:
                parts = line.split()
                if not parts:
                    continue
                cls_id = int(parts[0])
                if cls_id == basketball_id:
                    w, h = float(parts[3]), float(parts[4])
                    if w * h >= FULL_FRAME_AREA_THRESHOLD:
                        removed_here += 1
                        continue
                kept_lines.append(line)

            if removed_here:
                total_removed += removed_here
                files_changed += 1
                if not kept_lines:
                    files_emptied += 1

            (dst_labels / label_file.name).write_text(
                "\n".join(kept_lines) + ("\n" if kept_lines else ""), encoding="utf-8"
            )

            # Copy the matching image unchanged
            for ext in [".jpg", ".png", ".jpeg"]:
                src_img = src_images / (label_file.stem + ext)
                if src_img.exists():
                    shutil.copy(src_img, dst_images / src_img.name)
                    break

    # Copy data.yaml over too, pointing at the same class list
    shutil.copy(DATA_YAML, CLEANED_DIR / "data.yaml")

    print(f"Done. Cleaned dataset written to: {CLEANED_DIR}")
    print(f"Full-frame labels removed: {total_removed}")
    print(f"Files changed:             {files_changed}")
    print(f"Files left with NO labels at all (image had only the bad box): {files_emptied}")
    if files_emptied:
        print("\nThose fully-emptied files are now background-only images (no ball/rim/")
        print("backboard). That's fine for training -- YOLO uses label-less images as")
        print("negative examples -- but worth knowing the count.")
    print(f"\nNext step: point your training config at {CLEANED_DIR} instead of the")
    print("original dataset folder and retrain, then compare precision/recall/mAP50")
    print("against your original run (backboard 0.93/0.71/0.885, basketball 0.75/0.50/0.516).")


if __name__ == "__main__":
    main()
