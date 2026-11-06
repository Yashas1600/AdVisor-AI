"""
AdVisor Coordinator Agent - Copy this entire file to Agentverse
"""
from uagents import Agent, Context, Model
import requests
from typing import List, Dict, Any

class AdAnalysisRequest(Model):
    ad_description: str
    num_personas: int = 10

class AdAnalysisResponse(Model):
    analyses: List[Dict[str, Any]]
    summary: str
    total_personas: int
    aws_endpoint: str

AWS_API_URL = "http://52.53.159.105:8000"

coordinator = Agent(
    name="SupaVisor",
    seed="advisor_coordinator_production_seed_phrase_v1_2025",
)

@coordinator.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"🚀 AdVisor Coordinator started")
    ctx.logger.info(f"📡 AWS: {AWS_API_URL}")

@coordinator.on_message(model=AdAnalysisRequest)
async def handle_ad_analysis(ctx: Context, sender: str, msg: AdAnalysisRequest):
    ctx.logger.info(f"📥 Request from {sender}: {msg.ad_description[:50]}...")

    try:
        response = requests.post(
            f"{AWS_API_URL}/agents/analyze-ad-multi",
            json={"ad_description": msg.ad_description, "num_personas": msg.num_personas},
            timeout=90
        )
        response.raise_for_status()
        analyses = response.json()

        summary = generate_summary(analyses, msg.ad_description)

        await ctx.send(sender, AdAnalysisResponse(
            analyses=analyses,
            summary=summary,
            total_personas=len(analyses),
            aws_endpoint=AWS_API_URL
        ))

        ctx.logger.info(f"✅ Sent {len(analyses)} analyses to {sender}")

    except Exception as e:
        ctx.logger.error(f"❌ Error: {str(e)}")
        await ctx.send(sender, AdAnalysisResponse(
            analyses=[], summary=f"Error: {str(e)}",
            total_personas=0, aws_endpoint=AWS_API_URL
        ))

def generate_summary(analyses: List[Dict[str, Any]], ad_description: str) -> str:
    if not analyses:
        return "No analyses received."

    sentiments = {}
    for analysis in analyses:
        sentiment = analysis.get("sentiment", "neutral").lower()
        sentiments[sentiment] = sentiments.get(sentiment, 0) + 1

    total = len(analyses)
    summary_parts = [
        f"📊 Summary: {ad_description[:100]}",
        f"Total: {total} personas",
        "Sentiments:"
    ]

    for sentiment, count in sorted(sentiments.items(), key=lambda x: -x[1]):
        pct = (count / total) * 100
        summary_parts.append(f"  • {sentiment.title()}: {count} ({pct:.1f}%)")

    return "\n".join(summary_parts)

if __name__ == "__main__":
    coordinator.run()
