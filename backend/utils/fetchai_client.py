"""
Fetch.ai ASI:One API Client

Wrapper for Fetch.ai's ASI:One intelligent AI platform.
Uses OpenAI-compatible chat completions API with asi1-mini model.
"""
import os
import requests
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()


class FetchAIClient:
    """Client for interacting with Fetch.ai ASI:One API"""

    def __init__(self, api_key: Optional[str] = None, model: str = "asi1-mini"):
        """
        Initialize Fetch.ai client

        Args:
            api_key: Fetch.ai API key (defaults to FETCH_AI_API_KEY env var)
            model: Model to use (default: asi1-mini)
        """
        self.api_key = api_key or os.getenv("FETCH_AI_API_KEY")
        if not self.api_key:
            raise ValueError("FETCH_AI_API_KEY not found in environment")

        self.model = model
        self.base_url = "https://api.asi1.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Create a chat completion using Fetch.ai ASI:One

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response

        Returns:
            Response dict with 'choices', 'usage', etc.
        """
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Fetch.ai API error: {str(e)}")

    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a response from a single prompt (convenience method)

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt to set context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Extract message content from response
        if response and "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0]["message"]["content"]
        else:
            raise Exception("Invalid response from Fetch.ai API")

    def test_connection(self) -> bool:
        """
        Test connection to Fetch.ai API

        Returns:
            True if connection successful
        """
        try:
            response = self.generate_response("Hello! This is a test.")
            return bool(response)
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


# Module-level convenience functions
def create_client(model: str = "asi1-mini") -> FetchAIClient:
    """Create a Fetch.ai client instance"""
    return FetchAIClient(model=model)


def generate_text(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Generate text using default Fetch.ai client"""
    client = create_client()
    return client.generate_response(prompt, system_prompt=system_prompt)
