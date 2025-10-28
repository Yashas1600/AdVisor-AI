from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator


PriceEnum = Literal["budget", "mid", "premium"]


AgeCohortEnum = Literal["13-17", "18-24", "25-34", "35-44", "45+", "unknown"]
LifeStageEnum = Literal["student", "early-career", "parent", "retiree", "unknown"]
MediaPrefEnum = Literal["short videos", "long posts", "image carousels", "mixed", "unknown"]
TonePrefEnum = Literal["humorous", "authoritative", "minimalist", "hype", "unknown"]


class AudienceMetrics(BaseModel):
    age_cohort: AgeCohortEnum = "unknown"
    life_stage: LifeStageEnum = "unknown"
    region: str = "unknown"
    language: str = "unknown"
    media_preference: MediaPrefEnum = "unknown"
    values: List[str] = Field(default_factory=list)
    tone_preference: TonePrefEnum = "unknown"

    @field_validator("values")
    @classmethod
    def _values_lower(cls, v: List[str]) -> List[str]:
        return [s.strip().lower() for s in v if s and s.strip()]


class ConfidenceScores(BaseModel):
    product_name: float
    category: float
    price_positioning: float
    claimed_value_prop: float
    target_keywords: float


class Rationales(BaseModel):
    product_name: str
    category: str
    price_positioning: str
    claimed_value_prop: str
    target_keywords: str


class BrandMeta(BaseModel):
    product_name: str = ""
    category: str = "other"
    price_positioning: PriceEnum = "mid"
    claimed_value_prop: str = Field("", description="<= 2 sentences")
    target_keywords: List[str] = Field(default_factory=list)

    # new explicit fields
    product: str = ""
    industry: str = ""
    audience: AudienceMetrics = Field(default_factory=AudienceMetrics)

    confidence: ConfidenceScores
    rationales: Rationales
    warnings: List[str] = Field(default_factory=list)

    @field_validator("target_keywords")
    @classmethod
    def _kw_len_and_case(cls, v: List[str], info: ValidationInfo) -> List[str]:
        # enforce lowercase and 5-8 items where possible (validation, not repair)
        lowered = [s.strip().lower() for s in v if s and s.strip()]
        return lowered


class BrandMetaResponse(BaseModel):
    brand_meta: BrandMeta
    used_provider: Literal["local", "openai", "google", "anthropic"]
    latency_ms: int
    notes: List[str] = Field(default_factory=list, description="debug notes. include prompts only when DEBUG=true")


class BrandMetaRequest(BaseModel):
    # Path A: features blob (from /extract) and moondream summary
    features: Optional[Dict[str, Any]] = None
    moondream_summary: Optional[str] = None

    # Path B: raw fields
    ocr_text: Optional[str] = None
    detected_brand_names: Optional[List[str]] = None
    declared_company: Optional[str] = None
    numbers_found: Optional[List[str]] = None
    hints: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def _ensure_signals(self) -> "BrandMetaRequest":
        has_features = isinstance(self.features, dict)
        has_any_raw = any(
            [
                bool(self.ocr_text and self.ocr_text.strip()),
                bool(self.moondream_summary and self.moondream_summary.strip()),
                bool(self.detected_brand_names),
                bool(self.declared_company and self.declared_company.strip()),
                bool(self.numbers_found),
            ]
        )

        if not has_features and not has_any_raw:
            raise ValueError("Insufficient signals: provide features/moondream_summary or raw fields.")

        return self


# Helper types for pipeline
class Signals(BaseModel):
    ocr_text_raw: str = ""
    ocr_text_norm: str = ""
    moondream_summary: str = ""
    moondream_keywords: List[str] = Field(default_factory=list)
    moondream_extracted_text: str = ""
    moondream_target_audience: str = ""
    declared_company: Optional[str] = None
    detected_brand_names: List[str] = Field(default_factory=list)
    numbers_found: List[str] = Field(default_factory=list)
    hints: Dict[str, Any] = Field(default_factory=dict)


class Priors(BaseModel):
    candidate_product_name: Optional[str] = None
    category_prior: Optional[str] = None
    price_position_prior: Optional[PriceEnum] = None
    candidate_value_prop: Optional[str] = None
    candidate_keywords: List[str] = Field(default_factory=list)
    candidate_product: Optional[str] = None
    industry_prior: Optional[str] = None
    audience_prior: Optional[AudienceMetrics] = None


