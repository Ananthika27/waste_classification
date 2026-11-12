"""Real-time waste classification from a webcam.

Default engine: SigLIP 2 + 4-category head (biodegradable / recyclable / non-recyclable / medical).
Fallback engine: a CNN checkpoint (10 material classes) with --engine cnn.

    python scripts/realtime.py
    python scripts/realtime.py --camera 1 --mirror
    python scripts/realtime.py --engine cnn --model models/mobilenetv2_garbage10.pt

Keys:
  q / Esc  quit                 s      save snapshot
  m        box / full frame     space  pause
  1 2 3 4  save the current crop as Biodegradable / Recyclable / Non-recyclable / Medical
           (teaches the model your own items: re-run embed_dataset.py + train_waste4.py)
"""
import argparse
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np

from waste_classifier.cnn import get_device
from waste_classifier.config import CATEGORIES, CATEGORY_LABELS, RAW_DIR, RESULTS_DIR
from waste_classifier.engine import load_engine

CAPTURE_DIR = RAW_DIR / "user_captures"
COLORS = {  # BGR
    "biodegradable": (60, 180, 75),
    "recyclable": (230, 150, 20),
    "non_recyclable": (140, 140, 140),
    "medical": (40, 40, 230),
    "unknown": (0, 190, 255),
}


# ------------------------------------------------------------------ drawing
def roi_box(frame, frac):
    h, w = frame.shape[:2]
    side = int(min(h, w) * frac)
    x0, y0 = (w - side) // 2, (h - side) // 2
    return x0, y0, x0 + side, y0 + side


def draw_panel(frame, lines, bars, color):
    pad, lh, width = 12, 30, 400
    height = pad * 2 + lh * len(lines) + 26 * len(bars) + 6
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (10 + width, 10 + height), (25, 25, 25), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    cv2.rectangle(frame, (10, 10), (18, 10 + height), color, -1)
    y = 10 + pad + 22
    for i, (text, scale, col) in enumerate(lines):
        cv2.putText(frame, text, (30, y), cv2.FONT_HERSHEY_SIMPLEX, scale, col, 2 if i == 0 else 1, cv2.LINE_AA)
        y += lh
    for name, p, c in bars:
        cv2.putText(frame, name, (30, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1, cv2.LINE_AA)
        x0 = 170
        cv2.rectangle(frame, (x0, y - 12), (x0 + 170, y + 2), (70, 70, 70), -1)
        cv2.rectangle(frame, (x0, y - 12), (x0 + int(170 * p), y + 2), c, -1)
        cv2.putText(frame, f"{p * 100:4.0f}%", (x0 + 178, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1,
                    cv2.LINE_AA)
        y += 26


def flash(frame, text):
    h, w = frame.shape[:2]
    cv2.putText(frame, text, (20, h - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engine", choices=["siglip", "cnn"], help="default: siglip if trained, else cnn")
    ap.add_argument("--model", type=Path, help="CNN checkpoint for --engine cnn")
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--roi", type=float, default=0.65, help="box size as a fraction of the frame height")
    ap.add_argument("--full-frame", action="store_true")
    ap.add_argument("--threshold", type=float, help="confidence below this shows UNKNOWN")
    ap.add_argument("--smooth", type=float, default=0.35, help="weight of the newest frame (1 = no smoothing)")
    ap.add_argument("--mirror", action="store_true")
    args = ap.parse_args()

    device = get_device()
    engine = load_engine(args.engine, args.model, device)
    threshold = args.threshold or engine.threshold
    print(f"Engine: {engine.name} on {device} | UNKNOWN below {threshold:.2f}")

    backend = cv2.CAP_AVFOUNDATION if hasattr(cv2, "CAP_AVFOUNDATION") else cv2.CAP_ANY
    cap = cv2.VideoCapture(args.camera, backend)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    if not cap.isOpened():
        raise SystemExit("Could not open the camera. On macOS: System Settings > Privacy & Security > Camera, "
                         "allow your terminal / VS Code, then restart it.")

    full, paused = args.full_frame, False
    ema, times, message = None, deque(maxlen=30), ("", 0)
    window = "Waste Classifier  (q quit | 1-4 teach | s snapshot | m mode | space pause)"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    shown, crop_bgr, title = None, None, ""

    while True:
        if not paused:
            ok, frame = cap.read()
            if not ok:
                print("Camera stopped delivering frames.")
                break
            if args.mirror:
                frame = cv2.flip(frame, 1)
            x0, y0, x1, y1 = (0, 0, frame.shape[1], frame.shape[0]) if full else roi_box(frame, args.roi)
            crop_bgr = frame[y0:y1, x0:x1].copy()

            t = time.perf_counter()
            probs, hint = engine(cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB))
            infer_ms = (time.perf_counter() - t) * 1000
            ema = probs if ema is None else args.smooth * probs + (1 - args.smooth) * ema
            times.append(time.perf_counter())
            fps = (len(times) - 1) / (times[-1] - times[0]) if len(times) > 1 else 0

            k = int(np.argmax(ema))
            conf = float(ema[k])
            cat = CATEGORIES[k] if conf >= threshold else "unknown"
            title = CATEGORY_LABELS.get(cat, "UNKNOWN - check manually").upper()
            color = COLORS[cat]

            shown = frame.copy()
            if not full:
                cv2.rectangle(shown, (x0, y0), (x1, y1), color, 4)
            draw_panel(shown,
                       [(f"{title}  {conf * 100:.0f}%", 0.85, (255, 255, 255)),
                        (hint, 0.55, color),
                        (f"{fps:4.1f} FPS | {infer_ms:4.0f} ms | {engine.name}", 0.45, (190, 190, 190))],
                       [(CATEGORY_LABELS[c], float(ema[i]), COLORS[c]) for i, c in enumerate(CATEGORIES)],
                       color)
            if message[0] and time.time() - message[1] < 2.0:
                flash(shown, message[0])

        cv2.imshow(window, shown)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break
        if key == ord("s"):
            d = RESULTS_DIR / "snapshots"
            d.mkdir(parents=True, exist_ok=True)
            p = d / f"snapshot_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(str(p), shown)
            message = (f"Saved {p.name}", time.time())
        if key in (ord("1"), ord("2"), ord("3"), ord("4")) and crop_bgr is not None:
            cat = CATEGORIES[key - ord("1")]
            d = CAPTURE_DIR / cat
            d.mkdir(parents=True, exist_ok=True)
            p = d / f"{cat}_{time.strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 1000:03d}.jpg"
            cv2.imwrite(str(p), crop_bgr)
            n = len(list(d.glob("*.jpg")))
            message = (f"Taught: {CATEGORY_LABELS[cat]} ({n} photos)", time.time())
            print(f"Saved {p}")
        if key == ord("m"):
            full, ema = not full, None
        if key == ord(" "):
            paused = not paused
        if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
