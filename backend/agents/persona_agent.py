"""
Persona Agent System for AdVisor
Creates AI agents for each persona that can retrieve and reason about information
Uses Supabase (PostgreSQL + pgvector) for all data operations
Uses Fetch.ai ASI:One (asi1-mini) for agent reasoning
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
import json

sys.path.append(str(Path(__file__).parent.parent))

from db.persona_manager import PersonaManager
from utils.fetchai_client import FetchAIClient
from utils.openai_client import OpenAIClient  # Still needed for embeddings


class PersonaAgent:
    """
    AI Agent representing a specific persona
    Can retrieve information and provide insights based on persona characteristics
    Uses Supabase for data storage and pgvector for similarity search
    """

    def __init__(self, persona_id: str):
        self.pm = PersonaManager()
        self.fetchai = FetchAIClient(model="asi1-mini")
        self.openai = OpenAIClient()  # Keep for embeddings only
        self.persona_id = persona_id
        self.persona_data = None
        self._load_persona()

    def _load_persona(self):
        """Load persona data from Supabase"""
        try:
            persona = self.pm.get_persona(self.persona_id)
            if not persona:
                raise ValueError(f"Persona {self.persona_id} not found")
            self.persona_data = persona
        except Exception as e:
            raise ValueError(f"Failed to load persona {self.persona_id}: {e}")

    def get_context(self) -> str:
        """
        Generate context string for the agent based on persona characteristics

        Returns:
            Formatted context string describing the persona
        """
        if not self.persona_data:
            return ""

        demographics = self.persona_data.get("demographics", {})
        psychographics = self.persona_data.get("psychographics", {})

        context = f"""You are {self.persona_data.get('name', 'Unknown')}, a persona representing:

Summary: {self.persona_data.get('summary', 'N/A')}

Demographics:
- Age Range: {demographics.get('age_range', 'Unknown')}
- Gender: {demographics.get('gender', 'Unknown')}
- Income Level: {demographics.get('income_level', 'Unknown')}
- Education: {demographics.get('education', 'Unknown')}
- Occupation: {demographics.get('occupation', 'Unknown')}
- Location: {demographics.get('location', 'Unknown')}

Psychographics:
- Values: {', '.join(psychographics.get('values', []))}
- Interests: {', '.join(psychographics.get('interests', []))}
- Lifestyle: {psychographics.get('lifestyle', 'Unknown')}
- Personality Traits: {', '.join(psychographics.get('personality_traits', []))}

Pain Points:
{self._format_list(self.persona_data.get('pain_points', []))}

Motivations:
{self._format_list(self.persona_data.get('motivations', []))}

Preferred Channels:
{self._format_list(self.persona_data.get('preferred_channels', []))}

As this persona, you should:
1. Think and respond from this persona's perspective
2. Consider your pain points and motivations in your responses
3. Provide authentic insights based on your demographics and psychographics
4. Reference your preferred communication channels when relevant
"""
        return context

    def _format_list(self, items: List[str]) -> str:
        """Format a list of items as bullet points"""
        if not items:
            return "- None specified"
        return "\n".join([f"- {item}" for item in items])

    def retrieve_relevant_content(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant content using Supabase vector similarity search

        Args:
            query: The query string
            k: Number of results to return

        Returns:
            List of relevant items (communities, content, interests)
        """
        # Generate embedding for the query
        query_embedding = self.openai.generate_embedding(query)

        results = []

        # Search communities using pgvector
        communities = self.pm.search_communities_by_embedding(query_embedding, limit=3)
        for community in communities:
            results.append({
                "type": "community",
                "name": community.get("name"),
                "description": community.get("description"),
                "similarity": community.get("similarity_score", 0)
            })

        # Search content
        content_items = self.pm.search_content_by_embedding(query_embedding, limit=k)
        for content in content_items:
            results.append({
                "type": "content",
                "title": content.get("title"),
                "body": content.get("body"),
                "similarity": content.get("similarity_score", 0)
            })

        return results[:k]

    def chat(self, user_message: str, include_retrieval: bool = True) -> Dict[str, Any]:
        """
        Chat with the persona agent

        Args:
            user_message: The user's message/query
            include_retrieval: Whether to retrieve relevant context

        Returns:
            Response dictionary with persona's reply and retrieved context
        """
        context = self.get_context()

        retrieved_items = []
        retrieved_context = ""

        if include_retrieval:
            retrieved_items = self.retrieve_relevant_content(user_message, k=3)
            if retrieved_items:
                retrieved_context = "\n\nRelevant Information Retrieved:\n"
                for item in retrieved_items:
                    if item["type"] == "community":
                        retrieved_context += f"\nCommunity: {item['name']}\n"
                        retrieved_context += f"Description: {item['description']}\n"
                    elif item["type"] == "content":
                        retrieved_context += f"\nContent: {item['title']}\n"
                        retrieved_context += f"Body: {item['body'][:200]}...\n"

        user_prompt = f"""User Query: {user_message}

Please respond as this persona, incorporating the retrieved information if relevant.
Your response should reflect your demographics, psychographics, pain points, and motivations.
"""

        if retrieved_context:
            user_prompt = f"""{retrieved_context}

{user_prompt}"""

        # Use Fetch.ai ASI:One with system prompt for persona embodiment
        response = self.fetchai.generate_response(
            prompt=user_prompt,
            system_prompt=context,
            max_tokens=500
        )

        return {
            "persona_name": self.persona_data.get("name"),
            "persona_summary": self.persona_data.get("summary"),
            "response": response,
            "retrieved_context": retrieved_items
        }

    def analyze_ad_creative(self, ad_description: str) -> Dict[str, Any]:
        """
        Analyze an ad creative from this persona's perspective

        Args:
            ad_description: Description of the ad creative

        Returns:
            Analysis dictionary with persona's feedback
        """
        context = self.get_context()

        prompt = f"""You are being shown an advertisement: {ad_description}

As this persona, please provide:
1. Your initial reaction (positive, neutral, or negative)
2. What elements resonate with you and why (consider your pain points and motivations)
3. What elements don't work and why
4. Suggestions for improvement based on your preferences and values
5. On a scale of 1-10, how likely are you to engage with this ad

Be specific and authentic to your persona characteristics.
"""

        # Use Fetch.ai ASI:One with system prompt for persona embodiment
        response = self.fetchai.generate_response(
            prompt=prompt,
            system_prompt=context,
            max_tokens=700
        )

        return {
            "persona_name": self.persona_data.get("name"),
            "persona_summary": self.persona_data.get("summary"),
            "demographics": self.persona_data.get("demographics", {}),
            "analysis": response
        }

    def retrieve_similar_personas(self, k: int = 5) -> List[Dict[str, Any]]:
        """
        Find personas similar to this one using vector embeddings

        Args:
            k: Number of similar personas to return

        Returns:
            List of similar personas with similarity scores
        """
        if not self.persona_data.get("embedding"):
            return []

        embedding = self.persona_data["embedding"]
        similar = self.pm.search_personas_by_embedding(embedding, limit=k + 1)

        # Filter out self and return
        results = []
        for persona in similar:
            if persona.get("id") != self.persona_id:
                results.append({
                    "persona_id": persona.get("id"),
                    "name": persona.get("name"),
                    "summary": persona.get("summary"),
                    "similarity_score": persona.get("similarity_score", 0)
                })

        return results[:k]


