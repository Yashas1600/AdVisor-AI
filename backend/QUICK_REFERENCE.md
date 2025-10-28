# Quick Reference: Knowledge Graph + Vector Database

## Setup Checklist

- [ ] Enable pgvector in Supabase
- [ ] Run `sql/01_knowledge_graph_schema.sql`
- [ ] Run `sql/02_vector_database_schema.sql`
- [ ] Update `.env` with Supabase credentials
- [ ] Test with `python test_supabase.py`

## Common Operations

### Import
```python
from db import PersonaManager

pm = PersonaManager()
```

### Create Persona with Embedding
```python
persona = pm.create_persona_full(
    name="Fitness Enthusiasts 18-24",
    summary="Young adults focused on fitness and budget",
    embedding=embedding_vector,  # 1536-dim list
    demographics={"age_range": "18-24"},
    pain_points=["Limited budget"],
    motivations=["Build muscle"]
)
```

### Get Full Context (KG + Vector)
```python
context = pm.get_persona_full_context(persona_id)
# Returns: persona, communities, interests, creative_prefs, embedding
```

### Find Similar Personas
```python
similar = pm.find_similar_personas(
    query_embedding=embedding_vector,
    match_threshold=0.7,
    match_count=5
)
```

### Hybrid Search (Semantic + Relational)
```python
results = pm.find_personas_by_community_and_similarity(
    query_embedding=embedding_vector,
    community_name="r/Fitness",
    match_threshold=0.7
)
```

### Store Reddit Content
```python
pm.store_reddit_content_embedding(
    post_id="t3_abc123",
    text="Post text here...",
    embedding=embedding_vector,
    community_name="r/Fitness",
    metadata={"upvotes": 100}
)
```

### Find Content for Persona
```python
content = pm.find_relevant_content_for_persona(
    persona_id=persona_id,
    match_count=20,
    filter_community="r/Fitness"
)
```

### Store Ad Creative
```python
pm.store_ad_creative(
    ad_id="ad_001",
    ad_copy="Premium protein powder...",
    embedding=embedding_vector,
    metadata={"brand": "ProteinMax"}
)
```

### Match Personas to Ad
```python
personas = pm.recommend_personas_for_ad(
    ad_id="ad_001",
    match_count=5
)
```

## Tables

### KG Entities
- `personas` - Audience archetypes
- `communities` - Subreddits/platforms
- `interests` - Topics/products
- `creative_prefs` - Ad attributes

### KG Relationships
- `persona_community` - Persona ↔ Community
- `persona_interest` - Persona ↔ Interest
- `persona_pref` - Persona ↔ Creative Pref

### Vector Embeddings
- `persona_embeddings` - Persona vectors
- `community_embeddings` - Community vectors
- `content_embeddings` - Reddit content
- `ad_embeddings` - Ad creative vectors

## RPC Functions

- `match_personas(embedding, threshold, count)`
- `match_communities(embedding, threshold, count)`
- `match_content(embedding, threshold, count, type, community)`
- `match_ads(embedding, threshold, count, type)`
- `match_personas_hybrid(embedding, community, interest, threshold, count)`
- `get_persona_context(persona_id)`
- `cosine_similarity(vector_a, vector_b)`

## Examples

See `examples/kg_vector_example.py` for complete examples.

Run: `python examples/kg_vector_example.py`
