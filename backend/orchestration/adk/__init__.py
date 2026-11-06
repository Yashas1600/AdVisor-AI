"""
ADK-based orchestration for AdVisor ad analysis pipeline.

Uses Google Agent Development Kit (ADK) to coordinate:
- Feature extraction
- Persona selection
- Parallel persona critiques (fan-out)
- Result aggregation
"""
from orchestration.adk.coordinator import run_adk_analysis

__all__ = ["run_adk_analysis"]
