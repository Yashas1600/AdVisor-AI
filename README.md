# AdVisor: Agentic Ad Analytics Platform

Full-stack platform simulating 1,000 AI persona agents that critique ads from distinct audience perspectives, delivering 50+ concurrent agent insights per ad.

## Architecture

```
Next.js Frontend (Vercel)
     |
     v
FastAPI Backend (Cloud Run or local)
     |
     +-- Google ADK Coordinator (default orchestrator)
     |      |
     |      +-- Smart Persona Selector (Gemini / GPT-4o-mini)
     |      +-- Parallel Persona Critiques (50+ concurrent, semaphore-controlled)
     |      +-- Result Aggregation
     |
     +-- Gemini Video Understanding (Files API + structured timeline)
     +-- Feature Extraction (Moondream + OpenCV/Tesseract + Gemini)
     +-- Analytics Sink (BigQuery or JSONL)
     |
     v
Supabase (PostgreSQL + pgvector, 1536-dim OpenAI embeddings)
```

### Orchestration modes

Set `ORCHESTRATOR` env var:
- `adk` (default) -- Google ADK coordinator with parallel fan-out
- `legacy` -- concurrent asyncio.gather with configurable LLM provider

### LLM providers

Set `LLM_PROVIDER` env var:
- `gemini` (default) -- google-genai SDK with structured output
- `openai` -- GPT-4o-mini with JSON mode
- `asi` -- Fetch.ai ASI:One (asi1-mini, legacy)
- `mock` -- canned responses for tests

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, Tailwind, d3 |
| Backend | FastAPI, Python 3.11+ |
| Orchestration | Google ADK (BaseAgent, parallel fan-out) |
| LLM | Gemini (default), OpenAI, Fetch.ai ASI:One |
| Video | Gemini Files API (structured timeline extraction) |
| Image | Moondream + Gemini image analysis |
| Features | OpenCV, Tesseract OCR |
| Database | Supabase (PostgreSQL + pgvector) |
| Embeddings | OpenAI text-embedding-3-small (1536-dim) |
| Analytics | BigQuery (prod) / JSONL (local) |
| Deploy | Cloud Run (primary), EC2 (legacy), Vercel (frontend) |
| Tests | pytest (52 tests, offline, no keys needed) |

## Data Pipeline

```
Bright Data Reddit Scraping (10K+ posts, 1,577 communities)
     |
     v
GPT-4o-mini persona generation (50 per community)
     |
     v
OpenAI embeddings (1536 dimensions)
     |
     v
Supabase + pgvector storage
     |
     v
[TBD] persona count in DB (target: 1,000)
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+

### Setup

```bash
# Backend
cd backend
cp .env.example .env   # fill in keys
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cp .env.example .env.local   # fill in keys
npm install
npm run dev
```

See `.env.example` files for required variables.

### Run tests

```bash
make test
# Runs 52 tests offline with no API keys needed
```

## API

### Main endpoint

**POST** `/api/analyze-ad-smart`

```json
{
  "feature_vector": {
    "moondream": {"summary": "...", "caption": "...", "cta": "...", "keywords": []},
    "features": {"color": {...}, "layout": {...}},
    "gemini_timeline": null
  },
  "target_age_range": "18-24",
  "industry_keywords": ["fitness"],
  "num_personas": 50
}
```

Returns persona-level insights with attention levels (full/partial/ignore), aggregated summary, and for video ads: skip timestamps and key moments.

### Other endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/extract` | POST | Extract features from ad creative (image/video upload) |
| `/brandmeta` | POST | Generate brand metadata |
| `/agents/personas` | GET | List all personas |
| `/agents/chat` | POST | Chat with a persona |
| `/api/insights` | POST | Summarize agent insights |
| `/health` | GET | Health check |

## Deployment

### Cloud Run (primary)

See `docs/DEPLOY_GCP.md`. Requires Yashas's approval before creating GCP resources.

```bash
# After approval:
./deploy/gcp/deploy.sh
```

### Legacy: EC2

See `backend/EC2_DEPLOYMENT.md`. The Fetch.ai/Agentverse coordinator files are in `backend/legacy/agentverse/`.

## Project Structure

```
AdVisor-AI/
  app/                          # Next.js frontend
  backend/
    api/routes/                 # FastAPI endpoints
    api/smart_agent_selector.py # Persona selection (age + industry match)
    llm/                        # Provider abstraction (gemini, openai, asi, mock)
    orchestration/adk/          # ADK coordinator + persona fan-out
    extractor/                  # Gemini video/image, OpenCV pipeline
    analytics/                  # BigQuery/JSONL sink
    legacy/agentverse/          # Original Fetch.ai coordinator (preserved)
    sql/                        # Supabase schema files
  tests/                        # 52 pytest tests (offline)
  docs/
    BASELINE.md                 # Measured performance numbers
    DECISIONS.md                # Architecture decisions + dataset search
    DEPLOY_GCP.md               # Cloud Run deployment guide
    ANALYTICS.md                # BigQuery SQL queries
  deploy/gcp/                   # Cloud Run deploy script
  eval/                         # Engagement evaluation (no dataset found)
  Makefile                      # make test
```

## Key Numbers

| Metric | Value |
|--------|-------|
| Personas | [TBD -- run SELECT count(*) FROM personas] |
| Source communities | 1,577 |
| Scraped posts | 10,000+ |
| Concurrent persona analyses | 25 (configurable via ADVISOR_CONCURRENCY) |
| Latency (50 personas, concurrent) | [TBD -- measure with live run] |
| Vector dimensions | 1,536 |
| Similarity search | <100ms (pgvector IVFFlat) |
| Test suite | 52 tests, all offline |

## Docs

- `docs/BASELINE.md` -- performance measurements
- `docs/DECISIONS.md` -- architecture choices, engagement dataset search (11 candidates evaluated)
- `docs/DEPLOY_GCP.md` -- Cloud Run deployment
- `docs/ANALYTICS.md` -- BigQuery query examples
- `eval/NO_DATASET.md` -- why no engagement eval exists yet
