"""OpenAI provider wrapping AsyncOpenAI."""

import base64
import json
import os
import time

from openai import AsyncOpenAI

from llm.interface import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI provider (GPT-4o-mini by default)."""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY for OpenAI provider.")
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def _log(self, method: str, latency_ms: int, usage) -> None:
        input_tokens = getattr(usage, "prompt_tokens", 0) or 0
        output_tokens = getattr(usage, "completion_tokens", 0) or 0
        # Rough cost estimate (GPT-4o-mini pricing)
        cost = (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000
        print(
            f"[OpenAI] {method}  latency={latency_ms}ms  "
            f"in={input_tokens} out={output_tokens}  est_cost=${cost:.6f}"
        )

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> dict:
        t0 = time.time()
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        latency = int((time.time() - t0) * 1000)
        self._log("generate_json", latency, response.usage)
        text = response.choices[0].message.content
        return json.loads(text)

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        t0 = time.time()
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency = int((time.time() - t0) * 1000)
        self._log("generate_text", latency, response.usage)
        return response.choices[0].message.content

    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
        schema: dict | None = None,
        temperature: float = 0.2,
    ) -> dict | str:
        t0 = time.time()
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64}"

        kwargs: dict = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            "temperature": temperature,
            "max_tokens": 1000,
        }
        if schema is not None:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self._client.chat.completions.create(**kwargs)
        latency = int((time.time() - t0) * 1000)
        self._log("analyze_image", latency, response.usage)

        text = response.choices[0].message.content
        if schema is not None:
            return json.loads(text)
        return text

    async def analyze_video(
        self,
        video_path: str,
        prompt: str,
        schema: dict | None = None,
        temperature: float = 0.2,
    ) -> dict | str:
        raise NotImplementedError("OpenAI does not support direct video analysis.")
