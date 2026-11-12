"""Step-by-step visualisation of the classical segmentation pipeline on one image.

Replaces the old step3.py / step4.py / step5.py.

    python scripts/demo_segmentation_steps.py --image data/raw/trashnet/plastic/plastic1.jpg
"""
import argparse
from pathlib import Path

import cv2

from waste_classifier.config import PIPELINE_FIG_DIR, TRASHNET_DIR
from waste_classifier.plotting import save_image_grid
from waste_classifier.segmentation import clean_mask, draw_boxes, filter_small_components, otsu_mask


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--image", type=Path, default=TRASHNET_DIR / "plastic" / "plastic1.jpg")
    ap.add_argument("--out-dir", type=Path, default=PIPELINE_FIG_DIR)
    ap.add_argument("--show", action="store_true", help="also open the figures in a window")
    args = ap.parse_args()

    img = cv2.imread(str(args.image))
    if img is None:
        raise SystemExit(f"Could not read image: {args.image}")
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Step 3: grayscale, Gaussian blur, Otsu threshold
    gray, blur, mask, thresh = otsu_mask(img)
    print("Otsu threshold value:", thresh)
    save_image_grid([rgb, gray, blur, mask],
                    ["Original", "Grayscale", "Gaussian Blur", "Otsu Threshold"],
                    args.out_dir / "step3_threshold.png", show=args.show)

    # Step 4: morphology
    opened, cleaned = clean_mask(mask)
    save_image_grid([mask, opened, cleaned], ["Otsu Mask", "After Opening", "After Closing"],
                    args.out_dir / "step4_morphology.png", color_idx=(), show=args.show)

    # Step 5: connected components + size filtering + bounding box
    filtered, kept = filter_small_components(cleaned, min_area_frac=0.01)
    print("Objects kept after size filtering:", kept)
    result = cv2.cvtColor(draw_boxes(img, filtered, thickness=2), cv2.COLOR_BGR2RGB)
    save_image_grid([cleaned, filtered, result],
                    ["Cleaned Mask", "After Size Filtering", "Detected Object"],
                    args.out_dir / "step5_components.png", color_idx=(2,), show=args.show)


if __name__ == "__main__":
    main()
