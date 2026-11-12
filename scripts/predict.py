"""Classify one or more images with a trained CNN checkpoint.

Uses the checkpoint's calibrated temperature and its validation-chosen "unknown" threshold
unless --threshold is given.

    python scripts/predict.py samples/coconut_husks.png
    python scripts/predict.py img1.jpg img2.jpg --model models/convnext_tiny_waste10.pt --threshold 0.7
"""
import argparse
from pathlib import Path

import torch
from PIL import Image

from waste_classifier.cnn import get_device, load_checkpoint, make_eval_transform
from waste_classifier.config import (CLASS_TO_BIN, DEFAULT_CNN_PATH, UNKNOWN_THRESHOLD_CNN,
                                     WASTE10_CLASSES)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+", type=Path)
    ap.add_argument("--model", type=Path, default=DEFAULT_CNN_PATH)
    ap.add_argument("--threshold", type=float, help="below this confidence the result is UNKNOWN")
    ap.add_argument("--top-k", type=int, default=3)
    args = ap.parse_args()

    device = get_device()
    # Legacy checkpoints have no class names stored; fall back to the training class order.
    model, classes, meta = load_checkpoint(args.model, device, classes=WASTE10_CLASSES, return_meta=True)
    T = meta["temperature"]
    threshold = args.threshold or meta["threshold"] or UNKNOWN_THRESHOLD_CNN
    tf = make_eval_transform(meta["img_size"])
    print(f"Model: {args.model.name} ({meta['arch']}) | temperature {T:.2f} | threshold {threshold}")

    for path in args.images:
        x = tf(Image.open(path).convert("RGB")).unsqueeze(0).to(device)
        with torch.no_grad():
            probs = torch.softmax(model(x) / T, dim=1)[0].cpu()
        top = probs.topk(args.top_k)

        print(f"\n{path}")
        for p, i in zip(top.values, top.indices):
            print(f"  {classes[i]:12s} {p.item() * 100:5.1f}%")
        if top.values[0].item() < threshold:
            print("Result: UNKNOWN (not confident enough, send for manual sorting)")
        else:
            label = classes[top.indices[0]]
            print(f"Result: {label.upper()}  ->  {CLASS_TO_BIN[label]} bin")


if __name__ == "__main__":
    main()
