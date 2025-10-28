# Reddit Data Processing Guide

Complete guide to process Reddit data and populate Knowledge Graph + Vector Database using OpenAI.

---

## 📋 Overview

This system processes your scraped Reddit data (`keywords.json` and `subreddits.json`) and:

1. **Extracts communities** (subreddits) from posts
2. **Enriches with GPT-4o-mini** to generate profiles, personas, and interests
3. **Generates embeddings** using `text-embedding-3-small`
4. **Populates both databases**:
   - **Knowledge Graph**: Structured relational data (personas, communities, interests, relationships)
   - **Vector DB**: Semantic embeddings for similarity search

---

## 🚀 Quick Start

### 1. Prerequisites

#### A. Database Setup

Run in Supabase SQL Editor:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

Then execute:
1. `sql/01_knowledge_graph_schema.sql`
2. `sql/02_vector_database_schema.sql`

#### B. Environment Variables

Ensure `.env` has:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
OPENAI_API_KEY=sk-proj-...
```

### 2. Test Setup

```bash
cd backend
python scripts/test_processing.py
```

Expected output:
```
TEST SUMMARY
==================================================
OpenAI Connection: ✓ PASSED
Persona Generation: ✓ PASSED
Community Enrichment: ✓ PASSED
Interest Generation: ✓ PASSED
Batch Embeddings: ✓ PASSED

Total: 5/5 tests passed
```

### 3. Run Processing Pipeline

```bash
python scripts/process_reddit_data.py
```

**Runtime**: ~15-20 minutes
**Cost**: ~$0.08 in OpenAI API calls

---

## 📊 What Gets Created

### Knowledge Graph (Relational Data)

| Table | Count | Description |
|-------|-------|-------------|
| `communities` | 20 | Subreddits with GPT-enriched profiles |
| `interests` | 30 | Product/topic interests from keywords |
| `personas` | 10 | Audience personas with demographics |
| `persona_community` | ~10 | Links personas to communities |

### Vector Database (Embeddings)

| Table | Count | Vector Dim | Description |
|-------|-------|------------|-------------|
| `community_embeddings` | 20 | 1536 | Community semantic vectors |
| `persona_embeddings` | 10 | 1536 | Persona semantic vectors |
| `content_embeddings` | 100 | 1536 | Reddit post vectors with metadata |

---

## 🔧 Processing Pipeline

### Step 1: Community Extraction & Enrichment

**Input**: Reddit posts from both JSON files
**Process**:
1. Extract unique subreddit names (e.g., `r/Fitness`)
2. Collect sample post titles for each community
3. **GPT generates**:
   - Community description
   - Topic categories
   - Audience type
   - Tone/culture
   - Activity level

4. **Generate embedding** from description
5. **Store in**: `communities` + `community_embeddings`

**Example Output**:
```json
{
  "name": "r/Fitness",
  "description": "Community for fitness enthusiasts...",
  "topic_categories": ["fitness", "health", "nutrition"],
  "audience_type": "Young adults focused on wellness",
  "activity_level": "high"
}
```

### Step 2: Keyword Extraction & Interest Creation

**Input**: Post titles from all posts
**Process**:
1. Extract top 50 keywords (excluding stopwords)
2. For each keyword, **GPT generates** interest profiles:
   - Label (e.g., "Whey Protein Supplements")
   - Category (product/topic/service)
   - Description
   - Related keywords

3. **Store in**: `interests` table

**Example Output**:
```json
{
  "label": "Budget Gym Memberships",
  "category": "service",
  "description": "Affordable gym options for students",
  "keywords": ["planet fitness", "budget gym", "student discount"]
}
```

### Step 3: Persona Generation

**Input**: Top 10 communities by post count
**Process**:
1. For each community, **GPT generates** complete persona:
   - Name
   - Summary (2-3 sentences)
   - Demographics (age, gender, income)
   - Psychographics (values, lifestyle, traits)
   - Pain points
   - Motivations

2. **Generate embedding** from summary + interests + pain points
3. **Link to** associated community
4. **Store in**: `personas` + `persona_embeddings` + `persona_community`

**Example Output**:
```json
{
  "name": "Budget Fitness Enthusiasts 18-24",
  "summary": "Young adults focused on building muscle and maintaining health on a budget",
  "demographics": {
    "age_range": "18-24",
    "income_level": "student/entry-level"
  },
  "psychographics": {
    "values": ["health", "aesthetics", "self-improvement"],
    "lifestyle": "active"
  },
  "pain_points": ["Limited budget", "Information overload"],
  "motivations": ["Build muscle", "Boost confidence"]
}
```

### Step 4: Post Embedding Storage

**Input**: 100 posts (configurable)
**Process**:
1. Combine title + description (first 200 chars)
2. **Generate embeddings** in batches of 10
3. **Store with metadata**:
   - Upvotes
   - Comment count
   - Date posted
   - URL
   - Community name

4. **Store in**: `content_embeddings`

This enables semantic search like:
- "Find posts about budget protein recommendations"
- "Show content similar to this persona's interests"

---

## 🎯 Usage Examples

### After Processing: Query the Data

```python
from db import PersonaManager, KnowledgeGraph

