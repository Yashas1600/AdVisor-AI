"""
Ad Analysis Orchestration Endpoint
Selects relevant personas, uses OpenAI agents for analysis, saves results to Supabase
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import sys
from pathlib import Path
import time
import asyncio
import os

sys.path.append(str(Path(__file__).parent.parent.parent))

from api.smart_agent_selector import smart_selector
from db.supabase_client import supabase_client
from openai import AsyncOpenAI

router = APIRouter(prefix="/api", tags=["Ad Analysis"])

ADVISOR_CONCURRENCY = int(os.getenv("ADVISOR_CONCURRENCY", "25"))
PERSONA_TIMEOUT = int(os.getenv("PERSONA_TIMEOUT", "30"))


# Request/Response Models
class AdAnalysisRequest(BaseModel):
    """Request for intelligent ad analysis with persona selection"""
    ad_id: Optional[str] = Field(None, description="Optional: ID of existing ad analysis from Supabase")
    feature_vector: Dict[str, Any] = Field(..., description="Extracted features from the ad (moondream, colors, layout, etc.)")
    target_age_range: Optional[str] = Field(None, description="Target age range: '18-24', '25-34', '35-44', '45+'")
    industry_keywords: Optional[List[str]] = Field(None, description="Industry/interest keywords (e.g., ['fitness', 'health'])")
    num_personas: int = Field(50, description="Number of personas to select")

    # Optional: Full ad_analyses record data (for creating new record)
    ad_name: Optional[str] = Field(None, description="Name of the ad")
    brand_name: Optional[str] = Field(None, description="Brand name")
    image_url: Optional[str] = Field(None, description="URL of the ad image")
    user_id: Optional[str] = Field(None, description="User ID who created the ad")


class PersonaAnalysisResult(BaseModel):
    """Result from a single persona's analysis"""
    persona_id: str
    persona_name: str
    insight: str
    attention: str  # "full", "partial", "ignore"


class AdAnalysisResponse(BaseModel):
    """Response with analysis results and metadata"""
    ad_id: str
    selected_personas: List[Dict[str, Any]]
    analysis_results: Dict[str, Any]  # Maps persona_id -> {insight, attention}
    summary: Dict[str, Any]


def _build_persona_prompt(persona: Dict[str, Any]) -> str:
    """Build system prompt for a persona."""
    demographics = persona.get('demographics', {})
    psychographics = persona.get('psychographics', {})
    pain_points = persona.get('pain_points', [])
    motivations = persona.get('motivations', [])

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


def _build_ad_prompt(feature_vector: Dict[str, Any]) -> str:
    """Build user prompt from ad features."""
    moondream = feature_vector.get('moondream', {})
    features = feature_vector.get('features', {})

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


async def _analyze_single_persona(
    client: AsyncOpenAI,
    persona: Dict[str, Any],
    ad_prompt: str,
    semaphore: asyncio.Semaphore,
    index: int,
) -> tuple[int, str, Dict[str, Any]]:
    """Analyze ad from a single persona's perspective. Returns (index, persona_id, result)."""
    persona_id = str(persona['id'])
    system_prompt = _build_persona_prompt(persona)

    async with semaphore:
        try:
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": ad_prompt},
                    ],
                    temperature=0.7,
                    max_tokens=200,
                    response_format={"type": "json_object"},
                ),
                timeout=PERSONA_TIMEOUT,
            )

            response_text = response.choices[0].message.content
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                analysis = json.loads(response_text[json_start:json_end])
                attention = analysis.get('attention', 'partial')
                insight = analysis.get('insight', 'No specific feedback provided.')
            else:
                attention = _extract_attention_level(response_text)
                insight = response_text[:200]

        except asyncio.TimeoutError:
            print(f"Timeout for persona {persona_id}")
            attention = "partial"
            insight = "Analysis timed out."
        except Exception as e:
            error_msg = str(e)
            if "400" in error_msg or "Bad Request" in error_msg:
                print(f"API Error for persona {persona_id}: {error_msg[:100]}")
            else:
                print(f"Error analyzing with persona {persona_id}: {e}")
            attention = "partial"
            insight = "Analysis unavailable due to API error."

    return (index, persona_id, {
        "insight": insight,
        "attention": attention,
        "persona_name": persona.get('name', 'Unknown'),
    })


