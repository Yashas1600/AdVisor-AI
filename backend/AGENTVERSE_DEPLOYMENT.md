# Deploy Coordinator Agent to Agentverse

## 🎯 What This Does

The Coordinator Agent runs on Agentverse and:
1. Receives ad analysis requests from users/other agents
2. Forwards requests to your AWS API (932 persona agents)
3. Returns aggregated insights and summaries

## 📋 Step-by-Step Deployment

### Step 1: Go to Agentverse

Visit: **https://agentverse.ai**

Login with your Fetch.ai account

### Step 2: Create New Agent

1. Click **"+ New Agent"** or **"My Agents"** → **"Create Agent"**
2. **Name**: `AdVisor Coordinator`
3. **Description**: `Coordinates ad analysis across 932 AI persona agents on AWS`

### Step 3: Copy Agent Code

Open the file: `backend/agents/coordinator_agent_agentverse.py`

**Copy the ENTIRE code** and paste it into the Agentverse code editor

### Step 4: Set Environment Variables (Optional)

In Agentverse agent settings, you can set:
- **AWS_API_URL**: `http://52.53.159.105:8000`

(Already hardcoded in the script, so this is optional)

### Step 5: Deploy Agent

1. Click **"Deploy"** or **"Save & Run"**
2. Wait for agent to start (should see green "Running" status)
3. **Copy the Agent Address** - it will look like:
   `agent1q0kgxswxak4gjskugms083v5nkycd5xnmqsr56x40xq2pz6y82nlxkhedhv`

### Step 6: Test the Agent

#### Option A: Use Agentverse UI

1. Go to **"Messages"** or **"Interact"** tab
2. Send a test message:

```json
{
  "ad_description": "New fitness tracking app with AI coaching",
  "num_personas": 5
}
```

#### Option B: Send Message from Another Agent

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

# Your agent
my_agent = Agent(name="my_test_agent", seed="my_seed_123")

COORDINATOR_ADDRESS = "agent1q0kg..."  # Use actual coordinator address

@my_agent.on_interval(period=60.0)
async def send_request(ctx: Context):
    ctx.logger.info("Sending ad analysis request to coordinator...")

    await ctx.send(
        COORDINATOR_ADDRESS,
        AdAnalysisRequest(
            ad_description="New eco-friendly water bottle for athletes",
            num_personas=10
        )
    )

@my_agent.on_message(model=AdAnalysisResponse)
async def handle_response(ctx: Context, sender: str, msg: AdAnalysisResponse):
    ctx.logger.info(f"Received analysis from {msg.total_personas} personas!")
    ctx.logger.info(f"Summary:\n{msg.summary}")

if __name__ == "__main__":
    my_agent.run()
```

## 🔍 How to Find Your Agent

After deployment, your agent will be discoverable on Agentverse:

1. **Agent Address**: `agent1q0kg...` (copy this!)
2. **Agentverse Dashboard**: https://agentverse.ai/agents
3. **Agent Inspector**: Available in Agentverse UI

## 📊 Expected Response Format

When you send an `AdAnalysisRequest`, you'll receive:

```python
AdAnalysisResponse(
    analyses=[
        {
            "persona_name": "Fitness Enthusiasts 18-24",
            "persona_summary": "Young adults focused on...",
            "demographics": {...},
            "analysis": "1. Initial reaction: Positive..."
        },
        # ... more personas
    ],
    summary="""
    ═══════════════════════════════════════════════════════
    AD ANALYSIS SUMMARY - ADVISOR
    ═══════════════════════════════════════════════════════

    Ad: "New fitness tracking app..."
    Personas Analyzed: 10

    Sentiment Breakdown:
      • Positive:  7 personas (70.0%)
      • Negative:  2 personas (20.0%)
      • Neutral:   1 personas (10.0%)

    Top Persona Insights:
    1. Fitness Enthusiasts 18-24
       Young adults focused on building muscle...
    ...
    """,
    total_personas=10
)
```

## 🛠️ Troubleshooting

### Agent Won't Start
- Check code has no syntax errors
- Verify all imports are correct
- Check Agentverse logs

### No Response from AWS
- Verify AWS API is running: `curl http://52.53.159.105:8000/`
- Check AWS Security Group allows outbound HTTPS from Agentverse IPs
- Increase timeout in code (currently 90 seconds)

### Timeout Errors
- Reduce `num_personas` in request (try 3-5 instead of 10)
- AWS API might be slow - check EC2 instance size
- Increase timeout in coordinator code

## 🎉 Success Indicators

✅ Agent shows "Running" status in Agentverse
✅ Startup logs show:
   - `✓ Coordinator Agent Started`
   - `✓ Connected to AWS API: http://52.53.159.105:8000`
   - `✓ Ready to coordinate 932 persona agents!`

✅ Test request returns valid AdAnalysisResponse
✅ Summary shows sentiment breakdown and insights

## 🔐 Security Notes

- AWS API is currently **public** (no authentication)
- Consider adding API key authentication later
- Monitor AWS costs (Fetch.ai API calls add up)

## 📈 Next Steps

After deployment:
1. Share your agent address with users
2. Build frontend to interact with coordinator
3. Monitor Agentverse logs for usage
4. Scale AWS instance if needed
5. Add rate limiting to prevent abuse

## 💰 Costs

- **Agentverse**: Free tier available
- **AWS EC2**: ~$30-40/month (t3.medium)
- **Fetch.ai ASI:One API**: Pay-per-use (~$0.001 per request)

## 🆘 Support

- Agentverse Docs: https://docs.fetch.ai/
- GitHub Issues: https://github.com/s21sharan/AdVisor/issues
- Your AWS API: http://52.53.159.105:8000/docs
