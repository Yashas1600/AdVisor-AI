"""
Analytics sink for AdVisor.

Controlled by ANALYTICS_SINK env var:
  - "jsonl"    (default) append to data/analytics/*.jsonl
  - "bigquery" stream rows into BigQuery tables
  - "none"     discard silently

All public functions are fire-and-forget safe: errors are logged but
never propagate to the caller so analytics can never block an API response.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("analytics")

# ---------------------------------------------------------------------------
# Resolve sink mode once at import time
# ---------------------------------------------------------------------------
SINK_MODE: str = os.getenv("ANALYTICS_SINK", "jsonl").lower()

# BigQuery details (only used when SINK_MODE == "bigquery")
BQ_PROJECT: str = os.getenv("GCP_PROJECT_ID", "")
BQ_DATASET: str = os.getenv("BQ_DATASET", "advisor_analytics")

# JSONL output directory (relative to backend/)
JSONL_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "analytics"


# ---------------------------------------------------------------------------
# Lazy BigQuery client (imported only when needed)
# ---------------------------------------------------------------------------
_bq_client = None


def _get_bq_client():
    global _bq_client
    if _bq_client is None:
        from google.cloud import bigquery
        _bq_client = bigquery.Client(project=BQ_PROJECT)
    return _bq_client


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _write_jsonl(table_name: str, rows: List[Dict[str, Any]]) -> None:
    """Append rows to data/analytics/{table_name}.jsonl"""
    JSONL_DIR.mkdir(parents=True, exist_ok=True)
    filepath = JSONL_DIR / f"{table_name}.jsonl"
    with open(filepath, "a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, default=str) + "\n")


def _write_bigquery(table_name: str, rows: List[Dict[str, Any]]) -> None:
    """Insert rows into BigQuery table."""
    client = _get_bq_client()
    table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{table_name}"
    errors = client.insert_rows_json(table_id, rows)
    if errors:
        logger.error("BigQuery insert errors for %s: %s", table_id, errors)


def _write(table_name: str, rows: List[Dict[str, Any]]) -> None:
    """Route rows to the configured sink."""
    if SINK_MODE == "none" or not rows:
        return
    if SINK_MODE == "bigquery":
        _write_bigquery(table_name, rows)
    else:
        _write_jsonl(table_name, rows)


def _safe_write(table_name: str, rows: List[Dict[str, Any]]) -> None:
    """Write rows, swallowing any exception so analytics never blocks."""
    try:
        _write(table_name, rows)
    except Exception:
        logger.exception("Analytics write failed for %s", table_name)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_run_id() -> str:
    """Return a fresh unique run ID."""
    return str(uuid.uuid4())


def log_ad_run(
    *,
    run_id: str,
    ad_type: str = "image",
    provider: str = "openai",
    orchestrator: str = "smart_selector",
    persona_count: int = 0,
    latency_s: float = 0.0,
    tokens: Optional[int] = None,
    cost_usd: Optional[float] = None,
    status: str = "completed",
) -> None:
    """Log a single ad analysis run. Safe to call from sync or async code."""
    row = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ad_type": ad_type,
        "provider": provider,
        "orchestrator": orchestrator,
        "persona_count": persona_count,
        "latency_s": round(latency_s, 3),
        "tokens": tokens,
        "cost_usd": cost_usd,
        "status": status,
    }
    _safe_write("ad_runs", [row])


def log_persona_responses(
    *,
    run_id: str,
    responses: List[Dict[str, Any]],
) -> None:
    """
    Log per-persona analysis results.

    Each dict in *responses* should contain at minimum:
        persona_id, attention, insight
    Optional keys: community, age_range, income_level, skip_at_seconds, latency_ms
    """
    rows = []
    for resp in responses:
        rows.append({
            "run_id": run_id,
            "persona_id": str(resp.get("persona_id", "")),
            "community": resp.get("community"),
            "age_range": resp.get("age_range"),
            "income_level": resp.get("income_level"),
            "attention": resp.get("attention", "partial"),
            "insight": resp.get("insight", ""),
            "skip_at_seconds": resp.get("skip_at_seconds"),
            "latency_ms": resp.get("latency_ms"),
        })
    _safe_write("persona_responses", rows)


def log_ad_features(
    *,
    run_id: str,
    extracted_features: Dict[str, Any],
) -> None:
    """Log the feature vector for an analysis run."""
    row = {
        "run_id": run_id,
        "extracted_features": json.dumps(extracted_features, default=str),
    }
    _safe_write("ad_features", [row])


# ---------------------------------------------------------------------------
# Async wrappers (run blocking I/O in a thread so the event loop stays free)
# ---------------------------------------------------------------------------

async def alog_ad_run(**kwargs) -> None:
    """Async version of log_ad_run."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: log_ad_run(**kwargs))


async def alog_persona_responses(**kwargs) -> None:
    """Async version of log_persona_responses."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: log_persona_responses(**kwargs))


async def alog_ad_features(**kwargs) -> None:
    """Async version of log_ad_features."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: log_ad_features(**kwargs))
