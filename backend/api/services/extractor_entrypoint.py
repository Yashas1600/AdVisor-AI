import logging
import os
import cv2
from typing import List, Dict, Any
from typing import Dict, Literal, Tuple

import os
from api.schemas import ExtractFeatures, ExtractResponse, MediaInfo, MoondreamBlock
from api.services.moondream_adapter import analyze_image_bytes
from extractor.pipeline.image_features import extract_from_image
from extractor.pipeline.preprocess import decode_image_from_bytes, write_temp_video_file
from extractor.pipeline.video_features import extract_from_video


logger = logging.getLogger(__name__)


def _build_response(ad_id: str, media: Dict, features: Dict, moondream: Dict | None = None) -> ExtractResponse:
    media_model = MediaInfo(**media)
    features_model = ExtractFeatures(**features)
    md_block = MoondreamBlock(**moondream) if moondream else None
    return ExtractResponse(ad_id=ad_id, media=media_model, features=features_model, moondream=md_block)


def run_extraction(ad_id: str, data: bytes, modality: Literal["image", "video"], filename: str) -> ExtractResponse:
    """Dispatch extraction based on modality and build the response model."""
    if modality == "image":
        bgr = decode_image_from_bytes(data)
        media, features = extract_from_image(bgr)
        md = None
        # Optionally call Moondream when api key present
        if os.getenv("MOONDREAM_API_KEY"):
            try:
                md = analyze_image_bytes(data)
            except Exception:
                md = None
        return _build_response(ad_id, media, features, moondream=md)

    # video path
    video_path = write_temp_video_file(data, filename)
    try:
        media, features = extract_from_video(video_path)

        md = None
        if os.getenv("MOONDREAM_API_KEY"):
            try:
                cap = cv2.VideoCapture(video_path)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
                if total_frames <= 0:
                    raise RuntimeError("no frames")

                # Sample every 30th frame, capped to at most 12 frames
                step = 30
                indices: List[int] = list(range(0, total_frames, step))
                if not indices:
                    indices = [0]
                if len(indices) > 12:
                    # downsample indices evenly to 12 points
                    k = 12
                    indices = [indices[int(i * (len(indices) - 1) / (k - 1))] for i in range(k)]

                frame_results: List[Dict[str, Any]] = []
                for idx in indices:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                    ok, frame = cap.read()
                    if not ok or frame is None:
                        continue
                    ok2, buf = cv2.imencode('.jpg', frame)
                    if not ok2:
                        continue
                    res = analyze_image_bytes(buf.tobytes())
                    if res:
                        frame_results.append(res)
                cap.release()

                if not frame_results:
                    md = None
                else:
                    # Aggregate results across sampled frames
                    def majority(items: List[str]) -> str:
                        counts: Dict[str, int] = {}
                        for it in items:
                            if not it:
                                continue
                            counts[it] = counts.get(it, 0) + 1
                        if not counts:
                            return ""
                        return max(counts.items(), key=lambda x: x[1])[0]

                    summaries = [r.get("summary", "") for r in frame_results if r.get("summary")]
                    captions = [r.get("caption", "") for r in frame_results if r.get("caption")]
                    brands = [r.get("brand", "") for r in frame_results if r.get("brand")]
                    categories = [r.get("product_category", "") for r in frame_results if r.get("product_category")]
                    texts = [r.get("extracted_text", "") for r in frame_results if r.get("extracted_text")]
                    ctas = [r.get("cta", "") for r in frame_results if r.get("cta")]
                    audiences = [r.get("target_audience", "") for r in frame_results if r.get("target_audience")]
                    kw_all: List[str] = []
                    for r in frame_results:
                        kw_all.extend([k for k in (r.get("keywords") or []) if k])

                    # Build consolidated block
                    combined_summary = " ".join(summaries)[:500] if summaries else ""
                    best_caption = max(captions, key=len) if captions else ""
                    brand = majority(brands)
                    category = majority(categories)
                    extracted = " ".join(texts)[:600] if texts else ""
                    first_cta = next((c for c in ctas if c), "")
                    audience = majority(audiences)
                    # unique keywords, preserve order
                    seen = set()
                    keywords: List[str] = []
                    for k in kw_all:
                        if k not in seen:
                            seen.add(k)
                            keywords.append(k)
                        if len(keywords) >= 5:
                            break

                    md = {
                        "summary": combined_summary,
                        "caption": best_caption,
                        "brand": brand,
                        "product_category": category,
                        "extracted_text": extracted,
                        "keywords": keywords,
                        "cta": first_cta,
                        "target_audience": audience,
                    }
            except Exception:
                md = None

        return _build_response(ad_id, media, features, moondream=md)
    finally:
        try:
            os.remove(video_path)
        except OSError:
            logger.debug("Failed to remove temp video file: %s", video_path)


