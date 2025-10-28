import json
import re
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from api.schemas_brandmeta import (
    BrandMeta,
    BrandMetaRequest,
    BrandMetaResponse,
    AudienceMetrics,
    Priors,
    Signals,
)
from api.services.llm_adapter import complete_structured
from extractor.nlp.heuristics import (
    choose_product_name,
    extract_keywords,
    extract_value_prop,
    find_numbers,
    map_category,
    map_price_tier,
    normalize_text,
    infer_product,
    infer_industry,
    infer_audience,
)


logger = logging.getLogger(__name__)


def _collect_signals(payload: BrandMetaRequest) -> Signals:
    ocr_text_raw = ""
    md = payload.moondream_summary or ""
    declared_company = payload.declared_company
    detected_brand_names = payload.detected_brand_names or []
    numbers: List[str] = payload.numbers_found or []
    hints = payload.hints or {}

    if payload.features and isinstance(payload.features, dict):
        # Expect features.features.ocr.text and sibling moondream_summary/declared_company
        try:
            inner = payload.features
            if not md:
                md = inner.get("moondream_summary") or ""
            if not declared_company:
                declared_company = inner.get("declared_company")
            f2 = inner.get("features") or {}
            ocr = ((f2.get("ocr") or {}).get("text")) or ""
            ocr_text_raw = str(ocr)

            # Pull optional moondream block if present at top-level of extract response
            md_block = inner.get("moondream") or {}
            md_keywords = md_block.get("keywords") or []
            md_text = md_block.get("extracted_text") or ""
            md_audience = md_block.get("target_audience") or ""
        except Exception:
            logger.debug("Failed to parse nested features")
    else:
        ocr_text_raw = payload.ocr_text or ""

    # Normalize OCR for matching but keep raw
    ocr_norm = normalize_text(ocr_text_raw)
    combined_for_numbers = f"{ocr_text_raw} {md}"
    if not numbers:
        numbers = find_numbers(combined_for_numbers)

    return Signals(
        ocr_text_raw=ocr_text_raw,
        ocr_text_norm=ocr_norm,
        moondream_summary=md or "",
        moondream_keywords=md_keywords if 'md_keywords' in locals() else [],
        moondream_extracted_text=md_text if 'md_text' in locals() else "",
        moondream_target_audience=md_audience if 'md_audience' in locals() else "",
        declared_company=declared_company,
        detected_brand_names=detected_brand_names,
        numbers_found=numbers,
        hints=hints,
    )


def _build_priors(signals: Signals) -> Tuple[Priors, BrandMeta]:
    text_all_norm = normalize_text(
        f"{signals.moondream_summary} {signals.moondream_extracted_text} {signals.ocr_text_raw} {' '.join(signals.moondream_keywords)} {signals.moondream_target_audience}"
    )

    # Category
    category, cat_conf, cat_why = map_category(text_all_norm)

    # Price tier
    price, price_conf, price_why = map_price_tier(text_all_norm, signals.numbers_found)

    # Product name
    pname, pname_conf, pname_why = choose_product_name(
        signals.declared_company, signals.detected_brand_names, signals.moondream_summary, signals.ocr_text_raw
    )

    # Value prop
    vprop, v_conf, v_why = extract_value_prop(signals.moondream_summary, signals.ocr_text_raw)

    # Keywords
    kws, kw_conf, kw_why = extract_keywords(signals.moondream_summary, signals.ocr_text_raw, [])

    # New fields
    product, prod_conf, prod_why = infer_product(text_all_norm, signals.declared_company)
    industry, ind_conf, ind_why = infer_industry(category or "other", text_all_norm)
    audience_dict, aud_conf, aud_why = infer_audience(text_all_norm)

    priors = Priors(
        candidate_product_name=pname,
        category_prior=category if category else None,
        price_position_prior=price if price else None,
        candidate_value_prop=vprop,
        candidate_keywords=kws,
        candidate_product=product,
        industry_prior=industry,
        audience_prior=AudienceMetrics(**audience_dict),
    )

    # Heuristic brand meta as baseline
    brand_meta = BrandMeta(
        product_name=pname,
        category=category or "other",
        price_positioning=price or "mid",
        claimed_value_prop=vprop[:300],
        target_keywords=[k.lower() for k in kws][:8],
        product=product,
        industry=industry,
        audience=audience_dict,
        confidence={
            "product_name": float(pname_conf or 0.35),
            "category": float(cat_conf or 0.35),
            "price_positioning": float(price_conf or 0.35),
            "claimed_value_prop": float(v_conf or 0.35),
            "target_keywords": float(kw_conf or 0.35),
        },
        rationales={
            "product_name": pname_why,
            "category": cat_why,
            "price_positioning": price_why,
            "claimed_value_prop": v_why,
            "target_keywords": kw_why,
        },
        warnings=[],
    )

    return priors, brand_meta


