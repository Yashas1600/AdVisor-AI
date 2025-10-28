"""
Fix persona migration - parse string fields
"""
import sys
from pathlib import Path
import ast
import json

sys.path.append(str(Path(__file__).parent.parent))

from db.knowledge_graph import KnowledgeGraph
from db.vector_store import VectorStore
from es_search.es_client import ElasticsearchClient


def parse_embedding(emb_data):
    """Parse embedding from string or list"""
    if isinstance(emb_data, list):
        return emb_data
    elif isinstance(emb_data, str):
        return json.loads(emb_data)
    else:
        raise ValueError(f"Unknown embedding format: {type(emb_data)}")


def safe_parse(value, default):
    """Safely parse string to dict/list using ast.literal_eval"""
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return ast.literal_eval(str(value))
    except:
        return default


# Initialize clients
kg = KnowledgeGraph()
vs = VectorStore()
es = ElasticsearchClient()

print("Migrating personas from Supabase to Elasticsearch...")

personas = kg.list_personas()
print(f"Found {len(personas)} personas\n")

migrated = 0
for idx, persona in enumerate(personas, 1):
    try:
        persona_id = persona["id"]

        # Get embedding
        embedding_data = vs.get_persona_embedding(persona_id)
        if not embedding_data or not embedding_data.get("embedding"):
            print(f"  ⚠ Skipping {persona.get('name', persona_id)} - no embedding")
            continue

        embedding = parse_embedding(embedding_data["embedding"])

        # Get communities and interests
        communities_data = kg.get_persona_communities(persona_id)
        community_names = [c["name"] for c in communities_data] if communities_data else []

        interests_data = kg.get_persona_interests(persona_id)
        interest_labels = [i["label"] for i in interests_data] if interests_data else []

        # Parse string fields safely
        demographics = safe_parse(persona.get("demographics"), {})
        psychographics = safe_parse(persona.get("psychographics"), {})
        pain_points = safe_parse(persona.get("pain_points"), [])
        motivations = safe_parse(persona.get("motivations"), [])

        # Index in Elasticsearch
        es.index_persona(
            persona_id=persona_id,
            name=persona.get("name", "Unknown"),
            summary=persona.get("summary", ""),
            embedding=embedding,
            demographics=demographics,
            psychographics=psychographics,
            interests=interest_labels,
            pain_points=pain_points,
            motivations=motivations,
            communities=community_names,
        )

        migrated += 1
        if idx % 10 == 0:
            print(f"  Progress: {migrated}/{len(personas)} personas migrated")

    except Exception as e:
        print(f"  ✗ Error: {persona.get('name', persona_id)}: {e}")
        import traceback
        traceback.print_exc()

print(f"\n✓ Migrated {migrated}/{len(personas)} personas")

# Verify
counts = es.get_all_counts()
print(f"\nElasticsearch counts: {counts}")
