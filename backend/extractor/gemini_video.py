"""
Gemini video understanding via the google-genai SDK.
Uploads an mp4 through the Files API, extracts a structured VideoTimeline,
and merges with existing OpenCV features (motion, cuts).
"""
import json
import logging
import os
import time
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Scene(BaseModel):
    start_seconds: float
    end_seconds: float
    description: str
    visual_elements: list[str] = Field(default_factory=list)


class TextOverlay(BaseModel):
    text: str
    timestamp_seconds: float


class VideoTimeline(BaseModel):
    scenes: list[Scene] = Field(default_factory=list)
    hook: str = ""
    on_screen_text: list[TextOverlay] = Field(default_factory=list)
    transcript: str = ""
    brand_first_appearance: Optional[float] = None
    cta_first_appearance: Optional[float] = None
    pacing: str = "moderate"
    aspect_ratio: str = "landscape"
    duration_seconds: float = 0.0


_TIMELINE_PROMPT = """\
Analyze this video advertisement and produce a structured JSON timeline.

Return a JSON object with these fields:
- scenes: array of {start_seconds, end_seconds, description, visual_elements}
- hook: description of the first 3-5 seconds (the attention hook)
- on_screen_text: array of {text, timestamp_seconds} for all text overlays
- transcript: full voiceover/audio transcript
- brand_first_appearance: seconds when brand/logo first appears (null if never)
- cta_first_appearance: seconds when call-to-action first appears (null if never)
- pacing: "fast", "moderate", or "slow"
- aspect_ratio: "vertical", "landscape", or "square"
- duration_seconds: total video duration

Be precise with timestamps. Include every scene transition."""


def _get_client():
    """Lazily create a google-genai client."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as exc:
        logger.warning("Failed to create Gemini client: %s", exc)
        return None


def analyze_video(video_path: str) -> Optional[VideoTimeline]:
    """Upload video to Gemini Files API, extract structured timeline."""
    client = _get_client()
    if client is None:
        logger.debug("Gemini client unavailable; skipping video analysis")
        return None

    from google import genai
    from google.genai import types

    uploaded_file = None
    try:
        # Upload video
        logger.info("Uploading video to Gemini Files API: %s", video_path)
        uploaded_file = client.files.upload(file=video_path)

        # Poll until ACTIVE
        max_wait = 120
        poll_interval = 2
        elapsed = 0
        while uploaded_file.state.name != "ACTIVE":
            if elapsed >= max_wait:
                logger.warning("Gemini file upload timed out after %ds", max_wait)
                return None
            if uploaded_file.state.name == "FAILED":
                logger.warning("Gemini file upload failed")
                return None
            time.sleep(poll_interval)
            elapsed += poll_interval
            uploaded_file = client.files.get(name=uploaded_file.name)

        logger.info("Video file active, requesting timeline analysis")

        # Generate content with structured output
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Content(
                    parts=[
                        types.Part.from_uri(
                            file_uri=uploaded_file.uri,
                            mime_type="video/mp4",
                        ),
                        types.Part.from_text(text=_TIMELINE_PROMPT),
                    ]
                )
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=VideoTimeline,
                temperature=0.2,
            ),
        )

        # Parse response
        raw_text = response.text
        if not raw_text:
            logger.warning("Empty response from Gemini video analysis")
            return None

        timeline = VideoTimeline.model_validate_json(raw_text)
        logger.info("Gemini video analysis complete: %d scenes", len(timeline.scenes))
        return timeline

    except Exception as exc:
        logger.warning("Gemini video analysis failed: %s", exc)
        return None
    finally:
        # Clean up uploaded file
        if uploaded_file is not None:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass


def merge_with_opencv_features(
    timeline: VideoTimeline,
    opencv_features: dict,
) -> dict:
    """Merge Gemini timeline data into the existing OpenCV feature dict."""
    opencv_features["gemini_timeline"] = timeline.model_dump()
    return opencv_features
