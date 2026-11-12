"""Sanity check: libraries import, datasets are in place, compute device is available."""
import cv2
import sklearn
import skimage
import torch
import torchvision

from waste_classifier.cnn import get_device
from waste_classifier.config import DATASETS, DEFAULT_CNN_PATH
from waste_classifier.data import load_file_list

print(f"OpenCV {cv2.__version__} | scikit-learn {sklearn.__version__} | scikit-image {skimage.__version__}")
print(f"PyTorch {torch.__version__} | torchvision {torchvision.__version__} | device: {get_device()}")

for name, cfg in DATASETS.items():
    if not cfg["root"].exists():
        print(f"[missing] {name}: {cfg['root']}")
        continue
    files, labels, classes = load_file_list(name)
    print(f"[ok] {name}: {len(files)} images in {len(classes)} classes")

print(f"[{'ok' if DEFAULT_CNN_PATH.exists() else 'missing'}] model: {DEFAULT_CNN_PATH}")
