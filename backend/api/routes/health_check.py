"""
Health Check Endpoints for EC2 Deployment
Tests all critical components: Supabase, OpenAI, Fetch.ai
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

router = APIRouter(prefix="/health", tags=["Health Check"])


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    components: Dict[str, Any]
    message: str


@router.get("/", response_model=HealthCheckResponse)
async def basic_health_check():
    """Basic health check - API is running"""
    return {
        "status": "healthy",
        "components": {"api": "ok"},
        "message": "AdVisor API is running"
    }


@router.get("/smart-selector", response_model=HealthCheckResponse)
async def smart_selector_health_check():
    """
    Comprehensive health check for Smart Agent Selector
    Tests: Supabase connection, OpenAI API, Smart Selector functionality
    """
    components = {}
    errors = []

    # Test 1: Supabase Connection
    try:
        from db.supabase_client import supabase_client

        # Try to query personas table
        response = supabase_client.from_("personas").select("id").limit(1).execute()

        if response.data is not None:
            components["supabase"] = "ok"
        else:
            components["supabase"] = "error"
            errors.append("Supabase query returned no data")

    except Exception as e:
        components["supabase"] = "error"
        errors.append(f"Supabase error: {str(e)}")

    # Test 2: OpenAI API
    try:
        from openai import OpenAI
        import os

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Simple test call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )

        if response.choices[0].message.content:
            components["openai"] = "ok"
        else:
            components["openai"] = "error"
            errors.append("OpenAI returned empty response")

    except Exception as e:
        components["openai"] = "error"
        errors.append(f"OpenAI error: {str(e)}")

    # Test 3: Smart Selector
    try:
        from api.smart_agent_selector import smart_selector

        # Test with minimal parameters
        personas = smart_selector.select_relevant_personas(
            target_age_range="18-24",
            industry_keywords=["fitness"],
            num_personas=5,
            industry_match_ratio=0.4
        )

        if personas and len(personas) > 0:
            components["smart_selector"] = "ok"
            components["smart_selector_details"] = {
                "personas_returned": len(personas),
                "test_passed": True
            }
        else:
            components["smart_selector"] = "warning"
            components["smart_selector_details"] = {
                "personas_returned": 0,
                "test_passed": False
            }
            errors.append("Smart selector returned no personas")

    except Exception as e:
        components["smart_selector"] = "error"
        errors.append(f"Smart selector error: {str(e)}")

    # Determine overall status
    if all(v == "ok" for v in components.values() if isinstance(v, str)):
        status = "healthy"
        message = "All components operational"
    elif "error" in components.values():
        status = "unhealthy"
        message = f"Errors detected: {'; '.join(errors)}"
    else:
        status = "degraded"
        message = f"Some warnings: {'; '.join(errors)}"

    return {
        "status": status,
        "components": components,
        "message": message
    }


@router.get("/asi-one", response_model=HealthCheckResponse)
async def asi_one_health_check():
    """
    Health check for Fetch.ai ASI:One API
    Tests: ASI:One API connectivity and response
    """
    components = {}
    errors = []

    try:
        from utils.fetchai_client import FetchAIClient

        client = FetchAIClient(model="asi1-mini")

        # Simple test call
        response = client.generate_response(
            prompt="Hello",
            temperature=0.7,
            max_tokens=10
        )

        if response:
            components["asi_one"] = "ok"
            components["asi_one_details"] = {
                "model": "asi1-mini",
                "test_passed": True,
                "response_received": True
            }
        else:
            components["asi_one"] = "error"
            errors.append("ASI:One returned empty response")

    except Exception as e:
        components["asi_one"] = "error"
        errors.append(f"ASI:One error: {str(e)}")

    # Determine status
    if all(v == "ok" for v in components.values() if isinstance(v, str)):
        status = "healthy"
        message = "ASI:One API operational"
    else:
        status = "unhealthy"
        message = f"Errors: {'; '.join(errors)}"

    return {
        "status": status,
        "components": components,
        "message": message
    }
