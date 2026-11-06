"""Mock provider for tests."""

from llm.interface import LLMProvider


class MockProvider(LLMProvider):
    """Returns canned responses.  Useful for unit tests and local development."""

    def __init__(
        self,
        default_attention: str = "full",
        default_insight: str = "Mock insight",
    ):
        self.default_attention = default_attention
        self.default_insight = default_insight
        self.calls: list[dict] = []  # record calls for assertions

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> dict:
        self.calls.append(
            {"method": "generate_json", "system": system_prompt, "user": user_prompt}
        )
        return {
            "attention": self.default_attention,
            "insight": self.default_insight,
        }

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        self.calls.append(
            {"method": "generate_text", "system": system_prompt, "user": user_prompt}
        )
        return self.default_insight

    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
        schema: dict | None = None,
        temperature: float = 0.2,
    ) -> dict | str:
        self.calls.append({"method": "analyze_image", "prompt": prompt})
        if schema is not None:
            return {"description": self.default_insight}
        return self.default_insight

    async def analyze_video(
        self,
        video_path: str,
        prompt: str,
        schema: dict | None = None,
        temperature: float = 0.2,
    ) -> dict | str:
        self.calls.append({"method": "analyze_video", "prompt": prompt})
        if schema is not None:
            return {"description": self.default_insight}
        return self.default_insight
