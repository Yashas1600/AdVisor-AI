## Reddit Data Processing Pipeline

Automated pipeline to process Reddit data from `keywords.json` and `subreddits.json`, enrich with OpenAI GPT-4o-mini, and populate the Knowledge Graph + Vector Database.

---

## Overview

This script:
1. **Extracts communities** from Reddit posts
2. **Enriches communities** with GPT-generated profiles and embeddings
3. **Extracts keywords** from post titles
4. **Creates interests** based on keywords
5. **Generates personas** for top communities using GPT
6. **Stores post embeddings** in Vector DB for semantic search

---

## Prerequisites

### 1. Run SQL Schemas

In Supabase SQL Editor:

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

Then run:
1. `sql/01_knowledge_graph_schema.sql`
2. `sql/02_vector_database_schema.sql`

### 2. Environment Variables

Ensure `.env` contains:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
OPENAI_API_KEY=sk-proj-...
```

### 3. Install Dependencies

```bash
pip install supabase openai httpx python-dotenv
```

---

## Usage

### Run Full Pipeline

```bash
cd backend
python scripts/process_reddit_data.py
```

### Customize Parameters

Edit `main()` in the script:

```python
processor.process_json_files(
    keywords_path=str(keywords_path),
    subreddits_path=str(subreddits_path),
    max_communities=20,      # Process top 20 communities
    max_personas=10,         # Generate 10 personas
    max_interests=30,        # Create 30 interests
    max_posts_to_embed=100,  # Store 100 post embeddings
)
```

---

## Pipeline Steps

### Step 1: Extract Communities

Scans all posts and extracts unique subreddit names (e.g., `r/Fitness`, `r/marketing`)

### Step 2: Enrich Communities

For each community:
- **GPT generates**: description, audience type, tone, activity level, topic categories
- **Creates embedding** from description text
- **Stores in**: `communities` table (KG) + `community_embeddings` table (Vector DB)

**Example GPT Prompt:**
```
Analyze the community: r/Fitness

Sample posts:
- What has been your experience with protein powder?
- Best budget gym for college students?
- Tips for staying motivated?

Provide JSON:
{
    "description": "One sentence summary",
    "topic_categories": ["topic1", "topic2"],
    "audience_type": "Who participates here",
    "tone": "Overall culture/tone",
    "activity_level": "high/medium/low"
}
```

### Step 3: Extract Keywords & Create Interests

- Extracts top 50 keywords from post titles (excluding stopwords)
- **GPT generates** interest profiles for top keywords
- **Stores in**: `interests` table

**Example GPT Prompt:**
```
Generate 1 specific product or topic interest for people interested in: protein

Provide JSON:
[{
    "label": "Whey Protein Supplements",
    "category": "product",
    "description": "Protein powder for muscle building",
    "keywords": ["whey", "protein powder", "supplements"]
}]
```

### Step 4: Generate Personas

For top 10 communities:
- **GPT generates**: complete persona profile (name, summary, demographics, psychographics, pain points, motivations)
- **Creates embedding** from persona summary
- **Links to**: associated community
- **Stores in**: `personas` (KG) + `persona_embeddings` (Vector DB)

**Example GPT Prompt:**
```
Generate a detailed persona profile for an audience interested in: Fitness

Related terms: protein, gym, workout

