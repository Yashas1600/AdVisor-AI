"""
ADK Coordinator -- orchestrates the full ad-analysis pipeline.

Pipeline steps:
1. (Optional) Feature extraction -- in practice already done before this
   code runs; the feature_vector is passed in.
2. Persona selection via SmartAgentSelector (ADK tool).
3. Parallel persona critiques -- fan-out to N persona "agents".
4. Aggregation into the existing AdAnalysisResponse shape.

Design choice: we use a *custom BaseAgent* that programmatically drives
the pipeline rather than relying on an LLM to decide which tool to call
next.  This is deliberate -- the pipeline order is deterministic and we
don't want an LLM "deciding" whether to skip persona selection.  ADK's
BaseAgent is the right abstraction for structured workflows while still
fitting into the ADK runner/session model.

When ``google-adk`` is not installed (e.g. in CI or lightweight deploys)
the module falls back to a plain-async implementation that preserves the
same interface.
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

from orchestration.adk.tools import select_personas, aggregate_results
from orchestration.adk.persona_agent import fan_out_persona_analyses


# ---------------------------------------------------------------------------
# Try to import ADK.  If unavailable fall back to a slim async wrapper.
# ---------------------------------------------------------------------------
_ADK_AVAILABLE = False
try:
    from google.adk.agents import BaseAgent
    from google.adk.agents.invocation_context import InvocationContext
    from google.adk.events import Event
    from google.adk.runners import InMemoryRunner
    from google.genai.types import Content, Part
    import uuid as _uuid
    _ADK_AVAILABLE = True
except ImportError:
    pass


if _ADK_AVAILABLE:
    from typing import AsyncGenerator

    class AdvisorCoordinator(BaseAgent):
        """Custom ADK agent that drives the analysis pipeline.

        Session state contract (set before ``run_async``):
            - ``feature_vector``: Dict with moondream + visual features.
            - ``target_age_range``: Optional str.
            - ``industry_keywords``: Optional List[str].
            - ``num_personas``: int (default 50).

        After execution the following keys are written to session state:
            - ``selected_personas``: List of persona dicts.
            - ``analysis_results``: persona_id -> {insight, attention, persona_name}.
            - ``summary``: Aggregated attention counts & percentages.
        """

        model: str = ""  # Not an LLM agent -- no model needed.
        concurrency: int = 10

        async def _run_async_impl(
            self, ctx: InvocationContext
        ) -> AsyncGenerator[Event, None]:
            state = ctx.session.state

            # -- Step 1: Persona selection ------------------------------------
            personas = select_personas(
                target_age_range=state.get("target_age_range"),
                industry_keywords=state.get("industry_keywords"),
                num_personas=state.get("num_personas", 50),
            )
            state["selected_personas"] = personas

            yield Event(
                author=self.name,
                content=Content(parts=[Part(text=f"Selected {len(personas)} personas.")]),
            )

            # -- Step 2: Parallel persona critiques ---------------------------
            feature_vector = state.get("feature_vector", {})
            analysis_results = await fan_out_persona_analyses(
                personas, feature_vector, concurrency=self.concurrency,
            )
            state["analysis_results"] = analysis_results

            yield Event(
                author=self.name,
                content=Content(parts=[Part(text=f"Completed {len(analysis_results)} persona analyses.")]),
            )

            # -- Step 3: Aggregation ------------------------------------------
            summary = aggregate_results(analysis_results)
            state["summary"] = summary

            yield Event(
                author=self.name,
                content=Content(
                    parts=[
                        Part(
                            text=(
                                f"Aggregation complete. "
                                f"Full: {summary['attention']['full']}, "
                                f"Partial: {summary['attention']['partial']}, "
                                f"Ignore: {summary['attention']['ignore']}."
                            )
                        )
                    ]
                ),
            )

    async def _run_via_adk(
        feature_vector: Dict[str, Any],
        target_age_range: Optional[str],
        industry_keywords: Optional[List[str]],
        num_personas: int,
        concurrency: int = 10,
    ) -> Dict[str, Any]:
        """Run the full pipeline through the ADK runner."""
        coordinator = AdvisorCoordinator(
            name="advisor_coordinator",
            concurrency=concurrency,
        )
        runner = InMemoryRunner(agent=coordinator, app_name="AdVisor")

        user_id = "advisor-system"
        # create_session may be sync or async depending on ADK version
        session_or_coro = runner.session_service.create_session(
            app_name="AdVisor",
            user_id=user_id,
        )
        if asyncio.iscoroutine(session_or_coro):
            session = await session_or_coro
        else:
            session = session_or_coro

        # Seed session state
        session.state["feature_vector"] = feature_vector
        session.state["target_age_range"] = target_age_range
        session.state["industry_keywords"] = industry_keywords
        session.state["num_personas"] = num_personas

        # Drive the agent
        user_msg = Content(parts=[Part(text="Run analysis pipeline.")])
        async for _event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=user_msg,
        ):
            pass  # Events are informational; results live in state.

        # Read results back from session state
        return {
            "selected_personas": session.state.get("selected_personas", []),
            "analysis_results": session.state.get("analysis_results", {}),
            "summary": session.state.get("summary", {}),
        }


# ---------------------------------------------------------------------------
# Fallback path -- same logic, no ADK dependency
# ---------------------------------------------------------------------------

async def _run_without_adk(
    feature_vector: Dict[str, Any],
    target_age_range: Optional[str],
    industry_keywords: Optional[List[str]],
    num_personas: int,
    concurrency: int = 10,
) -> Dict[str, Any]:
    """Plain-async fallback when google-adk is not installed."""
    personas = select_personas(
        target_age_range=target_age_range,
        industry_keywords=industry_keywords,
        num_personas=num_personas,
    )
    analysis_results = await fan_out_persona_analyses(
        personas, feature_vector, concurrency=concurrency,
    )
    summary = aggregate_results(analysis_results)
    return {
        "selected_personas": personas,
        "analysis_results": analysis_results,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def run_adk_analysis(
    feature_vector: Dict[str, Any],
    target_age_range: Optional[str] = None,
    industry_keywords: Optional[List[str]] = None,
    num_personas: int = 50,
    concurrency: int = 10,
) -> Dict[str, Any]:
    """Run the full AdVisor analysis pipeline using ADK orchestration.

    This is the single entry point consumed by the ``/api/analyze-ad-smart``
    endpoint when ``ORCHESTRATOR=adk``.

    Returns:
        Dict with ``selected_personas``, ``analysis_results``, ``summary``.
    """
    if _ADK_AVAILABLE:
        print("[ADK] Running analysis via Google ADK coordinator")
        return await _run_via_adk(
            feature_vector, target_age_range, industry_keywords,
            num_personas, concurrency,
        )
    else:
        print("[ADK] google-adk not installed -- using fallback async path")
        return await _run_without_adk(
            feature_vector, target_age_range, industry_keywords,
            num_personas, concurrency,
        )
