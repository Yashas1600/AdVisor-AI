# SupaVisor - Agentverse Coordinator Agent

> Intelligent coordinator orchestrating multi-persona ad analysis across 932 distributed agents

## 🎯 Overview

SupaVisor is a cloud-hosted coordinator agent on Fetch.ai's Agentverse platform. It acts as intelligent middleware between user applications and 932 persona agents hosted on AWS EC2, orchestrating ad analysis requests, aggregating responses, and extracting key insights.

## 📍 Deployment Information

- **Agent Name**: @supavisor
- **Agent Address**: `agent1qw8kzfh7gfv63ravqmclx9uzkxwa6mkqycty7nfctuzqlmcuz0wfzzy8lpl`
- **Platform**: Fetch.ai Agentverse (cloud-hosted)
- **Status**: ✅ Live and operational
- **Upstream API**: http://52.53.159.105:8000 (AWS EC2 - 932 persona agents)

## 🏗️ Architecture

```
User Application
     ↓
SupaVisor (Agentverse)
  • Receives requests
  • Validates parameters
  • Forwards to AWS
     ↓
AWS EC2 API
  • Executes 932 persona agents
  • Powered by Fetch.ai ASI:One
     ↓
SupaVisor
  • Aggregates responses
  • Extracts sentiment breakdown
  • Generates summary
     ↓
User Application
  • Display insights dashboard
```

## 🔧 Core Functions

1. **Request Orchestration** - Receives `AdAnalysisRequest`, validates parameters, forwards to AWS
2. **Multi-Persona Coordination** - Triggers parallel execution of 1-932 personas (90s timeout)
3. **Response Aggregation** - Collects individual analyses with sentiment, reasoning, and insights
4. **Insight Extraction** - Calculates sentiment breakdown (% positive/neutral/negative), extracts top insights
5. **Error Handling** - Timeout management, network recovery, structured error responses

## 📡 Message Protocol

### Input: AdAnalysisRequest
```python
class AdAnalysisRequest(Model):
    ad_description: str      # Ad creative to analyze
    num_personas: int = 10   # 1-932 personas
```

### Output: AdAnalysisResponse
```python
class AdAnalysisResponse(Model):
    analyses: List[Dict[str, Any]]  # Individual persona analyses
    summary: str                     # Aggregated summary
    total_personas: int              # Count
    aws_endpoint: str                # AWS API used
```

**Example Response**:
```python
{
    "analyses": [
        {
            "persona_name": "Fitness-Focused Millennials 25-34",
            "sentiment": "positive",
            "reasoning": "This ad speaks to my morning routine goals..."
        }
    ],
    "summary": "📊 Summary: Nike ad...\nTotal: 10\nPositive: 7 (70%)\nNeutral: 2 (20%)\nNegative: 1 (10%)",
    "total_personas": 10
}
```

## 📊 Performance

| Metric | Value |
|--------|-------|
| Platform | Fetch.ai Agentverse |
| Uptime | 24/7 |
| Timeout | 90 seconds |
| Max Personas | 932 |
| Response Time | 3-8s (10 personas) |
| Parallel Execution | Yes |

## 🛠️ Technical Stack

- **Framework**: uAgents (Fetch.ai)
- **HTTP Client**: Python `requests`
- **Models**: Pydantic-based
- **Deployment**: Agentverse cloud
- **Upstream**: FastAPI (AWS EC2)

## 🔐 Security

- **Public Agent**: Discoverable on Agentverse
- **No Auth Required**: Open for integration
- **Rate Limiting**: Managed by Agentverse

## 🐛 Troubleshooting

**Timeout Errors**: Reduce `num_personas` (try <50) or increase timeout

**Empty Responses**: Check AWS health: `curl http://52.53.159.105:8000/agents/personas`

**Agent Not Responding**: Verify Agentverse dashboard shows agent as active

## 📈 Monitoring

**Agentverse Logs**:
- `📥 Request from {sender}` - Incoming
- `✅ Sent {count} analyses` - Success
- `❌ Error: {msg}` - Failures

**Test Connectivity**:
```python
await ctx.send(
    "agent1qw8kzfh7gfv63ravqmclx9uzkxwa6mkqycty7nfctuzqlmcuz0wfzzy8lpl",
    AdAnalysisRequest(ad_description="Test", num_personas=1)
)
```

---

**SupaVisor** - Bridging applications with 932 data-driven persona agents for authentic ad feedback.
