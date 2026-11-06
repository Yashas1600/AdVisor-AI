"""
Agentverse Coordinator Agent
This agent runs on Agentverse and coordinates with 932 persona agents on AWS
"""
import os
import requests
from typing import List, Dict, Any
from uagents import Agent, Context, Model
from dotenv import load_dotenv

load_dotenv()


# Message models
class AdAnalysisRequest(Model):
    ad_description: str
    num_personas: int = 10


class AdAnalysisResponse(Model):
    analyses: List[Dict[str, Any]]
    summary: str


# Create coordinator agent
coordinator = Agent(
    name="advisor_coordinator",
    seed="advisor_coordinator_seed_v1",
    port=8001,
    endpoint=["http://localhost:8001/submit"],
    agentverse={
        "use_mailbox": True,
    }
)

# AWS FastAPI endpoint
AWS_API_URL = os.getenv("AWS_API_URL", "http://52.53.159.105:8000")


@coordinator.on_event("startup")
async def introduce(ctx: Context):
    ctx.logger.info(f"Coordinator Agent Address: {coordinator.address}")
    ctx.logger.info(f"Connected to AWS API: {AWS_API_URL}")
    ctx.logger.info("Ready to analyze ads with 932 persona agents!")


@coordinator.on_message(model=AdAnalysisRequest)
async def handle_ad_analysis(ctx: Context, sender: str, msg: AdAnalysisRequest):
    """
    Handle ad analysis request from users/other agents
    Coordinates with 932 persona agents on AWS to get insights
    """
    ctx.logger.info(f"Received ad analysis request from {sender}")
    ctx.logger.info(f"Ad: {msg.ad_description}")
    ctx.logger.info(f"Requesting {msg.num_personas} persona analyses...")

    try:
        # Call AWS FastAPI endpoint for multi-persona analysis
        response = requests.post(
            f"{AWS_API_URL}/agents/analyze-ad-multi",
            json={
                "ad_description": msg.ad_description,
                "num_personas": msg.num_personas
            },
            timeout=60
        )
        response.raise_for_status()

        analyses = response.json()

        # Generate summary from all analyses
        summary = generate_summary(analyses)

        ctx.logger.info(f"✓ Received {len(analyses)} persona analyses")

        # Send response back to requester
        await ctx.send(
            sender,
            AdAnalysisResponse(
                analyses=analyses,
                summary=summary
            )
        )

    except Exception as e:
        ctx.logger.error(f"Error analyzing ad: {str(e)}")
        await ctx.send(
            sender,
            AdAnalysisResponse(
                analyses=[],
                summary=f"Error: {str(e)}"
            )
        )


def generate_summary(analyses: List[Dict]) -> str:
    """
    Generate an executive summary from multiple persona analyses
    """
    if not analyses:
        return "No analyses received"

    total = len(analyses)

    # Extract key insights
    positive_count = sum(1 for a in analyses if "positive" in a.get("analysis", "").lower())
    negative_count = sum(1 for a in analyses if "negative" in a.get("analysis", "").lower())

    summary = f"""
AD ANALYSIS SUMMARY
===================
Total Personas Analyzed: {total}

Sentiment Breakdown:
- Positive Reactions: {positive_count} ({positive_count/total*100:.1f}%)
- Negative Reactions: {negative_count} ({negative_count/total*100:.1f}%)
- Neutral: {total - positive_count - negative_count} ({(total - positive_count - negative_count)/total*100:.1f}%)

Top Personas Analyzed:
"""

    for i, analysis in enumerate(analyses[:5], 1):
        summary += f"\n{i}. {analysis.get('persona_name', 'Unknown')}"
        summary += f"\n   Summary: {analysis.get('persona_summary', 'N/A')[:100]}..."

    return summary


if __name__ == "__main__":
    print("=" * 80)
    print("ADVISOR COORDINATOR AGENT")
    print("=" * 80)
    print(f"Agent Address: {coordinator.address}")
    print(f"AWS API URL: {AWS_API_URL}")
    print()
    print("This agent coordinates ad analysis across 932 persona agents on AWS.")
    print("Send an AdAnalysisRequest message to this agent to analyze an ad.")
    print()
    print("Starting agent...")
    print("=" * 80)

    coordinator.run()
