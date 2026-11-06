"""
Gemini image analysis -- produces the same fields as moondream_adapter
so that `feature_vector.moondream` consumers keep working.

The result goes under a `gemini` key alongside the existing `moondream` key.
"""
import logging
import os
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


_IMAGE_PROMPT = """\
Analyze this advertisement image and return a JSON object with these fields:
- summary: one-sentence description of what product/service is being advertised
- caption: a descriptive caption for the image
- cta: the call-to-action or main message
- keywords: array of 3-5 main themes/keywords (lowercase)
- target_audience: who is the target audience (age group, gender, interests)
- product_category: category (food, fitness, technology, fashion, beauty, wellness, automotive, travel, finance, or other)
- brand: what brand or company is this ad for
- extracted_text: any visible text including prices, offers, slogans, headlines

Be specific and concise."""


def _get_client():
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as exc:
        logger.warning("Failed to create Gemini client: %s", exc)
        return None


def analyze_image_bytes(image_bytes: bytes) -> Optional[Dict[str, Any]]:
    """Analyze image bytes with Gemini. Returns dict matching moondream schema or None."""
    client = _get_client()
    if client is None:
        logger.debug("Gemini client unavailable; skipping image analysis")
        return None

    from google.genai import types

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Content(
                    parts=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type="image/jpeg",
                        ),
                        types.Part.from_text(text=_IMAGE_PROMPT),
                    ]
                )
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )

        raw_text = response.text
        if not raw_text:
            logger.warning("Empty response from Gemini image analysis")
            return None

        import json
        data = json.loads(raw_text)

        # Normalize to match moondream schema
        keywords = data.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [k.strip().lower() for k in keywords.split(",") if k.strip()]
        else:
            keywords = [str(k).strip().lower() for k in keywords][:5]

        return {
            "summary": data.get("summary", ""),
            "caption": data.get("caption", ""),
            "brand": data.get("brand", ""),
            "product_category": (data.get("product_category", "") or "").lower(),
            "extracted_text": data.get("extracted_text", ""),
            "keywords": keywords,
            "cta": data.get("cta", ""),
            "target_audience": data.get("target_audience", ""),
        }
    except Exception as exc:
        logger.warning("Gemini image analysis failed: %s", exc)
        return None
