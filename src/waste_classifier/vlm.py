"""SigLIP 2 vision-language backbone: image/text embeddings and the 4-category waste classifier.

The classifier combines two heads on the same image embedding:
  * a linear probe trained on labelled photos (fine-grained classes -> category), and
  * zero-shot text concepts (CONCEPTS) that cover items with little or no training data.
Category probabilities are a weighted blend of the two, see Waste4Classifier.predict.
"""
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from .config import CONCEPTS, PROMPT_TEMPLATES, VLM_MODEL_ID


def siglip_transform(size: int = 224):
    """Same preprocessing as the SigLIP image processor: resize, scale to [-1, 1]."""
    return transforms.Compose([
        transforms.Resize((size, size), interpolation=transforms.InterpolationMode.BILINEAR),
        transforms.ToTensor(),
        transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5]),
    ])


def _as_tensor(out):
    """transformers may return a tensor or a ModelOutput from get_*_features."""
    if isinstance(out, torch.Tensor):
        return out
    return out.pooler_output if getattr(out, "pooler_output", None) is not None else out[0]


class SigLIP:
    def __init__(self, model_id: str = VLM_MODEL_ID, device: str = "cpu"):
        from transformers import AutoModel, AutoTokenizer
        self.model_id, self.device = model_id, device
        self.model = AutoModel.from_pretrained(model_id).to(device).eval()
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.transform = siglip_transform()
        self.logit_scale = float(self.model.logit_scale.exp())
        self.logit_bias = float(self.model.logit_bias)

    @torch.no_grad()
    def encode_pixels(self, pixel_values: torch.Tensor) -> torch.Tensor:
        emb = _as_tensor(self.model.get_image_features(pixel_values=pixel_values.to(self.device)))
        return F.normalize(emb.float(), dim=-1).cpu()

    def encode_images(self, images: list[Image.Image]) -> torch.Tensor:
        return self.encode_pixels(torch.stack([self.transform(im.convert("RGB")) for im in images]))

    @torch.no_grad()
    def encode_texts(self, texts: list[str]) -> torch.Tensor:
        tok = self.tokenizer([t.lower() for t in texts], padding="max_length", max_length=64,
                             truncation=True, return_tensors="pt").to(self.device)
        emb = _as_tensor(self.model.get_text_features(**tok))
        return F.normalize(emb.float(), dim=-1).cpu()

    def concept_embeddings(self, concepts: dict = CONCEPTS, templates=PROMPT_TEMPLATES):
        """One embedding per concept (average over prompt templates). Returns (names, categories, emb)."""
        names, cats, embs = [], [], []
        for cat, items in concepts.items():
            for c in items:
                e = self.encode_texts([t.format(c) for t in templates]).mean(0)
                names.append(c)
                cats.append(cat)
                embs.append(F.normalize(e, dim=0))
        return names, cats, torch.stack(embs)


class Waste4Classifier:
    """Image embedding -> probabilities over CATEGORIES (biodegradable, recyclable, non_recyclable, medical)."""

    def __init__(self, state: dict):
        self.state = state
        self.categories = state["categories"]
        self.concept_emb = state["concept_emb"]                    # (C, D)
        self.concept_cat = np.array([self.categories.index(c) for c in state["concept_cats"]])
        self.concept_names = state["concept_names"]
        self.zs_scale = state["zs_scale"]                          # softmax temperature for concepts
        self.probe_W, self.probe_b = state["probe_W"], state["probe_b"]  # (K, D), (K,)
        self.probe_classes = state["probe_classes"]
        self.probe_cat = np.array([self.categories.index(c) for c in state["probe_class_cats"]])
        self.w_zs = state["w_zeroshot"]                            # blend weight of zero-shot head
        self.threshold = state["threshold"]

    @staticmethod
    def _to_categories(p: np.ndarray, idx: np.ndarray, n: int) -> np.ndarray:
        out = np.zeros((p.shape[0], n))
        for k in range(n):
            out[:, k] = p[:, idx == k].sum(1)
        return out

    def zero_shot(self, emb: torch.Tensor):
        """Returns (category probs, concept probs)."""
        logits = (emb @ self.concept_emb.T).numpy() * self.zs_scale
        p = torch.softmax(torch.as_tensor(logits), 1).numpy()
        return self._to_categories(p, self.concept_cat, len(self.categories)), p

    def probe(self, emb: torch.Tensor):
        logits = emb.numpy() @ self.probe_W.T + self.probe_b
        p = torch.softmax(torch.as_tensor(logits), 1).numpy()
        return self._to_categories(p, self.probe_cat, len(self.categories)), p

    def predict(self, emb: torch.Tensor) -> dict:
        zs_cat, zs_concepts = self.zero_shot(emb)
        pr_cat, pr_classes = self.probe(emb)
        probs = self.w_zs * zs_cat + (1 - self.w_zs) * pr_cat
        return {"probs": probs, "zero_shot": zs_cat, "probe": pr_cat,
                "concepts": zs_concepts, "probe_classes": pr_classes}

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.state, path)

    @classmethod
    def load(cls, path: Path):
        return cls(torch.load(path, map_location="cpu", weights_only=False))
