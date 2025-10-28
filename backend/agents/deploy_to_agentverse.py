"""
Deploy AdVisor Coordinator Agent to Agentverse
This script registers the coordinator agent with Agentverse using the official registration API
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from uagents_core.utils.registration import (
    register_chat_agent,
    RegistrationRequestCredentials,
)

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

print(f"🔧 Loading .env from: {env_path}")
print(f"✓ AGENTVERSE_KEY found: {os.environ.get('AGENTVERSE_KEY', 'NOT FOUND')[:50]}...")
print(f"✓ AGENT_SEED_PHRASE: {os.environ.get('AGENT_SEED_PHRASE', 'NOT FOUND')}")

# Register the AdVisor coordinator agent
register_chat_agent(
    "AdVisorCoordinator",  # Agent name on Agentverse
    "https://agentverse.ai",
    active=True,
    credentials=RegistrationRequestCredentials(
        agentverse_api_key=os.environ["AGENTVERSE_KEY"],
        agent_seed_phrase=os.environ["AGENT_SEED_PHRASE"],
    ),
)

print("✅ AdVisor Coordinator Agent successfully registered to Agentverse!")
print("Next steps:")
print("1. Check Agentverse dashboard for your agent status")
print("2. Note down the agent address")
print("3. Test sending AdAnalysisRequest messages to the agent")