pm = PersonaManager()
kg = KnowledgeGraph()

# 1. List all personas
personas = kg.list_personas()
for p in personas:
    print(f"{p['name']}: {p['summary'][:80]}...")

# 2. Get full persona context (KG + Vector)
persona_id = personas[0]["id"]
context = pm.get_persona_full_context(persona_id)

print(f"Persona: {context['persona']['name']}")
print(f"Communities: {[c['communities']['name'] for c in context['communities']]}")
print(f"Interests: {[i['interests']['label'] for i in context['interests']]}")

# 3. Find similar personas
embedding = context["embedding"]["embedding"]
similar = pm.find_similar_personas(embedding, match_count=5)

print("\nSimilar personas:")
for match in similar:
    print(f"  {match['persona_name']}: {match['similarity']:.3f}")

# 4. Find relevant content for a persona
content = pm.find_relevant_content_for_persona(
    persona_id=persona_id,
    match_count=10,
    filter_community="r/Fitness"
)

print(f"\nRelevant posts:")
for post in content:
    print(f"  {post['embedding_text'][:80]}... ({post['similarity']:.3f})")
```

### Hybrid Search: Semantic + Relational

```python
# Find personas that are:
# 1. Semantically similar to a query
# 2. Associated with r/Fitness

query_embedding = pm.vs.get_persona_embedding(persona_id)["embedding"]

results = pm.find_personas_by_community_and_similarity(
    query_embedding=query_embedding,
    community_name="r/Fitness",
    match_threshold=0.7,
    match_count=5
)

for r in results:
    print(f"{r['persona_name']} - Communities: {r['communities']}")
```

---

## ⚙️ Configuration

### Adjust Processing Limits

Edit `process_reddit_data.py`:

```python
processor.process_json_files(
    keywords_path=str(keywords_path),
    subreddits_path=str(subreddits_path),
    max_communities=20,       # Number of communities to process
    max_personas=10,          # Number of personas to generate
    max_interests=30,         # Number of interests to create
    max_posts_to_embed=100,   # Number of posts to embed
)
```

### Customize GPT Prompts

Edit `utils/openai_client.py`:

- `generate_persona_from_keyword()` - Persona generation prompt
- `generate_community_summary()` - Community enrichment prompt
- `generate_interests_from_keyword()` - Interest generation prompt

### Change Embedding Model

Default: `text-embedding-3-small` (1536 dimensions)

To use `text-embedding-ada-002`:

```python
embedding = self.openai.generate_embedding(text, model="text-embedding-ada-002")
```

**Note**: Update vector dimensions in SQL schema if using different model!

---

## 💰 Cost Breakdown

Based on default parameters (OpenAI pricing as of Jan 2025):

| Operation | Model | Calls | Tokens | Cost |
|-----------|-------|-------|--------|------|
| Community profiles | gpt-4o-mini | 20 | ~8k | $0.02 |
| Interest generation | gpt-4o-mini | 30 | ~12k | $0.03 |
| Persona generation | gpt-4o-mini | 10 | ~6k | $0.02 |
| Community embeddings | text-embedding-3-small | 20 | ~1k | $0.001 |
| Persona embeddings | text-embedding-3-small | 10 | ~500 | $0.0005 |
| Post embeddings | text-embedding-3-small | 100 | ~10k | $0.005 |

**Total**: **~$0.08** per full run

To process more data:
- 100 personas: ~$0.50
- 1,000 post embeddings: ~$0.05
- Full dataset (10k posts): ~$0.50

---

## 🔍 Verification & Testing

### Check Database Contents

```sql
-- Count entities
SELECT 'personas' as table_name, COUNT(*) FROM personas
UNION ALL
SELECT 'communities', COUNT(*) FROM communities
UNION ALL
SELECT 'interests', COUNT(*) FROM interests
UNION ALL
SELECT 'persona_embeddings', COUNT(*) FROM persona_embeddings
UNION ALL
SELECT 'content_embeddings', COUNT(*) FROM content_embeddings;
```

### Test Vector Search

```sql
-- Find similar personas to a query embedding
SELECT * FROM match_personas(
    query_embedding := (SELECT embedding FROM persona_embeddings LIMIT 1),
    match_threshold := 0.5,
    match_count := 5
);
```

### Python Verification

```python
from db import KnowledgeGraph, VectorStore

