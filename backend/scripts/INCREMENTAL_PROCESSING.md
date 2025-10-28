# Incremental Processing Architecture

## Overview
The Reddit data processing pipeline has been optimized to commit data to the database **after each community** is fully processed, rather than waiting for all communities to complete.

## Benefits

### 1. **Fault Tolerance**
- If the script crashes or is interrupted, all previously completed communities are already saved
- No need to reprocess communities that were successfully completed
- Partial progress is preserved

### 2. **Progress Visibility**
- Real-time progress tracking: "Progress: 150/1000 total personas created"
- Can query database mid-run to see what's been created
- Easier to monitor and debug

### 3. **Resource Management**
- No need to hold all data in memory before committing
- More predictable memory usage
- Can stop/resume processing as needed

## Processing Flow

```
For each community (1-20):
  1. Create enriched community in KG + Vector DB
  2. Generate 50 personas in 5 batches (10 personas per batch to avoid timeout)
     - Batch 1: Generate 10 personas (~20-30 seconds)
     - Batch 2: Generate 10 personas (~20-30 seconds)
     - Batch 3-5: Same pattern
  3. Create embeddings for all 50 personas
  4. Store all 50 personas in database (KG + Vector DB)
  5. ✓ Commit to database
  6. Display progress: "Progress: X/1000 total personas"
  7. Move to next community

Total: 20 sequential commits (one per community)
Batch size: 10 personas per GPT call (prevents API timeout)
```

## Database Commits

Each community processing results in:
- **1 community record** in Knowledge Graph
- **1 community embedding** in Vector DB
- **50 persona records** in Knowledge Graph
- **50 persona embeddings** in Vector DB
- **50 persona-community relationships** in Knowledge Graph

All committed together after each community completes.

## Example Output

```
[Community 1/20] r/BestofRedditorUpdates
  ✓ Created community: r/BestofRedditorUpdates (ID: abc-123)

  Processing r/BestofRedditorUpdates - generating 50 diverse personas...
    Batch 1/5: Generating 10 personas...
    ✓ Generated 10 personas (total: 10/50)
    Batch 2/5: Generating 10 personas...
    ✓ Generated 10 personas (total: 20/50)
    ... (batches 3-5)
    ✓ Generated 10 personas (total: 50/50)
  ✓ Created 50 embeddings
  ✓ Committed 50 personas to database for r/BestofRedditorUpdates
  ✓ Progress: 50/1000 total personas created

[Community 2/20] r/relationship_advice
  ✓ Created community: r/relationship_advice (ID: def-456)

  Processing r/relationship_advice - generating 50 diverse personas...
    Batch 1/5: Generating 10 personas...
    ✓ Generated 10 personas (total: 10/50)
    ... (batches 2-5)
  ✓ Committed 50 personas to database for r/relationship_advice
  ✓ Progress: 100/1000 total personas created

...
```

## Resuming After Interruption

If the script is interrupted, you can:

1. **Check what's been created**:
   ```sql
   SELECT COUNT(*) FROM personas;
   SELECT name FROM communities ORDER BY created_at DESC;
   ```

2. **Option A: Continue from where you left off**
   - Modify `max_communities` parameter to process remaining communities
   - The script checks for existing communities and skips them

3. **Option B: Start fresh**
   - Delete all data and rerun
   - Or just let it run - duplicate checks prevent re-creating existing communities

## Performance

- **Time per community**: ~3-4 minutes
  - GPT generation: ~30-60 seconds
  - Embedding creation: ~30 seconds
  - Database writes: ~60 seconds
  - Total for 20 communities: ~60-75 minutes

- **API calls**: 100 GPT calls (5 batches × 20 communities) + 20 embedding batches = 120 total API calls

- **Cost**: ~$3.85 total for 1,000 personas across 20 communities

## Code Changes

Modified `process_reddit_data.py`:

1. **New method**: `generate_personas_for_community()`
   - Takes a single community and generates 50 personas in 5 batches of 10
   - Uses smaller batch size to prevent API timeouts
   - Commits immediately after all batches complete
   - Returns list of persona IDs

2. **Updated pipeline**: `process_json_files()`
   - Changed from batch processing to sequential per-community processing
   - Creates community → Generates personas → Commits → Next community
   - Tracks cumulative progress across all communities

3. **Removed**: Old `generate_personas_from_communities()` method
   - Previously processed all communities then generated all personas
   - Now replaced with per-community processing
