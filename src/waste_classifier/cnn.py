"""CNN models, transforms, device selection and checkpoint I/O."""
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import Dataset
from torchvision import models, transforms

from .config import CNN_IMAGE_SIZE, IMAGENET_MEAN, IMAGENET_STD

# name -> (constructor, default pretrained weights)
ARCHS = {
    "mobilenet_v2":       (models.mobilenet_v2,       models.MobileNet_V2_Weights.DEFAULT),
    "mobilenet_v3_large": (models.mobilenet_v3_large, models.MobileNet_V3_Large_Weights.DEFAULT),
    "efficientnet_b0":    (models.efficientnet_b0,    models.EfficientNet_B0_Weights.DEFAULT),
    "efficientnet_v2_s":  (models.efficientnet_v2_s,  models.EfficientNet_V2_S_Weights.DEFAULT),
    "convnext_tiny":      (models.convnext_tiny,      models.ConvNeXt_Tiny_Weights.DEFAULT),
}


# ---------------------------------------------------------------- transforms
def make_train_transform(size: int = CNN_IMAGE_SIZE):
    return transforms.Compose([
        transforms.RandomResizedCrop(size, scale=(0.6, 1.0), ratio=(0.75, 1.33)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.TrivialAugmentWide(),
        transforms.ColorJitter(0.2, 0.2, 0.2, 0.02),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        transforms.RandomErasing(p=0.25, scale=(0.02, 0.15)),
    ])


def make_eval_transform(size: int = CNN_IMAGE_SIZE):
    return transforms.Compose([
        transforms.Resize((size, size)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


# Kept for backwards compatibility with the original MobileNetV2 recipe
train_transform = transforms.Compose([
    transforms.Resize((CNN_IMAGE_SIZE, CNN_IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ToTensor(), transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)])
eval_transform = make_eval_transform()


# ---------------------------------------------------------------- models
def get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def build_model(num_classes: int, arch: str = "mobilenet_v2", pretrained: bool = True) -> nn.Module:
    """Pre-trained backbone with the final Linear layer replaced for `num_classes`."""
    if arch not in ARCHS:
        raise ValueError(f"Unknown arch '{arch}'. Choose from {list(ARCHS)}")
    ctor, weights = ARCHS[arch]
    model = ctor(weights=weights if pretrained else None)
    head = model.classifier
    idx = max(i for i, m in enumerate(head) if isinstance(m, nn.Linear))
    head[idx] = nn.Linear(head[idx].in_features, num_classes)
    return model


def head_parameters(model: nn.Module):
    return model.classifier.parameters()


def backbone_parameters(model: nn.Module):
    head_ids = {id(p) for p in model.classifier.parameters()}
    return [p for p in model.parameters() if id(p) not in head_ids]


# ---------------------------------------------------------------- data
class ImageDataset(Dataset):
    def __init__(self, files, labels, transform):
        self.files, self.labels, self.transform = list(files), list(labels), transform

    def __len__(self):
        return len(self.files)

    def __getitem__(self, i):
        img = Image.open(self.files[i]).convert("RGB")
        return self.transform(img), self.labels[i]


# ---------------------------------------------------------------- checkpoints
def save_checkpoint(model: nn.Module, classes: list[str], path: Path, arch: str = "mobilenet_v2",
                    img_size: int = CNN_IMAGE_SIZE, temperature: float = 1.0,
                    threshold: float | None = None, extra: dict | None = None) -> None:
    """Save weights plus everything inference needs (classes, arch, input size, calibration)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"arch": arch, "classes": classes, "img_size": img_size,
                "temperature": temperature, "threshold": threshold,
                "extra": extra or {}, "state_dict": model.state_dict()}, path)


def load_checkpoint(path: Path, device: str, classes: list[str] | None = None,
                    return_meta: bool = False):
    """Load a checkpoint. Returns (model in eval mode, classes[, meta]).

    Also accepts the original format (a bare MobileNetV2 state_dict); then `classes` must be given.
    """
    ckpt = torch.load(path, map_location="cpu")
    if isinstance(ckpt, dict) and "state_dict" in ckpt:
        classes, state = ckpt["classes"], ckpt["state_dict"]
        meta = {k: v for k, v in ckpt.items() if k != "state_dict"}
    else:
        if classes is None:
            raise ValueError("Legacy checkpoint without class names: pass `classes`.")
        state, meta = ckpt, {}
    meta.setdefault("arch", "mobilenet_v2")
    meta.setdefault("img_size", CNN_IMAGE_SIZE)
    meta.setdefault("temperature", 1.0)
    meta.setdefault("threshold", None)
    meta["classes"] = classes

    model = build_model(len(classes), arch=meta["arch"], pretrained=False)
    model.load_state_dict(state)
    model = model.to(device).eval()
    return (model, classes, meta) if return_meta else (model, classes)