@router.post("/analyze-ad-smart", response_model=AdAnalysisResponse)
async def analyze_ad_with_smart_selection(request: AdAnalysisRequest):
    """
    Intelligently analyze an ad using:
    1. Smart persona selection (age + 40% industry match)
    2. OpenAI GPT-4o-mini to analyze feature vectors from each persona's perspective
    3. Aggregate results and save to Supabase

    Returns:
        Analysis results with persona insights and attention levels
    """
    try:
        # Step 1: Select relevant personas
        print(f"Selecting {request.num_personas} personas...")
        selected_personas = smart_selector.select_relevant_personas(
            target_age_range=request.target_age_range,
            industry_keywords=request.industry_keywords,
            num_personas=request.num_personas,
            industry_match_ratio=0.4
        )

        if not selected_personas:
            raise HTTPException(
                status_code=404,
                detail="No personas found matching criteria"
            )

        print(f"Selected {len(selected_personas)} personas")

        # Step 2: Run concurrent analysis
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        semaphore = asyncio.Semaphore(ADVISOR_CONCURRENCY)
        ad_prompt = _build_ad_prompt(request.feature_vector)

        t0 = time.monotonic()

        tasks = [
            _analyze_single_persona(client, persona, ad_prompt, semaphore, idx)
            for idx, persona in enumerate(selected_personas)
        ]
        results = await asyncio.gather(*tasks)

        elapsed = time.monotonic() - t0
        print(f"Completed {len(results)} persona analyses in {elapsed:.1f}s (concurrency={ADVISOR_CONCURRENCY})")

        # Build results dict in stable order
        results_sorted = sorted(results, key=lambda r: r[0])
        analysis_results = {}
        attention_counts = {"full": 0, "partial": 0, "ignore": 0}
        for _idx, persona_id, result in results_sorted:
            analysis_results[persona_id] = result
            attention_counts[result["attention"]] += 1

        # Step 3: Create summary
        total = len(analysis_results)
        summary = {
            "total_personas": total,
            "attention": {
                "full": attention_counts["full"],
                "partial": attention_counts["partial"],
                "ignore": attention_counts["ignore"]
            },
            "attention_percentages": {
                "full": round((attention_counts["full"] / total) * 100, 1) if total > 0 else 0,
                "partial": round((attention_counts["partial"] / total) * 100, 1) if total > 0 else 0,
                "ignore": round((attention_counts["ignore"] / total) * 100, 1) if total > 0 else 0
            },
            "latency_seconds": round(elapsed, 2),
        }

        # Step 4: Save to Supabase ad_analyses table
        agent_results = {
            "byId": analysis_results,
            "selected": list(analysis_results.keys())
        }

        saved_ad_id = request.ad_id

        if request.ad_id:
            print(f"Updating existing ad_analyses record: {request.ad_id}")
            try:
                check_response = supabase_client.from_("ad_analyses").select("id").eq("id", request.ad_id).execute()

                if not check_response.data or len(check_response.data) == 0:
                    print(f"Record {request.ad_id} does not exist. Creating instead...")
                    insert_data = {
                        "id": request.ad_id,
                        "title": request.ad_name or "Untitled Ad",
                        "input": {"brand": request.brand_name or "Unknown", "desc": ""},
                        "output": {"panelData": None},
                        "feature_output": request.feature_vector,
                        "agent_results": agent_results,
                    }
                    insert_response = supabase_client.from_("ad_analyses").insert(insert_data).execute()
                    if insert_response.data:
                        print(f"Created new record with id: {request.ad_id}")
                    else:
                        print(f"Failed to create record: {insert_response}")
                else:
                    update_response = supabase_client.from_("ad_analyses").update({
                        "agent_results": agent_results
                    }).eq("id", request.ad_id).execute()

                    if not update_response.data:
                        print(f"Update failed: {update_response}")
                    else:
                        print(f"Updated agent_results for ad_id: {request.ad_id}")
            except Exception as e:
                print(f"Error with Supabase: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("Creating new ad_analyses record with agent_results")
            try:
                insert_data = {
                    "ad_name": request.ad_name or "Untitled Ad",
                    "brand_name": request.brand_name or "Unknown Brand",
                    "image_url": request.image_url,
                    "user_id": request.user_id,
                    "features": request.feature_vector,
                    "agent_results": agent_results,
                    "status": "completed"
                }

                insert_response = supabase_client.from_("ad_analyses").insert(insert_data).execute()

                if insert_response.data and len(insert_response.data) > 0:
                    saved_ad_id = insert_response.data[0].get('id')
                    print(f"Created ad_analyses record with id: {saved_ad_id}")
                else:
                    print("Warning: Could not create ad_analyses record")
            except Exception as e:
                print(f"Error creating Supabase record: {e}")

        # Step 5: Return response
        return AdAnalysisResponse(
            ad_id=saved_ad_id,
            selected_personas=selected_personas,
            analysis_results=analysis_results,
            summary=summary
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in analyze_ad_with_smart_selection: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing ad: {str(e)}"
        )


def _extract_attention_level(analysis_text: str) -> str:
    """
    Extract attention level from analysis text using heuristics

    Returns: "full", "partial", or "ignore"
    """
    text_lower = analysis_text.lower()

    full_keywords = [
        "compelling", "engaging", "interested", "would consider",
        "strong hook", "clear value", "resonates", "relevant to my"
    ]

    ignore_keywords = [
        "not relevant", "doesn't apply", "wouldn't engage",
        "skip this", "not interested", "generic", "ineffective"
    ]

    if any(keyword in text_lower for keyword in full_keywords):
        return "full"

    if any(keyword in text_lower for keyword in ignore_keywords):
        return "ignore"

    return "partial"
