"""Tests for the /api/analyze-ad-smart endpoint contract."""
import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# conftest.py already mocked heavy deps and added backend to sys.path

# Force legacy orchestrator for these tests (avoids ADK import)
os.environ["ORCHESTRATOR"] = "legacy"

from api.routes.analyze import router, _extract_attention_level
from llm.mock import MockProvider
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ---- helpers ----

def _make_request_body(feature_vector, num_personas=5):
    return {
        "feature_vector": feature_vector,
        "num_personas": num_personas,
        "target_age_range": "18-24",
        "industry_keywords": ["fitness"],
    }


def _build_client(personas, mock_provider=None):
    """Build a TestClient with mocked smart_selector and provider."""
    mock_supabase = MagicMock()
    mock_supabase.from_.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "test-id"}])
    mock_supabase.from_.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "test-id"}])
    mock_supabase.from_.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "new-id"}])

    mock_selector = MagicMock()
    mock_selector.select_relevant_personas.return_value = personas

    if mock_provider is None:
        mock_provider = MockProvider(default_attention="full", default_insight="This ad speaks to me!")

    app = FastAPI()
    app.include_router(router)

    with patch("api.routes.analyze.smart_selector", mock_selector), \
         patch("api.routes.analyze.supabase_client", mock_supabase), \
         patch("api.routes.analyze.get_provider", return_value=mock_provider):
        yield TestClient(app)


# ---- tests ----

class TestAnalyzeAdSmartContract:
    """Test the request/response contract of /api/analyze-ad-smart."""

    def test_success_response_shape(self, mock_env, sample_personas, sample_feature_vector):
        personas = sample_personas[:5]
        for client in _build_client(personas):
            body = _make_request_body(sample_feature_vector, num_personas=5)
            resp = client.post("/api/analyze-ad-smart", json=body)
            assert resp.status_code == 200

            data = resp.json()
            assert "analysis_results" in data
            assert "summary" in data
            assert "selected_personas" in data

            summary = data["summary"]
            assert "total_personas" in summary
            assert "attention" in summary
            assert "attention_percentages" in summary
            assert summary["total_personas"] == 5

            att = summary["attention"]
            assert att["full"] + att["partial"] + att["ignore"] == 5

    def test_all_personas_get_results(self, mock_env, sample_personas, sample_feature_vector):
        personas = sample_personas[:5]
        for client in _build_client(personas):
            body = _make_request_body(sample_feature_vector, num_personas=5)
            resp = client.post("/api/analyze-ad-smart", json=body)
            data = resp.json()

            results = data["analysis_results"]
            assert len(results) == 5

            for result in results.values():
                assert "insight" in result
                assert "attention" in result
                assert result["attention"] in ("full", "partial", "ignore")

    def test_latency_in_summary(self, mock_env, sample_personas, sample_feature_vector):
        personas = sample_personas[:5]
        for client in _build_client(personas):
            body = _make_request_body(sample_feature_vector, num_personas=5)
            resp = client.post("/api/analyze-ad-smart", json=body)
            data = resp.json()
            assert "latency_seconds" in data["summary"]

    def test_no_personas_returns_404(self, mock_env, sample_feature_vector):
        for client in _build_client([]):
            body = _make_request_body(sample_feature_vector, num_personas=5)
            resp = client.post("/api/analyze-ad-smart", json=body)
            assert resp.status_code == 404

    def test_missing_feature_vector_returns_422(self, mock_env, sample_personas):
        for client in _build_client(sample_personas[:1]):
            resp = client.post("/api/analyze-ad-smart", json={})
            assert resp.status_code == 422


class TestConcurrency:
    """Test that concurrent execution is correct."""

    def test_stable_ordering(self, mock_env, sample_personas, sample_feature_vector):
        """Results should be in stable order regardless of completion order."""
        personas = sample_personas[:5]
        for client in _build_client(personas):
            body = _make_request_body(sample_feature_vector, num_personas=5)
            resp = client.post("/api/analyze-ad-smart", json=body)
            data = resp.json()

            result_keys = list(data["analysis_results"].keys())
            persona_ids = [str(p["id"]) for p in personas]
            assert result_keys == persona_ids

    def test_timeout_produces_partial(self, mock_env, sample_personas, sample_feature_vector):
        """A timed-out persona should get attention=partial."""
        personas = sample_personas[:2]

        class SlowProvider(MockProvider):
            async def generate_json(self, **kwargs):
                await asyncio.sleep(100)
                return {"attention": "full", "insight": "never reached"}

        with patch("api.routes.analyze.PERSONA_TIMEOUT", 0.1):
            for client in _build_client(personas, mock_provider=SlowProvider()):
                body = _make_request_body(sample_feature_vector, num_personas=2)
                resp = client.post("/api/analyze-ad-smart", json=body)
                data = resp.json()

                for result in data["analysis_results"].values():
                    assert result["attention"] == "partial"


class TestExtractAttentionLevel:
    """Test the heuristic fallback attention extractor."""

    def test_full(self):
        assert _extract_attention_level("This ad is really compelling and engaging") == "full"

    def test_ignore(self):
        assert _extract_attention_level("Not relevant to me at all") == "ignore"

    def test_partial_default(self):
        assert _extract_attention_level("I see the ad but meh") == "partial"
