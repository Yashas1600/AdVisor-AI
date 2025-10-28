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


class ExtractResponse(BaseModel):
    ad_id: str
    media: MediaInfo
    features: ExtractFeatures
    version: str = EXTRACTOR_VERSION
    moondream: Optional[MoondreamBlock] = None