kg = KnowledgeGraph()
vs = VectorStore()

print(f"Personas: {len(kg.list_personas())}")
print(f"Communities: {len(kg.list_communities())}")
print(f"Interests: {len(kg.list_interests())}")
```

---

## 🐛 Troubleshooting

### Issue: OpenAI API Key Invalid

```
ValueError: OPENAI_API_KEY not found in environment
```

**Solution**: Check `.env` file:
```bash
cat .env | grep OPENAI_API_KEY
```

### Issue: Rate Limit Exceeded

```
Error: Rate limit exceeded (429)
```

**Solution**: Increase sleep delays in `process_reddit_data.py`:
```python
time.sleep(2)  # Increase from 1 to 2 seconds
```

### Issue: JSON Parsing Error

```
Failed to parse JSON response: ...
```

**Cause**: GPT sometimes returns markdown code blocks

**Solution**: Script auto-cleans markdown, but if persistent:
1. Check OpenAI model (use `gpt-4o-mini`)
2. Add explicit instruction in prompt: "Return only valid JSON, no markdown"

### Issue: Supabase Insert Error

```
Error: insert or update on table "personas" violates foreign key constraint
```

**Solution**: Ensure SQL schemas were run in correct order:
1. `01_knowledge_graph_schema.sql` first
2. `02_vector_database_schema.sql` second

### Issue: Duplicate Entries

```
Error: duplicate key value violates unique constraint
```

**Solution**: Script checks for duplicates, but if occurs:
```python
# Clear all data (⚠️ destructive)
kg.client.table("personas").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
```

---

## 📁 File Structure

```
backend/
├── scripts/
│   ├── process_reddit_data.py      # Main processing pipeline
│   ├── test_processing.py          # Test OpenAI + processing
│   └── README_PROCESSING.md        # Processing docs
├── utils/
│   └── openai_client.py            # OpenAI API wrapper
├── db/
│   ├── knowledge_graph.py          # KG operations
│   ├── vector_store.py             # Vector operations
│   └── persona_manager.py          # Integration layer
├── data/
│   ├── keywords.json               # Input data
│   └── subreddits.json             # Input data
└── DATA_PROCESSING_GUIDE.md        # This file
```

---

## 🎯 Next Steps

After processing completes:

1. **Verify data**: Run SQL queries or Python verification scripts
2. **Test similarity search**: Use `examples/kg_vector_example.py`
3. **Refine personas**: Manually edit in Supabase dashboard
4. **Add more data**: Process additional JSON files
5. **Connect to agents**: Use personas for ad creative feedback
6. **Build dashboard**: Visualize personas and insights

---

## 🔗 Related Documentation

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - KG + Vector DB setup
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - API quick reference
- [scripts/README_PROCESSING.md](scripts/README_PROCESSING.md) - Processing pipeline details

---

**Status**: ✅ Ready to process Reddit data!

**Test first**: `python scripts/test_processing.py`
**Then run**: `python scripts/process_reddit_data.py`
