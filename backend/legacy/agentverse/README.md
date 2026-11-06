# Legacy Fetch.ai / Agentverse Coordinator Files

These files are the **original** Fetch.ai-based coordinator agents that were
used to orchestrate persona analysis through the Agentverse platform and AWS
EC2. They have been superseded by the ADK-based orchestration in
`backend/orchestration/adk/`.

## Files

| File | Purpose |
|------|---------|
| `coordinator_agent.py` | FastAPI-based coordinator that called the EC2-hosted persona agents |
| `coordinator_agent_agentverse.py` | Production-ready coordinator for Agentverse deployment with mailbox |
| `agentverse_coordinator_full.py` | Full Agentverse coordinator with protocol definitions |
| `COPY_THIS_TO_AGENTVERSE.py` | Paste-ready code for Agentverse web editor |
| `deploy_to_agentverse.py` | Script to register agents on Agentverse via uAgents SDK |

## Why they were replaced

The ADK orchestration provides:
- Parallel fan-out of persona analyses (vs sequential loop)
- No dependency on external EC2 instance or Agentverse platform
- Structured session/state management through ADK's BaseAgent model
- Simpler deployment -- single process, no inter-service HTTP calls

These files are kept for reference only.
