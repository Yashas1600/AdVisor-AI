# Deploy AdVisor Coordinator to Agentverse (Web Interface)

## ✅ Current Status
- Your agent "SupaVisor" has been successfully registered to Agentverse
- Agent seed phrase: `advisor_coordinator_production_seed_phrase_v1_2025`
- Agentverse Key is configured in `.env`

## 📋 Step-by-Step Deployment

### 1. Go to Agentverse Dashboard
Navigate to: https://agentverse.ai/agents

### 2. Find Your Registered Agent
Look for your agent named **"SupaVisor"** or **"AdVisorCoordinator"** in the agent list

### 3. Click "Edit" or "Configure" on Your Agent

### 4. Paste the Agent Code
Copy and paste the code from `agentverse_coordinator_code.py` (below) into the Agentverse code editor:

```python
"""
AdVisor Coordinator Agent - Agentverse Hosted
Communicates with AWS EC2 API to analyze ads using 932 personas
"""
from uagents import Agent, Context, Model
import requests
from typing import List, Dict, Any

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
    name="SupaVisor",
    seed="advisor_coordinator_production_seed_phrase_v1_2025",
)

@coordinator.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"🚀 AdVisor Coordinator Agent started")
    ctx.logger.info(f"📡 AWS API URL: {AWS_API_URL}")
    ctx.logger.info(f"🤖 Agent address: {coordinator.address}")

@coordinator.on_message(model=AdAnalysisRequest)
async def handle_ad_analysis(ctx: Context, sender: str, msg: AdAnalysisRequest):
    """Handle ad analysis requests by forwarding to AWS API"""
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
        f"📊 Analysis Summary for: {ad_description[:100]}...",
        f"\nTotal Personas Analyzed: {total}",
        f"\nSentiment Breakdown:"
    ]

    for sentiment, count in sorted(sentiments.items(), key=lambda x: -x[1]):
        percentage = (count / total) * 100
        summary_parts.append(f"  • {sentiment.title()}: {count} ({percentage:.1f}%)")

    # Find most common themes
    all_reasons = []
    for analysis in analyses:
        if "reasoning" in analysis:
            all_reasons.append(analysis["reasoning"][:200])

    summary_parts.append(f"\nSample Insights:")
    for i, reason in enumerate(all_reasons[:3], 1):
        summary_parts.append(f"  {i}. {reason}...")

    return "\n".join(summary_parts)

if __name__ == "__main__":
    coordinator.run()
```

### 5. Deploy and Activate
- Click "Save & Run" or "Deploy"
- Wait for the agent to start (you'll see logs)
- The agent should show status as "Active" or "Running"

### 6. Get Your Agent Address
Once deployed, you'll see the agent address in the dashboard. It should look like:
```
agent1q...
```
Copy this address - you'll need it to send messages to your coordinator.

## 🧪 Testing Your Deployed Agent

### Option 1: Using Agentverse Inspector
1. Go to your agent's page on Agentverse
2. Click "Inspector" or "Test"
3. Send a test message with format:
```json
{
  "ad_description": "Nike running shoes ad featuring an athlete sprinting. Tagline: Chase Your Best.",
  "num_personas": 5
}
```

### Option 2: Using Python Client (from your laptop)
Create a file `test_agentverse_coordinator.py`:
```python
from uagents import Agent, Context, Model
from typing import List, Dict, Any

class AdAnalysisRequest(Model):
    ad_description: str
    num_personas: int = 10

class AdAnalysisResponse(Model):
    analyses: List[Dict[str, Any]]
    summary: str
    total_personas: int
    aws_endpoint: str

# Your coordinator's address from Agentverse dashboard
COORDINATOR_ADDRESS = "agent1q..."  # REPLACE WITH YOUR ACTUAL ADDRESS

test_client = Agent(name="test_client", seed="test_seed_123", port=8003)

@test_client.on_event("startup")
async def send_test(ctx: Context):
    await ctx.send(
        COORDINATOR_ADDRESS,
        AdAnalysisRequest(
            ad_description="Nike running shoes ad. Tagline: Chase Your Best.",
            num_personas=5
        )
    )

@test_client.on_message(model=AdAnalysisResponse)
async def handle_response(ctx: Context, sender: str, msg: AdAnalysisResponse):
    ctx.logger.info(f"✅ Got response!")
    ctx.logger.info(f"{msg.summary}")

if __name__ == "__main__":
    test_client.run()
```

## 🔍 Troubleshooting

### Agent Not Reachable
- Make sure your AWS instance (52.53.159.105:8000) is running
- Check security group allows outbound traffic from Agentverse IPs
- Verify the FastAPI server is responding: `curl http://52.53.159.105:8000/agents/personas`

### Timeout Errors
- Increase timeout in coordinator code (currently 90 seconds)
- Reduce `num_personas` in requests (try 5 instead of 10)

### Authentication Errors
- Verify AGENTVERSE_KEY is correct and not expired
- Check agent seed phrase matches registration

## 📊 Architecture
```
User/Client Agent
     ↓
Agentverse Coordinator (SupaVisor)
     ↓
AWS EC2 FastAPI (52.53.159.105:8000)
     ↓
932 Persona Agents
     ↓
Fetch.ai ASI:One API
```

## ✅ Next Steps
1. Deploy the coordinator to Agentverse (follow steps above)
2. Get the agent address from Agentverse dashboard
3. Test with a simple ad description
4. Integrate into your frontend application
