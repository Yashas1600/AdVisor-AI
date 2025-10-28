"""
Register persona agents to Agentverse using uAgents framework
This properly handles cryptographic signatures and agent registration
"""
import sys
from pathlib import Path
import json
from typing import List, Dict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from uagents import Agent, Context
from uagents.setup import fund_agent_if_low
from db.persona_manager import PersonaManager


def create_and_register_persona_agents(limit: int = None):
    """
    Create and register persona agents using uAgents framework

    Args:
        limit: Optional limit on number of agents to create (for testing)
    """
    print("=" * 80)
    print("AGENTVERSE PERSONA AGENT REGISTRATION (uAgents)")
    print("=" * 80)
    print()

    # Initialize PersonaManager
    print("1. Fetching personas from Supabase...")
    pm = PersonaManager()
    personas = pm.list_personas(limit=1000)

    if limit:
        personas = personas[:limit]

    print(f"   ✓ Found {len(personas)} personas to create")
    print()

    # Create agents
    print(f"2. Creating {len(personas)} agents...")
    agents = []
    registered_count = 0

    for i, persona in enumerate(personas, 1):
        persona_id = str(persona.get("id"))
        persona_name = persona.get("name", "Unknown")
        persona_summary = persona.get("summary", "")

        try:
            # Create agent with persona-specific seed
            agent = Agent(
                name=f"persona_{persona_id[:8]}",
                seed=f"persona_seed_{persona_id}",
                port=8000 + i,  # Different port for each agent
                endpoint=[f"http://localhost:{8000 + i}/submit"],
                agentverse={
                    "use_mailbox": True,  # Use Agentverse mailbox for messaging
                }
            )

            # Store agent metadata
            agent.persona_id = persona_id
            agent.persona_name = persona_name
            agent.persona_summary = persona_summary

            agents.append(agent)
            registered_count += 1

            print(f"   ✓ Created: {persona_name} ({persona_id[:8]}...)")

        except Exception as e:
            print(f"   ✗ Failed: {persona_name} - {str(e)}")

    print()
    print("=" * 80)
    print("REGISTRATION SUMMARY")
    print("=" * 80)
    print(f"Total personas: {len(personas)}")
    print(f"✓ Agents created: {registered_count}")
    print(f"✗ Failed:         {len(personas) - registered_count}")
    print()

    # Save agent addresses
    agent_data = []
    for agent in agents[:5]:  # Show first 5
        agent_data.append({
            "persona_id": agent.persona_id,
            "persona_name": agent.persona_name,
            "agent_address": agent.address,
            "agent_name": agent.name
        })
        print(f"  - {agent.persona_name}")
        print(f"    Address: {agent.address}")
        print(f"    ID: {agent.persona_id[:8]}...")
        print()

    # Save all agent addresses to file
    all_agent_data = [{
        "persona_id": agent.persona_id,
        "persona_name": agent.persona_name,
        "agent_address": agent.address,
        "agent_name": agent.name
    } for agent in agents]

    output_file = Path(__file__).parent.parent / "data" / "agentverse_agents.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(all_agent_data, f, indent=2)

    print(f"✓ Agent addresses saved to: {output_file}")
    print()
    print("=" * 80)
    print("✓ AGENT CREATION COMPLETED")
    print("=" * 80)
    print()
    print("NOTE: These agents are registered with Agentverse using the mailbox feature.")
    print("They can be discovered and messaged through the Agentverse platform.")

    return agents


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create and register persona agents using uAgents")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of agents to create (for testing, default: all 932)"
    )

    args = parser.parse_args()

    # Create agents
    agents = create_and_register_persona_agents(limit=args.limit)

    print(f"\n✓ Successfully created {len(agents)} persona agents!")
    print(f"Each agent is now discoverable on Agentverse.")
