# Architecture Decisions -- ADK Orchestration

## Why Google ADK?

Google's Agent Development Kit (ADK) provides a structured framework for
multi-agent workflows with first-class support for parallel execution,
session/state management, and observability.  Compared to the previous
Fetch.ai/Agentverse approach (which required an external EC2 instance and
inter-service HTTP calls), ADK runs everything in-process.

## Custom BaseAgent vs LlmAgent

We use a **custom `BaseAgent`** (`AdvisorCoordinator`) rather than an
`LlmAgent` for the coordinator.  The pipeline order is deterministic:

1. Select personas
2. Fan-out persona critiques
3. Aggregate results

There is no reason for an LLM to "decide" which step to run next -- it would
add latency and cost for no benefit.  A `BaseAgent` with a hard-coded
`_run_async_impl` gives us full control, zero wasted tokens, and
predictable behaviour.

Individual persona analyses still use an LLM (GPT-4o-mini by default) but
they are invoked as plain async calls, not as `LlmAgent` instances, because
each call is a single-shot completion with no tool use or multi-turn
reasoning.

## Parallel fan-out design

Rather than using ADK's built-in `ParallelAgent` (which requires sub-agents
to be defined at construction time), we dynamically fan-out using
`asyncio.gather` with a semaphore inside `fan_out_persona_analyses()`.  This
is because:

- The number and identity of persona agents are determined at runtime from
  Supabase query results.
- Each "agent" is really a single LLM call -- no tools, no memory, no
  multi-turn.  Wrapping each in a full ADK `LlmAgent` would add overhead
  without benefit.
- The semaphore (`concurrency=10` by default) respects API rate limits
  while maximising throughput.

If persona agents grow more complex in the future (e.g. multi-turn
reasoning, tool use), they can be upgraded to proper ADK `LlmAgent`
instances without changing the coordinator.

## Dynamic persona agent creation

Persona agents are **never** hand-written.  They are created at request time
from Supabase persona records.  The `build_system_prompt()` function in
`persona_agent.py` templates the persona's demographics, psychographics,
pain points, and motivations into a system prompt.  This means:

- Adding new personas to Supabase automatically makes them available.
- No code changes are needed when the persona set changes.
- The same prompt template is shared by both ADK and legacy paths.

## ADK vs legacy comparison

| Dimension | ADK path | Legacy path |
|-----------|----------|-------------|
| Concurrency | 10 parallel LLM calls via semaphore | Sequential with 0.2s sleep |
| Latency (50 personas) | ~1-2 min | ~10+ min |
| Session/state | ADK session state | Local variables |
| Observability | ADK events | Print statements |
| Dependency | `google-adk` pip package | None (stdlib only) |

The `ORCHESTRATOR` env var (`adk` or `legacy`) controls which path is used.
Default is `adk`.  Setting `ORCHESTRATOR=legacy` preserves the original
behaviour for rollback safety.

## Graceful degradation

If `google-adk` is not installed (e.g. in a lightweight CI environment), the
ADK coordinator automatically falls back to a plain-async implementation
that uses the same `fan_out_persona_analyses` function.  This means the
`ORCHESTRATOR=adk` path works even without the pip package -- it just skips
the ADK runner/session wrapper.
## Engagement Dataset Search

**Date:** 2026-11-06
**Goal:** Find a public dataset of ad creatives (image or video) with real engagement or performance labels (CTR, views, likes, conversions) and a license permitting research use.

### Candidates Evaluated

#### 1. Art & Advertising Visual Optimization Dataset (Kaggle, zara2099)
- **URL:** https://www.kaggle.com/datasets/zara2099/art-and-advertising-visual-optimization-dataset
- **Metrics:** CTR, view duration, engagement ratio, conversion rate, bounce rate, interaction types
- **License:** CC0 (Public Domain)
- **Includes creatives:** Yes (1,000 images, ~305 MB)
- **Verdict: REJECTED** — The engagement metrics are simulated/synthetic, not measured from real ad serving. The dataset description refers to "simulated behavioral metrics." Synthetic labels cannot validate whether AdVisor predictions correlate with real-world performance.

#### 2. Video_Ads Engagement Dataset (Kaggle, karnikakapoor)
- **URL:** https://www.kaggle.com/datasets/karnikakapoor/video-ads-engagement-dataset
- **Metrics:** Video watch duration (engagement prediction)
- **License:** CC0 (Public Domain)
- **Includes creatives:** No — tabular auction log data only (3M rows). No video files or thumbnails included.
- **Verdict: REJECTED** — No actual ad creative files. Contains auction-level metadata from an advertising exchange. Cannot run visual analysis on tabular bid data.

#### 3. Criteo Click Logs (1TB / 1M sample)
- **URL:** https://huggingface.co/datasets/criteo/CriteoClickLogs
- **Metrics:** Binary click/no-click label
- **License:** Criteo custom license (research only)
- **Includes creatives:** No — anonymized hashed feature columns only. No images, text, or any reconstructable creative content.
- **Verdict: REJECTED** — Industry-standard CTR benchmark but entirely tabular with hashed features. No creative content to analyze.

