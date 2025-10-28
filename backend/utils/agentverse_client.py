"""
Agentverse Client for Fetch.ai
Handles registration and management of agents on Agentverse platform
"""
import os
import requests
import hashlib
from typing import Dict, Optional, Any, List
from dotenv import load_dotenv

load_dotenv()


class AgentverseClient:
    """Client for interacting with Fetch.ai Agentverse API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Agentverse client

        Args:
            api_key: Agentverse API key (defaults to AGENTVERSE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("AGENTVERSE_API_KEY")
        if not self.api_key:
            raise ValueError("AGENTVERSE_API_KEY not found in environment")

        self.base_url = "https://agentverse.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate_agent_address(self, persona_id: str, prefix: str = "agent") -> str:
        """
        Generate a unique agent address for a persona

        Args:
            persona_id: Unique persona identifier
            prefix: Address prefix (agent or test-agent)

        Returns:
            Agent address string
        """
        # Create a deterministic address based on persona_id
        hash_obj = hashlib.sha256(persona_id.encode())
        hash_hex = hash_obj.hexdigest()[:40]  # Take first 40 chars
        return f"{prefix}1{hash_hex}"

    def generate_challenge_response(self, address: str, challenge: str) -> str:
        """
        Generate challenge response for agent authentication

        Args:
            address: Agent address
            challenge: Challenge string from Agentverse

        Returns:
            Challenge response hash
        """
        # Combine address and challenge, then hash
        combined = f"{address}:{challenge}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def register_agent(
        self,
        address: str,
        challenge: str,
        challenge_response: str,
        agent_type: str = "custom",
        prefix: str = "agent",
        endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register an agent on Agentverse

        Args:
            address: Agent address identifier
            challenge: Security challenge value
            challenge_response: Response to the challenge
            agent_type: Type of agent (mailbox, proxy, or custom)
            prefix: Either 'agent' or 'test-agent'
            endpoint: Agent endpoint URL (optional)

        Returns:
            Response dict with 'success' boolean
        """
        url = f"{self.base_url}/agents"

        payload = {
            "address": address,
            "challenge": challenge,
            "challenge_response": challenge_response,
            "agent_type": agent_type,
            "prefix": prefix
        }

        if endpoint:
            payload["endpoint"] = endpoint

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Agentverse registration error: {str(e)}")

    def register_persona_agent(
        self,
        persona_id: str,
        persona_name: str,
        endpoint_url: Optional[str] = None,
        agent_type: str = "custom"
    ) -> Dict[str, Any]:
        """
        Register a persona agent on Agentverse

        Args:
            persona_id: Unique persona identifier
            persona_name: Name of the persona
            endpoint_url: Optional webhook endpoint for the agent
            agent_type: Type of agent (default: custom)

        Returns:
            Registration result with agent address and success status
        """
        # Generate agent address
        address = self.generate_agent_address(persona_id)

        # Generate challenge (in production, this would come from Agentverse)
        # For now, using persona_id as challenge
        challenge = hashlib.sha256(persona_id.encode()).hexdigest()

        # Generate challenge response
        challenge_response = self.generate_challenge_response(address, challenge)

        # Register agent
        result = self.register_agent(
            address=address,
            challenge=challenge,
            challenge_response=challenge_response,
            agent_type=agent_type,
            endpoint=endpoint_url
        )

        return {
            "persona_id": persona_id,
            "persona_name": persona_name,
            "agent_address": address,
            "success": result.get("success", False),
            "registration_result": result
        }

    def batch_register_personas(
        self,
        personas: List[Dict[str, str]],
        base_endpoint: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Register multiple persona agents in batch

        Args:
            personas: List of dicts with 'id' and 'name' keys
            base_endpoint: Base URL for agent endpoints (optional)

        Returns:
            List of registration results
        """
        results = []

        for persona in personas:
            persona_id = persona.get("id")
            persona_name = persona.get("name", "Unknown")

            # Generate endpoint URL if base provided
            endpoint = None
            if base_endpoint:
                endpoint = f"{base_endpoint}/agents/persona/{persona_id}"

            try:
                result = self.register_persona_agent(
                    persona_id=persona_id,
                    persona_name=persona_name,
                    endpoint_url=endpoint
                )
                results.append(result)
                print(f"✓ Registered: {persona_name} ({persona_id[:8]}...)")
            except Exception as e:
                print(f"✗ Failed: {persona_name} - {str(e)}")
                results.append({
                    "persona_id": persona_id,
                    "persona_name": persona_name,
                    "success": False,
                    "error": str(e)
                })

        return results


# Convenience functions
def create_client() -> AgentverseClient:
    """Create an Agentverse client instance"""
    return AgentverseClient()


def register_persona(persona_id: str, persona_name: str, endpoint: Optional[str] = None) -> Dict[str, Any]:
    """Register a single persona agent"""
    client = create_client()
    return client.register_persona_agent(persona_id, persona_name, endpoint)
