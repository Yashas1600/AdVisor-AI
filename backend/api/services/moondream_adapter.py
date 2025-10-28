import io
import os
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _load_client():
    api_key = os.getenv("MOONDREAM_API_KEY")
    if not api_key:
        logger.debug("MOONDREAM_API_KEY not set; skipping Moondream")
        return None
    try:
        import moondream as md  # type: ignore
    except Exception:
        logger.debug("moondream package not installed; skipping Moondream")
        return None
    try:
        return md.vl(api_key=api_key)
    except Exception as exc:
        logger.warning("Failed to initialize Moondream client: %s", exc)
        return None


def _load_pil_rgb(image_bytes: bytes):
    from PIL import Image  # lazy import

    img = Image.open(io.BytesIO(image_bytes))
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")
    return img


def analyze_image_bytes(image_bytes: bytes) -> Optional[Dict[str, Any]]:
    """Run Moondream analysis on image bytes. Returns dict or None if unavailable."""
    client = _load_client()
    if client is None:
        return None

    try:
        pil_img = _load_pil_rgb(image_bytes)
        caption_result = client.caption(image=pil_img) or {}
        caption = caption_result.get("caption", "")

        def ask(q: str) -> str:
            try:
                r = client.query(image=pil_img, question=q) or {}
                return str(r.get("answer", "")).strip()
            except Exception:
                return ""

        summary = ask("Describe this advertisement in one sentence. What product or service is being advertised?")
        category = ask(
            "What category does this ad belong to: food, fitness, technology, fashion, beauty, wellness, automotive, travel, finance, or other?"
        )
        text_content = ask("What text is visible in this ad? List any prices, offers, slogans, or headlines.")
        keywords_raw = ask("What are 3-5 main themes or keywords for this ad? Separate with commas.")
        cta = ask("What is the call-to-action or main message of this ad?")
        brand = ask("What brand or company is this ad for?")
        target_audience = ask(
            "Who is the target audience for this ad? (e.g., age group, gender, interests)"
        )

        keywords = [k.strip().lower() for k in (keywords_raw or "").split(",") if k.strip()][:5]

        return {
            "summary": summary,
            "caption": caption,
            "brand": brand,
            "product_category": (category or "").lower(),
            "extracted_text": text_content,
            "keywords": keywords,
            "cta": cta,
            "target_audience": target_audience,
        }
    except Exception as exc:
        logger.warning("Moondream analysis failed: %s", exc)
        return None


