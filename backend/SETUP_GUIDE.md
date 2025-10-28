# Knowledge Graph + Vector Database Setup Guide

Complete setup guide for AdVisor's integrated Knowledge Graph (relational) and Vector Database (semantic) system.

---

## Prerequisites

- Supabase project created ([supabase.com](https://supabase.com))
- Python environment with dependencies installed
- `.env` file configured with Supabase credentials

---

## Setup Steps

### 1. Enable pgvector Extension

In your Supabase SQL Editor, run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 2. Run SQL Schema Files

Execute the SQL files in order:

#### A. Knowledge Graph Schema

Run [sql/01_knowledge_graph_schema.sql](sql/01_knowledge_graph_schema.sql)

This creates:
- **Entity Tables**: `personas`, `communities`, `interests`, `creative_prefs`
- **Relationship Tables**: `persona_community`, `persona_interest`, `persona_pref`
- **Sample Data**: 3 personas, 5 communities, 5 interests, 5 creative preferences
- **Indexes**: Performance indexes on all tables
- **Triggers**: Auto-update `updated_at` timestamps

#### B. Vector Database Schema

Run [sql/02_vector_database_schema.sql](sql/02_vector_database_schema.sql)

This creates:
- **Embedding Tables**: `persona_embeddings`, `community_embeddings`, `content_embeddings`, `ad_embeddings`
- **Vector Indexes**: IVFFlat indexes for similarity search
- **RPC Functions**: `match_personas()`, `match_communities()`, `match_content()`, `match_ads()`, `match_personas_hybrid()`
- **Utility Functions**: `cosine_similarity()`, `get_persona_context()`

### 3. Verify Setup

Check that all tables were created:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

You should see:
- `personas`, `communities`, `interests`, `creative_prefs`
- `persona_community`, `persona_interest`, `persona_pref`
- `persona_embeddings`, `community_embeddings`, `content_embeddings`, `ad_embeddings`

---

## Python SDK Usage

### Import the Libraries

```python
from db import KnowledgeGraph, VectorStore, PersonaManager
```

### Option 1: Use PersonaManager (Recommended)

The `PersonaManager` class combines both KG and Vector operations:

```python
from db import PersonaManager

pm = PersonaManager()

# Create persona with embedding
persona = pm.create_persona_full(
    name="Fitness Enthusiasts 25-35",
    summary="Young professionals focused on wellness and efficiency",
    embedding=embedding_vector,  # 1536-dim vector from OpenAI
    demographics={"age_range": "25-35", "income_level": "middle"},
    psychographics={"values": ["health", "efficiency"]},
    pain_points=["Limited time", "Budget constraints"],
    motivations=["Stay healthy", "Build muscle"]
)

# Get full context (KG + Vector)
context = pm.get_persona_full_context(persona_id)

# Find similar personas
similar = pm.find_similar_personas(
    query_embedding=embedding_vector,
    match_threshold=0.7,
    match_count=5
)
```

### Option 2: Use KnowledgeGraph + VectorStore Separately

```python
from db import KnowledgeGraph, VectorStore

kg = KnowledgeGraph()
vs = VectorStore()

# Create persona in KG
persona = kg.create_persona(
    name="Budget-Conscious Students",
    summary="College students seeking affordable fitness solutions",
    demographics={"age_range": "18-24"},
    pain_points=["Limited budget", "Time constraints"]
)

# Store embedding in Vector DB
vs.store_persona_embedding(
    persona_id=persona["id"],
    embedding=embedding_vector,
    embedding_text=persona["summary"],
    metadata={"demographics": persona["demographics"]}
)
```

---

## Key Operations

### 1. Persona Management

```python
pm = PersonaManager()

# Create
persona = pm.create_persona_full(
    name="Gen Z Minimalists",
    summary="Young consumers valuing authenticity and simplicity",
    embedding=embedding_vector,
    demographics={"age_range": "18-26"},
    communities=[{"community_id": comm_id, "relevance_score": 0.9}],
    interests=[{"interest_id": interest_id, "affinity_score": 0.85}]
)

# Query
context = pm.get_persona_full_context(persona_id)

# Search
similar = pm.find_similar_personas(query_embedding, match_count=10)
```

### 2. Hybrid Search (KG + Vector)

```python
# Find personas that are:
# 1. Semantically similar to query
# 2. Associated with r/Fitness community
results = pm.find_personas_by_community_and_similarity(
    query_embedding=embedding_vector,
    community_name="r/Fitness",
    match_threshold=0.7,
    match_count=5
)
```

### 3. Store Reddit Content

```python
# Store Reddit post embedding
pm.store_reddit_content_embedding(
    post_id="t3_abc123",
    text="Post title and body text here...",
    embedding=embedding_vector,
    community_name="r/Fitness",
    content_type="post",
    metadata={"upvotes": 342, "sentiment": "positive"}
)

# Find content relevant to persona
content = pm.find_relevant_content_for_persona(
    persona_id=persona_id,
    match_count=20,
    filter_community="r/Fitness"
)
```

### 4. Ad Creative Management

```python
# Store ad creative
pm.store_ad_creative(
    ad_id="ad_001",
    ad_copy="Premium protein powder for serious athletes...",
    embedding=embedding_vector,
    ad_type="image",
    metadata={"brand": "ProteinMax", "visual_style": "bold"}
)

# Find personas for this ad
personas = pm.recommend_personas_for_ad(ad_id="ad_001", match_count=5)

# Find ads for a persona
ads = pm.find_ads_for_persona(persona_id=persona_id, match_count=10)
```

### 5. Community Recommendations

```python
# Recommend communities for a persona (semantic similarity)
communities = pm.recommend_communities_for_persona(
    persona_id=persona_id,
    top_n=5
)
```

---

## Database Schema Reference

### Entity Tables

#### `personas`
- Core persona data: name, summary, demographics, psychographics, pain points, motivations
- Includes JSONB fields for flexible demographic/psychographic data

#### `communities`
- Subreddit/community info: name, platform, description, member count, activity level

#### `interests`
- Product/topic interests: label, category, description, keywords

#### `creative_prefs`
- Ad creative attributes: label (e.g., "minimalist"), category, description, examples

### Relationship Tables

#### `persona_community`
- Links personas to communities with `relevance_score` (0-1)

#### `persona_interest`
- Links personas to interests with `affinity_score` (0-1)

#### `persona_pref`
- Links personas to creative preferences with `importance_score` (0-1)

### Embedding Tables

#### `persona_embeddings`
- Vector representation of personas (1536-dim for OpenAI ada-002)
- Includes metadata and embedding_text

#### `community_embeddings`
- Vector representation of communities

#### `content_embeddings`
- Reddit posts/comments embeddings
- Filterable by `content_type` and `community_name`

#### `ad_embeddings`
- Ad creative embeddings
- Filterable by `ad_type`

---

## RPC Functions

### Vector Similarity Functions

```sql
-- Find similar personas
SELECT * FROM match_personas(
    query_embedding := '[0.1, 0.2, ...]'::vector,
    match_threshold := 0.7,
    match_count := 10
);

-- Find similar communities
SELECT * FROM match_communities(query_embedding, 0.7, 10);

-- Find similar content
SELECT * FROM match_content(
    query_embedding := '[...]'::vector,
    match_threshold := 0.6,
    match_count := 20,
    filter_content_type := 'post',
    filter_community := 'r/Fitness'
);

-- Hybrid search (semantic + relational)
SELECT * FROM match_personas_hybrid(
    query_embedding := '[...]'::vector,
    filter_community_name := 'r/Fitness',
    filter_interest_label := NULL,
    match_threshold := 0.7,
    match_count := 10
);
```

### Utility Functions

```sql
-- Get full persona context (KG + Vector)
SELECT get_persona_context('persona-uuid-here');

-- Calculate cosine similarity
SELECT cosine_similarity(
    '[0.1, 0.2, ...]'::vector,
    '[0.3, 0.4, ...]'::vector
);
```

---

## Examples

See [examples/kg_vector_example.py](examples/kg_vector_example.py) for complete working examples:

1. Create persona with embedding
2. Query full persona context
3. Find similar personas (vector search)
4. Hybrid search (semantic + relational)
5. Store Reddit content embeddings
6. Find content for persona
7. Recommend communities
8. Store ad and match personas
9. Batch store content

Run examples:
```bash
cd backend
python examples/kg_vector_example.py
```

---

## Integration with Agent Simulation Layer

When an agent runs, it should:

1. **Query KG for structured facts**
   ```python
   context = pm.get_persona_full_context(persona_id)
   # Returns: persona details, communities, interests, creative_prefs
   ```

2. **Retrieve semantic context from Vector DB**
   ```python
   relevant_content = pm.find_relevant_content_for_persona(persona_id)
   # Returns: Similar Reddit posts/comments
   ```

3. **Combine into context bundle**
   ```python
   agent_context = {
       "persona": context["persona"],
       "communities": context["communities"],
       "interests": context["interests"],
       "creative_prefs": context["creative_prefs"],
       "example_content": relevant_content[:10],
       "embedding": context["embedding"]
   }
   ```

4. **Pass to agent for reasoning**
   - Agent uses structured KG data for facts
   - Agent uses vector-retrieved content for examples and context
   - Agent generates creative feedback based on full context

---

## Performance Considerations

### Vector Indexes

- **IVFFlat indexes** are used for approximate nearest neighbor (ANN) search
- `lists` parameter set to 100-200 for medium datasets
- For larger datasets (>1M vectors), increase lists or consider HNSW indexes

### Query Optimization

- Use `match_threshold` to filter low-similarity results early
- Use `match_count` to limit results
- Apply relational filters (`filter_community_name`, `filter_content_type`) to narrow search space

### Batch Operations

- Use `batch_store_content_embeddings()` for bulk inserts
- Process embeddings in batches of 100-1000 for optimal performance

---

## Troubleshooting

### pgvector not enabled
```sql
CREATE EXTENSION vector;
```

### Embedding dimension mismatch
- Ensure all embeddings are same dimension (1536 for OpenAI ada-002)
- Update `VECTOR(1536)` in schema if using different model

### No results from similarity search
- Lower `match_threshold` (try 0.0 to see all results)
- Check that embeddings are actually stored
- Verify embedding format is correct (array of floats)

### RPC function not found
- Ensure 02_vector_database_schema.sql was run completely
- Check function exists: `SELECT * FROM pg_proc WHERE proname = 'match_personas';`

---

## Next Steps

1. ✅ Run SQL schemas in Supabase
2. ✅ Test connection with `backend/test_supabase.py`
3. ✅ Run examples in `examples/kg_vector_example.py`
4. Generate embeddings for personas (use OpenAI API or similar)
5. Populate vector DB with Reddit content embeddings
6. Connect to Agent Simulation Layer
7. Build Creative Feedback Generator

---

## Files Created

- `sql/01_knowledge_graph_schema.sql` - KG tables, relationships, sample data
- `sql/02_vector_database_schema.sql` - Vector tables, indexes, RPC functions
- `db/knowledge_graph.py` - KG operations SDK
- `db/vector_store.py` - Vector DB operations SDK
- `db/persona_manager.py` - Unified integration layer
- `examples/kg_vector_example.py` - Working examples
- `SETUP_GUIDE.md` - This guide
