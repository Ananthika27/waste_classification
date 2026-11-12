"""Dataset discovery: turn a dataset name into (file paths, labels)."""
import os
import random
from pathlib import Path

from .config import DATASETS, IMAGE_EXTS, SEED


def list_images(folder: Path) -> list[str]:
    """All image files in a folder, sorted so results are reproducible on any machine."""
    return sorted(os.path.join(folder, f) for f in os.listdir(folder)
                  if f.lower().endswith(IMAGE_EXTS))


def load_file_list(dataset: str, seed: int = SEED) -> tuple[list[str], list[str], list[str]]:
    """Return (files, labels, classes) for a dataset defined in config.DATASETS.

    Folders that map to the same class are merged; if the dataset has a
    per-class cap, a seeded random subset is taken.
    """
    if dataset not in DATASETS:
        raise ValueError(f"Unknown dataset '{dataset}'. Choose from {list(DATASETS)}")
    cfg = DATASETS[dataset]
    rng = random.Random(seed)
    classes = sorted(cfg["class_map"])

    files, labels = [], []
    for label in classes:
        paths = []
        for folder in cfg["class_map"][label]:
            paths += list_images(cfg["root"] / folder)
        if cfg["max_per_class"]:
            rng.shuffle(paths)
            paths = paths[:cfg["max_per_class"]]
        files += paths
        labels += [label] * len(paths)
    return files, labels, classes
