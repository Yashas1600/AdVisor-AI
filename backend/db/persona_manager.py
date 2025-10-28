"""
Persona Manager - Integration Layer
Combines Knowledge Graph (relational) and Vector Store (semantic) operations
"""
from typing import List, Dict, Optional, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from .knowledge_graph import KnowledgeGraph
from .vector_store import VectorStore


class PersonaManager:
    """
    High-level interface for managing personas with both
    structured (KG) and semantic (vector) data
    """

    def __init__(self):
        self.kg = KnowledgeGraph()
        self.vector = VectorStore()

    # ========================================================================
    # UNIFIED PERSONA OPERATIONS
    # ========================================================================

    def create_persona_full(
        self,
        name: str,
        summary: str,
        embedding: List[float],
        demographics: Optional[Dict] = None,
        psychographics: Optional[Dict] = None,
        pain_points: Optional[List[str]] = None,
        motivations: Optional[List[str]] = None,
        communities: Optional[List[Dict]] = None,
        interests: Optional[List[Dict]] = None,
        creative_prefs: Optional[List[Dict]] = None,
        embedding_model: str = "text-embedding-ada-002",
    ) -> Dict:
        """
        Create a complete persona with both KG and vector data

        Args:
            name: Persona name
            summary: Text description
            embedding: Vector representation of the persona
            demographics: Age, gender, location, income, etc.
            psychographics: Values, lifestyle, personality traits
            pain_points: List of pain points
            motivations: List of motivations
            communities: List of dicts with {community_id, relevance_score, context}
            interests: List of dicts with {interest_id, affinity_score, context}
            creative_prefs: List of dicts with {pref_id, importance_score, rationale}
            embedding_model: Model used for embeddings

        Returns:
            Complete persona record with ID
        """
        # 1. Create persona in KG
        persona = self.kg.create_persona(
            name=name,
            summary=summary,
            demographics=demographics,
            psychographics=psychographics,
            pain_points=pain_points,
            motivations=motivations,
        )

        if not persona:
            raise ValueError("Failed to create persona")

        persona_id = persona["id"]

        # 2. Store embedding
        self.vector.store_persona_embedding(
            persona_id=persona_id,
            embedding=embedding,
            embedding_text=summary,
            model_name=embedding_model,
            metadata={
                "demographics": demographics,
                "psychographics": psychographics,
            },
        )

        # 3. Link to communities
        if communities:
            for comm in communities:
                self.kg.link_persona_community(
                    persona_id=persona_id,
                    community_id=comm["community_id"],
                    relevance_score=comm.get("relevance_score", 1.0),
                    context=comm.get("context", ""),
                )

        # 4. Link to interests
        if interests:
            for interest in interests:
                self.kg.link_persona_interest(
                    persona_id=persona_id,
                    interest_id=interest["interest_id"],
                    affinity_score=interest.get("affinity_score", 1.0),
                    context=interest.get("context", ""),
                )

        # 5. Link to creative preferences
        if creative_prefs:
            for pref in creative_prefs:
                self.kg.link_persona_pref(
                    persona_id=persona_id,
                    pref_id=pref["pref_id"],
                    importance_score=pref.get("importance_score", 1.0),
                    rationale=pref.get("rationale", ""),
                )

        return persona

    def get_persona_full_context(self, persona_id: str) -> Dict:
        """
        Get complete persona context: KG relationships + vector embedding

        Returns:
            {
                "persona": {...},
                "communities": [...],
                "interests": [...],
                "creative_prefs": [...],
                "embedding": {...}
            }
        """
        # Use the RPC function that combines everything
        context = self.kg.get_persona_with_relationships(persona_id)
        return context

    def find_similar_personas(
        self,
        query_embedding: List[float],
        match_threshold: float = 0.5,
        match_count: int = 10,
        include_full_context: bool = False,
    ) -> List[Dict]:
        """
        Find personas similar to a query embedding

        Args:
            query_embedding: Query vector
            match_threshold: Minimum similarity (0-1)
            match_count: Number of results
            include_full_context: If True, fetch full KG context for each match

        Returns:
            List of similar personas with similarity scores
        """
        matches = self.vector.match_personas(query_embedding, match_threshold, match_count)

        if include_full_context:
            # Enrich with full KG context
            for match in matches:
                persona_id = match["persona_id"]
                context = self.get_persona_full_context(persona_id)
                match["full_context"] = context

        return matches

    def find_personas_by_community_and_similarity(
        self,
        query_embedding: List[float],
        community_name: str,
        match_threshold: float = 0.5,
        match_count: int = 10,
    ) -> List[Dict]:
        """
        Hybrid search: Find personas that are:
        1. Semantically similar to query
        2. Associated with a specific community

        Args:
            query_embedding: Query vector
            community_name: Filter by community (e.g., 'r/Fitness')
            match_threshold: Minimum similarity
            match_count: Number of results

        Returns:
            Personas with similarity scores, communities, and interests
        """
        return self.vector.match_personas_hybrid(
            query_embedding=query_embedding,
            filter_community_name=community_name,
            match_threshold=match_threshold,
            match_count=match_count,
        )

    # ========================================================================
    # COMMUNITY-BASED OPERATIONS
    # ========================================================================

    def create_community_full(
        self,
        name: str,
        description: str,
        embedding: List[float],
        platform: str = "reddit",
        member_count: Optional[int] = None,
        activity_level: Optional[str] = None,
        topic_categories: Optional[List[str]] = None,
        embedding_model: str = "text-embedding-ada-002",
    ) -> Dict:
        """
        Create community with both KG and vector representation

        Args:
            name: Community name (e.g., 'r/Fitness')
            description: Text description
            embedding: Vector representation
            platform: Platform name
            member_count: Number of members
            activity_level: 'high', 'medium', 'low'
            topic_categories: List of topic tags
            embedding_model: Model used

        Returns:
            Community record with ID
        """
        # Create in KG
        community = self.kg.create_community(
            name=name,
            platform=platform,
            description=description,
            member_count=member_count,
            activity_level=activity_level,
            topic_categories=topic_categories,
        )

        if not community:
            raise ValueError("Failed to create community")

        community_id = community["id"]

        # Store embedding
        self.vector.store_community_embedding(
            community_id=community_id,
            embedding=embedding,
            embedding_text=description,
            model_name=embedding_model,
            metadata={
                "member_count": member_count,
                "activity_level": activity_level,
                "topic_categories": topic_categories,
            },
        )

        return community

    def find_similar_communities(
        self, query_embedding: List[float], match_threshold: float = 0.5, match_count: int = 10
    ) -> List[Dict]:
        """Find communities similar to a query embedding"""
        return self.vector.match_communities(query_embedding, match_threshold, match_count)

    def recommend_communities_for_persona(self, persona_id: str, top_n: int = 5) -> List[Dict]:
        """
        Recommend communities for a persona based on semantic similarity

        Args:
            persona_id: Persona UUID
            top_n: Number of recommendations

        Returns:
            List of recommended communities with similarity scores
        """
        # Get persona embedding
        persona_emb = self.vector.get_persona_embedding(persona_id)
        if not persona_emb:
            raise ValueError(f"No embedding found for persona {persona_id}")

        # Find similar communities
        recommendations = self.find_similar_communities(
            query_embedding=persona_emb["embedding"], match_count=top_n
        )

        return recommendations

    # ========================================================================
    # CONTENT-BASED OPERATIONS
    # ========================================================================

    def store_reddit_content_embedding(
        self,
        post_id: str,
        text: str,
        embedding: List[float],
        community_name: str,
        content_type: str = "post",
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Store Reddit post/comment embedding with metadata

        Args:
            post_id: Reddit post ID (e.g., 't3_abc123')
            text: Post title + body or comment text
            embedding: Vector representation
            community_name: Subreddit (e.g., 'r/Fitness')
            content_type: 'post', 'comment_cluster', 'thread'
            metadata: Upvotes, sentiment, keywords, etc.

        Returns:
            Stored embedding record
        """
        return self.vector.store_content_embedding(
            content_id=post_id,
            content_type=content_type,
            embedding=embedding,
            embedding_text=text,
            community_name=community_name,
            metadata=metadata,
        )

    def find_relevant_content_for_persona(
        self, persona_id: str, match_count: int = 20, filter_community: Optional[str] = None
    ) -> List[Dict]:
        """
        Find Reddit content relevant to a persona

        Args:
            persona_id: Persona UUID
            match_count: Number of results
            filter_community: Optional filter by subreddit

        Returns:
            Relevant posts/comments with similarity scores
        """
        # Get persona embedding
        persona_emb = self.vector.get_persona_embedding(persona_id)
        if not persona_emb:
            raise ValueError(f"No embedding found for persona {persona_id}")

        # Find similar content
        return self.vector.match_content(
            query_embedding=persona_emb["embedding"],
            match_count=match_count,
            filter_community=filter_community,
        )

    # ========================================================================
    # AD CREATIVE OPERATIONS
    # ========================================================================

    def store_ad_creative(
        self,
        ad_id: str,
        ad_copy: str,
        embedding: List[float],
        ad_type: str = "image",
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Store ad creative with embedding

        Args:
            ad_id: Unique ad identifier
            ad_copy: Ad text/description
            embedding: Vector representation
            ad_type: 'image', 'video', 'text'
            metadata: Visual features, performance, brand info

        Returns:
            Stored ad embedding
        """
        return self.vector.store_ad_embedding(
            ad_id=ad_id,
            embedding=embedding,
            embedding_text=ad_copy,
            ad_type=ad_type,
            metadata=metadata,
        )

    def find_ads_for_persona(
        self, persona_id: str, match_count: int = 10, filter_ad_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Find ad creatives that would resonate with a persona

        Args:
            persona_id: Persona UUID
            match_count: Number of results
            filter_ad_type: Filter by ad type ('image', 'video', etc.)

        Returns:
            Matching ads with similarity scores
        """
        persona_emb = self.vector.get_persona_embedding(persona_id)
        if not persona_emb:
            raise ValueError(f"No embedding found for persona {persona_id}")

        return self.vector.match_ads(
            query_embedding=persona_emb["embedding"],
            match_count=match_count,
            filter_ad_type=filter_ad_type,
        )

    def recommend_personas_for_ad(self, ad_id: str, match_count: int = 5) -> List[Dict]:
        """
        Recommend which personas would respond best to an ad

        Args:
            ad_id: Ad identifier
            match_count: Number of persona recommendations

        Returns:
            Personas with similarity scores
        """
        # Get ad embedding
        ad_emb = self.vector.client.table("ad_embeddings").select("*").eq("ad_id", ad_id).execute()

        if not ad_emb.data:
            raise ValueError(f"No embedding found for ad {ad_id}")

        ad_embedding = ad_emb.data[0]["embedding"]

        # Find similar personas
        return self.vector.match_personas(query_embedding=ad_embedding, match_count=match_count)

    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================

    def batch_store_reddit_embeddings(self, embeddings_data: List[Dict]) -> List[Dict]:
        """
        Batch insert Reddit content embeddings

        Args:
            embeddings_data: List of dicts with:
                - content_id, content_type, embedding, embedding_text,
                  community_name, metadata

        Returns:
            List of inserted records
        """
        return self.vector.batch_store_content_embeddings(embeddings_data)

    # ========================================================================
    # SIMPLE RETRIEVAL METHODS (for persona agents)
    # ========================================================================

    def list_personas(self, limit: int = 1000) -> List[Dict]:
        """
        List all personas

        Args:
            limit: Maximum number of personas to return (default 1000)

        Returns:
            List of persona dictionaries
        """
        result = self.kg.client.table("personas").select("*").limit(limit).execute()
        return result.data if result.data else []

    def get_persona(self, persona_id: str) -> Optional[Dict]:
        """
        Get a single persona by ID

        Args:
            persona_id: ID of the persona

        Returns:
            Persona dictionary or None
        """
        result = self.kg.client.table("personas").select("*").eq("id", persona_id).execute()
        return result.data[0] if result.data else None

    def search_personas_by_embedding(self, embedding: List[float], limit: int = 10) -> List[Dict]:
        """
        Search personas using vector similarity

        Args:
            embedding: Query embedding vector
            limit: Number of results to return

        Returns:
            List of similar personas with similarity scores
        """
        matches = self.vector.match_personas(embedding, match_threshold=0.5, match_count=limit)

        personas = []
        for match in matches:
            persona = self.get_persona(match.get("persona_id"))
            if persona:
                persona["similarity_score"] = match.get("similarity")
                personas.append(persona)

        return personas

    def search_communities_by_embedding(self, embedding: List[float], limit: int = 10) -> List[Dict]:
        """
        Search communities using vector similarity

        Args:
            embedding: Query embedding vector
            limit: Number of results to return

        Returns:
            List of similar communities with similarity scores
        """
        try:
            matches = self.vector.match_communities(embedding, match_threshold=0.5, match_count=limit)

            communities = []
            for match in matches:
                result = self.kg.client.table("communities").select("*").eq("community_id", match.get("community_id")).execute()
                if result.data:
                    community = result.data[0]
                    community["similarity_score"] = match.get("similarity")
                    communities.append(community)

            return communities
        except Exception as e:
            # If there's a database error, return empty list so agent can still function
            print(f"Warning: community search failed: {e}")
            return []

    def search_content_by_embedding(self, embedding: List[float], limit: int = 10) -> List[Dict]:
        """
        Search content using vector similarity

        Args:
            embedding: Query embedding vector
            limit: Number of results to return

        Returns:
            List of similar content items with similarity scores
        """
        try:
            matches = self.vector.match_content(embedding, match_threshold=0.5, match_count=limit)

            content_items = []
            for match in matches:
                result = self.kg.client.table("content").select("*").eq("content_id", match.get("content_id")).execute()
                if result.data:
                    content = result.data[0]
                    content["similarity_score"] = match.get("similarity")
                    content_items.append(content)

            return content_items
        except Exception as e:
            # If there's a database error, return empty list so agent can still function
            print(f"Warning: content search failed: {e}")
            return []
