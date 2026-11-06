# AdVisor: Agentic Ad Analytics Platform

**Python, PostgreSQL, AWS, Google ADK, Cloud Run, BigQuery**

AdVisor is a full-stack platform that simulates 1,000 AI persona agents -- each representing a real audience segment distilled from Reddit community data -- to critique ad creatives from distinct perspectives. Upload an image or video ad, and AdVisor delivers 50+ concurrent persona insights in under 3 minutes, telling you exactly how different demographics would react.

## How It Works

1. **Upload** an ad creative (image or video) along with brand/industry context
2. **Feature extraction** runs multimodal analysis: Gemini vision for creative understanding, Moondream for caption/CTA extraction, OpenCV for color palettes and layout metrics, and for video ads, Gemini Files API produces a structured scene-by-scene timeline with hook analysis, on-screen text, transcript, and brand/CTA timing
3. **Smart persona selection** picks the 50 most relevant personas from the database: 40% matched by industry relevance (ranked by Gemini/GPT-4o-mini), 60% diverse age-matched perspectives for breadth
4. **Parallel persona critiques** fan out to all 50 personas concurrently through the Google ADK coordinator. Each persona receives the full feature vector and responds authentically based on their demographics, psychographics, pain points, and motivations. For video ads, personas also report the exact second they would stop watching and which moment stands out
5. **Aggregation** produces attention distribution (full/partial/ignore with percentages), per-persona insights, and for video ads, a skip-time heatmap. Results are saved to Supabase and logged to the analytics sink

## Architecture

```
                    Next.js Frontend (Vercel)
                            |
                            v
                    FastAPI Backend (Cloud Run or local)
                            |
            +---------------+---------------+
            |               |               |
   Feature Extraction   ADK Coordinator   Analytics Sink
   - Gemini vision      - Select personas  - BigQuery (prod)
   - Moondream           - Fan-out 50      - JSONL (local)
   - OpenCV/Tesseract      concurrent
   - Gemini Files API      critiques
     (video timeline)    - Aggregate
            |               |
            v               v
        Supabase (PostgreSQL + pgvector)
        - 1,000 personas with embeddings
        - 1,536-dim vectors (OpenAI)
        - <100ms similarity search
```

### Orchestration

The analysis pipeline supports two modes via the `ORCHESTRATOR` env var:

- **`adk`** (default) -- Google ADK coordinator using a custom `BaseAgent` that drives a deterministic pipeline: persona selection, parallel fan-out via `asyncio.gather` with a semaphore, then aggregation. The coordinator is not LLM-driven (no wasted tokens on routing decisions) but each persona critique is a real LLM call.
- **`legacy`** -- Same concurrent `asyncio.gather` pattern without the ADK wrapper, useful for environments where `google-adk` is not installed.

### LLM Providers

Swappable via `LLM_PROVIDER` env var:

| Provider | Model | Use case |
|----------|-------|----------|
| `gemini` (default) | gemini-2.5-flash | Persona critiques, image/video analysis, persona selection |
| `openai` | gpt-4o-mini | Alternative for critiques and selection |
| `asi` | asi1-mini (Fetch.ai) | Legacy path, kept for backwards compatibility |
| `mock` | n/a | Tests (canned responses, no network) |

All providers implement the same async interface (`generate_json`, `generate_text`, `analyze_image`, `analyze_video`), so switching is a single env var change.

## ETL Pipeline

The persona database was built from real Reddit community data:

```
Bright Data Reddit Scraping
  - 10,000+ posts across 1,577 communities
  - Keyword-based discovery (101 keywords) + URL-based extraction (1,508 posts)
        |
        v
Community Analysis
  - Extract top communities by activity and topic diversity
  - Keyword extraction with 180+ stopword filter
        |
        v
Persona Generation (GPT-4o-mini)
  - 50 diverse personas per community (varying age, income, goals)
  - 5 batches of 10 per community to avoid timeouts
  - Full demographic + psychographic profiles
        |
        v
Embedding Generation (OpenAI text-embedding-3-small)
  - 1,536-dimensional vectors per persona
        |
        v
Supabase + pgvector
  - IVFFlat indexing for <100ms similarity search
  - Row Level Security policies
```

## Video Ad Analysis

For video ads, Gemini produces a structured timeline via the Files API:

- **Scene breakdown** with timestamps, descriptions, and visual elements
- **Hook analysis** of the first 3-5 seconds
- **On-screen text** with timestamps
- **Voiceover transcript**
- **Brand and CTA first appearance** timestamps
- **Pacing** classification (fast/moderate/slow)

