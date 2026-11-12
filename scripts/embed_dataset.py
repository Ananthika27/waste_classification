"""Compute SigLIP 2 image embeddings for the whole dataset (+ medical images) once.

Writes data/processed/siglip_embeddings.npz with: emb (float16), label, category, source, split, path.
Medical images from Wikimedia Commons get a stratified 50/20/30 train/val/test split; drawings,
diagrams and documents are filtered out with a zero-shot check.

    python scripts/embed_dataset.py
"""
import argparse
import random

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from waste_classifier.cnn import ImageDataset, get_device
from waste_classifier.config import (CATEGORIES, CLASS_TO_CATEGORY, MANIFEST_PATH, MEDICAL_DIR, PROCESSED_DIR,
                                     PROJECT_ROOT, RAW_DIR, SEED)
from waste_classifier.data import list_images
from waste_classifier.vlm import SigLIP

OUT = PROCESSED_DIR / "siglip_embeddings.npz"
CAPTURE_DIR = RAW_DIR / "user_captures"


def medical_frame():
    rows = []
    for sub in sorted(p for p in MEDICAL_DIR.iterdir() if p.is_dir()):
        for f in list_images(sub):
            rows.append({"path": str(f), "label": "medical", "subtype": sub.name, "source": "medical_commons"})
    df = pd.DataFrame(rows)
    rng = random.Random(SEED)
    df["split"] = ""
    for sub, g in df.groupby("subtype"):
        idx = list(g.index)
        rng.shuffle(idx)
        n = len(idx)
        a, b = round(n * 0.5), round(n * 0.7)
        df.loc[idx[:a], "split"] = "train"
        df.loc[idx[a:b], "split"] = "val"
        df.loc[idx[b:], "split"] = "test"
    return df


def user_frame():
    rows = []
    if CAPTURE_DIR.exists():
        rng = random.Random(SEED)
        for cat in CATEGORIES:
            files = list_images(CAPTURE_DIR / cat) if (CAPTURE_DIR / cat).exists() else []
            rng.shuffle(files)
            n_train = round(len(files) * 0.8)
            for i, f in enumerate(files):
                rows.append({"path": f, "label": f"user_{cat}", "subtype": f"user_{cat}", "category": cat,
                             "source": "user_captures", "split": "train" if i < n_train else "val"})
    return pd.DataFrame(rows, columns=["path", "label", "subtype", "category", "source", "split"])


def embed(vlm, files, batch_size, workers):
    dl = DataLoader(ImageDataset(files, [0] * len(files), vlm.transform),
                    batch_size=batch_size, num_workers=workers)
    out = []
    for i, (x, _) in enumerate(dl):
        out.append(vlm.encode_pixels(x))
        if i % 20 == 0:
            print(f"  {i * batch_size}/{len(files)}", flush=True)
    return torch.cat(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    device = get_device()
    vlm = SigLIP(device=device)
    print(f"Model {vlm.model_id} on {device}")

    df = pd.read_csv(MANIFEST_PATH)[["path", "label", "source", "split"]]
    df["path"] = df.path.map(lambda p: str(PROJECT_ROOT / p))
    df["subtype"] = df.label
    if MEDICAL_DIR.exists():
        med = medical_frame()
        # Drop drawings / diagrams / documents from the web-sourced medical images
        emb_med = embed(vlm, med.path.tolist(), args.batch_size, args.workers)
        checks = vlm.encode_texts(["a photo of a real object.",
                                   "a drawing, diagram, illustration, icon or logo.",
                                   "a scanned document, chart or screenshot with text."])
        p = torch.softmax(emb_med @ checks.T * vlm.logit_scale, 1)[:, 0].numpy()
        keep = p > 0.5
        print(f"Medical images: {len(med)} downloaded, {keep.sum()} kept as photos")
        med, emb_med = med[keep].reset_index(drop=True), emb_med[keep]
        print(pd.crosstab(med.subtype, med.split).to_string())
    else:
        med, emb_med = pd.DataFrame(columns=list(df.columns)), torch.zeros(0, 768)

    # Photos taught in the real-time app (keys 1-4): 80 % train, 20 % val
    user = user_frame()
    if len(user):
        print(f"User captures: {len(user)}\n" + pd.crosstab(user.category, user.split).to_string())

    print(f"Embedding {len(df) + len(user)} dataset images ...")
    emb = embed(vlm, df.path.tolist() + user.path.tolist(), args.batch_size, args.workers)

    df["category"] = df.label.map(CLASS_TO_CATEGORY)
    med["category"] = "medical"
    all_df = pd.concat([df, user, med], ignore_index=True)
    all_emb = torch.cat([emb, emb_med]).numpy().astype(np.float16)
    np.savez_compressed(OUT, emb=all_emb, **{c: np.array(all_df[c].astype(str).tolist(), dtype=str) for c in
                                             ["path", "label", "subtype", "category", "source", "split"]})
    print(f"Saved {all_emb.shape} to {OUT}")


if __name__ == "__main__":
    main()
