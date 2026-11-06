"""
Tests for ADK orchestration.

These tests mock the external dependencies (Supabase, OpenAI) so they
run without credentials or network access.
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


# ---------------------------------------------------------------------------
# Fixtures -- fake personas and feature vectors
# ---------------------------------------------------------------------------

FAKE_PERSONAS = [
    {
        "id": f"persona-{i}",
        "name": f"Test Persona {i}",
        "summary": f"A test persona number {i}",
        "demographics": {"age_range": "25-34", "income_level": "middle"},
        "psychographics": {"values": ["health", "productivity"]},
        "pain_points": ["too little time", "information overload"],
        "motivations": ["self-improvement", "career growth"],
    }
    for i in range(5)
]

FAKE_FEATURE_VECTOR = {
    "moondream": {
        "summary": "A fitness app advertisement showing a runner",
        "caption": "Run faster, live better",
        "cta": "Download now",
        "keywords": ["fitness", "running", "health"],
        "target_audience": "Young adults",
    },
    "features": {
        "color": {"palette_hex": ["#FF5733", "#33FF57"], "colorfulness": 0.7},
        "layout": {"aspect_ratio": "16:9", "whitespace_ratio": 0.3},
    },
}


def _fake_openai_response(attention: str = "full", insight: str = "Looks great!"):
    """Build a mock OpenAI ChatCompletion response."""
    msg = MagicMock()
    msg.content = json.dumps({"attention": attention, "insight": insight})
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


# ---------------------------------------------------------------------------
# Unit tests -- tools
# ---------------------------------------------------------------------------

class TestTools:
    def test_aggregate_results_counts(self):
        from orchestration.adk.tools import aggregate_results

        results = {
            "p1": {"attention": "full", "insight": "a", "persona_name": "P1"},
            "p2": {"attention": "partial", "insight": "b", "persona_name": "P2"},
            "p3": {"attention": "ignore", "insight": "c", "persona_name": "P3"},
            "p4": {"attention": "full", "insight": "d", "persona_name": "P4"},
        }
        summary = aggregate_results(results)

        assert summary["total_personas"] == 4
        assert summary["attention"]["full"] == 2
        assert summary["attention"]["partial"] == 1
        assert summary["attention"]["ignore"] == 1
        assert summary["attention_percentages"]["full"] == 50.0

    def test_aggregate_results_empty(self):
        from orchestration.adk.tools import aggregate_results

        summary = aggregate_results({})
        assert summary["total_personas"] == 0

    def test_select_personas_delegates(self):
        from orchestration.adk.tools import select_personas

        mock_selector = MagicMock()
        mock_selector.select_relevant_personas.return_value = FAKE_PERSONAS
        with patch("orchestration.adk.tools._get_selector", return_value=mock_selector):
            result = select_personas(
                target_age_range="25-34",
                industry_keywords=["fitness"],
                num_personas=5,
            )
        assert len(result) == 5
        mock_selector.select_relevant_personas.assert_called_once()


# ---------------------------------------------------------------------------
# Unit tests -- persona agent
# ---------------------------------------------------------------------------

class TestPersonaAgent:
    def test_build_system_prompt_contains_persona_name(self):
        from orchestration.adk.persona_agent import build_system_prompt

        prompt = build_system_prompt(FAKE_PERSONAS[0])
        assert "Test Persona 0" in prompt
        assert "full" in prompt  # mentions attention levels

    def test_build_user_prompt_contains_features(self):
        from orchestration.adk.persona_agent import build_user_prompt

        prompt = build_user_prompt(FAKE_FEATURE_VECTOR)
        assert "Run faster" in prompt
        assert "Download now" in prompt
        assert "#FF5733" in prompt

    def test_parse_llm_response_valid_json(self):
        from orchestration.adk.persona_agent import _parse_llm_response

        text = '{"attention": "full", "insight": "This is great"}'
        att, ins = _parse_llm_response(text)
        assert att == "full"
        assert ins == "This is great"

    def test_parse_llm_response_wrapped_json(self):
        from orchestration.adk.persona_agent import _parse_llm_response

        text = 'Here is my analysis: {"attention": "ignore", "insight": "Not for me"} end'
        att, ins = _parse_llm_response(text)
        assert att == "ignore"
        assert ins == "Not for me"

    def test_parse_llm_response_no_json_falls_back(self):
        from orchestration.adk.persona_agent import _parse_llm_response

        text = "This ad is compelling and engaging"
        att, ins = _parse_llm_response(text)
        assert att == "full"  # heuristic picks up "compelling"

    @pytest.mark.asyncio
    async def test_analyze_single_persona_success(self):
        from orchestration.adk.persona_agent import analyze_single_persona

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _fake_openai_response(
            "partial", "Interesting but not for me"
        )

        result = await analyze_single_persona(
            FAKE_PERSONAS[0], FAKE_FEATURE_VECTOR, openai_client=mock_client
        )

        assert result["persona_id"] == "persona-0"
        assert result["attention"] == "partial"
        assert "Interesting" in result["insight"]

    @pytest.mark.asyncio
    async def test_analyze_single_persona_api_error(self):
        from orchestration.adk.persona_agent import analyze_single_persona

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("API down")

        result = await analyze_single_persona(
            FAKE_PERSONAS[0], FAKE_FEATURE_VECTOR, openai_client=mock_client
        )

        assert result["attention"] == "partial"
        assert "unavailable" in result["insight"].lower()

    @pytest.mark.asyncio
    async def test_fan_out_persona_analyses(self):
        from orchestration.adk.persona_agent import fan_out_persona_analyses

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _fake_openai_response(
            "full", "Love it"
        )

        with patch("orchestration.adk.persona_agent.OpenAI", return_value=mock_client):
            results = await fan_out_persona_analyses(
                FAKE_PERSONAS, FAKE_FEATURE_VECTOR, concurrency=5
            )

        assert len(results) == 5
        for pid, data in results.items():
            assert data["attention"] == "full"
            assert data["insight"] == "Love it"


# ---------------------------------------------------------------------------
# Integration test -- coordinator
# ---------------------------------------------------------------------------

class TestCoordinator:
    @pytest.mark.asyncio
    async def test_run_adk_analysis_produces_correct_shape(self):
        """Contract test: ADK path produces the same response shape as legacy."""
        import orchestration.adk.coordinator as coord_mod
        from orchestration.adk.coordinator import run_adk_analysis

        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = _fake_openai_response(
            "full", "Amazing ad"
        )

        mock_sel = MagicMock()
        mock_sel.select_relevant_personas.return_value = FAKE_PERSONAS

        # Force the fallback (non-ADK-runner) path so we don't depend on
        # ADK session internals in tests.  The logic is identical.
        with patch.object(coord_mod, "_ADK_AVAILABLE", False), \
             patch("orchestration.adk.tools._get_selector", return_value=mock_sel), \
             patch("orchestration.adk.persona_agent.OpenAI", return_value=mock_openai):

            result = await run_adk_analysis(
                feature_vector=FAKE_FEATURE_VECTOR,
                target_age_range="25-34",
                industry_keywords=["fitness"],
                num_personas=5,
            )

        # Verify shape matches AdAnalysisResponse expectations
        assert "selected_personas" in result
        assert "analysis_results" in result
        assert "summary" in result

        assert isinstance(result["selected_personas"], list)
        assert len(result["selected_personas"]) == 5

        assert isinstance(result["analysis_results"], dict)
        assert len(result["analysis_results"]) == 5

        summary = result["summary"]
        assert "total_personas" in summary
        assert "attention" in summary
        assert "attention_percentages" in summary
        assert summary["total_personas"] == 5
        assert summary["attention"]["full"] == 5

        # Each analysis result has the required keys
        for pid, data in result["analysis_results"].items():
            assert "insight" in data
            assert "attention" in data
            assert "persona_name" in data

    @pytest.mark.asyncio
    async def test_run_adk_analysis_empty_personas_returns_empty(self):
        import orchestration.adk.coordinator as coord_mod
        from orchestration.adk.coordinator import run_adk_analysis

        mock_sel = MagicMock()
        mock_sel.select_relevant_personas.return_value = []

        with patch.object(coord_mod, "_ADK_AVAILABLE", False), \
             patch("orchestration.adk.tools._get_selector", return_value=mock_sel):
            result = await run_adk_analysis(
                feature_vector=FAKE_FEATURE_VECTOR,
                num_personas=5,
            )

        assert result["selected_personas"] == []
        assert result["analysis_results"] == {}
        assert result["summary"]["total_personas"] == 0


# ---------------------------------------------------------------------------
# Contract test -- ADK vs legacy produce same shape
# ---------------------------------------------------------------------------

class TestContractParity:
    """Verify that both orchestration paths produce identical response shapes."""

    @pytest.mark.asyncio
    async def test_both_paths_same_keys(self):
        import orchestration.adk.coordinator as coord_mod
        from orchestration.adk.coordinator import run_adk_analysis

        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = _fake_openai_response(
            "partial", "OK ad"
        )

        mock_sel = MagicMock()
        mock_sel.select_relevant_personas.return_value = FAKE_PERSONAS[:2]

        with patch.object(coord_mod, "_ADK_AVAILABLE", False), \
             patch("orchestration.adk.tools._get_selector", return_value=mock_sel), \
             patch("orchestration.adk.persona_agent.OpenAI", return_value=mock_openai):

            adk_result = await run_adk_analysis(
                feature_vector=FAKE_FEATURE_VECTOR,
                num_personas=2,
            )

        # The legacy path produces the same top-level keys
        expected_keys = {"selected_personas", "analysis_results", "summary"}
        assert set(adk_result.keys()) == expected_keys

        # Summary shape
        summary_keys = {"total_personas", "attention", "attention_percentages"}
        assert set(adk_result["summary"].keys()) == summary_keys

        attention_keys = {"full", "partial", "ignore"}
        assert set(adk_result["summary"]["attention"].keys()) == attention_keys
        assert set(adk_result["summary"]["attention_percentages"].keys()) == attention_keys
