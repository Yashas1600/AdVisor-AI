import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api.schemas_insights import (
    AttentionTally,
    InsightsSummaryRequest,
    InsightsSummaryResponse,
    InsightsSummarySelectedRequest,
    AgentInsight,
    ByIdItem,
)
from api.services.insights_summarizer import summarize_insights


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/insights", response_model=InsightsSummaryResponse)
def insights(
    payload: InsightsSummaryRequest,
    provider: Optional[str] = Query(None, description="Provider override: local|openai|google|anthropic"),
    temperature: Optional[float] = Query(None, description="LLM temperature (default 0.2)"),
    debug: Optional[bool] = Query(False, description="Include per_insight_scores and raw prompts in notes when true"),
    fast: Optional[bool] = Query(True, description="Enable dedupe fast-path to reduce latency"),
    timeout_s: Optional[float] = Query(30.0, description="Request timeout to provider in seconds"),
    max_tokens: Optional[int] = Query(1500, description="Max tokens for provider response"),
):
    try:
        used_provider = (provider or "openai").lower()
        used_temp = temperature if temperature is not None else 0.2

        llm_output, dbg = summarize_insights(
            payload=payload,
            provider=used_provider,
            temperature=used_temp,
            debug=bool(debug),
            fast=bool(fast),
            timeout_s=float(timeout_s) if timeout_s is not None else 20.0,
            max_tokens=int(max_tokens) if max_tokens is not None else 600,
        )

        # Compute averaged score
        per_scores = llm_output.per_insight_scores
        avg_score = sum(per_scores) / max(len(per_scores), 1)

        # Tally attention buckets
        tally = AttentionTally()
        for ins in payload.insights:
            attn = ins.attention
            if attn == "neutral":  # backward compatibility
                attn = "partial"
            if attn == "full":
                tally.full += 1
            elif attn == "partial":
                tally.partial += 1
            else:
                tally.ignore += 1

        notes = []
        if debug:
            notes.append("Debug: provider=%s" % used_provider)
            # We intentionally do not include raw prompts here for now; can be added if needed

        return InsightsSummaryResponse(
            averaged_impact_score=avg_score,
            attention_tally=tally,
            overall_insights=llm_output.overall_insights,
            demographics=llm_output.demographics,
            per_insight_scores=per_scores if debug else None,
            used_provider=used_provider,  # type: ignore[arg-type]
            latency_ms=int(dbg.get("latency_ms", 0)),
            notes=notes,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Insights summarization failed: %s", exc)
        raise HTTPException(status_code=502, detail="Provider failure or internal error.")


def _convert_selected_payload(sel: InsightsSummarySelectedRequest) -> InsightsSummaryRequest:
    insights: list[AgentInsight] = []
    for key in sel.selected:
        str_key = str(key)
        item = sel.byId.get(str_key)
        if not item:
            continue
        insights.append(
            AgentInsight(agent_id=str_key, sentence=item.insight, attention=item.attention, persona_name=item.persona_name)
        )
    return InsightsSummaryRequest(insights=insights, ad_context=sel.ad_context)


@router.post("/insights/selected", response_model=InsightsSummaryResponse)
def insights_selected(
    payload: InsightsSummarySelectedRequest,
    provider: Optional[str] = Query(None, description="Provider override: local|openai|google|anthropic"),
    temperature: Optional[float] = Query(None, description="LLM temperature (default 0.2)"),
    debug: Optional[bool] = Query(False, description="Include per_insight_scores and raw prompts in notes when true"),
    fast: Optional[bool] = Query(True, description="Enable dedupe fast-path to reduce latency"),
    timeout_s: Optional[float] = Query(30.0, description="Request timeout to provider in seconds"),
    max_tokens: Optional[int] = Query(1500, description="Max tokens for provider response"),
):
    try:
        normalized = _convert_selected_payload(payload)
        return insights(
            payload=normalized,
            provider=provider,
            temperature=temperature,
            debug=debug,
            fast=fast,
            timeout_s=timeout_s,
            max_tokens=max_tokens,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Insights selected summarization failed: %s", exc)
        raise HTTPException(status_code=502, detail="Provider failure or internal error.")


def _fetch_supabase_row(analysis_id: str) -> dict:
    try:
        # Import lazily to avoid hard dependency unless this route is used
        from backend.config.supabase_client import get_client  # type: ignore
    except Exception as exc:  # pragma: no cover - import failure path
        raise RuntimeError("Supabase client is not available. Ensure supabase-py is installed and env vars are set.") from exc

    sb = get_client()
    resp = sb.table("ad_analyses").select("id,title,input,agent_results").eq("id", analysis_id).execute()
    data = getattr(resp, "data", None)
    if isinstance(data, list) and data:
        return data[0]
    if isinstance(data, dict):
        return data
    raise HTTPException(status_code=404, detail="Analysis not found")


@router.get("/insights/from_supabase", response_model=InsightsSummaryResponse)
def insights_from_supabase(
    analysis_id: str = Query(..., description="UUID of ad_analyses row"),
    provider: Optional[str] = Query(None, description="Provider override: local|openai|google|anthropic"),
    temperature: Optional[float] = Query(None, description="LLM temperature (default 0.2)"),
    debug: Optional[bool] = Query(False, description="Include per_insight_scores and raw prompts in notes when true"),
    fast: Optional[bool] = Query(True, description="Enable dedupe fast-path to reduce latency"),
    timeout_s: Optional[float] = Query(30.0, description="Request timeout to provider in seconds"),
    max_tokens: Optional[int] = Query(1500, description="Max tokens for provider response"),
):
    try:
        row = _fetch_supabase_row(analysis_id)
        agent_results = row.get("agent_results")
        if not agent_results:
            raise HTTPException(status_code=400, detail="Row has no agent_results")

        # agent_results is expected to be a dict with byId and selected
        by_id = agent_results.get("byId") if isinstance(agent_results, dict) else None
        selected = agent_results.get("selected") if isinstance(agent_results, dict) else None
        if not isinstance(by_id, dict) or not isinstance(selected, list):
            raise HTTPException(status_code=400, detail="agent_results must contain byId and selected")

        ad_context = row.get("title")
        sel_payload = InsightsSummarySelectedRequest(byId=by_id, selected=selected, ad_context=ad_context)
        normalized = _convert_selected_payload(sel_payload)

        used_provider = (provider or "openai").lower()
        used_temp = temperature if temperature is not None else 0.2

        llm_output, dbg = summarize_insights(
            payload=normalized,
            provider=used_provider,
            temperature=used_temp,
            debug=bool(debug),
            fast=bool(fast),
            timeout_s=float(timeout_s) if timeout_s is not None else 20.0,
            max_tokens=int(max_tokens) if max_tokens is not None else 600,
        )

        per_scores = llm_output.per_insight_scores
        avg_score = sum(per_scores) / max(len(per_scores), 1)

        tally = AttentionTally()
        for ins in normalized.insights:
            attn = ins.attention
            if attn == "neutral":
                attn = "partial"
            if attn == "full":
                tally.full += 1
            elif attn == "partial":
                tally.partial += 1
            else:
                tally.ignore += 1

        notes = []
        if debug:
            notes.append("Debug: provider=%s" % used_provider)

        return InsightsSummaryResponse(
            averaged_impact_score=avg_score,
            attention_tally=tally,
            overall_insights=llm_output.overall_insights,
            demographics=llm_output.demographics,
            per_insight_scores=per_scores if debug else None,
            used_provider=used_provider,  # type: ignore[arg-type]
            latency_ms=int(dbg.get("latency_ms", 0)),
            notes=notes,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Insights from Supabase failed: %s", exc)
        raise HTTPException(status_code=502, detail="Supabase or provider failure.")


