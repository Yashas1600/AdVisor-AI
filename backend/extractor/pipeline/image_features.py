import logging
from typing import Dict, Tuple

import cv2
import numpy as np

from extractor.pipeline.utils import (
    aspect_ratio,
    compute_colorfulness_hs,
    compute_mean_std_bgr,
    kmeans_palette_hex,
    whitespace_ratio,
)
from extractor.pipeline.ocr import compute_ocr_stats


logger = logging.getLogger(__name__)


def _media_from_bgr(bgr: np.ndarray) -> Dict:
    h, w = bgr.shape[:2]
    return {"modality": "image", "width": int(w), "height": int(h), "duration_ms": None, "fps": None}


def extract_from_image(bgr: np.ndarray) -> Tuple[Dict, Dict]:
    """Compute features for an image (color, layout)."""
    h, w = bgr.shape[:2]

    colorfulness = compute_colorfulness_hs(bgr)
    mean_bgr, std_bgr = compute_mean_std_bgr(bgr)
    palette_hex = kmeans_palette_hex(bgr, k=5)
    ar = aspect_ratio(w, h)
    ws_ratio = whitespace_ratio(bgr)

    media = _media_from_bgr(bgr)
    # OCR removed from schema
    features = {
        "color": {
            "colorfulness": float(colorfulness),
            "mean_bgr": mean_bgr,
            "std_bgr": std_bgr,
            "palette_hex": palette_hex,
        },
        "layout": {"aspect_ratio": float(ar), "whitespace_ratio": float(ws_ratio)},
        "video": None,
        "objects": [],
        "logos": {"present": False, "area_pct": 0.0},
    }
    return media, features


