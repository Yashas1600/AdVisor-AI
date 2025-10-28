from __future__ import annotations

from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, conlist, field_validator


AttentionBucket = Literal["full", "partial", "ignore", "neutral"]


class AgentInsight(BaseModel):
    agent_id: Optional[str] = Field(None, description="Optional identifier for the agent/persona")
    sentence: str = Field(..., description="Single sentence summarizing the agent's feedback")
    attention: AttentionBucket = Field(..., description="Attention bucket for the ad content")
    persona_name: Optional[str] = Field(None, description="Optional persona display name")

    @classmethod
    def _normalize_attention(cls, v: str) -> str:
        lv = (v or "").strip().lower()
        if lv == "neutral":
            return "partial"
        return lv

    @classmethod
    @field_validator("attention", mode="before")
    def _attention_alias(cls, v: str) -> str:  # type: ignore[override]
        return cls._normalize_attention(v)


class DemographicPoint(BaseModel):
    statement: str = Field(..., description="Pro or con phrased as a short insight")
    percent: float = Field(..., ge=0, le=100, description="Estimated percentage of audience")
    demographic: str = Field(..., description="Group label, e.g., 'Gen Z', 'Parents 25-34, US'")


class DemographicInsights(BaseModel):
    pros: List[DemographicPoint] = Field(default_factory=list)
    cons: List[DemographicPoint] = Field(default_factory=list)


class LLMInsightsAggregate(BaseModel):
    # Output shape expected from the LLM tool call
    per_insight_scores: conlist(float, min_length=1)  # type: ignore[type-arg]
    overall_insights: conlist(str, min_length=3, max_length=8)  # type: ignore[type-arg]
    demographics: DemographicInsights


class InsightsSummaryRequest(BaseModel):
    insights: conlist(AgentInsight, min_length=1)  # type: ignore[type-arg]
    ad_context: Optional[str] = Field(
        None,
        description="Optional freeform context about the ad (brand, product, audience, platform)",
    )


class ByIdItem(BaseModel):
    insight: str
    attention: AttentionBucket
    persona_name: Optional[str] = None


class InsightsSummarySelectedRequest(BaseModel):
    byId: Dict[str, ByIdItem]
    selected: List[Union[str, int]]
    ad_context: Optional[str] = None


class AttentionTally(BaseModel):
    full: int = 0
    partial: int = 0
    ignore: int = 0


class InsightsSummaryResponse(BaseModel):
    averaged_impact_score: float
    attention_tally: AttentionTally
    overall_insights: List[str]
    demographics: DemographicInsights
    per_insight_scores: Optional[List[float]] = Field(
        default=None, description="Present when debug=true; individual impact scores per insight in input order"
    )
    used_provider: Literal["local", "openai", "google", "anthropic"]
    latency_ms: int
    notes: List[str] = Field(default_factory=list, description="debug notes; may include prompts when debug=true")