Each persona then reacts to the full timeline and reports:
- `attention`: full, partial, or ignore
- `insight`: one-sentence authentic reaction
- `skip_at_seconds`: the exact second they would stop watching (or null)
- `moment`: the key moment that stood out to them

The frontend renders a visual timeline with scene bars, brand/CTA markers, and persona skip-point overlays.

## Analytics

Every analysis run is logged to an analytics sink (`ANALYTICS_SINK` env var):

- **`jsonl`** (default) -- appends to `data/analytics/*.jsonl` locally
- **`bigquery`** -- streams to BigQuery tables (`ad_runs`, `persona_responses`, `ad_features`)
- **`none`** -- discard

Analytics never block the API response (fire-and-forget via `asyncio.ensure_future`).

Example queries in `docs/ANALYTICS.md` cover attention by community/age, cost per ad, most common video skip moments, and provider comparison.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, Tailwind CSS, d3.js (agent graph visualization) |
| Backend | FastAPI, Python 3.11+, uvicorn |
| Orchestration | Google ADK (custom BaseAgent with parallel fan-out) |
| LLM | Gemini 2.5 Flash (default), OpenAI GPT-4o-mini, Fetch.ai ASI:One |
| Video Understanding | Gemini Files API (upload, poll, structured timeline) |
| Image Analysis | Moondream (caption/CTA/keywords) + Gemini (visual understanding) |
| Computer Vision | OpenCV (color palette, layout), Tesseract (OCR) |
| Database | Supabase (PostgreSQL + pgvector, 1536-dim embeddings) |
| Analytics | BigQuery (production) / JSONL (local development) |
| Deployment | Cloud Run (primary), AWS EC2 (legacy), Vercel (frontend) |
| Testing | pytest, 52 tests, fully offline with mock provider |

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+

### Setup

```bash
# Clone
git clone https://github.com/Yashas1600/AdVisor-AI.git
cd AdVisor-AI

# Backend
cd backend
cp .env.example .env        # fill in: GEMINI_API_KEY, OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd ..
cp .env.example .env.local   # fill in: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_BACKEND_URL
npm install
npm run dev
```

### Run tests

```bash
make test
# 52 tests, fully offline, no API keys needed
```

### Environment variables

See `.env.example` (root) and `backend/.env.example` for the full list. Key ones:

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes (if using Gemini) | Google AI Studio API key |
| `OPENAI_API_KEY` | Yes | For embeddings and fallback provider |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase service role key |
| `LLM_PROVIDER` | No | `gemini` (default), `openai`, `asi`, `mock` |
| `ORCHESTRATOR` | No | `adk` (default), `legacy` |
| `ADVISOR_CONCURRENCY` | No | Max parallel persona calls, default 25 |
| `ANALYTICS_SINK` | No | `jsonl` (default), `bigquery`, `none` |

## API Reference

### POST `/api/analyze-ad-smart`

The primary endpoint. Accepts an ad's extracted features, selects relevant personas, runs parallel analysis, and returns aggregated results.

**Request:**
```json
{
  "feature_vector": {
    "moondream": {
      "summary": "Fitness app ad showing runner in urban setting",
      "caption": "Your next mile starts here",
      "cta": "Download free",
      "keywords": ["fitness", "running", "health"],
      "target_audience": "18-35 health-conscious adults"
    },
    "features": {
      "color": {"palette_hex": ["#FF5733", "#33FF57"], "colorfulness": 0.65},
      "layout": {"aspect_ratio": "16:9", "whitespace_ratio": 0.3}
    },
    "gemini_timeline": null
  },
  "target_age_range": "18-24",
  "industry_keywords": ["fitness", "health"],
  "num_personas": 50
}
```

**Response:**
```json
{
  "ad_id": "uuid",
  "selected_personas": [...],
  "analysis_results": {
    "persona-001": {
      "attention": "full",
      "insight": "This speaks directly to my goal of getting fit on a budget",
      "persona_name": "Budget-Conscious College Athlete"
    }
  },
  "summary": {
    "total_personas": 50,
    "attention": {"full": 28, "partial": 15, "ignore": 7},
    "attention_percentages": {"full": 56.0, "partial": 30.0, "ignore": 14.0},
    "latency_seconds": 12.4
  }
}
```

### Other endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/extract` | POST | Upload image/video, get multimodal features (Moondream + Gemini + OpenCV) |
| `/brandmeta` | POST | Generate brand metadata from ad context |
| `/agents/personas` | GET | List all personas with demographics |
| `/agents/chat` | POST | Chat with a specific persona |
| `/agents/analyze-ad` | POST | Single persona ad analysis |
| `/api/insights` | POST | Aggregate and summarize agent insights |
| `/health` | GET | Health check |

## Deployment

### Cloud Run (primary)

