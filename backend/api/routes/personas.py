"""
Personas API Routes
Fetch all personas from Supabase for frontend visualization
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from db.supabase_client import supabase_client

router = APIRouter(prefix="/api/personas", tags=["Personas"])

# Mapping of subreddit names to display names (1:1 mapping for 20 communities)
COMMUNITY_DISPLAY_NAMES = {
    "r/Fitness": "Fitness Enthusiasts",
    "r/bodyweightfitness": "Bodyweight Fitness Enthusiasts",
    "r/Anxiety": "Mental Health Advocates",
    "r/minimalism": "Minimalist Lifestyle",
    "r/motorcycles": "Automotive Hobbyists",
    "r/ProRevenge": "Revenge Story Enthusiasts",
    "r/tifu": "TIFU Community",
    "r/relationship_advice": "Relationship Advisors",
    "r/MaliciousCompliance": "Malicious Compliance Fans",
    "r/BestofRedditorUpdates": "Reddit Drama Followers",
    "r/pokemon": "Avid Gamers",
    "r/CuratedTumblr": "Fashion Enthusiasts",
    "r/YouShouldKnow": "Knowledge Seekers",
    "r/science": "Science Enthusiasts",
    "r/AmItheAsshole": "AITA Community",
    "r/LifeProTips": "Life Hackers",
    "r/todayilearned": "TIL Community",
    "r/Showerthoughts": "Philosophical Thinkers",
    "r/politics": "Political Discussants",
    "r/mildlyinfuriating": "Mildly Infuriated",
    "r/pics": "Photography Creators",
    "r/cats": "Pet Parents",
    "r/nosleep": "Horror Story Fans",
    "r/onebag": "Outdoor Adventurers",
    "r/funny": "Humor Enthusiasts",
}


@router.get("/all")
async def get_all_personas():
    """
    Fetch all personas from Supabase database with their community mappings

    Returns:
        List of all persona records with their full data and community display names
    """
    try:
        # Step 1: Fetch all personas
        personas_response = supabase_client.from_("personas").select(
            "id, name, summary, demographics, psychographics, pain_points, motivations"
        ).execute()

        if not personas_response.data:
            return {
                "personas": [],
                "total": 0,
                "communities": []
            }

        # Step 2: Fetch all persona_community relationships
        persona_community_response = supabase_client.from_("persona_community").select(
            "persona_id, community_id, communities(name)"
        ).execute()

        # Create mapping: persona_id -> community_name
        persona_to_community = {}
        if persona_community_response.data:
            for rel in persona_community_response.data:
                persona_id = rel.get('persona_id')
                community_info = rel.get('communities')
                if community_info and persona_id:
                    community_name = community_info.get('name')
                    if community_name:
                        persona_to_community[persona_id] = community_name

        personas = []
        community_set = set()  # Track unique community display names

        for persona in personas_response.data:
            # Parse JSON fields if they're stored as strings
            demographics = persona.get('demographics', {})
            psychographics = persona.get('psychographics', {})
            pain_points = persona.get('pain_points', [])
            motivations = persona.get('motivations', [])

            if isinstance(demographics, str):
                try:
                    demographics = json.loads(demographics)
                except:
                    demographics = {}

            if isinstance(psychographics, str):
                try:
                    psychographics = json.loads(psychographics)
                except:
                    psychographics = {}

            if isinstance(pain_points, str):
                try:
                    pain_points = json.loads(pain_points)
                except:
                    pain_points = []

            if isinstance(motivations, str):
                try:
                    motivations = json.loads(motivations)
                except:
                    motivations = []

            # Get community name from mapping
            persona_id = persona['id']
            community_name = persona_to_community.get(persona_id)
            community_display_name = None

            if community_name:
                # Map to display name (1:1 mapping for 20 separate communities)
                community_display_name = COMMUNITY_DISPLAY_NAMES.get(community_name, community_name)
                if community_display_name:
                    community_set.add(community_display_name)

            personas.append({
                "id": persona['id'],
                "name": persona.get('name', 'Unknown'),
                "summary": persona.get('summary', ''),
                "demographics": demographics,
                "psychographics": psychographics,
                "pain_points": pain_points,
                "motivations": motivations,
                "community_name": community_name,  # Original subreddit name
                "community_display_name": community_display_name  # Display name for UI
            })

        print(f"✓ Fetched {len(personas)} personas from Supabase with community mappings")
        print(f"✓ Found {len(community_set)} unique communities: {sorted(community_set)}")

        return {
            "personas": personas,
            "total": len(personas),
            "communities": sorted(list(community_set))  # List of unique display names
        }

    except Exception as e:
        print(f"Error fetching personas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching personas: {str(e)}"
        )
