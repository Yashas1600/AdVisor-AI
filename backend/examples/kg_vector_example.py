"""
Example: Using Knowledge Graph + Vector Database Integration
Demonstrates how to work with PersonaManager for combined KG + Vector operations
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from db import PersonaManager, KnowledgeGraph, VectorStore


def example_1_create_persona_with_embedding():
    """
    Example 1: Create a complete persona with both KG and vector data
    """
    print("\n=== Example 1: Create Persona with Embedding ===\n")

    pm = PersonaManager()

    # Simulated embedding (in real use, you'd get this from OpenAI or similar)
    # This would be a 1536-dimensional vector from text-embedding-ada-002
    fake_embedding = [0.01] * 1536  # Placeholder

    persona = pm.create_persona_full(
        name="Tech-Savvy College Students",
        summary="College students interested in technology, gaming, and online communities",
        embedding=fake_embedding,
        demographics={
            "age_range": "18-24",
            "gender": "mixed",
            "income_level": "student",
            "education": "undergraduate",
        },
        psychographics={
            "values": ["innovation", "community", "authenticity"],
            "lifestyle": "digital-native",
            "personality_traits": ["curious", "social", "tech-literate"],
        },
        pain_points=["Limited budget", "Information overload", "Time management"],
        motivations=["Career growth", "Skill development", "Social connection"],
    )

    print(f"Created persona: {persona['name']} (ID: {persona['id']})")
    return persona["id"]


def example_2_query_full_persona_context():
    """
    Example 2: Retrieve full persona context (KG + Vector)
    """
    print("\n=== Example 2: Query Full Persona Context ===\n")

    pm = PersonaManager()
    kg = KnowledgeGraph()

    # Get first persona
    personas = kg.list_personas(limit=1)
    if not personas:
        print("No personas found. Run example_1 first or load sample data.")
        return

    persona_id = personas[0]["id"]
    context = pm.get_persona_full_context(persona_id)

    print(f"Persona: {context['persona']['name']}")
    print(f"Communities: {len(context['communities']) if context['communities'] else 0}")
    print(f"Interests: {len(context['interests']) if context['interests'] else 0}")
    print(f"Creative Prefs: {len(context['creative_prefs']) if context['creative_prefs'] else 0}")
    print(f"Has Embedding: {context['embedding'] is not None}")


def example_3_find_similar_personas():
    """
    Example 3: Find similar personas using vector search
    """
    print("\n=== Example 3: Find Similar Personas ===\n")

    pm = PersonaManager()
    vs = VectorStore()

    # Get an existing persona's embedding to use as query
    kg = KnowledgeGraph()
    personas = kg.list_personas(limit=1)

    if not personas:
        print("No personas found. Run example_1 first.")
        return

    persona_id = personas[0]["id"]
    persona_emb = vs.get_persona_embedding(persona_id)

    if not persona_emb:
        print("No embedding found. Create personas with embeddings first.")
        return

    # Find similar personas
    query_embedding = persona_emb["embedding"]
    similar = pm.find_similar_personas(
        query_embedding=query_embedding, match_threshold=0.0, match_count=5, include_full_context=False
    )

    print(f"Found {len(similar)} similar personas:")
    for match in similar:
        print(f"  - {match['persona_name']}: {match['similarity']:.3f} similarity")


def example_4_hybrid_search():
    """
    Example 4: Hybrid search (semantic + relational)
    Find personas similar to a query AND associated with a specific community
    """
    print("\n=== Example 4: Hybrid Search (Semantic + Relational) ===\n")

    pm = PersonaManager()
    vs = VectorStore()
    kg = KnowledgeGraph()

    # Get an embedding to use as query
    personas = kg.list_personas(limit=1)
    if not personas:
        print("No personas found.")
        return

    persona_emb = vs.get_persona_embedding(personas[0]["id"])
    if not persona_emb:
        print("No embedding found.")
        return

    # Search for personas similar to query AND linked to 'r/Fitness'
    results = pm.find_personas_by_community_and_similarity(
        query_embedding=persona_emb["embedding"],
        community_name="r/Fitness",
        match_threshold=0.0,
        match_count=5,
    )

    print(f"Personas similar to query + in r/Fitness community:")
    for match in results:
        print(f"  - {match['persona_name']}: {match['similarity']:.3f}")
        print(f"    Communities: {match['communities']}")
        print(f"    Interests: {match['interests']}")


def example_5_store_reddit_content():
    """
    Example 5: Store Reddit post embeddings
    """
    print("\n=== Example 5: Store Reddit Content Embeddings ===\n")

    pm = PersonaManager()

    # Simulated embeddings for Reddit posts
    fake_embedding = [0.02] * 1536

    post = pm.store_reddit_content_embedding(
        post_id="t3_example123",
        text="Looking for budget protein powder recommendations. What brands do you trust?",
        embedding=fake_embedding,
        community_name="r/Fitness",
        content_type="post",
        metadata={"upvotes": 342, "num_comments": 89, "sentiment": "positive", "keywords": ["protein", "budget"]},
    )

    print(f"Stored Reddit post: {post['content_id']}")
    print(f"Community: {post['community_name']}")
    print(f"Metadata: {post['metadata']}")


def example_6_find_content_for_persona():
    """
    Example 6: Find relevant Reddit content for a persona
    """
    print("\n=== Example 6: Find Relevant Content for Persona ===\n")

    pm = PersonaManager()
    kg = KnowledgeGraph()

    # Get a persona
    personas = kg.list_personas(limit=1)
    if not personas:
        print("No personas found.")
        return

    persona_id = personas[0]["id"]

    # Find relevant Reddit content
    try:
        content = pm.find_relevant_content_for_persona(persona_id, match_count=5, filter_community="r/Fitness")

        print(f"Relevant content for {personas[0]['name']}:")
        for item in content:
            print(f"  - {item['content_id']}: {item['similarity']:.3f} similarity")
            print(f"    Text: {item['embedding_text'][:100]}...")
    except ValueError as e:
        print(f"Error: {e}")


def example_7_recommend_communities():
    """
    Example 7: Recommend communities for a persona
    """
    print("\n=== Example 7: Recommend Communities for Persona ===\n")

    pm = PersonaManager()
    kg = KnowledgeGraph()

    personas = kg.list_personas(limit=1)
    if not personas:
        print("No personas found.")
        return

    persona_id = personas[0]["id"]

    try:
        recommendations = pm.recommend_communities_for_persona(persona_id, top_n=3)

        print(f"Community recommendations for {personas[0]['name']}:")
        for rec in recommendations:
            print(f"  - {rec['community_name']}: {rec['similarity']:.3f} similarity")
    except ValueError as e:
        print(f"Error: {e}")


def example_8_store_ad_and_match():
    """
    Example 8: Store ad creative and find matching personas
    """
    print("\n=== Example 8: Store Ad Creative and Match Personas ===\n")

    pm = PersonaManager()

    # Simulated ad embedding
    fake_embedding = [0.03] * 1536

    ad = pm.store_ad_creative(
        ad_id="ad_protein_powder_001",
        ad_copy="Premium protein powder for serious athletes. 25g protein per serving. Limited time offer!",
        embedding=fake_embedding,
        ad_type="image",
        metadata={
            "brand": "ProteinMax",
            "visual_style": "bold_colorful",
            "messaging_tone": "urgency",
            "price_point": "premium",
        },
    )

    print(f"Stored ad: {ad['ad_id']}")
    print(f"Metadata: {ad['metadata']}")

    # Find personas that would respond to this ad
    try:
        matches = pm.recommend_personas_for_ad(ad["ad_id"], match_count=3)

        print(f"\nPersonas likely to respond to this ad:")
        for match in matches:
            print(f"  - {match['persona_name']}: {match['similarity']:.3f} similarity")
    except ValueError as e:
        print(f"Error: {e}")


def example_9_batch_store_content():
    """
    Example 9: Batch insert Reddit content embeddings
    """
    print("\n=== Example 9: Batch Store Reddit Embeddings ===\n")

    pm = PersonaManager()

    # Prepare batch data
    embeddings_batch = [
        {
            "content_id": f"t3_batch_{i}",
            "content_type": "post",
            "embedding": [0.01 * i] * 1536,
            "embedding_text": f"This is sample post #{i} about fitness and nutrition",
            "community_name": "r/Fitness",
            "metadata": {"upvotes": i * 10, "sentiment": "positive"},
        }
        for i in range(1, 6)
    ]

    results = pm.batch_store_reddit_embeddings(embeddings_batch)
    print(f"Batch inserted {len(results)} Reddit post embeddings")


def run_all_examples():
    """Run all examples in sequence"""
    print("\n" + "=" * 80)
    print("KNOWLEDGE GRAPH + VECTOR DATABASE EXAMPLES")
    print("=" * 80)

    try:
        # Note: Some examples depend on data from previous examples
        example_1_create_persona_with_embedding()
        example_2_query_full_persona_context()
        example_3_find_similar_personas()
        example_4_hybrid_search()
        example_5_store_reddit_content()
        example_6_find_content_for_persona()
        example_7_recommend_communities()
        example_8_store_ad_and_match()
        example_9_batch_store_content()

        print("\n" + "=" * 80)
        print("All examples completed!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("\nMake sure you have:")
        print("1. Run the SQL schema files in Supabase")
        print("2. Set SUPABASE_URL and SUPABASE_KEY in .env")
        print("3. Enabled pgvector extension in Supabase")


if __name__ == "__main__":
    # Run individual examples or all at once
    run_all_examples()

    # Or run individual examples:
    # example_1_create_persona_with_embedding()
    # example_2_query_full_persona_context()
    # etc.
