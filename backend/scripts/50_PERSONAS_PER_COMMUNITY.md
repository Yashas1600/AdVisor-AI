# 50 Personas Per Community - Updated System

## Overview

The system now generates **50 diverse personas for each community** instead of just 1 persona per community.

---

## What Changed

### Before
- 20 communities → 10 personas total (1 per top community)
- **Total**: 10 personas

### After
- 20 communities → **50 personas EACH**
- **Total**: **1,000 personas**

---

## How It Works

### 1. Single Batch Generation

GPT generates all 50 personas at once per community:
- **1 batch** per community (50 personas all at once)
- **Total batches**: 20 (20 communities × 1 batch each)

### 2. Diversity Strategy

Each batch of 50 personas varies across:
- **Age ranges**: 18-24, 25-34, 35-44, 45-54, 55+
- **Income levels**: student, entry-level, middle, upper, premium
- **Experience levels**: beginner, intermediate, advanced, expert
- **Goals & motivations**: Different objectives
- **Pain points**: Unique challenges

### Example for r/Fitness

50 personas might include:
1. Budget Fitness Beginners 18-24
2. Premium Gym Enthusiasts 30-45
3. Home Workout Parents 35-44
4. Senior Fitness Maintainers 55+
5. College Athlete Trainees 18-22
6. Bodybuilding Competitors 25-34
7. CrossFit Professionals 28-35
8. Yoga & Mindfulness 30-50
9. Post-Injury Recovery 40-55
10. Marathon Training Beginners 25-40
... (40 more diverse personas)

---

## Processing Pipeline

```
For each of top 20 communities:
    └─ Generate 50 diverse personas in one batch

    = 50 personas per community
```

**Total across 20 communities**: **1,000 personas**
**Total API calls**: **20 GPT calls** (one per community)

---

## Cost & Performance

### OpenAI API Costs

| Operation | Count | Cost per | Total |
|-----------|-------|----------|-------|
| Persona generation (batches of 10) | 100 batches | $0.02 | **$2.00** |
| Persona embeddings | 1,000 | $0.005 | **$0.05** |
| Community enrichment | 20 | $0.02 | **$0.40** |
| Interest generation | 30 | $0.03 | **$0.90** |
| Post embeddings | 100 | $0.005 | **$0.50** |

**Total Cost**: **~$3.85**

### Processing Time

- **Persona generation**: ~45-60 minutes
  - 100 batches × 2 sec rate limit = ~3 minutes
  - GPT generation time: ~30-40 seconds per batch
  - Total: ~40-50 minutes for personas
- **Embedding generation**: ~5 minutes
- **Community enrichment**: ~5 minutes
- **Interest creation**: ~5 minutes

**Total Time**: **~60-75 minutes**

---

## Running the Pipeline

### Default (1,000 personas)

```bash
cd backend
python scripts/process_reddit_data.py
```

This creates:
- 20 communities
- **1,000 personas** (50 per community)
- 30 interests
- 100 post embeddings

### Customized

Edit `main()` in the script:

```python
processor.process_json_files(
    keywords_path=str(keywords_path),
    subreddits_path=str(subreddits_path),
    max_communities=10,           # Process top 10 communities
    personas_per_community=20,    # Generate 20 personas per community
    max_interests=30,
    max_posts_to_embed=100,
)
# Total: 10 × 20 = 200 personas
```

---

## Output Example

### Community: r/Fitness

**50 Personas Created**:

1. **Budget-Conscious Beginners 18-24**
   - Student/entry-level income
   - New to fitness, seeking affordable options
   - Pain points: Limited budget, lack of knowledge
   - Motivations: Get in shape, build confidence

2. **Premium Professionals 35-45**
   - Upper income, busy schedules
   - Advanced fitness level, time-constrained
   - Pain points: Time management, maintaining consistency
   - Motivations: Health optimization, stress relief

3. **Post-Pregnancy Recovery 28-35**
   - Middle income, new mothers
   - Beginner/intermediate, body image concerns
   - Pain points: Finding time, body changes
   - Motivations: Return to pre-pregnancy fitness

... (47 more diverse personas)

---

## Database Impact

### Storage

| Table | Records | Size Estimate |
|-------|---------|---------------|
| `personas` | 1,000 | ~2 MB |
| `persona_embeddings` | 1,000 | ~6 MB (1536-dim vectors) |
| `persona_community` | 1,000 | ~100 KB |
| `communities` | 20 | ~20 KB |
| `interests` | 30 | ~10 KB |

**Total**: ~8 MB

### Query Performance

With IVFFlat indexes:
- **Vector similarity search**: <100ms for 1,000 personas
- **Hybrid search** (vector + relational): <200ms

---

## Benefits

### 1. Richer Audience Segmentation
- Cover all age ranges, income levels, experience levels
- Better representation of community diversity

### 2. More Precise Ad Targeting
- Match ads to highly specific personas
- Better creative feedback from agents

### 3. Better Insights
- Identify niche segments within communities
- Discover underserved audiences

### 4. Scalable Agent Simulations
- Run simulations across 1,000 unique personas
- Get diverse perspectives on ad creatives

---

## Verification

After processing, verify persona count:

```python
from db import KnowledgeGraph

kg = KnowledgeGraph()

# Count personas
personas = kg.list_personas(limit=2000)
print(f"Total personas: {len(personas)}")

# Count personas per community
from collections import Counter

community_counts = Counter()
for persona in personas:
    communities = kg.get_persona_communities(persona["id"])
    for comm in communities:
        community_counts[comm["communities"]["name"]] += 1

print("\nPersonas per community:")
for comm, count in community_counts.most_common():
    print(f"  {comm}: {count}")
```

Expected output:
```
Total personas: 1000

Personas per community:
  r/Fitness: 50
  r/marketing: 50
  r/Entrepreneur: 50
  ...
```

---

## Next Steps

1. **Run the pipeline**: `python scripts/process_reddit_data.py`
2. **Wait ~60-75 minutes** for completion
3. **Verify**: Check database has 1,000 personas
4. **Test**: Run similarity searches
5. **Connect to agents**: Use rich persona data for creative feedback

---

## Configuration Options

### Fewer Personas (Faster, Cheaper)

```python
# 200 total personas (10 communities × 20 each)
max_communities=10,
personas_per_community=20,
```

Cost: ~$0.80, Time: ~20 minutes

### More Personas (Max Coverage)

```python
# 2,000 total personas (20 communities × 100 each)
max_communities=20,
personas_per_community=100,
```

Cost: ~$7.00, Time: ~2 hours

---

**Status**: ✅ Ready to generate 1,000 diverse personas!

**Run**: `python scripts/process_reddit_data.py`