```bash
# Requires gcloud CLI authenticated + Yashas's approval for resource creation
./deploy/gcp/deploy.sh
```

Full guide: `docs/DEPLOY_GCP.md` (required APIs, IAM roles, Secret Manager setup, cost estimate, teardown).

### Vercel (frontend)

The Next.js frontend deploys to Vercel. Set `NEXT_PUBLIC_BACKEND_URL` to point at your Cloud Run service URL.

### Legacy: AWS EC2

The original deployment used EC2 with a Fetch.ai Agentverse coordinator. These files are preserved in `backend/legacy/agentverse/` with documentation at `backend/EC2_DEPLOYMENT.md`.

## Project Structure

```
AdVisor-AI/
  app/                              # Next.js 14 frontend
    components/AnalysisPanel.tsx     #   Video timeline + persona reactions UI
    dashboard/page.tsx               #   Main dashboard
    api/                             #   API route proxies to backend
  backend/
    main.py                          # FastAPI application entry point
    api/
      routes/analyze.py              #   Main analysis endpoint (ADK + legacy paths)
      smart_agent_selector.py        #   Persona selection (age + industry match)
      services/                      #   Feature extraction, brand meta, insights
    llm/                             # LLM provider abstraction layer
      interface.py                   #   Abstract base class
      gemini.py                      #   Gemini provider (default)
      openai_provider.py             #   OpenAI provider
      asi.py                         #   Fetch.ai ASI:One provider (legacy)
      mock.py                        #   Mock provider for tests
      router.py                      #   Provider factory
    orchestration/adk/               # Google ADK orchestration
      coordinator.py                 #   BaseAgent driving the pipeline
      persona_agent.py               #   Dynamic persona agent creation + fan-out
      tools.py                       #   ADK tools (select, aggregate, extract)
    extractor/                       # Feature extraction
      gemini_video.py                #   Video timeline via Gemini Files API
      gemini_image.py                #   Image analysis via Gemini
      pipeline/                      #   OpenCV + Tesseract features
    analytics/                       # Analytics sink
      sink.py                        #   BigQuery / JSONL / none
      schemas/                       #   BigQuery table schemas (JSON)
    legacy/agentverse/               # Original Fetch.ai coordinator (preserved)
    sql/                             # Supabase schema files
    db/                              # Database clients and persona manager
  tests/                             # 52 pytest tests (fully offline)
    test_analyze.py                  #   Endpoint contract, concurrency, timeouts
    test_adk.py                      #   ADK tools, fan-out, contract parity
    test_llm_providers.py            #   Provider interface and mock
    test_video.py                    #   Video timeline parsing, prompt integration
    fixtures/                        #   Recorded Gemini responses
  docs/
    BASELINE.md                      # Performance measurements and data counts
    DECISIONS.md                     # Architecture decisions + engagement dataset search
    DEPLOY_GCP.md                    # Cloud Run deployment guide
    ANALYTICS.md                     # BigQuery SQL query examples
  deploy/gcp/deploy.sh              # Cloud Run deploy script
  eval/NO_DATASET.md                # Engagement eval: no suitable dataset found
  Makefile                           # make test
```

## Key Numbers

| Metric | Value |
|--------|-------|
| Persona agents | ~1,000 (generated from Reddit data) |
| Source communities | 1,577 |
| Scraped posts | 10,000+ |
| Max concurrent persona analyses | 25 (configurable via `ADVISOR_CONCURRENCY`) |
| Per-persona timeout | 30s (configurable via `PERSONA_TIMEOUT`) |
| Vector dimensions | 1,536 (OpenAI text-embedding-3-small) |
| Similarity search latency | <100ms (pgvector IVFFlat) |
| Test suite | 52 tests, all offline, no API keys |
| Persona generation cost | ~$3.85 one-time (GPT-4o-mini + embeddings) |
| Per-ad analysis cost | ~$0.004 (Gemini) or ~$0.004 (GPT-4o-mini) |

## Documentation

| Document | Description |
|----------|-------------|
| `docs/BASELINE.md` | Measured performance numbers, before/after concurrency comparison |
| `docs/DECISIONS.md` | Architecture choices (ADK vs Fetch.ai, BaseAgent vs LlmAgent, fan-out design) + engagement dataset search (11 candidates evaluated) |
| `docs/DEPLOY_GCP.md` | Cloud Run deployment: prerequisites, APIs, IAM, secrets, cost, teardown |
| `docs/ANALYTICS.md` | 6 BigQuery SQL queries for analyzing persona response patterns |
| `eval/NO_DATASET.md` | Why no engagement evaluation exists yet (no public dataset with both ad creatives and real engagement metrics) |
