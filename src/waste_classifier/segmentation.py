"""Classical object segmentation: grayscale -> Gaussian blur -> Otsu -> morphology -> largest component."""
import cv2
import numpy as np

KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))


def otsu_mask(img: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Return (gray, blur, mask, threshold). The mask has the object white on black."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Backgrounds are mostly bright: if most pixels are white, invert.
    if np.mean(mask) > 127:
        mask = cv2.bitwise_not(mask)
    return gray, blur, mask, thresh


def clean_mask(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Opening (removes specks) then closing (fills holes). Returns (opened, closed)."""
    opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, KERNEL)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, KERNEL)
    return opened, closed


def largest_component(mask: np.ndarray) -> np.ndarray:
    """Keep only the largest connected component; fall back to the whole image."""
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if n <= 1:
        return np.full_like(mask, 255)
    largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    return np.where(labels == largest, 255, 0).astype(np.uint8)


def filter_small_components(mask: np.ndarray, min_area_frac: float = 0.01) -> tuple[np.ndarray, int]:
    """Keep every component larger than min_area_frac of the image. Returns (mask, kept_count)."""
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    min_area = min_area_frac * mask.shape[0] * mask.shape[1]
    out = np.zeros_like(mask)
    kept = 0
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            out[labels == i] = 255
            kept += 1
    return out, kept


def get_object_mask(img: np.ndarray) -> np.ndarray:
    """Full segmentation pipeline used for feature extraction."""
    _, _, mask, _ = otsu_mask(img)
    _, mask = clean_mask(mask)
    return largest_component(mask)


def draw_boxes(img: np.ndarray, mask: np.ndarray, thickness: int = 3) -> np.ndarray:
    """Draw a green bounding box around every external contour of the mask."""
    out = img.copy()
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 0), thickness)
    return out
