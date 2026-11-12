"""Extract hand-crafted features for every image in a dataset and save them as CSV.

Replaces build_dataset.py / build_dataset12.py.

    python scripts/build_features.py --dataset trashnet
    python scripts/build_features.py --dataset garbage10
"""
import argparse
from pathlib import Path

import cv2
import pandas as pd

from waste_classifier.config import DATASETS, PROCESSED_DIR
from waste_classifier.data import load_file_list
from waste_classifier.features import extract_features


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", choices=list(DATASETS), required=True)
    ap.add_argument("--out", type=Path, help="output CSV (default: data/processed/features_<dataset>.csv)")
    args = ap.parse_args()
    out = args.out or PROCESSED_DIR / f"features_{args.dataset}.csv"

    files, labels, classes = load_file_list(args.dataset)
    print(f"{args.dataset}: {len(files)} images, {len(classes)} classes")

    rows = []
    for i, (path, label) in enumerate(zip(files, labels), 1):
        img = cv2.imread(path)
        if img is None:
            print("Unreadable, skipped:", path)
            continue
        try:
            rows.append(list(extract_features(img)) + [label])
        except Exception as e:  # segmentation can fail on odd images
            print("Skipped", path, "-", e)
        if i % 500 == 0:
            print(f"  {i}/{len(files)}")

    df = pd.DataFrame(rows)
    df = df.rename(columns={df.columns[-1]: "label"})
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Saved {len(df)} rows to {out}")
    print(df["label"].value_counts())


if __name__ == "__main__":
    main()
