"""Build the combined, de-duplicated, split dataset used to train the CNN.

For every image in every source (config.SOURCES):
  1. map its folder to one of the 10 target classes
  2. drop exact duplicates (same file bytes, MD5)
  3. compute a perceptual hash (dHash); near-identical images share a group and always
     land in the same split, so the test set never contains a copy of a training image
  4. save a resized copy (shorter side = PREPARED_SHORT_SIDE) under data/interim/
Then a stratified 70/15/15 train/val/test split is made per class at group level, and
everything is written to data/processed/manifest.csv.

    python scripts/prepare_data.py
"""
import argparse
import hashlib
import os
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageOps

from waste_classifier.config import (INTERIM_DIR, MANIFEST_PATH, PREPARED_SHORT_SIDE, SEED, SOURCES,
                                     SPLIT_FRACTIONS)
from waste_classifier.data import list_images


HASH_SIZE = 16  # 16x16 = 256-bit dHash: far fewer accidental matches than the classic 8x8


def dhash(img: Image.Image, size: int = HASH_SIZE) -> str:
    """Difference hash: fingerprint robust to resizing / re-compression, as a hex string."""
    g = np.asarray(img.convert("L").resize((size + 1, size), Image.BILINEAR), dtype=np.int16)
    bits = (g[:, :-1] > g[:, 1:]).flatten()
    return np.packbits(bits).tobytes().hex()


def near_duplicate_groups(hashes: list[str], max_dist: int, chunk: int = 256) -> list[int]:
    """Union-find over all pairs with Hamming distance <= max_dist. Returns a group id per item."""
    h = np.stack([np.frombuffer(bytes.fromhex(x), dtype=np.uint64) for x in hashes])  # (N, words)
    parent = list(range(len(h)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for start in range(0, len(h), chunk):
        block = h[start:start + chunk]
        dist = np.bitwise_count(block[:, None, :] ^ h[None, :, :]).sum(-1)
        ii, jj = np.nonzero(dist <= max_dist)
        for i, j in zip(ii + start, jj):
            if i < j:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[rj] = ri
    return [find(i) for i in range(len(h))]


def process(job):
    src_path, out_path = job
    try:
        raw = Path(src_path).read_bytes()
        md5 = hashlib.md5(raw).hexdigest()
        img = ImageOps.exif_transpose(Image.open(src_path)).convert("RGB")
        w, h = img.size
        s = PREPARED_SHORT_SIDE / min(w, h)
        if s < 1:
            img = img.resize((round(w * s), round(h * s)), Image.BICUBIC)
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path, "JPEG", quality=93)
        return md5, dhash(img), w, h, None
    except Exception as e:
        return None, None, None, None, str(e)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--max-dist", type=int, default=20,
                    help="max Hamming distance (of 256 bits) for two images to count as near-duplicates")
    args = ap.parse_args()

    rows, jobs = [], []
    for source, (root, folder_map) in SOURCES.items():
        if not root.exists():
            print(f"[skip] {source}: {root} not found")
            continue
        for folder, label in folder_map.items():
            for p in list_images(root / folder):
                out = INTERIM_DIR / source / label / f"{Path(folder).name}__{Path(p).stem}.jpg"
                rows.append({"path": str(out.relative_to(INTERIM_DIR.parent.parent)),
                             "label": label, "source": source, "original": p})
                jobs.append((p, str(out)))
    print(f"Processing {len(jobs)} images with {args.workers} workers ...")

    with ProcessPoolExecutor(args.workers) as pool:
        results = list(pool.map(process, jobs, chunksize=64))
    for r, (md5, dh, w, h, err) in zip(rows, results):
        r.update(md5=md5, dhash=dh, width=w, height=h, error=err)

    df = pd.DataFrame(rows)
    bad = df[df.error.notna()]
    if len(bad):
        print(f"Unreadable images dropped: {len(bad)}")
    df = df[df.error.isna()].drop(columns="error")

    # Exact duplicates: keep the first occurrence; conflicting labels -> drop all copies
    conflict = df.groupby("md5").label.nunique() > 1
    n_before = len(df)
    df = df[~df.md5.isin(conflict[conflict].index)]
    df = df.drop_duplicates("md5")
    print(f"Exact duplicates removed: {n_before - len(df)} "
          f"({conflict.sum()} with conflicting labels)")

    # Near-duplicates: images whose dHashes differ in <= max_dist bits form one group
    df = df.reset_index(drop=True)
    df["group"] = near_duplicate_groups(df.dhash.tolist(), max_dist=args.max_dist)
    sizes = df.group.value_counts()
    print(f"Near-duplicate groups (hamming <= {args.max_dist}): {(sizes > 1).sum()} groups "
          f"covering {sizes[sizes > 1].sum()} images")

    # Split at group level, stratified by the group's majority class
    rng = random.Random(SEED)
    group_label = df.groupby("group").label.agg(lambda s: s.mode().iloc[0])
    assign = {}
    for label in sorted(group_label.unique()):
        groups = sorted(group_label[group_label == label].index)
        rng.shuffle(groups)
        n = len(groups)
        n_train = round(n * SPLIT_FRACTIONS["train"])
        n_val = round(n * SPLIT_FRACTIONS["val"])
        for i, gid in enumerate(groups):
            assign[gid] = "train" if i < n_train else "val" if i < n_train + n_val else "test"
    df["split"] = df.group.map(assign)

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(MANIFEST_PATH, index=False)
    print(f"\nSaved {len(df)} images to {MANIFEST_PATH}\n")
    print(pd.crosstab(df.label, df.split, margins=True).to_string())
    print()
    print(pd.crosstab(df.source, df.split, margins=True).to_string())


if __name__ == "__main__":
    main()
