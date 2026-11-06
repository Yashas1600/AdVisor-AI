"""ASI / Fetch.ai provider (legacy)."""

import json
import os
import time
from typing import Optional

import requests

from llm.interface import LLMProvider


class ASIProvider(LLMProvider):
    """Wraps the Fetch.ai ASI:One API (asi1-mini).

    Only text-based methods are supported.  Image and video analysis
    raise ``NotImplementedError``.
    """

    def __init__(self):
        self._api_key = os.getenv("FETCH_AI_API_KEY")
        if not self._api_key:
            raise RuntimeError("Missing FETCH_AI_API_KEY for ASI provider.")
        self._model = os.getenv("ASI_MODEL", "asi1-mini")
        self._base_url = "https://api.asi1.ai/v1"
        self._headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _log(self, method: str, latency_ms: int, usage: dict) -> None:
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        print(
            f"[ASI] {method}  latency={latency_ms}ms  "
            f"in={input_tokens} out={output_tokens}"
        )

    def _call(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> dict:
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = requests.post(
            f"{self._base_url}/chat/completions",
            headers=self._headers,
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> dict:
        t0 = time.time()
        # ASI doesn't support response_format, so we instruct via prompt
        augmented_system = (
            system_prompt
            + "\n\nYou MUST respond with valid JSON only. No markdown, no extra text."
        )
        messages = [
            {"role": "system", "content": augmented_system},
            {"role": "user", "content": user_prompt},
        ]
        data = self._call(messages, temperature, max_tokens)
        latency = int((time.time() - t0) * 1000)
        self._log("generate_json", latency, data.get("usage", {}))

        text = data["choices"][0]["message"]["content"].strip()
        # Strip markdown fences
        if text.startswith("```"):
            lines = text.splitlines()
            lines = [l for l in lines if not l.startswith("```")]
            text = "\n".join(lines).strip()
        return json.loads(text)

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        t0 = time.time()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        data = self._call(messages, temperature, max_tokens)
        latency = int((time.time() - t0) * 1000)
        self._log("generate_text", latency, data.get("usage", {}))
        return data["choices"][0]["message"]["content"]

    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
        schema: dict | None = None,
        temperature: float = 0.2,
    ) -> dict | str:
        raise NotImplementedError("ASI provider does not support image analysis.")

    async def analyze_video(
        self,
        video_path: str,
        prompt: str,
        schema: dict | None = None,
        temperature: float = 0.2,
    ) -> dict | str:
        raise NotImplementedError("ASI provider does not support video analysis.")
