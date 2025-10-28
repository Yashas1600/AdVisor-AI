"""
OpenAI Client Utility for AdVisor
Handles GPT-5 Nano API calls and embeddings generation
"""
import os
import json
import httpx
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = "https://api.openai.com/v1"


class OpenAIClient:
    """
    Client for OpenAI API with GPT-5 Nano support
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generate_response(
        self, prompt: str, model: str = "gpt-4o-mini", max_tokens: int = 500, store: bool = False
    ) -> str:
        """
        Generate response using GPT model

        Args:
            prompt: Input prompt
            model: Model to use (gpt-4o-mini, gpt-5-nano when available)
            max_tokens: Maximum response length
            store: Whether to store the response

        Returns:
            Generated text response
        """
        url = f"{OPENAI_BASE_URL}/chat/completions"

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        if store:
            payload["store"] = True

        try:
            # Use longer timeout for large batch requests (up to 5 minutes)
            timeout = httpx.Timeout(300.0, read=300.0)
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            print(f"Response: {e.response.text}")
            raise
        except Exception as e:
            print(f"Error generating response: {e}")
            raise

    def generate_embedding(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """
        Generate embedding vector for text

        Args:
            text: Input text to embed
            model: Embedding model (text-embedding-3-small, text-embedding-ada-002)

        Returns:
            Embedding vector (list of floats)
        """
        url = f"{OPENAI_BASE_URL}/embeddings"

        payload = {"model": model, "input": text}

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["data"][0]["embedding"]
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            print(f"Response: {e.response.text}")
            raise
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise

    def batch_generate_embeddings(self, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batched)

        Args:
            texts: List of input texts
            model: Embedding model

        Returns:
            List of embedding vectors
        """
        url = f"{OPENAI_BASE_URL}/embeddings"

        payload = {"model": model, "input": texts}

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()
                # Sort by index to ensure correct order
                embeddings = sorted(data["data"], key=lambda x: x["index"])
                return [item["embedding"] for item in embeddings]
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            print(f"Response: {e.response.text}")
            raise
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            raise

    # ========================================================================
    # PERSONA ENRICHMENT PROMPTS
    # ========================================================================

    def generate_persona_from_keyword(self, keyword: str, related_terms: List[str] = None) -> Dict:
        """
        Generate enriched persona profile from a keyword

        Args:
            keyword: Main topic/keyword
            related_terms: Related search terms

        Returns:
            Dict with persona details (name, summary, demographics, etc.)
        """
        related_str = ", ".join(related_terms) if related_terms else "N/A"

        prompt = f"""Generate a detailed persona profile for an audience interested in: {keyword}

Related terms: {related_str}

Provide a JSON response with:
{{
    "name": "Short persona name (e.g., 'Budget Fitness Enthusiasts 18-24')",
    "summary": "2-3 sentence description of this audience",
    "demographics": {{
        "age_range": "age range",
        "gender": "mixed/male/female/other",
        "income_level": "student/entry-level/middle/upper"
    }},
    "psychographics": {{
        "values": ["value1", "value2", "value3"],
        "lifestyle": "lifestyle description",
        "personality_traits": ["trait1", "trait2", "trait3"]
    }},
    "pain_points": ["pain point 1", "pain point 2", "pain point 3"],
    "motivations": ["motivation 1", "motivation 2", "motivation 3"]
}}

Only return valid JSON, no markdown formatting."""

        response = self.generate_response(prompt, max_tokens=800)

        # Clean up markdown formatting if present
        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join([line for line in lines if not line.startswith("```")])

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {response}")
            raise

    def generate_diverse_personas_batch(
        self, keyword: str, sample_posts: List[str], count: int = 10
    ) -> List[Dict]:
        """
        Generate multiple diverse personas for a single community/keyword

        Args:
            keyword: Main topic/keyword (e.g., "Fitness", "r/Fitness")
            sample_posts: Sample post titles for context
            count: Number of diverse personas to generate

        Returns:
            List of persona dicts
        """
        sample_str = "\n- ".join(sample_posts[:10]) if sample_posts else "N/A"

        prompt = f"""Generate {count} DIVERSE persona profiles for the community/topic: {keyword}

Sample posts from this community:
- {sample_str}

Create personas that represent DIFFERENT audience segments with varying:
- Age ranges (18-24, 25-34, 35-44, 45-54, 55+)
- Income levels (student, entry-level, middle, upper, premium)
- Experience levels (beginner, intermediate, advanced, expert)
- Goals and motivations
- Pain points and challenges

Provide a JSON array with {count} personas:
[
    {{
        "name": "Unique descriptive name (e.g., 'Budget-Conscious Beginners 18-24')",
        "summary": "2-3 sentence description",
        "demographics": {{
            "age_range": "specific range",
            "gender": "mixed/male/female/other",
            "income_level": "specific level"
        }},
        "psychographics": {{
            "values": ["value1", "value2", "value3"],
            "lifestyle": "lifestyle description",
            "personality_traits": ["trait1", "trait2", "trait3"]
        }},
        "pain_points": ["pain point 1", "pain point 2", "pain point 3"],
        "motivations": ["motivation 1", "motivation 2", "motivation 3"]
    }}
]

IMPORTANT: Make each persona DISTINCTLY DIFFERENT from others. Return only valid JSON array, no markdown."""

        # Adjust max_tokens based on count (more personas = more tokens needed)
        # Rough estimate: ~150 tokens per persona
        max_tokens = min(4000, count * 150 + 500)

        response = self.generate_response(prompt, max_tokens=max_tokens)

        # Clean up markdown
        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join([line for line in lines if not line.startswith("```")])

        try:
            personas = json.loads(response)
            # Ensure it's a list
            if isinstance(personas, dict):
                personas = [personas]
            return personas[:count]  # Limit to requested count
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {response}")
            raise

    def generate_interests_from_keyword(self, keyword: str, count: int = 3) -> List[Dict]:
        """
        Generate specific interests/products for a keyword

        Args:
            keyword: Main topic
            count: Number of interests to generate

        Returns:
            List of interest dicts with label, category, description
        """
        prompt = f"""Generate {count} specific product or topic interests for people interested in: {keyword}

Provide a JSON array with:
[
    {{
        "label": "Interest name",
        "category": "product/topic/service/activity",
        "description": "Brief description",
        "keywords": ["keyword1", "keyword2", "keyword3"]
    }}
]

Only return valid JSON array, no markdown."""

        response = self.generate_response(prompt, max_tokens=600)

        # Clean up markdown
        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join([line for line in lines if not line.startswith("```")])

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON: {response}")
            raise

    def generate_creative_prefs_from_keyword(self, keyword: str, count: int = 3) -> List[Dict]:
        """
        Generate creative ad preferences for a keyword-based audience

        Args:
            keyword: Main topic
            count: Number of preferences

        Returns:
            List of creative preference dicts
        """
        prompt = f"""Generate {count} ad creative preferences for an audience interested in: {keyword}

Focus on visual style, messaging tone, and format preferences.

Provide JSON array:
[
    {{
        "label": "Preference name (e.g., 'Minimalist Design', 'Motivational Tone')",
        "category": "visual_style/tone/format/messaging",
        "description": "Why this resonates with this audience",
        "examples": {{"characteristics": ["char1", "char2"]}}
    }}
]

Only return valid JSON array, no markdown."""

        response = self.generate_response(prompt, max_tokens=600)

        # Clean up
        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join([line for line in lines if not line.startswith("```")])

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON: {response}")
            raise

    # ========================================================================
    # COMMUNITY ENRICHMENT PROMPTS
    # ========================================================================

    def generate_community_summary(self, community_name: str, sample_posts: List[str] = None) -> Dict:
        """
        Generate enriched community profile

        Args:
            community_name: Subreddit name (e.g., 'r/Fitness')
            sample_posts: Optional sample post titles/content

        Returns:
            Dict with description, topics, audience type, tone
        """
        sample_str = "\n- ".join(sample_posts[:5]) if sample_posts else "N/A"

        prompt = f"""Analyze the community: {community_name}

Sample posts:
- {sample_str}

Provide JSON:
{{
    "description": "One sentence summary of this community",
    "topic_categories": ["topic1", "topic2", "topic3"],
    "audience_type": "Description of who participates here",
    "tone": "Overall tone/culture of the community",
    "activity_level": "high/medium/low"
}}

Only return valid JSON, no markdown."""

        response = self.generate_response(prompt, max_tokens=400)

        # Clean up
        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join([line for line in lines if not line.startswith("```")])

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON: {response}")
            raise


# Convenience instance
openai_client = OpenAIClient()
