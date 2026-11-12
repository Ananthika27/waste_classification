"""Evaluate any trained checkpoint on a split of the prepared dataset, broken down by source.

    python scripts/evaluate.py --model models/convnext_tiny_waste10.pt
    python scripts/evaluate.py --model models/mobilenetv2_garbage10.pt --source realwaste
"""
import argparse
from pathlib import Path

import pandas as pd
import torch
from sklearn.metrics import accuracy_score, classification_report, f1_score
from torch.utils.data import DataLoader

from waste_classifier.cnn import ImageDataset, get_device, load_checkpoint, make_eval_transform
from waste_classifier.config import DEFAULT_CNN_PATH, MANIFEST_PATH, PROJECT_ROOT, WASTE10_CLASSES


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", type=Path, default=DEFAULT_CNN_PATH)
    ap.add_argument("--split", choices=["train", "val", "test"], default="test")
    ap.add_argument("--source", help="only evaluate images from this source (e.g. realwaste)")
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    device = get_device()
    model, classes, meta = load_checkpoint(args.model, device, classes=WASTE10_CLASSES, return_meta=True)
    df = pd.read_csv(MANIFEST_PATH)
    df = df[df.split == args.split]
    if args.source:
        df = df[df.source == args.source]
    df = df.reset_index(drop=True)
    y = df.label.map(classes.index).values

    dl = DataLoader(ImageDataset([str(PROJECT_ROOT / p) for p in df.path], y,
                                 make_eval_transform(meta["img_size"])),
                    batch_size=args.batch_size, num_workers=args.workers)
    preds, confs = [], []
    with torch.no_grad():
        for x, _ in dl:
            p = torch.softmax(model(x.to(device)) / meta["temperature"], 1).cpu()
            c, i = p.max(1)
            preds += i.tolist()
            confs += c.tolist()
    df["pred"] = [classes[i] for i in preds]
    df["conf"] = confs

    print(f"Model: {args.model.name} ({meta['arch']}) | split: {args.split} | images: {len(df)}")
    print(f"Accuracy: {accuracy_score(y, preds):.4f} | macro-F1: {f1_score(y, preds, average='macro'):.4f}")
    by_src = df.assign(ok=df.label == df.pred).groupby("source").ok.agg(["mean", "size"])
    print("\nPer source:\n" + by_src.rename(columns={"mean": "accuracy", "size": "images"}).round(4).to_string())
    present = sorted(set(y) | set(preds))
    print("\n" + classification_report(y, preds, labels=present,
                                       target_names=[classes[i] for i in present], digits=3, zero_division=0))


if __name__ == "__main__":
    main()
