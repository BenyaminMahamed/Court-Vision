import os, glob, cv2

CLIPS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "clips")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "frames", "raw")
SAMPLE_EVERY = 5  # grab every 5th frame

os.makedirs(OUT_DIR, exist_ok=True)

clip_paths = sorted(glob.glob(os.path.join(CLIPS_DIR, "*.mov")) + glob.glob(os.path.join(CLIPS_DIR, "*.mp4")))

for clip_path in clip_paths:
    clip_name = os.path.splitext(os.path.basename(clip_path))[0]
    cap = cv2.VideoCapture(clip_path)
    idx = 0
    saved = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % SAMPLE_EVERY == 0:
            out_path = os.path.join(OUT_DIR, f"{clip_name}_f{idx:05d}.jpg")
            cv2.imwrite(out_path, frame)
            saved += 1
        idx += 1
    cap.release()
    print(f"{clip_name}: saved {saved} frames")

print(f"\nAll raw frames written to {OUT_DIR}")
