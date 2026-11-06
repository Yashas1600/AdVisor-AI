"""
AdVisor Coordinator Agent - Full Agentverse Deployment
This agent runs ON Agentverse and communicates with AWS API to analyze ads using 932 personas
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from uagents import Agent, Context, Model
import requests
from typing import List, Dict, Any

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

# Message Models
class AdAnalysisRequest(Model):
    """Request to analyze an ad with multiple personas"""
    ad_description: str
    num_personas: int = 10

class AdAnalysisResponse(Model):
    """Response with persona analyses and summary"""
    analyses: List[Dict[str, Any]]
    summary: str
    total_personas: int
    aws_endpoint: str

# AWS API Configuration
AWS_API_URL = "http://52.53.159.105:8000"

# Create the coordinator agent
coordinator = Agent(
    name="AdVisorCoordinator",
    seed="advisor_coordinator_production_seed_phrase_v1_2025",
    port=8001,  # Different from local dev
)

@coordinator.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"🚀 AdVisor Coordinator Agent started")
    ctx.logger.info(f"📡 AWS API URL: {AWS_API_URL}")
    ctx.logger.info(f"🤖 Agent address: {coordinator.address}")

@coordinator.on_message(model=AdAnalysisRequest)
async def handle_ad_analysis(ctx: Context, sender: str, msg: AdAnalysisRequest):
    """
    Handle ad analysis requests by forwarding to AWS API
    and returning aggregated results
    """
    ctx.logger.info(f"📥 Received ad analysis request from {sender}")
    ctx.logger.info(f"   Ad: {msg.ad_description[:100]}...")
    ctx.logger.info(f"   Requested personas: {msg.num_personas}")

    try:
        # Call AWS API for multi-persona analysis
        ctx.logger.info(f"🌐 Calling AWS API: {AWS_API_URL}/agents/analyze-ad-multi")
        response = requests.post(
            f"{AWS_API_URL}/agents/analyze-ad-multi",
            json={
                "ad_description": msg.ad_description,
                "num_personas": msg.num_personas
            },
            timeout=90
        )
        response.raise_for_status()
        analyses = response.json()

        ctx.logger.info(f"✅ Received {len(analyses)} persona analyses from AWS")

        # Generate summary
        summary = generate_summary(analyses, msg.ad_description)

        # Send response back to requester
        await ctx.send(
            sender,
            AdAnalysisResponse(
                analyses=analyses,
                summary=summary,
                total_personas=len(analyses),
                aws_endpoint=AWS_API_URL
            )
        )

        ctx.logger.info(f"📤 Sent analysis response to {sender}")

    except requests.exceptions.Timeout:
        ctx.logger.error(f"⏱️ Timeout calling AWS API")
        await ctx.send(
            sender,
            AdAnalysisResponse(
                analyses=[],
                summary="Error: Request timed out after 90 seconds",
                total_personas=0,
                aws_endpoint=AWS_API_URL
            )
        )
    except requests.exceptions.RequestException as e:
        ctx.logger.error(f"❌ Error calling AWS API: {str(e)}")
        await ctx.send(
            sender,
            AdAnalysisResponse(
                analyses=[],
                summary=f"Error: {str(e)}",
                total_personas=0,
                aws_endpoint=AWS_API_URL
            )
        )

def generate_summary(analyses: List[Dict[str, Any]], ad_description: str) -> str:
    """Generate a summary of all persona analyses"""
    if not analyses:
        return "No analyses received from personas."

    # Extract sentiments
    sentiments = {}
    for analysis in analyses:
        sentiment = analysis.get("sentiment", "neutral").lower()
        sentiments[sentiment] = sentiments.get(sentiment, 0) + 1

    # Build summary
    total = len(analyses)
    summary_parts = [
        f"📊 **Analysis Summary for:** {ad_description[:100]}...",
        f"\n**Total Personas Analyzed:** {total}",
        f"\n**Sentiment Breakdown:**"
    ]

    for sentiment, count in sorted(sentiments.items(), key=lambda x: -x[1]):
        percentage = (count / total) * 100
        summary_parts.append(f"  • {sentiment.title()}: {count} ({percentage:.1f}%)")

    # Find most common themes
    all_reasons = []
    for analysis in analyses:
        if "reasoning" in analysis:
            all_reasons.append(analysis["reasoning"][:200])

    summary_parts.append(f"\n**Sample Insights:**")
    for i, reason in enumerate(all_reasons[:3], 1):
        summary_parts.append(f"  {i}. {reason}...")

    return "\n".join(summary_parts)

if __name__ == "__main__":
    print(f"🚀 Starting AdVisor Coordinator Agent")
    print(f"📍 Agent Address: {coordinator.address}")
    print(f"📡 AWS API: {AWS_API_URL}")
    print(f"🔧 Make sure AWS instance is running at {AWS_API_URL}")
    coordinator.run()
