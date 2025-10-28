"""
Test script to send an ad analysis request to the coordinator agent
"""
from uagents import Agent, Context, Model
from typing import List, Dict, Any
import asyncio

# Message Models (must match coordinator's models)
class AdAnalysisRequest(Model):
    ad_description: str
    num_personas: int = 10

class AdAnalysisResponse(Model):
    analyses: List[Dict[str, Any]]
    summary: str
    total_personas: int
    aws_endpoint: str

# Create a test client agent
test_client = Agent(
    name="test_client",
    seed="test_client_seed_12345",
    port=8002,
)

# Coordinator agent address (from the running agent)
COORDINATOR_ADDRESS = "agent1q0ck77ktk82hyvprjcp3zd3k3pckycgt4n99w40shjlks3k6xjzux6nnkw4"

@test_client.on_event("startup")
async def send_test_request(ctx: Context):
    """Send a test ad analysis request on startup"""
    ctx.logger.info(f"📤 Sending test ad analysis request to coordinator")

    # Send the request
    await ctx.send(
        COORDINATOR_ADDRESS,
        AdAnalysisRequest(
            ad_description="Nike running shoes ad featuring an athlete sprinting through a city at dawn. Tagline: 'Chase Your Best.'",
            num_personas=5
        )
    )
    ctx.logger.info(f"✅ Request sent! Waiting for response...")

@test_client.on_message(model=AdAnalysisResponse)
async def handle_response(ctx: Context, sender: str, msg: AdAnalysisResponse):
    """Handle the response from coordinator"""
    ctx.logger.info(f"📥 Received response from {sender}")
    ctx.logger.info(f"   Total personas analyzed: {msg.total_personas}")
    ctx.logger.info(f"   AWS endpoint: {msg.aws_endpoint}")
    ctx.logger.info(f"\n{msg.summary}")

    # Print first analysis as example
    if msg.analyses:
        first = msg.analyses[0]
        ctx.logger.info(f"\n📋 Example Analysis:")
        ctx.logger.info(f"   Persona: {first.get('persona_name', 'Unknown')}")
        ctx.logger.info(f"   Sentiment: {first.get('sentiment', 'Unknown')}")
        ctx.logger.info(f"   Reasoning: {first.get('reasoning', 'N/A')[:200]}...")

if __name__ == "__main__":
    print("🧪 Starting test client agent")
    print(f"📍 Client address: {test_client.address}")
    print(f"🎯 Will send request to coordinator: {COORDINATOR_ADDRESS}")
    test_client.run()
