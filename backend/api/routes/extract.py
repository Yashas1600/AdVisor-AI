import logging
import uuid
from typing import Literal, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from api.schemas import ExtractResponse
from api.services.extractor_entrypoint import run_extraction


router = APIRouter()
logger = logging.getLogger(__name__)


SUPPORTED_IMAGE_MIME = {"image/png", "image/jpeg"}
SUPPORTED_VIDEO_MIME = {"video/mp4"}


def _detect_modality(mime: Optional[str], filename: str) -> Literal["image", "video"]:
    """Detect modality using content-type, falling back to filename extension."""
    if mime:
        if mime in SUPPORTED_IMAGE_MIME:
            logger.debug("Detected modality via content-type: image (%s)", mime)
            return "image"
        if mime in SUPPORTED_VIDEO_MIME:
            logger.debug("Detected modality via content-type: video (%s)", mime)
            return "video"
        logger.warning("Unsupported content-type; falling back to filename: %s", mime)

    lower = filename.lower()
    if lower.endswith((".png", ".jpg", ".jpeg")):
        return "image"
    if lower.endswith(".mp4"):
        return "video"
    raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f"Unsupported type: {mime or filename}")


@router.post("/extract", response_model=ExtractResponse)
async def extract(file: UploadFile = File(...)) -> ExtractResponse:
    """Extract minimal visual features from an uploaded image or video file (file blob)."""
    if file is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file upload.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file upload.")

    mime = file.content_type
    modality = _detect_modality(mime, file.filename or "")

    ad_id = uuid.uuid4().hex[:8]
    logger.debug("Starting extraction ad_id=%s modality=%s filename=%s", ad_id, modality, file.filename)

    try:
        response = run_extraction(ad_id=ad_id, data=content, modality=modality, filename=file.filename or "uploaded")
        logger.info("Extraction succeeded ad_id=%s modality=%s", ad_id, modality)
        return response
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - generic error path
        logger.exception("Extraction failed ad_id=%s error=%s", ad_id, exc)
        raise HTTPException(status_code=500, detail="Extraction failed.")


