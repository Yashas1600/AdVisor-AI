"""
Diagnostic endpoint to check Moondream configuration on EC2
"""
import os
import logging
from fastapi import APIRouter

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health/moondream")
async def moondream_diagnostic():
    """Check Moondream API configuration and availability"""
    diagnostics = {
        "moondream_api_key_set": bool(os.getenv("MOONDREAM_API_KEY")),
        "moondream_api_key_length": len(os.getenv("MOONDREAM_API_KEY", "")),
    }

    # Test moondream package import
    try:
        import moondream as md
        diagnostics["moondream_package_installed"] = True
        diagnostics["moondream_version"] = getattr(md, "__version__", "unknown")
    except ImportError as e:
        diagnostics["moondream_package_installed"] = False
        diagnostics["import_error"] = str(e)

    # Test client initialization
    api_key = os.getenv("MOONDREAM_API_KEY")
    if api_key:
        try:
            import moondream as md
            client = md.vl(api_key=api_key)
            diagnostics["moondream_client_initialized"] = True
        except Exception as e:
            diagnostics["moondream_client_initialized"] = False
            diagnostics["client_error"] = str(e)
    else:
        diagnostics["moondream_client_initialized"] = False
        diagnostics["client_error"] = "MOONDREAM_API_KEY not set"

    return diagnostics
