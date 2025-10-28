"""
Knowledge Graph Operations for AdVisor
Handles CRUD operations for personas, communities, interests, and creative preferences
"""
from typing import List, Dict, Optional, Any
from uuid import UUID
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import get_client


class KnowledgeGraph:
    """
    Wrapper for Knowledge Graph operations on Supabase
    """

    def __init__(self):
        self.client = get_client()

    # ========================================================================
    # PERSONA OPERATIONS
    # ========================================================================

    def create_persona(
        self,
        name: str,
        summary: str,
        demographics: Optional[Dict] = None,
        psychographics: Optional[Dict] = None,
        pain_points: Optional[List[str]] = None,
        motivations: Optional[List[str]] = None,
    ) -> Dict:
        """Create a new persona"""
        data = {
            "name": name,
            "summary": summary,
            "demographics": demographics or {},
            "psychographics": psychographics or {},
            "pain_points": pain_points or [],
            "motivations": motivations or [],
        }
        response = self.client.table("personas").insert(data).execute()
        return response.data[0] if response.data else None

    def get_persona(self, persona_id: str) -> Optional[Dict]:
        """Get persona by ID"""
        response = self.client.table("personas").select("*").eq("id", persona_id).execute()
        return response.data[0] if response.data else None

    def get_persona_by_name(self, name: str) -> Optional[Dict]:
        """Get persona by name"""
        response = self.client.table("personas").select("*").eq("name", name).execute()
        return response.data[0] if response.data else None

    def list_personas(self, limit: int = 100) -> List[Dict]:
        """List all personas"""
        response = self.client.table("personas").select("*").limit(limit).execute()
        return response.data or []

    def update_persona(self, persona_id: str, updates: Dict) -> Dict:
        """Update persona fields"""
        response = self.client.table("personas").update(updates).eq("id", persona_id).execute()
        return response.data[0] if response.data else None

    def delete_persona(self, persona_id: str) -> bool:
        """Delete persona (cascades to relationships)"""
        response = self.client.table("personas").delete().eq("id", persona_id).execute()
        return len(response.data) > 0

    # ========================================================================
    # COMMUNITY OPERATIONS
    # ========================================================================

    def create_community(
        self,
        name: str,
        platform: str = "reddit",
        description: Optional[str] = None,
        member_count: Optional[int] = None,
        activity_level: Optional[str] = None,
        topic_categories: Optional[List[str]] = None,
    ) -> Dict:
        """Create a new community"""
        data = {
            "name": name,
            "platform": platform,
            "description": description,
            "member_count": member_count,
            "activity_level": activity_level,
            "topic_categories": topic_categories or [],
        }
        response = self.client.table("communities").insert(data).execute()
        return response.data[0] if response.data else None

    def get_community(self, community_id: str) -> Optional[Dict]:
        """Get community by ID"""
        response = self.client.table("communities").select("*").eq("id", community_id).execute()
        return response.data[0] if response.data else None

    def get_community_by_name(self, name: str) -> Optional[Dict]:
        """Get community by name"""
        response = self.client.table("communities").select("*").eq("name", name).execute()
        return response.data[0] if response.data else None

    def list_communities(self, limit: int = 100) -> List[Dict]:
        """List all communities"""
        response = self.client.table("communities").select("*").limit(limit).execute()
        return response.data or []

    # ========================================================================
    # INTEREST OPERATIONS
    # ========================================================================

    def create_interest(
        self,
        label: str,
        category: Optional[str] = None,
        description: Optional[str] = None,
        keywords: Optional[List[str]] = None,
    ) -> Dict:
        """Create a new interest"""
        data = {
            "label": label,
            "category": category,
            "description": description,
            "keywords": keywords or [],
        }
        response = self.client.table("interests").insert(data).execute()
        return response.data[0] if response.data else None

    def get_interest(self, interest_id: str) -> Optional[Dict]:
        """Get interest by ID"""
        response = self.client.table("interests").select("*").eq("id", interest_id).execute()
        return response.data[0] if response.data else None

    def list_interests(self, limit: int = 100) -> List[Dict]:
        """List all interests"""
        response = self.client.table("interests").select("*").limit(limit).execute()
        return response.data or []

    # ========================================================================
    # CREATIVE PREFERENCE OPERATIONS
    # ========================================================================

    def create_creative_pref(
        self,
        label: str,
        category: Optional[str] = None,
        description: Optional[str] = None,
        examples: Optional[Dict] = None,
    ) -> Dict:
        """Create a new creative preference"""
        data = {
            "label": label,
            "category": category,
            "description": description,
            "examples": examples or {},
        }
        response = self.client.table("creative_prefs").insert(data).execute()
        return response.data[0] if response.data else None

    def get_creative_pref(self, pref_id: str) -> Optional[Dict]:
        """Get creative preference by ID"""
        response = self.client.table("creative_prefs").select("*").eq("id", pref_id).execute()
        return response.data[0] if response.data else None

    def list_creative_prefs(self, limit: int = 100) -> List[Dict]:
        """List all creative preferences"""
        response = self.client.table("creative_prefs").select("*").limit(limit).execute()
        return response.data or []

    # ========================================================================
    # RELATIONSHIP OPERATIONS
    # ========================================================================

    def link_persona_community(
        self, persona_id: str, community_id: str, relevance_score: float = 1.0, context: str = ""
    ) -> Dict:
        """Link persona to community"""
        data = {
            "persona_id": persona_id,
            "community_id": community_id,
            "relevance_score": relevance_score,
            "context": context,
        }
        response = self.client.table("persona_community").insert(data).execute()
        return response.data[0] if response.data else None

    def link_persona_interest(
        self, persona_id: str, interest_id: str, affinity_score: float = 1.0, context: str = ""
    ) -> Dict:
        """Link persona to interest"""
        data = {
            "persona_id": persona_id,
            "interest_id": interest_id,
            "affinity_score": affinity_score,
            "context": context,
        }
        response = self.client.table("persona_interest").insert(data).execute()
        return response.data[0] if response.data else None

    def link_persona_pref(
        self, persona_id: str, pref_id: str, importance_score: float = 1.0, rationale: str = ""
    ) -> Dict:
        """Link persona to creative preference"""
        data = {
            "persona_id": persona_id,
            "pref_id": pref_id,
            "importance_score": importance_score,
            "rationale": rationale,
        }
        response = self.client.table("persona_pref").insert(data).execute()
        return response.data[0] if response.data else None

    # ========================================================================
    # COMPLEX QUERIES
    # ========================================================================

    def get_persona_with_relationships(self, persona_id: str) -> Dict:
        """
        Get persona with all related entities (communities, interests, prefs)
        Uses the get_persona_context RPC function
        """
        response = self.client.rpc("get_persona_context", {"persona_id_input": persona_id}).execute()
        return response.data if response.data else None

    def get_persona_communities(self, persona_id: str) -> List[Dict]:
        """Get all communities linked to a persona"""
        response = (
            self.client.table("persona_community")
            .select("*, communities(*)")
            .eq("persona_id", persona_id)
            .execute()
        )
        return response.data or []

    def get_persona_interests(self, persona_id: str) -> List[Dict]:
        """Get all interests linked to a persona"""
        response = (
            self.client.table("persona_interest")
            .select("*, interests(*)")
            .eq("persona_id", persona_id)
            .execute()
        )
        return response.data or []

    def get_persona_prefs(self, persona_id: str) -> List[Dict]:
        """Get all creative preferences linked to a persona"""
        response = (
            self.client.table("persona_pref")
            .select("*, creative_prefs(*)")
            .eq("persona_id", persona_id)
            .execute()
        )
        return response.data or []

    def get_community_personas(self, community_id: str) -> List[Dict]:
        """Get all personas linked to a community"""
        response = (
            self.client.table("persona_community")
            .select("*, personas(*)")
            .eq("community_id", community_id)
            .execute()
        )
        return response.data or []

    def search_personas_by_demographics(self, age_range: str = None, income_level: str = None) -> List[Dict]:
        """Search personas by demographic filters"""
        query = self.client.table("personas").select("*")

        if age_range:
            query = query.eq("demographics->>age_range", age_range)
        if income_level:
            query = query.eq("demographics->>income_level", income_level)

        response = query.execute()
        return response.data or []
