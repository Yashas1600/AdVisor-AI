# AdVisor Analytics

## Overview

Every ad analysis run emits structured events to an analytics sink.
The sink is controlled by the `ANALYTICS_SINK` environment variable:

| Value      | Behaviour                                        |
|------------|--------------------------------------------------|
| `jsonl`    | **(default)** Append to `backend/data/analytics/*.jsonl` |
| `bigquery` | Stream into BigQuery tables                      |
| `none`     | Discard all events silently                      |

Analytics writes are fire-and-forget: they never block the API response.

## Tables

| Table               | Description                         |
|---------------------|-------------------------------------|
| `ad_runs`           | One row per analysis run            |
| `persona_responses` | One row per persona per run         |
| `ad_features`       | Feature vector JSON per run         |

Schemas live in `backend/analytics/schemas/`.

## BigQuery Setup

1. Create a dataset (e.g. `advisor_analytics`) in your GCP project.
2. Create tables from the JSON schemas:
   ```bash
   bq mk --table PROJECT:advisor_analytics.ad_runs        backend/analytics/schemas/ad_runs.json
   bq mk --table PROJECT:advisor_analytics.persona_responses backend/analytics/schemas/persona_responses.json
   bq mk --table PROJECT:advisor_analytics.ad_features     backend/analytics/schemas/ad_features.json
   ```
3. Set env vars:
   ```
   ANALYTICS_SINK=bigquery
   GCP_PROJECT_ID=your-project
   BQ_DATASET=advisor_analytics
   ```

## Useful SQL Queries

### 1. Attention distribution by community and age range

```sql
SELECT
  community,
  age_range,
  attention,
  COUNT(*)                                             AS cnt,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER
        (PARTITION BY community, age_range), 1)        AS pct
FROM `advisor_analytics.persona_responses`
GROUP BY community, age_range, attention
ORDER BY community, age_range, attention;
```

### 2. Cost and latency per ad run

```sql
SELECT
  run_id,
  timestamp,
  persona_count,
  ROUND(latency_s, 1)                AS latency_s,
  ROUND(cost_usd, 4)                 AS cost_usd,
  ROUND(cost_usd / persona_count, 5) AS cost_per_persona
FROM `advisor_analytics.ad_runs`
ORDER BY timestamp DESC
LIMIT 50;
```

### 3. Most common skip moment in video ads

```sql
SELECT
  ROUND(skip_at_seconds, 0) AS skip_second,
  COUNT(*)                   AS occurrences
FROM `advisor_analytics.persona_responses`
WHERE skip_at_seconds IS NOT NULL
GROUP BY skip_second
ORDER BY occurrences DESC
LIMIT 20;
```

### 4. Provider / orchestrator comparison

```sql
SELECT
  provider,
  orchestrator,
  COUNT(*)                          AS runs,
  ROUND(AVG(latency_s), 1)         AS avg_latency_s,
  ROUND(AVG(cost_usd), 4)          AS avg_cost_usd,
  ROUND(AVG(persona_count), 0)     AS avg_personas
FROM `advisor_analytics.ad_runs`
GROUP BY provider, orchestrator
ORDER BY runs DESC;
```

### 5. Top communities by engagement (full-attention rate)

```sql
SELECT
  community,
  COUNT(*)                                                    AS total_responses,
  COUNTIF(attention = 'full')                                 AS full_count,
  ROUND(COUNTIF(attention = 'full') * 100.0 / COUNT(*), 1)   AS full_pct
FROM `advisor_analytics.persona_responses`
GROUP BY community
HAVING total_responses >= 10
ORDER BY full_pct DESC;
```

### 6. Persona attention variance (which personas are most polarizing)

```sql
WITH scored AS (
  SELECT
    persona_id,
    CASE attention
      WHEN 'full' THEN 1.0
      WHEN 'partial' THEN 0.5
      ELSE 0.0
    END AS score
  FROM `advisor_analytics.persona_responses`
)
SELECT
  persona_id,
  COUNT(*)                  AS runs,
  ROUND(AVG(score), 3)     AS avg_score,
  ROUND(STDDEV(score), 3)  AS stddev_score
FROM scored
GROUP BY persona_id
HAVING runs >= 5
ORDER BY stddev_score DESC
LIMIT 25;
```

## Local Development

With the default `jsonl` sink, data lands in `backend/data/analytics/`:

```
backend/data/analytics/
  ad_runs.jsonl
  persona_responses.jsonl
  ad_features.jsonl
```

These files are gitignored (under `data/`). You can inspect them with `jq`:

```bash
cat backend/data/analytics/ad_runs.jsonl | jq .
```

## Backfill

To load existing `ad_analyses` rows from Supabase into the analytics sink:

```bash
# JSONL (default, no cloud needed)
python scripts/backfill_bigquery.py --sink jsonl

# BigQuery (requires GCP credentials)
python scripts/backfill_bigquery.py --sink bigquery
```
