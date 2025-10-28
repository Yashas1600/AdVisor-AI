import io
import logging
import os
import tempfile
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
from PIL import Image


logger = logging.getLogger(__name__)


def decode_image_from_bytes(data: bytes) -> np.ndarray:
    """Decode image bytes to BGR ndarray using PIL -> numpy -> BGR.

    Returns a contiguous BGR image (H, W, 3) uint8.
    """
    with Image.open(io.BytesIO(data)) as img:
        rgb = img.convert("RGB")
        arr = np.array(rgb)
    # Convert RGB to BGR
    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    return bgr.copy()


def write_temp_video_file(data: bytes, filename: str) -> str:
    """Write bytes to a temporary mp4 file and return its path."""
    suffix = ".mp4" if filename.lower().endswith(".mp4") else Path(filename).suffix or ".mp4"
    fd, path = tempfile.mkstemp(prefix="advisor_", suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    logger.debug("Wrote temp video file: %s", path)
    return path


