import json
import os
from typing import Dict, List, Tuple

from api.schemas_insights import AgentInsight, DemographicInsights, InsightsSummaryRequest, LLMInsightsAggregate
from api.services.llm_adapter import complete_structured_generic


SYSTEM_PROMPT = (
    "You are an expert advertising analyst specializing in creative optimization. "
    "Your task is to deeply analyze ad performance based on persona feedback. "
    "\n\n"
    "First, assign a 0-100 impact score to each persona insight (100=very strong positive signal, 0=negligible). "
    "Use attention buckets as priors (full=high score, partial=medium, ignore=low) but refine based on sentiment. "
    "\n\n"
    "Then provide 5-8 DETAILED, ACTIONABLE insights covering: "
    "1. VISUAL FEATURES: What visual elements work well? What needs improvement? (colors, layout, imagery, CTA visibility) "
    "2. MESSAGING: Is the copy clear, compelling, relevant? What changes would improve resonance? "
    "3. AUDIENCE FIT: Which demographics engage vs. disengage? Why? "
    "4. SPECIFIC CRITIQUES: Summarize recurring negative feedback and suggest concrete fixes "
    "5. STRENGTHS TO AMPLIFY: What features are working well that should be emphasized? "
    "6. MISSING ELEMENTS: What key features are lacking or underutilized? "
    "\n\n"
    "Be specific about which ad features to change, improve, or add. Reference actual persona critiques. "
    "Finally, generate demographic pros and cons with estimated percentages."
)


def _build_user_prompt(payload: InsightsSummaryRequest, counts: List[int] | None = None) -> str:
    lines: List[str] = []
    if payload.ad_context:
        lines.append(f"Ad context: {payload.ad_context}")
    lines.append("Agent insights (sentence | attention):")
    for idx, ins in enumerate(payload.insights, start=1):
        tag = ins.agent_id or f"agent_{idx}"
        label = f"{tag}"
        if ins.persona_name:
            label = f"{tag} ({ins.persona_name})"
        suffix = ""
        if counts is not None and idx - 1 < len(counts) and counts[idx - 1] > 1:
            suffix = f" (x{counts[idx - 1]} similar)"
        lines.append(f"- {label}: {ins.sentence.strip()} | attention={ins.attention}{suffix}")
    return "\n".join(lines)


def _dedupe_payload(payload: InsightsSummaryRequest) -> Tuple[InsightsSummaryRequest, List[int]]:
    """Deduplicate identical (sentence, attention) pairs to reduce prompt size.

    Returns (deduped_payload, counts) where counts[i] is how many originals map to deduped[i].
    """
    seen: Dict[tuple[str, str], int] = {}
    deduped: List = []
    counts: List[int] = []
    for ins in payload.insights:
        key = (ins.sentence.strip(), ins.attention)
        if key in seen:
            counts[seen[key]] += 1
        else:
            seen[key] = len(deduped)
            deduped.append(ins)
            counts.append(1)
    return InsightsSummaryRequest(insights=deduped, ad_context=payload.ad_context), counts


def _json_schema_for_output() -> Dict:
    # Mirror LLMInsightsAggregate schema in JSON Schema format
    return {
        "type": "object",
        "properties": {
            "per_insight_scores": {
                "type": "array",
                "items": {"type": "number", "minimum": 0, "maximum": 100},
                "minItems": 1,
            },
            "overall_insights": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 5,
                "maxItems": 12,
            },
            "demographics": {
                "type": "object",
                "properties": {
                    "pros": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "statement": {"type": "string"},
                                "percent": {"type": "number", "minimum": 0, "maximum": 100},
                                "demographic": {"type": "string"},
                            },
                            "required": ["statement", "percent", "demographic"],
                        },
                    },
                    "cons": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "statement": {"type": "string"},
                                "percent": {"type": "number", "minimum": 0, "maximum": 100},
                                "demographic": {"type": "string"},
                            },
                            "required": ["statement", "percent", "demographic"],
                        },
                    },
                },
                "required": ["pros", "cons"],
            },
        },
        "required": ["per_insight_scores", "overall_insights", "demographics"],
        "additionalProperties": False,
    }


def summarize_insights(
    payload: InsightsSummaryRequest,
    provider: str = "openai",
    temperature: float = 0.2,
    debug: bool = False,
    fast: bool = True,
    timeout_s: float = 20.0,
    max_tokens: int = 600,
) -> Tuple[LLMInsightsAggregate, Dict]:
    # Optionally dedupe repeated insights to reduce token usage
    working = payload
    counts: List[int] | None = None
    if fast:
        working, counts = _dedupe_payload(payload)

    user_prompt = _build_user_prompt(working, counts)
    schema = _json_schema_for_output()
    tool_name = "emit_insights_summary"
    tool_desc = "Return structured aggregate of impact scores, overall insights, and demographic pros/cons."

    base_count = len(working.insights)
    # More meaningful default scores for fallback: derive from attention bucket
    hint_scores: List[float] = []
    for ins in working.insights:
        attn = ins.attention
        if attn == "neutral":  # backward compat
            attn = "partial"
        if attn == "full":
            hint_scores.append(85.0)
        elif attn == "partial":
            hint_scores.append(55.0)
        else:
            hint_scores.append(15.0)

    schema_hint = {
        "per_insight_scores": hint_scores or [50.0 for _ in range(base_count)],
        "overall_insights": [
            "VISUAL STRENGTHS: The color palette is eye-catching and aligns well with brand identity. The high-contrast CTA button effectively draws attention.",
            "VISUAL WEAKNESSES: Layout feels cluttered with too many elements competing for focus. Consider simplifying to 2-3 key visual hierarchy levels.",
            "MESSAGING STRENGTHS: The headline is clear and benefit-driven, immediately communicating value to the target audience.",
            "MESSAGING WEAKNESSES: Copy is too generic and doesn't address specific pain points mentioned by personas. Add more concrete examples and social proof.",
            "AUDIENCE FIT: Strong resonance with 18-24 fitness enthusiasts due to authentic imagery, but lacks appeal to 35+ professionals who want efficiency-focused messaging.",
            "CRITICAL FIXES NEEDED: 47% of personas mentioned the CTA is confusing. Change 'Learn More' to specific action like 'Start Free Trial' or 'Get 20% Off'.",
            "AMPLIFY THESE STRENGTHS: The product demonstration in the hero image is highly effective - personas cited this as most engaging element. Feature it more prominently.",
            "MISSING ELEMENTS: No testimonials or social proof visible. Add 2-3 short customer quotes or star ratings to build trust, especially for skeptical demographics.",
        ],
        "demographics": {
            "pros": [{"statement": "Clear benefits resonate with budget-conscious viewers", "percent": 38.0, "demographic": "25-34, US"}],
            "cons": [{"statement": "Message feels generic to tech-savvy audiences", "percent": 41.0, "demographic": "18-24, global"}],
        },
    }

    data, dbg = complete_structured_generic(
        provider=provider,
        temperature=temperature,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        tool_name=tool_name,
        tool_description=tool_desc,
        json_schema=schema,
        schema_hint=schema_hint,
        timeout_s=timeout_s,
        max_tokens=max_tokens,
    )

    # Validate with Pydantic model for safety
    llm_output = LLMInsightsAggregate.model_validate(data)
    # Expand scores if we deduped
    if fast and counts is not None and len(counts) == len(llm_output.per_insight_scores):
        expanded: List[float] = []
        for score, cnt in zip(llm_output.per_insight_scores, counts):
            expanded.extend([score] * cnt)
        llm_output.per_insight_scores = expanded
    return llm_output, dbg


