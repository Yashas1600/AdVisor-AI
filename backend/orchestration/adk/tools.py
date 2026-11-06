"""
ADK tools for AdVisor analysis pipeline.

Each tool wraps an existing service (feature extraction, persona selection,
result aggregation) so the coordinator agent can invoke them.
"""
import json
from typing import Dict, Any, List, Optional

# Lazy-loaded reference to the smart selector singleton.
# Stored at module level so tests can patch ``orchestration.adk.tools._get_selector``.
_selector_instance = None


def _get_selector():
    """Return the SmartAgentSelector singleton (lazy import)."""
    global _selector_instance
    if _selector_instance is None:
        from api.smart_agent_selector import smart_selector
        _selector_instance = smart_selector
    return _selector_instance


def extract_features(
    ad_id: str,
    file_data_b64: Optional[str] = None,
    modality: str = "image",
    filename: str = "ad.png",
) -> Dict[str, Any]:
    """Run the feature extraction pipeline on an uploaded ad creative.

    This tool is exposed to the coordinator but in practice we call it
    *before* the ADK pipeline starts (feature extraction requires raw bytes
    that don't travel well through LLM context).  The tool is kept here so
    the coordinator can reference it in its plan and so tests can mock it.

    Args:
        ad_id: Unique identifier for the ad.
        file_data_b64: Base-64 encoded file bytes (unused in the ADK path
            because extraction happens before orchestration).
        modality: "image" or "video".
        filename: Original file name.

    Returns:
        Dict with keys ``media``, ``features``, and optionally ``moondream``.
    """
    # In the real ADK flow the feature_vector is already extracted and
    # passed into session state before the coordinator runs.  This
    # function exists as a callable placeholder / for tests.
    return {
        "ad_id": ad_id,
        "status": "pre-extracted",
        "note": "Feature vector should already be in session state.",
    }


def select_personas(
    target_age_range: Optional[str] = None,
    industry_keywords: Optional[List[str]] = None,
    num_personas: int = 50,
    industry_match_ratio: float = 0.4,
) -> List[Dict[str, Any]]:
    """Select relevant personas using the SmartAgentSelector.

    Wraps ``api.smart_agent_selector.smart_selector.select_relevant_personas``
    so the coordinator can call it as an ADK tool.

    Args:
        target_age_range: e.g. "18-24", "25-34", "35-44", "45+"
        industry_keywords: Interest/industry tags for matching.
        num_personas: How many personas to return (default 50).
        industry_match_ratio: Fraction that should match industry (default 0.4).

    Returns:
        List of persona dicts from Supabase.
    """
    selector = _get_selector()
    personas = selector.select_relevant_personas(
        target_age_range=target_age_range,
        industry_keywords=industry_keywords,
        num_personas=num_personas,
        industry_match_ratio=industry_match_ratio,
    )
    return personas


def aggregate_results(
    analysis_results: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Aggregate per-persona analysis results into a summary.

    Args:
        analysis_results: Mapping of persona_id -> {insight, attention, persona_name}.

    Returns:
        Summary dict with attention counts and percentages.
    """
    total = len(analysis_results)
    attention_counts = {"full": 0, "partial": 0, "ignore": 0}

    for result in analysis_results.values():
        level = result.get("attention", "partial")
        if level in attention_counts:
            attention_counts[level] += 1
        else:
            attention_counts["partial"] += 1

    summary = {
        "total_personas": total,
        "attention": dict(attention_counts),
        "attention_percentages": {
            k: round((v / total) * 100, 1) if total > 0 else 0
            for k, v in attention_counts.items()
        },
    }
    return summary
