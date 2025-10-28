# Knowledge Graph + Vector Database System

Complete implementation of AdVisor's integrated Knowledge Graph (relational) and Vector Database (semantic search) system.

## Overview

This system combines:
- **Knowledge Graph (KG)**: Structured relational data for personas, communities, interests, and creative preferences
- **Vector Database**: Semantic embeddings for similarity search and content matching
- **Integration Layer**: Unified API combining both systems

## What's Been Created

### SQL Schemas
- **[sql/01_knowledge_graph_schema.sql](sql/01_knowledge_graph_schema.sql)** - Entity and relationship tables with sample data
- **[sql/02_vector_database_schema.sql](sql/02_vector_database_schema.sql)** - Vector embeddings, indexes, and RPC functions

### Python SDK
- **[db/knowledge_graph.py](db/knowledge_graph.py)** - KG operations (CRUD for entities and relationships)
- **[db/vector_store.py](db/vector_store.py)** - Vector operations (embeddings and similarity search)
- **[db/persona_manager.py](db/persona_manager.py)** - **⭐ Main Integration Layer** (combines KG + Vector)

### Configuration
- **[config/supabase_client.py](config/supabase_client.py)** - Supabase client setup

### Documentation
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Complete setup instructions
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference card
- **[README_KG_VECTOR.md](README_KG_VECTOR.md)** - This file

### Examples
- **[examples/kg_vector_example.py](examples/kg_vector_example.py)** - 9 working examples

### Testing
- **[test_supabase.py](test_supabase.py)** - Connection test

---

## Quick Start

### 1. Setup Database

In Supabase SQL Editor:

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

Run SQL files in order:
1. `sql/01_knowledge_graph_schema.sql`
2. `sql/02_vector_database_schema.sql`

### 2. Configure Environment

Update `.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

### 3. Test Connection

```bash
python test_supabase.py
```

### 4. Run Examples

```bash
python examples/kg_vector_example.py
```

---

## Usage

### Basic Pattern

```python
from db import PersonaManager

pm = PersonaManager()

# Create persona with both KG and vector data
persona = pm.create_persona_full(
    name="Tech-Savvy Students",
    summary="College students interested in tech and gaming",
    embedding=embedding_vector,  # From OpenAI or similar
    demographics={"age_range": "18-24"},
    pain_points=["Limited budget"],
    motivations=["Career growth"]
)

# Get full context (structured + semantic)
context = pm.get_persona_full_context(persona["id"])

# Find similar personas
similar = pm.find_similar_personas(
    query_embedding=embedding_vector,
    match_threshold=0.7,
    match_count=5
)
```

### Agent Integration

When running agent simulations:

```python
from db import PersonaManager

pm = PersonaManager()

# 1. Get persona structured data from KG
context = pm.get_persona_full_context(persona_id)

# 2. Get semantic examples from Vector DB
relevant_posts = pm.find_relevant_content_for_persona(
    persona_id=persona_id,
    match_count=20,
    filter_community="r/Fitness"
)

# 3. Combine into agent context
agent_context = {
    "persona": context["persona"],
    "communities": context["communities"],
    "interests": context["interests"],
    "creative_prefs": context["creative_prefs"],
    "example_posts": relevant_posts
}

# 4. Pass to agent for creative analysis
# agent.analyze_ad(ad_creative, agent_context)
```

---

## Architecture

### Data Flow

```
Reddit Scraper → Feature Extraction
                       ↓
              ┌────────┴────────┐
              ↓                 ↓
    Knowledge Graph      Vector Store
    (Structured)        (Embeddings)
              ↓                 ↓
              └────────┬────────┘
                       ↓
              PersonaManager
              (Integration)
                       ↓
              Agent Simulation
```

### Database Tables

**Knowledge Graph (Relational)**
```
personas ──┬── persona_community ──→ communities
           ├── persona_interest ──→ interests
           └── persona_pref ──→ creative_prefs
