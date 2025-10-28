"""
Dual Store Integration
Writes to both Supabase (PostgreSQL + pgvector) and Elasticsearch
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional

sys.path.append(str(Path(__file__).parent.parent))

from db.persona_manager import PersonaManager
from es_search.es_client import ElasticsearchClient


class DualStoreManager:
    """
    Manages dual writes to both Supabase and Elasticsearch
    Ensures data consistency across both stores
    """

    def __init__(self):
        self.pm = PersonaManager()  # Supabase + pgvector
        self.es = ElasticsearchClient()  # Elasticsearch

    # ========================================================================
    # PERSONA OPERATIONS
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
        interests: Optional[List[str]] = None,
    ) -> Dict:
        """
        Create persona in both Supabase and Elasticsearch

        Args:
            name: Persona name
            summary: Persona description
            embedding: 1536-dim vector
            demographics: Age, gender, location, etc.
            psychographics: Values, lifestyle, personality
            pain_points: List of pain points
            motivations: List of motivations
            communities: List of community associations
            interests: List of interest labels

        Returns:
            Persona object from Supabase
        """
        # 1. Create in Supabase (PostgreSQL + pgvector)
        persona = self.pm.create_persona_full(
            name=name,
            summary=summary,
            embedding=embedding,
            demographics=demographics,
            psychographics=psychographics,
            pain_points=pain_points,
            motivations=motivations,
            communities=communities,
        )

        # 2. Index in Elasticsearch
        try:
            # Extract community names for Elasticsearch
            community_names = []
            if communities:
                for comm in communities:
                    if isinstance(comm, dict) and "community_id" in comm:
                        # Look up community name from Supabase
                        # For now, just store the ID
                        community_names.append(comm.get("community_id"))
                    elif isinstance(comm, str):
                        community_names.append(comm)

            self.es.index_persona(
                persona_id=persona["id"],
                name=name,
                summary=summary,
                embedding=embedding,
                demographics=demographics or {},
                psychographics=psychographics or {},
                interests=interests or [],
                pain_points=pain_points or [],
                motivations=motivations or [],
                communities=community_names,
            )

            print(f"    ✓ Indexed persona in Elasticsearch: {name}")

        except Exception as e:
            print(f"    ⚠ Warning: Failed to index persona in Elasticsearch: {e}")
            # Don't fail if Elasticsearch write fails - we have the data in Supabase

        return persona

    # ========================================================================
    # COMMUNITY OPERATIONS
    # ========================================================================

    def create_community_full(
        self,
        name: str,
        description: str,
        embedding: List[float],
        platform: str = "reddit",
        activity_level: Optional[str] = None,
        topic_categories: Optional[List[str]] = None,
        audience_type: Optional[str] = None,
        tone: Optional[str] = None,
    ) -> Dict:
        """
        Create community in both Supabase and Elasticsearch

        Returns:
            Community object from Supabase
        """
        # 1. Create in Supabase
        community = self.pm.create_community_full(
            name=name,
            description=description,
            embedding=embedding,
            platform=platform,
            activity_level=activity_level,
            topic_categories=topic_categories,
        )

        # 2. Index in Elasticsearch
        try:
            self.es.index_community(
                community_id=community["id"],
                name=name,
                description=description,
                embedding=embedding,
                platform=platform,
                audience_type=audience_type or "general",
                tone=tone or "neutral",
                activity_level=activity_level or "medium",
                topic_categories=topic_categories or [],
            )

            print(f"    ✓ Indexed community in Elasticsearch: {name}")

        except Exception as e:
            print(f"    ⚠ Warning: Failed to index community in Elasticsearch: {e}")

        return community

    # ========================================================================
    # CONTENT OPERATIONS
    # ========================================================================

    def batch_store_reddit_embeddings(self, content_list: List[Dict]) -> int:
        """
        Store Reddit post embeddings in both Supabase and Elasticsearch

        Args:
            content_list: List of content dictionaries with embeddings

        Returns:
            Number of successfully stored items
        """
        # 1. Store in Supabase (via PersonaManager)
        supabase_count = self.pm.batch_store_reddit_embeddings(content_list)

        # 2. Bulk index in Elasticsearch
        try:
            es_docs = []
            for item in content_list:
                doc = {
                    "content_id": item.get("content_id"),
                    "content_type": item.get("content_type", "post"),
                    "title": item.get("embedding_text", "")[:200],  # Use first 200 chars as title
                    "body": item.get("embedding_text", ""),
                    "community_name": item.get("community_name", ""),
                    "embedding": item.get("embedding"),
                    "created_at": item.get("metadata", {}).get("date_posted"),
                }

                # Add metadata
                metadata = item.get("metadata", {})
                doc.update({
                    "upvotes": metadata.get("upvotes", 0),
                    "num_comments": metadata.get("num_comments", 0),
                    "url": metadata.get("url", ""),
                    "date_posted": metadata.get("date_posted"),
                })

                es_docs.append(doc)

            result = self.es.bulk_index_content(es_docs)
            print(f"    ✓ Bulk indexed {result['success']} content items in Elasticsearch")

        except Exception as e:
            print(f"    ⚠ Warning: Failed to bulk index content in Elasticsearch: {e}")

        return supabase_count

    # ========================================================================
    # INTEREST OPERATIONS
    # ========================================================================

    def create_interest(
        self,
        label: str,
        category: str,
        description: Optional[str] = None,
        keywords: Optional[List[str]] = None,
    ) -> Dict:
        """
        Create interest in both Supabase and Elasticsearch

        Returns:
            Interest object from Supabase
        """
        # 1. Create in Supabase
        interest = self.pm.kg.create_interest(
            label=label,
            category=category,
            description=description,
            keywords=keywords,
        )

        # 2. Index in Elasticsearch
        try:
            self.es.index_interest(
                interest_id=interest["id"],
                label=label,
                category=category,
                description=description,
                keywords=keywords or [],
            )

            print(f"    ✓ Indexed interest in Elasticsearch: {label}")

        except Exception as e:
            print(f"    ⚠ Warning: Failed to index interest in Elasticsearch: {e}")

        return interest

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def setup_elasticsearch_indices(self, force_recreate: bool = False):
        """
        Set up Elasticsearch indices

        Args:
            force_recreate: If True, delete and recreate indices
        """
        print("\nSetting up Elasticsearch indices...")
        self.es.create_all_indices(force_recreate=force_recreate)

    def get_all_counts(self) -> Dict:
        """Get document counts from both stores"""
        supabase_counts = {
            "supabase_personas": len(self.pm.kg.list_personas()),
            "supabase_communities": len(self.pm.kg.list_communities()),
            "supabase_interests": len(self.pm.kg.list_interests()),
        }

        es_counts = self.es.get_all_counts()

        return {
            **supabase_counts,
            **{f"elasticsearch_{k}": v for k, v in es_counts.items()},
        }


if __name__ == "__main__":
    # Test dual store
    print("Testing Dual Store Manager...\n")

    ds = DualStoreManager()

    # Setup Elasticsearch
    ds.setup_elasticsearch_indices()

    # Get counts
    print("\nDocument counts:")
    counts = ds.get_all_counts()
    for key, value in counts.items():
        print(f"  {key}: {value}")
