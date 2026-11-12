"""Shared plotting helpers."""
from pathlib import Path

import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix


def save_confusion_matrix(y_true, y_pred, labels, title: str, path: Path, show: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    ConfusionMatrixDisplay(cm, display_labels=labels).plot(cmap="Blues", xticks_rotation=45)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path)
    print("Saved", path)
    if show:
        plt.show()
    plt.close()


def save_image_grid(images, titles, path: Path, color_idx=(0,), suptitle=None,
                    figsize=None, dpi=100, show=False):
    """One row of images. Indices in color_idx are RGB, the rest are shown in gray."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n = len(images)
    plt.figure(figsize=figsize or (4 * n, 4))
    for i, (im, t) in enumerate(zip(images, titles)):
        plt.subplot(1, n, i + 1)
        plt.imshow(im, cmap=None if i in color_idx else "gray")
        plt.title(t)
        plt.axis("off")
    if suptitle:
        plt.suptitle(suptitle, fontsize=14)
    plt.tight_layout()
    plt.savefig(path, dpi=dpi)
    print("Saved", path)
    if show:
        plt.show()
    plt.close()
