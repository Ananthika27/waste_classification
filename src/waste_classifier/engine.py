"""Inference engines shared by the camera app and the web server.

An engine takes an RGB numpy image and returns (category probabilities over CATEGORIES, hint text).
"""
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from .cnn import get_device, load_checkpoint, make_eval_transform
from .config import (CATEGORIES, CLASS_TO_CATEGORY, MODELS_DIR, RESULTS_DIR, UNKNOWN_THRESHOLD_CNN,
                     WASTE4_MODEL_PATH, WASTE10_CLASSES)

CNN_PREFERENCE = ["convnext_tiny_waste10.pt", "mobilenet_v3_large_waste10.pt", "mobilenetv2_garbage10.pt"]


class SigLIPEngine:
    kind = "siglip"

    def __init__(self, device):
        from .vlm import SigLIP, Waste4Classifier
        self.vlm = SigLIP(device=device)
        self.head = Waste4Classifier.load(WASTE4_MODEL_PATH)
        self.threshold = self.head.threshold
        self.name = "SigLIP 2 + 4-category head"
        self.metrics_path = RESULTS_DIR / "metrics" / "waste4_siglip.json"

    def __call__(self, rgb: np.ndarray):
        emb = self.vlm.encode_images([Image.fromarray(rgb)])
        out = self.head.predict(emb)
        probs, c = out["probs"][0], out["concepts"][0]
        # Explain with the closest text concepts *within the predicted category*
        in_cat = np.where(self.head.concept_cat == int(np.argmax(probs)))[0]
        top = in_cat[np.argsort(c[in_cat])[::-1][:3]]
        share = c[top] / max(c[in_cat].sum(), 1e-9)
        self.last_concepts = [(self.head.concept_names[i], float(s)) for i, s in zip(top, share)]
        return probs, f"looks like: {self.head.concept_names[int(top[0])]}"


class CNNEngine:
    kind = "cnn"

    def __init__(self, device, path: Path):
        self.device = device
        self.model, self.classes, meta = load_checkpoint(path, device, classes=WASTE10_CLASSES,
                                                         return_meta=True)
        self.T, self.tf = meta["temperature"], make_eval_transform(meta["img_size"])
        self.threshold = meta["threshold"] or UNKNOWN_THRESHOLD_CNN
        self.name = f"{meta['arch']} ({path.name})"
        self.metrics_path = RESULTS_DIR / "metrics" / f"{path.stem}.json"

    @torch.no_grad()
    def __call__(self, rgb: np.ndarray):
        x = self.tf(Image.fromarray(rgb)).unsqueeze(0).to(self.device)
        p = torch.softmax(self.model(x) / self.T, 1)[0].cpu().numpy()
        cat = np.zeros(len(CATEGORIES))
        for i, c in enumerate(self.classes):
            cat[CATEGORIES.index(CLASS_TO_CATEGORY[c])] += p[i]
        top = np.argsort(p)[::-1][:3]
        self.last_concepts = [(self.classes[i], float(p[i])) for i in top]
        return cat, f"material: {self.classes[int(top[0])]}"


def load_engine(kind: str | None = None, model: Path | None = None, device: str | None = None):
    """kind: 'siglip', 'cnn' or None (siglip if its head is trained, otherwise the best CNN)."""
    device = device or get_device()
    kind = kind or ("siglip" if WASTE4_MODEL_PATH.exists() else "cnn")
    if kind == "siglip":
        return SigLIPEngine(device)
    path = model or next((MODELS_DIR / n for n in CNN_PREFERENCE if (MODELS_DIR / n).exists()), None)
    if path is None:
        raise SystemExit("No trained model found in models/. Train one first (see README).")
    return CNNEngine(device, path)


def engine_metrics(engine) -> dict:
    try:
        return json.loads(Path(engine.metrics_path).read_text())
    except (OSError, ValueError):
        return {}
