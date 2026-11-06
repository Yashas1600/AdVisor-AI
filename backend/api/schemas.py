from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field, conlist


EXTRACTOR_VERSION = "fx-0.1.0"


class MediaInfo(BaseModel):
    modality: Literal["image", "video"]
    width: int
    height: int
    duration_ms: Optional[int] = None
    fps: Optional[float] = None


class ColorStats(BaseModel):
    colorfulness: float
    mean_bgr: conlist(float, min_length=3, max_length=3)  # type: ignore[type-arg]
    std_bgr: conlist(float, min_length=3, max_length=3)  # type: ignore[type-arg]
    palette_hex: conlist(str, min_length=5, max_length=5)  # type: ignore[type-arg]


class LayoutStats(BaseModel):
    aspect_ratio: float
    whitespace_ratio: float


class MotionStats(BaseModel):
    sampled_frames: int
    motion_intensity: float
    cuts_per_min: float
    text_first_second_pct: float = Field(0.0, description="Placeholder")
    audio_energy: float = Field(0.0, description="Placeholder")


class LogosStats(BaseModel):
    present: bool = False
    area_pct: float = 0.0


class ExtractFeatures(BaseModel):
    color: ColorStats
    layout: LayoutStats
    video: Optional[MotionStats] = None
    objects: List[Any] = Field(default_factory=list)
    logos: LogosStats = Field(default_factory=LogosStats)


class MoondreamBlock(BaseModel):
    summary: str = ""
    caption: str = ""
    brand: str = ""
    product_category: str = ""
    extracted_text: str = ""
    keywords: List[str] = Field(default_factory=list)
    cta: str = ""
    target_audience: str = ""


class GeminiTimelineScene(BaseModel):
    start_seconds: float = 0.0
    end_seconds: float = 0.0
    description: str = ""
    visual_elements: List[str] = Field(default_factory=list)


class GeminiTimelineTextOverlay(BaseModel):
    text: str = ""
    timestamp_seconds: float = 0.0


class GeminiTimeline(BaseModel):
    scenes: List[GeminiTimelineScene] = Field(default_factory=list)
    hook: str = ""
    on_screen_text: List[GeminiTimelineTextOverlay] = Field(default_factory=list)
    transcript: str = ""
    brand_first_appearance: Optional[float] = None
    cta_first_appearance: Optional[float] = None
    pacing: str = "moderate"
    aspect_ratio: str = "landscape"
    duration_seconds: float = 0.0


class ExtractResponse(BaseModel):
    ad_id: str
    media: MediaInfo
    features: ExtractFeatures
    version: str = EXTRACTOR_VERSION
    moondream: Optional[MoondreamBlock] = None
    gemini: Optional[MoondreamBlock] = None
    gemini_timeline: Optional[GeminiTimeline] = None