def _ensure_constraints(meta: Dict[str, Any]) -> Dict[str, Any]:
    bm = meta.get("brand_meta") or meta
    # Trim value prop to <= 2 sentences
    v = (bm.get("claimed_value_prop") or "").strip()
    if v:
        # simple two-sentence cap
        splits = [s.strip() for s in re.split(r"(?<=[.!?])\s+", v) if s.strip()]
        v2 = " ".join(splits[:2])
        bm["claimed_value_prop"] = v2[:400]

    # Keywords: 5-8 unique lowercase
    kws = [str(k).strip().lower() for k in (bm.get("target_keywords") or []) if str(k).strip()]
    seen = set()
    uniq = []
    for k in kws:
        if k not in seen:
            seen.add(k)
            uniq.append(k)
    if len(uniq) < 5:
        while len(uniq) < 5:
            uniq.append("keyword")
    bm["target_keywords"] = uniq[:8]

    # Confidences in [0,1]
    conf = bm.get("confidence") or {}
    for k in ["product_name", "category", "price_positioning", "claimed_value_prop", "target_keywords"]:
        v = float(conf.get(k, 0.35))
        v = 0.0 if v < 0 else 1.0 if v > 1 else v
        conf[k] = v
    bm["confidence"] = conf

    # Rationales: ensure all keys present as short strings
    rats = bm.get("rationales") or {}
    if not isinstance(rats, dict):
        rats = {}
    for k in ["product_name", "category", "price_positioning", "claimed_value_prop", "target_keywords"]:
        rv = rats.get(k)
        if not isinstance(rv, str) or not rv.strip():
            rats[k] = "heuristic"
    bm["rationales"] = rats

    # Enums: fallback
    if bm.get("category") not in [
        "meal-prep",
        "wearable health",
        "insurance",
        "fintech",
        "gaming",
        "beauty",
        "other",
    ]:
        bm["category"] = "other"
    if bm.get("price_positioning") not in ["budget", "mid", "premium"]:
        bm["price_positioning"] = "mid"

    meta["brand_meta"] = bm

    return meta


def _build_prompts(signals: Signals, priors: Priors) -> Tuple[str, str]:
    system = (
        "Role: transform ad signals (Moondream + hints) into BrandMeta strictly matching schema.\n"
        "Rules: output only JSON; be conservative; keep value_prop <= 2 sentences; keywords 5–8 concise; "
        "mention ambiguities in warnings; use priors as hints, not mandates."
    )
    user = (
        "Category is freeform (e.g., automotive, fitness, technology, insurance, fintech, gaming, beauty, travel, meal-prep, wearable health).\n"
        "Price positioning enum: [\"budget\",\"mid\",\"premium\"].\n\n"
        "Audience enums:\n"
        "- age_cohort: [\"13-17\",\"18-24\",\"25-34\",\"35-44\",\"45+\",\"unknown\"]\n"
        "- life_stage: [\"student\",\"early-career\",\"parent\",\"retiree\",\"unknown\"]\n"
        "- media_preference: [\"short videos\",\"long posts\",\"image carousels\",\"mixed\",\"unknown\"]\n"
        "- tone_preference: [\"humorous\",\"authoritative\",\"minimalist\",\"hype\",\"unknown\"]\n\n"
        f"Signals:\n- Declared company: {signals.declared_company}\n"
        f"- Detected brand names: {', '.join(signals.detected_brand_names)}\n"
        f"- Moondream summary: {signals.moondream_summary}\n"
        f"- Extracted text (normalized): {signals.ocr_text_norm}\n"
        f"- Numbers found (price candidates): {', '.join(signals.numbers_found)}\n\n"
        f"Priors (from heuristics; may be wrong):\n"
        f"- candidate_product_name: {priors.candidate_product_name}\n"
        f"- category_prior: {priors.category_prior}\n"
        f"- price_position_prior: {priors.price_position_prior}\n"
        f"- candidate_value_prop: {priors.candidate_value_prop}\n"
        f"- candidate_keywords: {', '.join(priors.candidate_keywords)}\n"
        f"- candidate_product: {priors.candidate_product}\n"
        f"- industry_prior: {priors.industry_prior}\n"
        f"- audience_prior: {priors.audience_prior}\n\n"
        "Requirements:\n"
        "1) Output strict JSON adhering to the BrandMeta schema (no extra keys).\n"
        "2) Fill all confidences ∈ [0,1] based on evidence strength.\n"
        "3) target_keywords: 5–8 unique, lowercase tags; audience/intent/style over generic words.\n"
        "4) Keep claimed_value_prop ≤ 2 sentences and faithful to evidence.\n"
        "5) Include explicit fields: product, industry, and audience (age_cohort, life_stage, region, language, media_preference, values, tone_preference).\n"
        "   - age_cohort: extract explicit ages only; otherwise choose 'unknown'.\n"
        "   - life_stage: infer conservatively from context (student/early-career/parent/retiree/unknown).\n"
        "   - region: prefer broad region/time-zone (e.g., 'North America (EST)'), not precise locations.\n"
        "   - language: dominant language of the text.\n"
        "   - media_preference: short videos/long posts/image carousels/mixed/unknown.\n"
        "   - values: concise tags like sustainability, frugality, performance, aesthetics.\n"
        "   - tone_preference: humorous/authoritative/minimalist/hype/unknown.\n"
        "6) Category MUST NOT be 'other' or 'unknown'. Choose the closest plausible specific category using industry/keywords/hints.\n"
        "7) If evidence is thin or conflicting, pick the strongest single answer, and add an explanation to \"warnings\".\n"
    )
    return system, user