class PersonaAgentManager:
    """
    Manager for multiple persona agents
    Provides utilities for multi-persona analysis and batch operations
    """

    def __init__(self):
        self.pm = PersonaManager()
        self.agents = {}  # Cache for loaded agents

    def list_available_personas(self) -> List[Dict[str, str]]:
        """
        List all available personas

        Returns:
            List of persona summaries (id, name, summary)
        """
        personas = self.pm.list_personas()
        return [
            {
                "id": str(p.get("id")) if p.get("id") else "",
                "name": p.get("name") or "Unknown",
                "summary": p.get("summary") or ""
            }
            for p in personas
            if p.get("id")  # Only include personas with valid IDs
        ]

    def get_agent(self, persona_id: str) -> PersonaAgent:
        """
        Get or create a persona agent (with caching)

        Args:
            persona_id: ID of the persona

        Returns:
            PersonaAgent instance
        """
        if persona_id not in self.agents:
            self.agents[persona_id] = PersonaAgent(persona_id)
        return self.agents[persona_id]

    def multi_persona_analysis(
        self,
        ad_description: str,
        persona_ids: Optional[List[str]] = None,
        num_personas: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get feedback from multiple personas on an ad

        Args:
            ad_description: Description of the ad creative
            persona_ids: Optional list of specific persona IDs to use
            num_personas: Number of random personas if persona_ids not provided

        Returns:
            List of analyses from different personas
        """
        if persona_ids is None:
            available = self.list_available_personas()
            if len(available) == 0:
                return []

            import random
            selected = random.sample(available, min(num_personas, len(available)))
            persona_ids = [p["id"] for p in selected]

        analyses = []
        for persona_id in persona_ids:
            try:
                agent = self.get_agent(persona_id)
                analysis = agent.analyze_ad_creative(ad_description)
                analyses.append(analysis)
            except Exception as e:
                print(f"Error analyzing with persona {persona_id}: {e}")
                continue

        return analyses


# Demo usage
if __name__ == "__main__":
    print("=" * 80)
    print("PERSONA AGENT DEMO (Supabase-Only Architecture)")
    print("=" * 80)
    print()

    # Initialize manager
    manager = PersonaAgentManager()

    # List available personas
    print("1. Listing available personas...")
    personas = manager.list_available_personas()
    print(f"   Found {len(personas)} personas\n")

    if len(personas) > 0:
        # Show first 5
        for i, persona in enumerate(personas[:5], 1):
            print(f"   {i}. {persona['name']}")
            print(f"      {persona['summary'][:80]}...\n")

        # Test chat with first persona
        print("\n2. Testing chat with first persona...")
        agent = manager.get_agent(personas[0]["id"])
        chat_result = agent.chat(
            "What do you think about productivity apps?",
            include_retrieval=True
        )

        print(f"   Persona: {chat_result['persona_name']}")
        print(f"   Response: {chat_result['response'][:200]}...\n")
        print(f"   Retrieved {len(chat_result['retrieved_context'])} context items\n")

        # Test ad analysis
        print("\n3. Testing ad analysis...")
        analysis = agent.analyze_ad_creative(
            "A new productivity app for remote workers with AI-powered task prioritization"
        )

        print(f"   Persona: {analysis['persona_name']}")
        print(f"   Analysis: {analysis['analysis'][:300]}...\n")

        # Test multi-persona analysis
        print("\n4. Testing multi-persona analysis...")
        multi_analysis = manager.multi_persona_analysis(
            ad_description="Email marketing platform: 'Professional email marketing made simple'",
            num_personas=3
        )

        print(f"   Got {len(multi_analysis)} persona analyses\n")
        for i, analysis in enumerate(multi_analysis, 1):
            print(f"   {i}. {analysis['persona_name']}")
            print(f"      {analysis['analysis'][:150]}...\n")

    print("\n" + "=" * 80)
    print("✓ DEMO COMPLETED")
    print("=" * 80)
