#!/usr/bin/env python3
"""
Backfill analytics tables from existing ad_analyses rows in Supabase.

Usage:
    python scripts/backfill_bigquery.py --sink jsonl      # local (default)
    python scripts/backfill_bigquery.py --sink bigquery    # requires GCP creds
    python scripts/backfill_bigquery.py --sink none        # dry-run
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure backend/ is on the path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

# Override sink mode before importing analytics
parser = argparse.ArgumentParser(description="Backfill analytics from Supabase ad_analyses")
parser.add_argument("--sink", choices=["jsonl", "bigquery", "none"], default="jsonl",
                    help="Target sink (default: jsonl)")
parser.add_argument("--limit", type=int, default=1000,
                    help="Max rows to fetch from Supabase (default: 1000)")
args = parser.parse_args()

os.environ["ANALYTICS_SINK"] = args.sink

# Now import analytics (picks up overridden env var)
from analytics import sink as analytics
from db.supabase_client import supabase_client


def parse_json_field(value):
    """Safely parse a field that might be a JSON string, dict, or None."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


def main():
    print(f"Backfilling analytics with sink={args.sink}, limit={args.limit}")

    # Fetch ad_analyses rows from Supabase
    response = supabase_client.from_("ad_analyses").select("*").limit(args.limit).execute()
    rows = response.data or []
    print(f"Fetched {len(rows)} ad_analyses rows from Supabase")

    if not rows:
        print("Nothing to backfill.")
        return

    backfilled = 0
    for row in rows:
        run_id = analytics.generate_run_id()
        created_at = row.get("created_at", row.get("timestamp", ""))

        # Parse agent_results
        agent_results = parse_json_field(row.get("agent_results"))
        by_id = agent_results.get("byId", {})
        persona_count = len(by_id)

        # Parse features
        features = parse_json_field(row.get("features", row.get("feature_output")))

        # Determine ad type from features
        ad_type = "video" if features.get("video") else "image"

        # Log the ad run
        analytics.log_ad_run(
            run_id=run_id,
            ad_type=ad_type,
            provider="openai",
            orchestrator="smart_selector",
            persona_count=persona_count,
            latency_s=0.0,  # unknown for historical data
            tokens=None,
            cost_usd=None,
            status=row.get("status", "completed"),
        )

        # Log persona responses
        if by_id:
            responses = []
            for persona_id, result in by_id.items():
                if not isinstance(result, dict):
                    continue
                responses.append({
                    "persona_id": persona_id,
                    "attention": result.get("attention", "partial"),
                    "insight": result.get("insight", ""),
                    "community": result.get("community"),
                    "age_range": result.get("age_range"),
                    "income_level": result.get("income_level"),
                })
            if responses:
                analytics.log_persona_responses(run_id=run_id, responses=responses)

        # Log features
        if features:
            analytics.log_ad_features(run_id=run_id, extracted_features=features)

        backfilled += 1

    print(f"Backfilled {backfilled} runs to {args.sink} sink")
    if args.sink == "jsonl":
        print(f"Files written to: {analytics.JSONL_DIR}/")


if __name__ == "__main__":
    main()
