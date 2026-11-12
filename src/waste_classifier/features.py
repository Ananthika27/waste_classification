"""Hand-crafted features: shape (geometry + Hu moments), colour (HSV histogram), texture (LBP)."""
import cv2
import numpy as np
from skimage.feature import local_binary_pattern

from .config import FEATURE_IMAGE_SIZE
from .segmentation import get_object_mask

N_FEATURES = 4 + 7 + 8 * 4 * 4 + 10  # 149


def extract_features(img: np.ndarray) -> np.ndarray:
    size = FEATURE_IMAGE_SIZE
    img = cv2.resize(img, (size, size))
    mask = get_object_mask(img)
    features = []

    # ---- Shape ----
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c)
    perimeter = cv2.arcLength(c, True)
    circularity = 4 * np.pi * area / (perimeter ** 2 + 1e-6)
    x, y, w, h = cv2.boundingRect(c)
    features += [area / (size * size), circularity, w / h, area / (w * h)]

    # Hu moments, log-scaled so they are comparable
    hu = cv2.HuMoments(cv2.moments(mask)).flatten()
    features += list(-np.sign(hu) * np.log10(np.abs(hu) + 1e-12))

    # ---- Colour: HSV histogram inside the object ----
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1, 2], mask, [8, 4, 4], [0, 180, 0, 256, 0, 256])
    features += list(cv2.normalize(hist, hist).flatten())

    # ---- Texture: uniform LBP histogram inside the object ----
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lbp = local_binary_pattern(gray, 8, 1, method="uniform")
    lbp_hist, _ = np.histogram(lbp[mask == 255], bins=10, range=(0, 10), density=True)
    features += list(lbp_hist)

    return np.array(features)
