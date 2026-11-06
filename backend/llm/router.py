"""Provider factory -- resolves provider name to an LLMProvider instance."""

import os
from functools import lru_cache

from llm.interface import LLMProvider

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")


@lru_cache(maxsize=8)
def get_provider(override: str | None = None) -> LLMProvider:
    """Return a cached LLMProvider for the requested backend.

    Parameters
    ----------
    override : str | None
        If given, use this provider name instead of the ``LLM_PROVIDER`` env
        variable.
    """
    name = (override or LLM_PROVIDER).lower()

    if name == "gemini":
        from llm.gemini import GeminiProvider
        return GeminiProvider()

    if name == "openai":
        from llm.openai_provider import OpenAIProvider
        return OpenAIProvider()

    if name == "asi":
        from llm.asi import ASIProvider
        return ASIProvider()

    if name == "mock":
        from llm.mock import MockProvider
        return MockProvider()

    raise ValueError(f"Unknown LLM provider: {name}")
