"""
Vector Store Operations for AdVisor
Handles embedding storage and similarity search using pgvector
"""
from typing import List, Dict, Optional, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import get_client


class VectorStore:
    """
    Wrapper for Vector Database operations on Supabase with pgvector
    """

    def __init__(self):
        self.client = get_client()

    # ========================================================================
    # PERSONA EMBEDDINGS
    # ========================================================================

    def store_persona_embedding(
        self,
        persona_id: str,
        embedding: List[float],
        embedding_text: str,
        model_name: str = "text-embedding-ada-002",
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Store or update persona embedding

        Args:
            persona_id: UUID of the persona
            embedding: Vector representation (list of floats)
            embedding_text: The original text that was embedded
            model_name: Name of embedding model used
            metadata: Additional context (communities, topics, etc.)

        Returns:
            Inserted/updated record
        """
        data = {
            "persona_id": persona_id,
            "embedding": embedding,
            "embedding_text": embedding_text,
            "model_name": model_name,
            "metadata": metadata or {},
        }
        response = self.client.table("persona_embeddings").upsert(data, on_conflict="persona_id,model_name").execute()
        return response.data[0] if response.data else None

    def get_persona_embedding(self, persona_id: str, model_name: str = "text-embedding-ada-002") -> Optional[Dict]:
        """Get stored embedding for a persona"""
        response = (
            self.client.table("persona_embeddings")
            .select("*")
            .eq("persona_id", persona_id)
            .eq("model_name", model_name)
            .execute()
        )
        return response.data[0] if response.data else None

    def match_personas(
        self,
        query_embedding: List[float],
        match_threshold: float = 0.5,
        match_count: int = 10,
    ) -> List[Dict]:
        """
        Find similar personas using vector similarity

        Args:
            query_embedding: Query vector
            match_threshold: Minimum similarity score (0-1)
            match_count: Number of results to return

        Returns:
            List of matching personas with similarity scores
        """
        response = self.client.rpc(
            "match_personas",
            {
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": match_count,
            },
        ).execute()
        return response.data or []

    # ========================================================================
    # COMMUNITY EMBEDDINGS
    # ========================================================================

    def store_community_embedding(
        self,
        community_id: str,
        embedding: List[float],
        embedding_text: str,
        model_name: str = "text-embedding-ada-002",
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """Store or update community embedding"""
        data = {
            "community_id": community_id,
            "embedding": embedding,
            "embedding_text": embedding_text,
            "model_name": model_name,
            "metadata": metadata or {},
        }
        response = (
            self.client.table("community_embeddings").upsert(data, on_conflict="community_id,model_name").execute()
        )
        return response.data[0] if response.data else None

    def get_community_embedding(
        self, community_id: str, model_name: str = "text-embedding-ada-002"
    ) -> Optional[Dict]:
        """Get stored embedding for a community"""
        response = (
            self.client.table("community_embeddings")
            .select("*")
            .eq("community_id", community_id)
            .eq("model_name", model_name)
            .execute()
        )
        return response.data[0] if response.data else None

    def match_communities(
        self,
        query_embedding: List[float],
        match_threshold: float = 0.5,
        match_count: int = 10,
    ) -> List[Dict]:
        """Find similar communities using vector similarity"""
        response = self.client.rpc(
            "match_communities",
            {
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": match_count,
            },
        ).execute()
        return response.data or []

    # ========================================================================
    # CONTENT EMBEDDINGS (Reddit posts/comments)
    # ========================================================================

    def store_content_embedding(
        self,
        content_id: str,
        content_type: str,
        embedding: List[float],
        embedding_text: str,
        community_name: Optional[str] = None,
        model_name: str = "text-embedding-ada-002",
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Store embedding for Reddit content (posts, comments, threads)

        Args:
            content_id: Reddit post ID or cluster ID
            content_type: 'post', 'comment_cluster', 'thread'
            embedding: Vector representation
            embedding_text: Original text or summary
            community_name: Subreddit name (e.g., 'r/Fitness')
            model_name: Embedding model used
            metadata: Additional context (upvotes, sentiment, keywords, etc.)
        """
        data = {
            "content_id": content_id,
            "content_type": content_type,
            "embedding": embedding,
            "embedding_text": embedding_text,
            "community_name": community_name,
            "model_name": model_name,
            "metadata": metadata or {},
        }
        response = self.client.table("content_embeddings").insert(data).execute()
        return response.data[0] if response.data else None

    def match_content(
        self,
        query_embedding: List[float],
        match_threshold: float = 0.5,
        match_count: int = 20,
        filter_content_type: Optional[str] = None,
        filter_community: Optional[str] = None,
    ) -> List[Dict]:
        """
        Find similar content using vector similarity

        Args:
            query_embedding: Query vector
            match_threshold: Minimum similarity score
            match_count: Number of results
            filter_content_type: Filter by type ('post', 'comment_cluster', etc.)
            filter_community: Filter by subreddit name
        """
        response = self.client.rpc(
            "match_content",
            {
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": match_count,
                "filter_content_type": filter_content_type,
                "filter_community": filter_community,
            },
        ).execute()
        return response.data or []

    # ========================================================================
    # AD CREATIVE EMBEDDINGS
    # ========================================================================

    def store_ad_embedding(
        self,
        ad_id: str,
        embedding: List[float],
        embedding_text: str,
        ad_type: str = "image",
        model_name: str = "text-embedding-ada-002",
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Store embedding for an ad creative

        Args:
            ad_id: Unique ad identifier
            embedding: Vector representation
            embedding_text: Ad copy, description, or multimodal summary
            ad_type: 'image', 'video', 'text'
            model_name: Embedding model used
            metadata: Visual features, performance metrics, brand info
        """
        data = {
            "ad_id": ad_id,
            "embedding": embedding,
            "embedding_text": embedding_text,
            "ad_type": ad_type,
            "model_name": model_name,
            "metadata": metadata or {},
        }
        response = self.client.table("ad_embeddings").upsert(data, on_conflict="ad_id").execute()
        return response.data[0] if response.data else None

    def match_ads(
        self,
        query_embedding: List[float],
        match_threshold: float = 0.5,
        match_count: int = 10,
        filter_ad_type: Optional[str] = None,
    ) -> List[Dict]:
        """Find similar ad creatives using vector similarity"""
        response = self.client.rpc(
            "match_ads",
            {
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": match_count,
                "filter_ad_type": filter_ad_type,
            },
        ).execute()
        return response.data or []

    # ========================================================================
    # HYBRID SEARCH (KG + Vector)
    # ========================================================================

    def match_personas_hybrid(
        self,
        query_embedding: List[float],
        filter_community_name: Optional[str] = None,
        filter_interest_label: Optional[str] = None,
        match_threshold: float = 0.5,
        match_count: int = 10,
    ) -> List[Dict]:
        """
        Find similar personas using both semantic similarity and relational filters

        Args:
            query_embedding: Query vector
            filter_community_name: Filter personas by community (e.g., 'r/Fitness')
            filter_interest_label: Filter personas by interest
            match_threshold: Minimum similarity score
            match_count: Number of results

        Returns:
            Personas with similarity scores, communities, and interests
        """
        response = self.client.rpc(
            "match_personas_hybrid",
            {
                "query_embedding": query_embedding,
                "filter_community_name": filter_community_name,
                "filter_interest_label": filter_interest_label,
                "match_threshold": match_threshold,
                "match_count": match_count,
            },
        ).execute()
        return response.data or []

    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================

    def batch_store_content_embeddings(self, content_embeddings: List[Dict]) -> List[Dict]:
        """
        Store multiple content embeddings at once

        Args:
            content_embeddings: List of dicts with keys:
                - content_id, content_type, embedding, embedding_text,
                  community_name, metadata

        Returns:
            List of inserted records
        """
        response = self.client.table("content_embeddings").insert(content_embeddings).execute()
        return response.data or []

    def delete_embeddings_by_community(self, community_name: str) -> int:
        """Delete all content embeddings for a specific community"""
        response = self.client.table("content_embeddings").delete().eq("community_name", community_name).execute()
        return len(response.data)

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def calculate_similarity(self, embedding_a: List[float], embedding_b: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        (Uses Supabase RPC function)
        """
        response = self.client.rpc(
            "cosine_similarity",
            {"a": embedding_a, "b": embedding_b},
        ).execute()
        return response.data if response.data else None
