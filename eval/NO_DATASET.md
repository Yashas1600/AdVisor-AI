# No Suitable Engagement Dataset Found

**Date:** 2026-11-06

## What we looked for

A public dataset containing:
1. Actual ad creative files (images or videos) analyzable by AdVisor
2. Real engagement or performance labels (CTR, clicks, views, conversions) from actual ad serving
3. A license permitting research use

## What we found

We evaluated 11 candidate datasets across Kaggle, academic sources, Google Ads Transparency Center, and Meta Ad Library. See `docs/DECISIONS.md` for the full evaluation of each candidate.

**No dataset satisfies all three requirements.**

The landscape splits into two non-overlapping categories:
- **Datasets with real engagement metrics** (Criteo, Avazu, Google Ads Transparency) contain only anonymized tabular features or metadata — no creative files.
- **Datasets with actual ad creatives** (Pitt Ads, ADS-16) have semantic annotations or lab ratings — no real deployment engagement data.
- **Datasets claiming both** (Art & Advertising Visual Optimization, Social Media Ad datasets) use synthetic/simulated engagement metrics, not real measurements.

The most promising candidate, **Creative4U/CreativePair** (real e-commerce ad images with real CTR-derived pairwise labels), has not been publicly released despite being described in an August 2025 arXiv paper.

## What this means for AdVisor evaluation

Until a suitable dataset becomes available, we cannot compute a validated correlation between AdVisor persona attention scores and real-world ad engagement. The `eval/` directory is prepared for this evaluation and the script can be built once a dataset is identified.

## Monitoring for future availability

Candidates to watch:
- **Creative4U/CreativePair** — check https://arxiv.org/abs/2508.12628 and authors' GitHub periodically
- **EngagingImageNet** — phased release at https://behavior-in-the-wild.github.io/image-engagement.html (CC-BY 4.0, but measures tweet engagement not ad performance)
- **Meta Ad Library API** — expanding researcher access; may eventually include performance metrics for approved researchers
