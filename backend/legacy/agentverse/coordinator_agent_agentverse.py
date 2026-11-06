"""
Agentverse Coordinator Agent for AdVisor
Deploy this to Agentverse to coordinate with 932 persona agents on AWS

COPY THIS ENTIRE FILE TO AGENTVERSE
"""
from uagents import Agent, Context, Model
import requests
from typing import List, Dict, Any


# Message models
class AdAnalysisRequest(Model):
    ad_description: str
    num_personas: int = 10


class AdAnalysisResponse(Model):
    analyses: List[Dict[str, Any]]
    summary: str
    total_personas: int


# AWS FastAPI endpoint - your deployed API
AWS_API_URL = "http://52.53.159.105:8000"

# Create coordinator agent
coordinator = Agent(
    name="advisor_coordinator",
    seed="advisor_coordinator_seed_v1_production",
)


@coordinator.on_event("startup")
async def introduce(ctx: Context):
    ctx.logger.info(f"✓ Coordinator Agent Started")
    ctx.logger.info(f"✓ Agent Address: {coordinator.address}")
    ctx.logger.info(f"✓ Connected to AWS API: {AWS_API_URL}")
    ctx.logger.info(f"✓ Ready to coordinate 932 persona agents!")


@coordinator.on_message(model=AdAnalysisRequest)
async def handle_ad_analysis(ctx: Context, sender: str, msg: AdAnalysisRequest):
    """
    Handle ad analysis request from users/other agents
    Coordinates with 932 persona agents on AWS to get insights
    """
    ctx.logger.info(f"📨 Received ad analysis request from {sender}")
    ctx.logger.info(f"📝 Ad: {msg.ad_description}")
    ctx.logger.info(f"👥 Requesting {msg.num_personas} persona analyses...")

    try:
        # Call AWS FastAPI endpoint for multi-persona analysis
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

        # Generate summary from all analyses
        summary = generate_summary(analyses, msg.ad_description)

        ctx.logger.info(f"✅ Received {len(analyses)} persona analyses")
        ctx.logger.info(f"📊 Summary: {summary[:200]}...")

        # Send response back to requester
        await ctx.send(
            sender,
            AdAnalysisResponse(
                analyses=analyses,
                summary=summary,
                total_personas=len(analyses)
            )
        )

    except Exception as e:
        error_msg = f"Error analyzing ad: {str(e)}"
        ctx.logger.error(f"❌ {error_msg}")

        await ctx.send(
            sender,
            AdAnalysisResponse(
                analyses=[],
                summary=error_msg,
                total_personas=0
            )
        )


def generate_summary(analyses: List[Dict], ad_description: str) -> str:
    """
    Generate an executive summary from multiple persona analyses
    """
    if not analyses:
        return "No analyses received"

    total = len(analyses)

    # Count sentiment
    positive = 0
    negative = 0
    neutral = 0

    for a in analyses:
        analysis_text = a.get("analysis", "").lower()
        if "positive" in analysis_text[:200]:
            positive += 1
        elif "negative" in analysis_text[:200]:
            negative += 1
        else:
            neutral += 1

    # Calculate percentages
    pos_pct = (positive / total * 100) if total > 0 else 0
    neg_pct = (negative / total * 100) if total > 0 else 0
    neu_pct = (neutral / total * 100) if total > 0 else 0

    summary = f"""
═══════════════════════════════════════════════════════════════
AD ANALYSIS SUMMARY - ADVISOR
═══════════════════════════════════════════════════════════════

Ad: "{ad_description}"

Personas Analyzed: {total}

Sentiment Breakdown:
  • Positive:  {positive} personas ({pos_pct:.1f}%)
  • Negative:  {negative} personas ({neg_pct:.1f}%)
  • Neutral:   {neutral} personas ({neu_pct:.1f}%)

Top Persona Insights:
"""

    # Add top 3 persona insights
    for i, analysis in enumerate(analyses[:3], 1):
        name = analysis.get('persona_name', 'Unknown')
        summary_text = analysis.get('persona_summary', 'N/A')
        summary += f"\n{i}. {name}\n   {summary_text[:80]}...\n"

    summary += f"\n{'═' * 63}\n"
    summary += f"Powered by 932 AI Persona Agents | AWS + Fetch.ai ASI:One\n"
    summary += f"{'═' * 63}"

    return summary


if __name__ == "__main__":
    coordinator.run()
