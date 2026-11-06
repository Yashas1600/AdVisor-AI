"""Gemini provider using the google-genai SDK."""

import json
import os
import time
from typing import Optional

from google import genai
from google.genai import types

from llm.interface import LLMProvider


class GeminiProvider(LLMProvider):
    """Google Gemini provider (default).

    Works in API-key mode by default.  When ``GOOGLE_CLOUD_PROJECT`` is set the
    client automatically switches to Vertex AI mode.
    """

    def __init__(self):
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        if project:
            self._client = genai.Client(
                vertexai=True,
                project=project,
                location=location,
            )
        else:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "Set GEMINI_API_KEY or GOOGLE_CLOUD_PROJECT to use the Gemini provider."
                )
            self._client = genai.Client(api_key=api_key)

        self._model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _log(self, method: str, latency_ms: int, usage) -> None:
        input_tokens = getattr(usage, "prompt_token_count", 0) or 0
        output_tokens = getattr(usage, "candidates_token_count", 0) or 0
        # Rough cost estimate (Gemini 2.5 Flash pricing as of 2025-06)
        cost = (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000
        print(
            f"[Gemini] {method}  latency={latency_ms}ms  "
            f"in={input_tokens} out={output_tokens}  est_cost=${cost:.6f}"
        )

    def _parse_json(self, text: str) -> dict:
        """Best-effort JSON extraction from model output."""
        text = text.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            lines = text.splitlines()
            lines = [l for l in lines if not l.startswith("```")]
            text = "\n".join(lines).strip()
        return json.loads(text)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> dict:
        t0 = time.time()
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
            response_schema=schema,
        )
        response = self._client.models.generate_content(
            model=self._model,
            contents=user_prompt,
            config=config,
        )
        latency = int((time.time() - t0) * 1000)
        self._log("generate_json", latency, response.usage_metadata)
        return self._parse_json(response.text)

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        t0 = time.time()
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        response = self._client.models.generate_content(
            model=self._model,
            contents=user_prompt,
            config=config,
        )
        latency = int((time.time() - t0) * 1000)
        self._log("generate_text", latency, response.usage_metadata)
        return response.text

    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
        schema: dict | None = None,
        temperature: float = 0.2,
    ) -> dict | str:
        t0 = time.time()
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        config_kwargs: dict = {
            "temperature": temperature,
        }
        if schema is not None:
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_schema"] = schema

        config = types.GenerateContentConfig(**config_kwargs)
        response = self._client.models.generate_content(
            model=self._model,
            contents=[image_part, prompt],
            config=config,
        )
        latency = int((time.time() - t0) * 1000)
        self._log("analyze_image", latency, response.usage_metadata)

        if schema is not None:
            return self._parse_json(response.text)
        return response.text

    async def analyze_video(
        self,
        video_path: str,
        prompt: str,
        schema: dict | None = None,
        temperature: float = 0.2,
    ) -> dict | str:
        t0 = time.time()

        # Upload the video file and poll until ACTIVE
        uploaded = self._client.files.upload(file=video_path)
        while uploaded.state.name == "PROCESSING":
            time.sleep(2)
            uploaded = self._client.files.get(name=uploaded.name)

        if uploaded.state.name != "ACTIVE":
            raise RuntimeError(
                f"Video upload failed with state: {uploaded.state.name}"
            )

        video_part = types.Part.from_uri(
            file_uri=uploaded.uri,
            mime_type=uploaded.mime_type,
        )

        config_kwargs: dict = {
            "temperature": temperature,
        }
        if schema is not None:
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_schema"] = schema

        config = types.GenerateContentConfig(**config_kwargs)
        response = self._client.models.generate_content(
            model=self._model,
            contents=[video_part, prompt],
            config=config,
        )
        latency = int((time.time() - t0) * 1000)
        self._log("analyze_video", latency, response.usage_metadata)

        if schema is not None:
            return self._parse_json(response.text)
        return response.text
