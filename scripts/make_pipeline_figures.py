"""Generate the 6-stage pipeline figure for one example of every TrashNet class (for slides/report)."""
import argparse
from pathlib import Path

import cv2
import matplotlib.pyplot as plt

from waste_classifier.config import PIPELINE_FIG_DIR, TRASHNET_CLASS_MAP, TRASHNET_DIR
from waste_classifier.data import list_images
from waste_classifier.plotting import save_image_grid
from waste_classifier.segmentation import clean_mask, draw_boxes, largest_component, otsu_mask

TITLES = ["Original", "Grayscale", "Gaussian Blur", "Otsu Mask", "After Morphology", "Detected Object"]
COLOR = (0, 5)


def run_pipeline(img):
    gray, blur, otsu, _ = otsu_mask(img)
    _, clean = clean_mask(otsu)
    clean = largest_component(clean)
    rgb = lambda im: cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    return [rgb(img), gray, blur, otsu, clean, rgb(draw_boxes(img, clean))]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=PIPELINE_FIG_DIR)
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    classes = sorted(TRASHNET_CLASS_MAP)
    all_stages = []
    for label in classes:
        first = list_images(TRASHNET_DIR / label)[0]
        stages = run_pipeline(cv2.imread(first))
        all_stages.append(stages)
        save_image_grid(stages, TITLES, args.out_dir / f"pipeline_{label}.png",
                        color_idx=COLOR, suptitle=label.upper(), figsize=(18, 3.5), dpi=150)

    # Combined figure: classes x stages
    fig, axes = plt.subplots(len(classes), 6, figsize=(18, 3 * len(classes)))
    for r, label in enumerate(classes):
        for c in range(6):
            axes[r, c].imshow(all_stages[r][c], cmap=None if c in COLOR else "gray")
            axes[r, c].axis("off")
            if r == 0:
                axes[r, c].set_title(TITLES[c])
        axes[r, 0].text(-0.05, 0.5, label, transform=axes[r, 0].transAxes,
                        ha="right", va="center", fontsize=12)
    plt.tight_layout()
    out = args.out_dir / "pipeline_all_classes.png"
    plt.savefig(out, dpi=120)
    print("Saved", out)
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