```

**Vector Database (Semantic)**
```
persona_embeddings    (1536-dim vectors)
community_embeddings  (1536-dim vectors)
content_embeddings    (Reddit posts/comments)
ad_embeddings         (Ad creatives)
```

### Key Features

1. **Cascading Deletes**: Deleting a persona removes all relationships
2. **Auto Timestamps**: `created_at` and `updated_at` managed automatically
3. **Vector Indexes**: IVFFlat indexes for fast similarity search
4. **RPC Functions**: Server-side similarity queries
5. **Hybrid Search**: Combine semantic + relational filters

---

## API Reference

### PersonaManager (Main Interface)

#### Persona Operations
- `create_persona_full()` - Create persona with KG + embedding
- `get_persona_full_context()` - Get all data for persona
- `find_similar_personas()` - Vector similarity search
- `find_personas_by_community_and_similarity()` - Hybrid search

#### Community Operations
- `create_community_full()` - Create community with embedding
- `find_similar_communities()` - Find similar communities
- `recommend_communities_for_persona()` - Recommend communities

#### Content Operations
- `store_reddit_content_embedding()` - Store Reddit post/comment
- `find_relevant_content_for_persona()` - Find relevant content
- `batch_store_reddit_embeddings()` - Bulk insert

#### Ad Operations
- `store_ad_creative()` - Store ad with embedding
- `find_ads_for_persona()` - Find ads for persona
- `recommend_personas_for_ad()` - Find personas for ad

### KnowledgeGraph (Direct Access)

#### CRUD Operations
- `create_persona()`, `get_persona()`, `update_persona()`, `delete_persona()`
- `create_community()`, `create_interest()`, `create_creative_pref()`
- `link_persona_community()`, `link_persona_interest()`, `link_persona_pref()`

#### Queries
- `get_persona_with_relationships()` - Full persona + relations
- `get_persona_communities()`, `get_persona_interests()`, `get_persona_prefs()`
- `search_personas_by_demographics()`

### VectorStore (Direct Access)

#### Embedding Storage
- `store_persona_embedding()`, `store_community_embedding()`
- `store_content_embedding()`, `store_ad_embedding()`

#### Similarity Search
- `match_personas()`, `match_communities()`
- `match_content()`, `match_ads()`
- `match_personas_hybrid()` - Semantic + relational

---

## Sample Data Included

The schema includes sample data:

### Personas (3)
- Fitness Enthusiasts 18-24
- Busy Professionals 30-45
- Gen Z Minimalists

### Communities (5)
- r/Fitness, r/bodyweightfitness, r/Anxiety, r/minimalism, r/motorcycles

### Interests (5)
- Protein Supplements, Budget Gym Memberships, Home Workouts, Mental Wellness Apps, Sustainable Fashion

### Creative Preferences (5)
- Minimalist Design, Text-Heavy, Motion Graphics, User-Generated Content, Bold & Colorful

All with pre-linked relationships ready to query!

---

## Next Steps

1. **Generate Embeddings**: Use OpenAI API to create embeddings for personas and content
2. **Populate Vector DB**: Store embeddings for existing Reddit data
3. **Test Similarity Search**: Verify vector search returns relevant results
4. **Connect to Agents**: Pass persona context to agent simulation layer
5. **Build Feedback Loop**: Use agent insights to refine personas

---

## Performance Tips

- Use `match_threshold` to filter results (0.7-0.9 recommended)
- Apply relational filters early (`filter_community_name`, `filter_content_type`)
- Batch insert content embeddings (100-1000 at a time)
- Monitor vector index performance, adjust `lists` parameter if needed

---

## Troubleshooting

**Q: No results from similarity search?**
- Lower `match_threshold` to 0.0 to see all results
- Verify embeddings are stored: `SELECT COUNT(*) FROM persona_embeddings;`
- Check embedding dimension matches (1536 for OpenAI)

**Q: RPC function not found?**
- Ensure `02_vector_database_schema.sql` ran completely
- Check: `SELECT * FROM pg_proc WHERE proname = 'match_personas';`

**Q: Slow queries?**
- Ensure vector indexes exist: `\d persona_embeddings`
- Increase `lists` parameter for larger datasets
- Use filters to narrow search space

---

## Files Structure

```
backend/
├── sql/
│   ├── 01_knowledge_graph_schema.sql    # KG tables
│   └── 02_vector_database_schema.sql    # Vector tables
├── db/
│   ├── knowledge_graph.py               # KG SDK
│   ├── vector_store.py                  # Vector SDK
│   └── persona_manager.py               # Integration ⭐
├── config/
│   └── supabase_client.py               # Supabase setup
├── examples/
│   └── kg_vector_example.py             # Working examples
├── SETUP_GUIDE.md                       # Complete guide
├── QUICK_REFERENCE.md                   # Quick reference
└── README_KG_VECTOR.md                  # This file
```

---

## Support

See documentation:
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed setup
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick reference
- [examples/kg_vector_example.py](examples/kg_vector_example.py) - Code examples

---

**Status**: ✅ Complete and ready to use!

Run examples to verify:
```bash
python examples/kg_vector_example.py
```
