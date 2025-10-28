"""
FastAPI Endpoints for Persona Agent System
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from agents.persona_agent import PersonaAgentManager

router = APIRouter(prefix="/agents", tags=["Persona Agents"])

# Global agent manager instance
agent_manager = PersonaAgentManager()


# Request/Response Models
class ChatRequest(BaseModel):
    persona_id: str = Field(..., description="ID of the persona to chat with")
    message: str = Field(..., description="User's message/query")
    include_retrieval: bool = Field(True, description="Whether to retrieve relevant context")


class ChatResponse(BaseModel):
    persona_name: str
    persona_summary: str
    response: str
    retrieved_context: List[Dict[str, Any]]


class AdAnalysisRequest(BaseModel):
    ad_description: str = Field(..., description="Description of the ad creative")
    persona_id: Optional[str] = Field(None, description="Specific persona ID (optional)")


class PersonaAnalysis(BaseModel):
    persona_name: str
    persona_summary: str
    demographics: Dict[str, Any]
    analysis: str


class MultiAdAnalysisRequest(BaseModel):
    ad_description: str = Field(..., description="Description of the ad creative")
    persona_ids: Optional[List[str]] = Field(None, description="List of persona IDs to use")
    num_personas: int = Field(5, description="Number of random personas if persona_ids not provided")


class PersonaSummary(BaseModel):
    id: str
    name: str
    summary: str


# Endpoints
@router.get("/personas", response_model=List[PersonaSummary])
async def list_personas():
    """
    List all available personas that can be used as agents

    Returns a list of persona summaries with their IDs, names, and descriptions.
    """
    try:
        personas = agent_manager.list_available_personas()
        return personas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing personas: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat_with_persona(request: ChatRequest):
    """
    Chat with a specific persona agent

    The agent will respond from the persona's perspective and can retrieve
    relevant information from Elasticsearch to inform its response.

    Args:
        request: Chat request with persona_id, message, and retrieval flag

    Returns:
        Response from the persona including retrieved context
    """
    try:
        agent = agent_manager.get_agent(request.persona_id)
        result = agent.chat(request.message, include_retrieval=request.include_retrieval)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Persona not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error chatting with persona: {str(e)}")


@router.post("/analyze-ad", response_model=PersonaAnalysis)
async def analyze_ad_single_persona(request: AdAnalysisRequest):
    """
    Get feedback on an ad creative from a single persona's perspective

    Args:
        request: Ad analysis request with ad_description and optional persona_id

    Returns:
        Detailed analysis from the persona including reactions, suggestions, and engagement likelihood
    """
    try:
        # If no persona_id provided, use a random one
        if not request.persona_id:
            personas = agent_manager.list_available_personas()
            if not personas:
                raise HTTPException(status_code=404, detail="No personas available")
            import random
            request.persona_id = random.choice(personas)["id"]

        agent = agent_manager.get_agent(request.persona_id)
        analysis = agent.analyze_ad_creative(request.ad_description)
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Persona not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing ad: {str(e)}")


@router.post("/analyze-ad-multi", response_model=List[PersonaAnalysis])
async def analyze_ad_multiple_personas(request: MultiAdAnalysisRequest):
    """
    Get feedback on an ad creative from multiple personas

    This endpoint is useful for getting diverse perspectives on an ad from
    different audience segments.

    Args:
        request: Multi-ad analysis request with ad_description, optional persona_ids, and num_personas

    Returns:
        List of analyses from different personas
    """
    try:
        analyses = agent_manager.multi_persona_analysis(
            ad_description=request.ad_description,
            persona_ids=request.persona_ids,
            num_personas=request.num_personas
        )
        return analyses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing ad: {str(e)}")


@router.get("/persona/{persona_id}/context")
async def get_persona_context(persona_id: str):
    """
    Get the full context/profile for a specific persona

    Args:
        persona_id: ID of the persona

    Returns:
        Full persona context including demographics, psychographics, pain points, etc.
    """
    try:
        agent = agent_manager.get_agent(persona_id)
        return {
            "persona_id": persona_id,
            "context": agent.get_context(),
            "persona_data": agent.persona_data
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Persona not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving persona: {str(e)}")


@router.get("/persona/{persona_id}/similar")
async def get_similar_personas(
    persona_id: str,
    k: int = Query(3, description="Number of similar personas to return")
):
    """
    Find personas similar to the given persona

    Args:
        persona_id: ID of the persona
        k: Number of similar personas to return

    Returns:
        List of similar personas with similarity scores
    """
    try:
        agent = agent_manager.get_agent(persona_id)
        similar = agent.retrieve_similar_personas(k=k)
        return {
            "persona_id": persona_id,
            "persona_name": agent.persona_data.get("name", "Unknown"),
            "similar_personas": similar
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Persona not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding similar personas: {str(e)}")
