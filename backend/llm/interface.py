"""Abstract interface for LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional


class LLMProvider(ABC):
    """Base class for all LLM provider implementations."""

    @abstractmethod
    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> dict:
        """Generate a structured JSON response conforming to the given schema."""
        ...

    @abstractmethod
    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Generate a plain-text response."""
        ...

    @abstractmethod
    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
        schema: dict | None = None,
        temperature: float = 0.2,
    ) -> dict | str:
        """Analyze an image and return structured JSON (if schema) or text."""
        ...

    @abstractmethod
    async def analyze_video(
        self,
        video_path: str,
        prompt: str,
        schema: dict | None = None,
        temperature: float = 0.2,
    ) -> dict | str:
        """Analyze a video file and return structured JSON (if schema) or text."""
        ...
