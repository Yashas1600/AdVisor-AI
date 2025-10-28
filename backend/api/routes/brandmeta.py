import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api.schemas_brandmeta import BrandMetaRequest, BrandMetaResponse
from api.services.brandmeta_pipeline import run_brandmeta_pipeline


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/brandmeta", response_model=BrandMetaResponse)
def brandmeta(
    payload: BrandMetaRequest,
    provider: Optional[str] = Query(None, description="Provider override: local|openai|google|anthropic"),
    temperature: Optional[float] = Query(None, description="LLM temperature (default 0.2)"),
    debug: Optional[bool] = Query(None, description="Include raw prompts in notes when true"),
) -> BrandMetaResponse:
    try:
        return run_brandmeta_pipeline(payload, provider=provider, temperature=temperature, debug=debug)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("BrandMeta failed: %s", exc)
        raise HTTPException(status_code=502, detail="Provider failure or internal error.")


