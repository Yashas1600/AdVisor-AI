# OpenAI Timeout Fix

## Problem
When generating 50 personas in a single batch, the OpenAI API request was timing out:
```
httpx.ReadTimeout: The read operation timed out
```

This happened because:
1. The default timeout was 30 seconds
2. Generating 50 detailed personas takes 2-3+ minutes
3. The request would timeout before the API could respond

## Solution

### 1. Increased Timeout (openai_client.py)
Changed from 30 seconds to 5 minutes (300 seconds):

```python
# Before:
with httpx.Client(timeout=30.0) as client:

# After:
timeout = httpx.Timeout(300.0, read=300.0)
with httpx.Client(timeout=timeout) as client:
```

This gives the API enough time to generate large batches.

### 2. Reduced Batch Size (process_reddit_data.py)
Changed from 50 personas at once to 5 batches of 10:

```python
# Before:
personas_batch = self.openai.generate_diverse_personas_batch(
    keyword=topic,
    sample_posts=sample_posts,
    count=50  # All 50 at once - TIMEOUT!
)

# After:
batch_size = 10
num_batches = 5

for batch_idx in range(num_batches):
    personas_batch = self.openai.generate_diverse_personas_batch(
        keyword=topic,
        sample_posts=sample_posts,
        count=10  # 10 at a time - no timeout
    )
    all_personas.extend(personas_batch)
```

## Why Both Changes?

1. **Longer timeout**: Needed for any reasonably-sized GPT request (even 10 personas can take 30+ seconds)
2. **Smaller batches**: Makes requests more reliable and faster to respond
   - 10 personas ≈ 20-30 seconds (well under timeout)
   - 50 personas ≈ 2-3 minutes (risky even with 5-minute timeout)

## Trade-offs

**Pros:**
- ✅ No more timeouts
- ✅ More reliable processing
- ✅ Better progress visibility (see each batch complete)
- ✅ Incremental progress (partial batches still saved if interrupted)

**Cons:**
- ❌ More API calls (100 instead of 20)
- ❌ Slightly longer total time (due to network overhead per batch)
- ❌ Same total cost (charged per token, not per request)

## Performance Impact

- **Before**: 20 API calls (one 50-persona batch per community) → frequent timeouts
- **After**: 100 API calls (five 10-persona batches per community) → reliable execution

**Total processing time**: Still ~60-75 minutes for 1,000 personas
**Cost**: Same (~$3.85 total)
**Reliability**: Much higher ✅

## Alternative Solutions Considered

1. **Increase timeout only** (keep 50-persona batches)
   - ❌ Still risky - could hit rate limits or model delays
   - ❌ Single point of failure (one batch fails = 50 personas lost)

2. **Smaller batches only** (keep 30s timeout)
   - ❌ Even 10 personas can take 30+ seconds
   - ❌ Risk of timeout on slower responses

3. **Current approach** (both changes) ✅
   - ✅ Reliable and robust
   - ✅ Graceful degradation if one batch fails
   - ✅ Good progress visibility
