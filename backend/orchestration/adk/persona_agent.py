"""
Persona agent factory for ADK orchestration.

Creates lightweight persona "agents" from Supabase persona records.
Each agent analyses an ad from its persona's unique perspective and
returns a structured result: {attention, insight, persona_name, persona_id}.

These are NOT hand-written agents -- they are built dynamically from
database records at runtime.
"""
import json
import asyncio
import os
from typing import Dict, Any, List, Optional, Tuple

from openai import OpenAI


def build_system_prompt(persona: Dict[str, Any]) -> str:
    """Build the system prompt that makes the LLM embody *this* persona.

    Args:
        persona: A Supabase persona record with fields like name, summary,
            demographics, psychographics, pain_points, motivations.

    Returns:
        A system-prompt string.
    """
    demographics = persona.get("demographics", {})
    psychographics = persona.get("psychographics", {})
    pain_points = persona.get("pain_points", [])
    motivations = persona.get("motivations", [])

    # Parse JSON strings if stored as text in Supabase
    if isinstance(demographics, str):
        try:
            demographics = json.loads(demographics)
        except Exception:
            demographics = {}
    if isinstance(psychographics, str):
        try:
            psychographics = json.loads(psychographics)
        except Exception:
            psychographics = {}

    return f"""You are embodying this persona:
Name: {persona.get('name', 'Unknown')}
Summary: {persona.get('summary', '')}
Demographics: Age {demographics.get('age_range', 'unknown')}, Income {demographics.get('income_level', 'unknown')}
Values: {psychographics.get('values', [])}
Pain Points: {', '.join(pain_points) if pain_points else 'None'}
Motivations: {', '.join(motivations) if motivations else 'None'}

You are reviewing an advertisement. Respond authentically from this persona's perspective.
Your response must be in this exact JSON format:
{{
  "attention": "full" | "partial" | "ignore",
  "insight": "A single sentence explaining your reaction as this persona"
}}

Attention levels:
- "full": This ad is highly relevant and compelling to you
- "partial": Somewhat interesting but needs refinement
- "ignore": Not relevant or appealing to you

Be honest and specific based on your persona's demographics, values, and pain points."""


def build_user_prompt(feature_vector: Dict[str, Any]) -> str:
    """Build the user message describing the ad's extracted features.

    Args:
        feature_vector: The extracted feature dict (moondream + visual features).

    Returns:
        User-prompt string.
    """
    moondream = feature_vector.get("moondream", {})
    features = feature_vector.get("features", {})

    return f"""Analyze this advertisement:

CREATIVE SUMMARY: {moondream.get('summary', 'N/A')}
CAPTION: {moondream.get('caption', 'N/A')}
CALL TO ACTION: {moondream.get('cta', 'N/A')}
KEYWORDS: {', '.join(moondream.get('keywords', []))}
TARGET AUDIENCE: {moondream.get('target_audience', 'N/A')}

VISUAL FEATURES:
- Colors: {features.get('color', {}).get('palette_hex', [])}
- Colorfulness: {features.get('color', {}).get('colorfulness', 'N/A')}
- Aspect Ratio: {features.get('layout', {}).get('aspect_ratio', 'N/A')}
- Whitespace: {features.get('layout', {}).get('whitespace_ratio', 'N/A')}

How would YOU as this persona react to this ad? Provide your response in JSON format."""


def _parse_llm_response(text: str) -> Tuple[str, str]:
    """Extract attention + insight from LLM response text.

    Returns:
        (attention, insight) tuple.  Falls back to ("partial", <raw text>)
        if JSON parsing fails.
    """
    json_start = text.find("{")
    json_end = text.rfind("}") + 1
    if json_start >= 0 and json_end > json_start:
        try:
            data = json.loads(text[json_start:json_end])
            attention = data.get("attention", "partial")
            insight = data.get("insight", "No specific feedback provided.")
            return attention, insight
        except json.JSONDecodeError:
            pass
    # Fallback heuristic
    return _heuristic_attention(text), text[:200]


def _heuristic_attention(text: str) -> str:
    lower = text.lower()
    full_kw = ["compelling", "engaging", "interested", "resonates", "relevant to my"]
    ignore_kw = ["not relevant", "doesn't apply", "wouldn't engage", "skip this", "not interested"]
    if any(k in lower for k in full_kw):
        return "full"
    if any(k in lower for k in ignore_kw):
        return "ignore"
    return "partial"


# ---------------------------------------------------------------------------
# Core async analysis -- called during the fan-out phase
# ---------------------------------------------------------------------------

async def analyze_single_persona(
    persona: Dict[str, Any],
    feature_vector: Dict[str, Any],
    openai_client: Optional[OpenAI] = None,
) -> Dict[str, Any]:
    """Run a single persona's ad analysis via the LLM.

    This is the function invoked in parallel for each persona during the
    ADK fan-out step.  It uses the OpenAI client (or whichever LLM
    provider is configured) to generate a response.

    Args:
        persona: Supabase persona record.
        feature_vector: Extracted ad features.
        openai_client: An OpenAI client instance (shared across calls).

    Returns:
        Dict with persona_id, persona_name, insight, attention.
    """
    persona_id = str(persona["id"])
    system_prompt = build_system_prompt(persona)
    user_prompt = build_user_prompt(feature_vector)

    if openai_client is None:
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    try:
        # Run the blocking OpenAI call in a thread so we don't block the
        # event loop during fan-out.
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=200,
                response_format={"type": "json_object"},
            ),
        )
        text = response.choices[0].message.content
        attention, insight = _parse_llm_response(text)
    except Exception as exc:
        print(f"Error analysing with persona {persona_id}: {exc}")
        attention, insight = "partial", "Analysis unavailable due to API error."

    return {
        "persona_id": persona_id,
        "persona_name": persona.get("name", "Unknown"),
        "insight": insight,
        "attention": attention,
    }


async def fan_out_persona_analyses(
    personas: List[Dict[str, Any]],
    feature_vector: Dict[str, Any],
    concurrency: int = 10,
) -> Dict[str, Dict[str, Any]]:
    """Fan-out ad analysis across many personas concurrently.

    Uses ``asyncio.Semaphore`` to cap the number of concurrent LLM calls
    (to respect rate limits) while still running them in parallel.

    Args:
        personas: List of Supabase persona records.
        feature_vector: Extracted ad features.
        concurrency: Max concurrent LLM calls (default 10).

    Returns:
        Dict mapping persona_id -> {insight, attention, persona_name}.
    """
    if not personas:
        return {}

    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    sem = asyncio.Semaphore(concurrency)

    async def _guarded(persona: Dict[str, Any]) -> Dict[str, Any]:
        async with sem:
            return await analyze_single_persona(persona, feature_vector, openai_client)

    tasks = [_guarded(p) for p in personas]
    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    results: Dict[str, Dict[str, Any]] = {}
    for item in results_list:
        if isinstance(item, Exception):
            print(f"Persona analysis exception: {item}")
            continue
        pid = item["persona_id"]
        results[pid] = {
            "insight": item["insight"],
            "attention": item["attention"],
            "persona_name": item["persona_name"],
        }
    return results