#### 4. Avazu CTR Dataset (Kaggle competition)
- **URL:** https://www.kaggle.com/c/avazu-ctr-prediction
- **Metrics:** Binary click label
- **License:** Competition rules (research use OK)
- **Includes creatives:** No — anonymized categorical features only.
- **Verdict: REJECTED** — Same issue as Criteo: tabular click logs with no creative content.

#### 5. Pitt Ads Dataset (CMU/Pitt, Kovashka et al.)
- **URL:** https://people.cs.pitt.edu/~kovashka/ads/
- **Metrics:** None — annotations are semantic (topic, sentiment, persuasion strategies, Q&A about what action the viewer is prompted to take).
- **License:** Academic use, images available by email request
- **Includes creatives:** Yes (64,832 image ads, 3,477 video ads)
- **Verdict: REJECTED** — Rich semantic annotations but no engagement/performance metrics (no CTR, clicks, views, conversions). Cannot correlate AdVisor scores against engagement.

#### 6. Creative4U / CreativePair (arxiv 2508.12628, Aug 2025)
- **URL:** https://arxiv.org/abs/2508.12628
- **Metrics:** Pairwise "which ad is better" labels based on real CTR differences (>60% CTR gap between pairs). 10,000 e-commerce image pairs.
- **License:** Not yet released. Paper states "code and dataset will be made public" but no download link found as of Nov 2026.
- **Includes creatives:** Yes (if/when released) — real e-commerce ad images with 8,879 annotated pairs.
- **Verdict: REJECTED** — Most promising candidate but dataset is not publicly available. No GitHub repo or download link exists. Cannot use what cannot be downloaded.

#### 7. EngagingImageNet (ICLR 2025, Khurana et al.)
- **URL:** https://behavior-in-the-wild.github.io/image-engagement.html
- **Metrics:** Engagement labels derived from tweet likes/retweets (168M tweets, 837K image samples)
- **License:** CC-BY 4.0
- **Includes creatives:** Yes — images from enterprise Twitter accounts
- **Verdict: REJECTED** — Measures social media post engagement, not ad creative performance. Images are general enterprise tweets (product photos, memes, announcements), not advertising creatives. Engagement reflects brand following/timing/virality, not creative quality. Also, download requires contacting authors (not self-serve), and "open-sourced in phases" suggests incomplete availability.

#### 8. Google Ads Transparency Center (BigQuery)
- **URL:** https://console.cloud.google.com/marketplace/product/bigquery-public-data/google-ads-transparency-center
- **Metrics:** Impression ranges (bucketed, not exact), first/last shown dates. No clicks, CTR, conversions, or spend.
- **License:** Public dataset, free BigQuery access
- **Includes creatives:** Metadata only (advertiser name, ad format, topic). Creative content viewable in UI but not bulk-downloadable.
- **Verdict: REJECTED** — Only impression count ranges (bucketed), no click or conversion data. Covers EEA/Turkey only. Cannot compute CTR or any meaningful engagement metric from impression buckets alone.

#### 9. Meta Ad Library
- **URL:** https://transparency.meta.com/researchtools/ad-library-tools/
- **Metrics:** For political/social issue ads: spend ranges, reach. For commercial ads: no performance metrics at all.
- **License:** Researcher access program (approval required)
- **Includes creatives:** Yes (viewable), but no bulk download API for commercial ad creatives.
- **Verdict: REJECTED** — No engagement metrics for commercial ads. Political ad data has spend/reach but not CTR/clicks/conversions. Bulk download of creatives not supported.

#### 10. ADS-16 Computational Advertising Dataset (Kaggle, groffo)
- **URL:** https://www.kaggle.com/datasets/groffo/ads16-dataset
- **Metrics:** Human ratings from 120 raters (not real engagement metrics — lab-collected preference scores)
- **License:** "Other (specified in description)"
- **Includes creatives:** Yes (300 real ads: rich media, image, text)
- **Verdict: REJECTED** — Only 300 ads (too small for statistical power). Metrics are lab ratings, not real deployment engagement. License unclear.

#### 11. Kaggle Social Media Ad Datasets (ziya07, various)
- **URL:** https://www.kaggle.com/datasets/ziya07/social-media-ad-dataset
- **Metrics:** Impressions, clicks, conversions, time spent
- **License:** Various (mostly CC0)
- **Includes creatives:** No — tabular data only, no images or videos.
- **Verdict: REJECTED** — Synthetic/simulated data. No actual ad creative files included.

### Summary

No publicly available dataset was found that satisfies all three requirements simultaneously:
1. Contains actual ad creative files (images or videos) that can be analyzed
2. Has real (not synthetic) engagement/performance labels (CTR, clicks, conversions)
3. Is available for download under a research-compatible license

The closest candidate is **Creative4U/CreativePair** which pairs real e-commerce ad images with real CTR-derived labels, but it has not been released publicly despite the authors' stated intention. If it becomes available in the future, it would be the strongest candidate for this evaluation.

The fundamental gap is that companies with real engagement data (Meta, Google, ad exchanges) do not release creative assets alongside performance metrics, and academic datasets with creative assets (Pitt Ads, ADS-16) lack real deployment engagement data.
