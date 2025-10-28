import logging
from typing import List, Tuple

import cv2
import numpy as np
from sklearn.cluster import KMeans


logger = logging.getLogger(__name__)


def compute_colorfulness_hs(bgr: np.ndarray) -> float:
    """Compute Hasler–Süsstrunk colorfulness metric for a BGR image."""
    b, g, r = cv2.split(bgr.astype(np.float32))
    rg = np.abs(r - g)
    yb = np.abs(0.5 * (r + g) - b)
    std_rg, mean_rg = np.std(rg), np.mean(rg)
    std_yb, mean_yb = np.std(yb), np.mean(yb)
    colorfulness = np.sqrt(std_rg**2 + std_yb**2) + 0.3 * np.sqrt(mean_rg**2 + mean_yb**2)
    return float(np.round(colorfulness, 4))


def compute_mean_std_bgr(bgr: np.ndarray) -> Tuple[List[float], List[float]]:
    """Return mean and std per channel (B, G, R) rounded to 2 decimals."""
    means = [float(np.round(np.mean(bgr[:, :, i]), 2)) for i in range(3)]
    stds = [float(np.round(np.std(bgr[:, :, i]), 2)) for i in range(3)]
    return means, stds


def kmeans_palette_hex(bgr: np.ndarray, k: int = 5, max_samples: int = 100_000) -> List[str]:
    """Compute a KMeans palette of size k from BGR image; return hex colors in RGB order."""
    pixels = bgr.reshape(-1, 3)
    if pixels.shape[0] > max_samples:
        idx = np.random.RandomState(42).choice(pixels.shape[0], size=max_samples, replace=False)
        pixels = pixels[idx]
    # Convert to RGB for human-readable palette
    rgb_pixels = pixels[:, ::-1].astype(np.float32)
    km = KMeans(n_clusters=k, n_init=5, random_state=42)
    km.fit(rgb_pixels)
    centers = np.clip(km.cluster_centers_.astype(int), 0, 255)
    # Sort by luminance descending to stabilize ordering
    luminance = 0.2126 * centers[:, 0] + 0.7152 * centers[:, 1] + 0.0722 * centers[:, 2]
    order = np.argsort(-luminance)
    centers = centers[order]
    hex_colors = ["#%02x%02x%02x" % (r, g, b) for r, g, b in centers]
    return hex_colors


def whitespace_ratio(bgr: np.ndarray, threshold: int = 245) -> float:
    """Estimate whitespace ratio as fraction of near-white pixels (in RGB) above threshold.

    Converts to RGB first, then counts pixels where all channels >= threshold.
    """
    rgb = bgr[:, :, ::-1]
    mask = (rgb >= threshold).all(axis=2)
    ratio = float(mask.sum()) / float(mask.size) if mask.size else 0.0
    return float(np.round(ratio, 4))


def aspect_ratio(width: int, height: int) -> float:
    if height == 0:
        return 0.0
    return float(np.round(width / height, 4))


