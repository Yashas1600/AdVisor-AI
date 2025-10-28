import logging
import os
from typing import Dict, Optional, Tuple

import cv2
import numpy as np


logger = logging.getLogger(__name__)


def _import_pytesseract():  # type: ignore[override]
    try:
        import pytesseract  # type: ignore
        tcmd = os.getenv("TESSERACT_CMD")
        if tcmd:
            pytesseract.pytesseract.tesseract_cmd = tcmd
        return pytesseract
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.debug("pytesseract unavailable: %s", exc)
        return None


def _ocr_enabled() -> bool:
    return os.getenv("ENABLE_OCR", "false").lower() in {"1", "true", "yes"}


def compute_ocr_stats(bgr: np.ndarray) -> Dict[str, object]:
    """Compute naive OCR text and coverage pct using pytesseract when enabled.

    Returns placeholders if disabled or missing runtime deps.
    coverage_pct is in [0, 100].
    """
    if not _ocr_enabled():
        return {"coverage_pct": 0.0, "text": ""}

    pytesseract = _import_pytesseract()
    if pytesseract is None:
        logger.warning("ENABLE_OCR=1 set but pytesseract not available; returning placeholders")
        return {"coverage_pct": 0.0, "text": ""}

    try:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        data = pytesseract.image_to_data(rgb, output_type=pytesseract.Output.DICT)
        n = len(data.get("text", []))
        words = []
        covered_area = 0
        for i in range(n):
            try:
                conf_str = data.get("conf", ["-1"])[i]
                conf = float(conf_str) if conf_str not in ("-1", "" ) else -1.0
            except Exception:
                conf = -1.0
            txt = (data.get("text", [""])[i] or "").strip()
            if txt:
                words.append(txt)
            if conf >= 40.0:  # threshold for confident text
                try:
                    bw = int(data.get("width", [0])[i])
                    bh = int(data.get("height", [0])[i])
                except Exception:
                    bw, bh = 0, 0
                if bw > 0 and bh > 0:
                    covered_area += bw * bh

        text = " ".join(words)
        coverage_pct = 0.0
        if w > 0 and h > 0:
            coverage_pct = float(np.round((covered_area / float(w * h)) * 100.0, 4))
        return {"coverage_pct": coverage_pct, "text": text}
    except Exception as exc:  # pragma: no cover - robustness
        logger.debug("OCR failed; returning placeholders: %s", exc)
        return {"coverage_pct": 0.0, "text": ""}