def run_brandmeta_pipeline(
    payload: BrandMetaRequest,
    provider: Optional[str] = None,
    temperature: Optional[float] = None,
    debug: Optional[bool] = None,
) -> BrandMetaResponse:
    start = time.time()
    provider_sel = (provider or os.getenv("BRANDMETA_PROVIDER", "local")).lower()
    temperature = 0.2 if temperature is None else float(temperature)
    debug = bool(debug) if debug is not None else os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}

    signals = _collect_signals(payload)

    # Validate sufficient signals again (server-side), specifically require at least md or ocr
    if not (signals.moondream_summary or signals.ocr_text_raw):
        raise ValueError("Insufficient signals: provide moondream_summary or ocr_text")

    priors, heur_meta = _build_priors(signals)

    # Prepare prompts
    system_prompt, user_prompt = _build_prompts(signals, priors)

    # Try provider
    notes: List[str] = []
    if debug:
        notes.append(f"system_prompt: {system_prompt}")
        notes.append(f"user_prompt: {user_prompt}")

    used_provider = provider_sel
    llm_failed = False
    result_data: Dict[str, Any]

    try:
        # For local provider, we pass the heuristic BrandMeta as the schema_hint
        llm_dict, dbg = complete_structured(
            provider=provider_sel,
            temperature=temperature,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema_hint={
                "brand_meta": heur_meta.model_dump(),
                "used_provider": provider_sel,
                "latency_ms": 0,
                "notes": [],
            },
        )
        if dbg:
            if dbg.get("latency_ms") is not None:
                notes.append(f"provider_latency_ms={dbg['latency_ms']}")
            if dbg.get("provider"):
                notes.append(f"provider={dbg['provider']} model={dbg.get('model')}")
            if dbg.get("fallback"):
                notes.append(f"provider_fallback={dbg['fallback']}")
    except Exception as exc:
        logger.warning("Provider call failed: %s", exc)
        llm_dict = {}
        llm_failed = True
        if debug:
            notes.append(f"provider_error: {exc}")

    # Validate and possibly repair
    final_obj: Optional[BrandMetaResponse] = None
    warnings: List[str] = []
    if llm_dict:
        candidate = _ensure_constraints(llm_dict)
        # Fill wrapper fields with current context (force override)
        candidate["used_provider"] = used_provider
        candidate["latency_ms"] = candidate.get("latency_ms", 0)
        candidate["notes"] = notes
        try:
            final_obj = BrandMetaResponse(**candidate)
        except Exception as exc:
            # one repair attempt: fall back to heuristics structure
            logger.debug("Validation failed, attempting repair: %s", exc)
            repaired = {
                "brand_meta": heur_meta.model_dump(),
                "used_provider": used_provider,
                "latency_ms": 0,
                "notes": notes,
            }
            try:
                final_obj = BrandMetaResponse(**repaired)
                llm_failed = True
                warnings.append("LLM_failed_validation")
            except Exception as exc2:
                logger.warning("Repair failed: %s", exc2)
                final_obj = None

    if final_obj is None:
        # Fall back to heuristics-only
        heur = heur_meta.model_dump()
        if llm_failed:
            heur["warnings"].append("LLM_failed_validation")
        final_obj = BrandMetaResponse(
            brand_meta=BrandMeta(**heur),
            used_provider=used_provider,
            latency_ms=int((time.time() - start) * 1000),
            notes=notes,
        )
    else:
        # Propagate warnings if any
        if warnings:
            bm = final_obj.brand_meta
            bm.warnings.extend(warnings)
            final_obj.brand_meta = bm
        # Update latency
        final_obj.latency_ms = int((time.time() - start) * 1000)

    # Server-side guard: avoid 'other'/'unknown' category; replace with better guess
    try:
        bm = final_obj.brand_meta
        cat = (bm.category or "").strip().lower()
        if cat in {"other", "unknown", ""}:
            # prefer industry, else heuristic category
            replacement = (bm.industry or "").strip() or (priors.category_prior or "").strip()
            if not replacement:
                # derive from keywords
                kws = bm.target_keywords or []
                for k in kws:
                    k2 = k.lower()
                    if any(x in k2 for x in ["auto", "car", "vehicle", "van"]):
                        replacement = "automotive"; break
                    if any(x in k2 for x in ["fitness", "gym", "workout"]):
                        replacement = "fitness"; break
                    if any(x in k2 for x in ["tech", "software", "ai"]):
                        replacement = "technology"; break
                    if any(x in k2 for x in ["insurance", "policy", "coverage"]):
                        replacement = "insurance"; break
                    if any(x in k2 for x in ["finance", "card", "credit", "bank"]):
                        replacement = "fintech"; break
            if replacement:
                bm.category = replacement
                if "category_overridden_from_other" not in bm.warnings:
                    bm.warnings.append("category_overridden_from_other")
                final_obj.brand_meta = bm
    except Exception:
        pass

    return final_obj