Provide JSON:
{
    "name": "Budget Fitness Enthusiasts 18-24",
    "summary": "Young adults focused on building muscle...",
    "demographics": {"age_range": "18-24", ...},
    "psychographics": {"values": ["health", ...], ...},
    "pain_points": ["Limited budget", ...],
    "motivations": ["Build muscle", ...]
}
```

### Step 5: Store Post Embeddings

- Processes 100 posts (configurable)
- Combines title + description into embedding text
- **Generates embeddings** using `text-embedding-3-small`
- **Stores in**: `content_embeddings` (Vector DB)
- **Metadata**: upvotes, comments, date, URL

---

## Output

After running, your Supabase database will have:

### Knowledge Graph Tables
- **communities**: 20 subreddits with GPT-enriched profiles
- **interests**: 30 topic/product interests
- **personas**: 10 audience personas with demographics/psychographics
- **Relationships**: personas linked to communities

### Vector Database Tables
- **community_embeddings**: 20 community vectors for similarity search
- **persona_embeddings**: 10 persona vectors
- **content_embeddings**: 100 Reddit post vectors with metadata

---

## Rate Limiting

The script includes automatic rate limiting:
- 0.5s delay between interest generations
- 1s delay between community/persona creations
- Batch embedding generation (10 posts at a time)

**Estimated Runtime**: 15-20 minutes for default parameters

---

## Cost Estimation

OpenAI API costs (approximate):

| Operation | Model | Count | Cost |
|-----------|-------|-------|------|
| Community enrichment | gpt-4o-mini | 20 | ~$0.02 |
| Interest generation | gpt-4o-mini | 30 | ~$0.03 |
| Persona generation | gpt-4o-mini | 10 | ~$0.02 |
| Community embeddings | text-embedding-3-small | 20 | ~$0.001 |
| Persona embeddings | text-embedding-3-small | 10 | ~$0.0005 |
| Post embeddings | text-embedding-3-small | 100 | ~$0.005 |

**Total**: ~$0.08 for default run

---

## Verification

### Check Created Data

```python
from db import KnowledgeGraph, VectorStore

kg = KnowledgeGraph()
vs = VectorStore()

# List personas
personas = kg.list_personas()
print(f"Personas: {len(personas)}")

# List communities
communities = kg.list_communities()
print(f"Communities: {len(communities)}")

# Check persona embeddings
persona_id = personas[0]["id"]
embedding = vs.get_persona_embedding(persona_id)
print(f"Embedding exists: {embedding is not None}")
```

### Test Similarity Search

```python
from db import PersonaManager

pm = PersonaManager()

# Find similar personas
embedding = vs.get_persona_embedding(persona_id)["embedding"]
similar = pm.find_similar_personas(embedding, match_count=5)

print("Similar personas:")
for match in similar:
    print(f"  - {match['persona_name']}: {match['similarity']:.3f}")
```

---

## Troubleshooting

### OpenAI API Key Invalid
```
Error: OPENAI_API_KEY not found in environment
```
**Solution**: Check `.env` file has `OPENAI_API_KEY=sk-proj-...`

### Rate Limit Exceeded
```
Error: Rate limit exceeded
```
**Solution**: Increase sleep delays in script or reduce batch size

### JSON Parsing Error
```
Failed to parse JSON response
```
**Solution**: GPT sometimes returns markdown. Script auto-cleans, but may need manual retry

### Supabase Connection Error
```
Error: Invalid Supabase credentials
```
**Solution**: Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`

---

## Advanced Usage

### Process Only Communities

```python
processor = RedditDataProcessor()

# Just extract and enrich communities
community_posts = processor.extract_communities_from_posts(posts)
for community, posts in community_posts.items():
    community_id = processor.create_enriched_community(community, posts)
```

### Custom Persona Generation

```python
# Generate persona manually
persona_data = processor.openai.generate_persona_from_keyword(
    keyword="fitness",
    related_terms=["gym", "protein", "workout"]
)
```

### Batch Store Custom Embeddings

```python
# Store custom embeddings
embeddings_batch = [
    {
        "content_id": "custom_id_1",
        "content_type": "post",
        "embedding": embedding_vector,
        "embedding_text": "Sample text",
        "community_name": "r/Fitness",
        "metadata": {"upvotes": 100}
    }
]

processor.pm.batch_store_reddit_embeddings(embeddings_batch)
```

---

## Next Steps

After processing:

1. **Test queries** with examples in `examples/kg_vector_example.py`
2. **Refine personas** by manually editing in Supabase dashboard
3. **Add more data** by running on additional JSON files
4. **Connect to agents** for creative feedback generation

---

## Files

- `scripts/process_reddit_data.py` - Main processing script
- `utils/openai_client.py` - OpenAI API wrapper
- `db/persona_manager.py` - Integration layer for KG + Vector DB
