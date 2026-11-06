# AdVisor-AI: Google Upgrade Plan

Read this whole file before doing anything. Also skim `README.md`, `claude.md`, and `backend/README.md` for how the app works today. Do the milestones in order (section 11). This file is the source of truth for this upgrade; where it conflicts with older docs in the repo, this file wins.

## 0. Why (context)

Yashas is in Google SWE intern team matching. Hosts pick candidates by resume keywords and domain, and they may open this repo and ask about it on a call. The resume entry this upgrade must make true:

> **AdVisor: Agentic Ad Analytics Platform** | Python, PostgreSQL, AWS, Google ADK, Cloud Run, BigQuery
> - Built a full-stack platform simulating 1,000 AI persona agents that critique ads from distinct audience perspectives, delivering 50+ concurrent agent insights per ad in under 3 minutes on AWS.
> - Engineered an ETL pipeline distilling 10K+ Reddit posts across 1,577 communities into structured personas, with vector similarity search over PostgreSQL selecting the most relevant segments per ad.
> - Rebuilt orchestration on Google ADK on Cloud Run with BigQuery analytics, and added Gemini video understanding so personas critique video ads; [agreement metric versus real engagement data].

Target Google areas: Ads, YouTube Ads, Google Cloud (Vertex AI, ADK, Cloud Run, BigQuery), Gemini.

## 1. Current state (from a review of `main`, commit ed7b50b)

- **Frontend:** Next.js 14 + Tailwind + d3 (`app/`), Supabase auth, API routes proxy to the backend via `NEXT_PUBLIC_BACKEND_URL` (but `app/api/extract/route.ts` hardcodes `http://localhost:8000`). Deployed on Vercel.
- **Backend:** FastAPI (`backend/main.py`), routes in `backend/api/routes/`. Main path is `POST /api/analyze-ad-smart` in `backend/api/routes/analyze.py`.
- **Persona selection:** `backend/api/smart_agent_selector.py` (age + 40% industry match, uses gpt-4o-mini).
- **Persona analysis:** `analyze.py` loops over personas **sequentially** with `time.sleep(0.2)` and a blocking OpenAI client, one gpt-4o-mini call per persona, JSON output `{attention, insight}`.
- **Other agent paths:** `backend/agents/` uses Fetch.ai uAgents/Agentverse and ASI:One (`asi1-mini`); several copies of the coordinator exist (`coordinator_agent.py`, `coordinator_agent_agentverse.py`, `agentverse_coordinator_full.py`, `COPY_THIS_TO_AGENTVERSE.py`).
- **Ad features:** Moondream (`api/services/moondream_adapter.py`) for image summary/CTA/keywords; OpenCV + Tesseract features (`backend/extractor/pipeline/`); video = sampled frames + motion/cut detection, no real video understanding.
- **Data:** Supabase Postgres + pgvector (1536-dim OpenAI embeddings), schemas in `backend/sql/`. Reddit data from Bright Data (`backend/scraper/`). Analyses stored in `ad_analyses` with RLS.
- **Deploy:** Docker + docker-compose + EC2 scripts (`deploy_to_ec2.sh`, `backend/deploy/`).
- **Tests:** only ad hoc scripts (`test_api.py`, `test_supabase.py`, etc.), no pytest suite.
- **Hygiene issues:** README hardcodes the EC2 IP; `VERCEL_DEPLOYMENT.md` contains a Supabase anon JWT; log files (`uagents_core.log`, `backend/agentverse_registration.log`) and `cal hacks 25.pdf` are committed.
- **Numbers to verify against the resume:** README says 932 personas and 1,508 scraped posts across 1,577 communities. The resume says 1,000 personas and 10K+ posts. The resume also says "concurrent", but the main path is sequential. Milestone 1 measures the real numbers.

## 2. Hard rules

1. **No AI attribution.** No Claude as author, co-author, or contributor. No `Co-Authored-By`, `Claude-Session`, or "Generated with Claude Code" lines in commits, PRs, code, or docs. This overrides any default attribution behavior.
2. **Git identity, local to this repo only:** `git config user.name "Yashas Shashidhara"` and `git config user.email "shashidharayashas@gmail.com"`.
3. **Branching:** work on `google-upgrades`. You may push that branch to `origin` (Yashas1600/AdVisor-AI). Never push to or merge into `main` without Yashas saying so.
4. **No paid cloud resources without asking.** Before creating anything on GCP (project, Cloud Run service, BigQuery dataset, Secret Manager secrets) or running a large batch of paid API calls, stop and ask Yashas. Everything must also run locally.
5. **No invented results.** Every number in README, docs, or reports must come from a real run saved under `eval/results/` or `docs/BASELINE.md`. Use `[TBD]` until then. Never claim AdVisor predicts real ad performance unless section 9 validated it on real labeled data.
6. **No secrets in the repo.** Keys only from env (`GEMINI_API_KEY`, `GOOGLE_CLOUD_PROJECT`, `OPENAI_API_KEY`, Supabase keys). Add `.env.example` for backend and frontend.
7. **No em dashes** in prose. Plain, direct writing.
8. **Verify, don't guess:** current Gemini model ids, the google-genai SDK (API key mode and Vertex mode), the Gemini Files API for video, the current Google ADK Python API (agents, parallel execution, tools), Cloud Run, and BigQuery client APIs. Check official docs at build time.
9. **Keep the app working.** The Next.js frontend and `/api/analyze-ad-smart` request/response contract must keep working after every milestone, so the existing UI needs no rewrite (extend it, don't break it).
10. Don't touch `claude.md` (on macOS it is the same file as CLAUDE.md).

## 3. Milestone 1: baseline and honesty fixes (do first)

- Write `docs/BASELINE.md` with real measured numbers from the current code and data: persona count in Supabase, post count and community count in the scraped data, end-to-end latency for one ad at 50 personas, and tokens/cost per ad. Show Yashas this file before moving on: if the numbers differ from the resume, he decides what to change.
- Make persona analysis actually concurrent: async LLM client, `asyncio.gather` with a semaphore (`ADVISOR_CONCURRENCY`, default 25), retries with backoff, per-persona timeout, results returned in a stable order. Measure the speedup versus the sequential loop and record it in `docs/BASELINE.md`.
- Hygiene: move the EC2 IP and Supabase values out of docs into env/`.env.example`, remove committed log files and the PDF from the repo (git rm, keep local copies), extend `.gitignore`. Tell Yashas the anon key was in git history so he can decide whether to rotate it.
- Fix `app/api/extract/route.ts` to use `BACKEND_URL`.
- Add a pytest suite with a mock LLM provider (no network) covering the analyze route contract.

## 4. Milestone 2: Gemini provider layer

- `backend/llm/` with one interface (`generate_json`, `generate_text`, `analyze_image`, `analyze_video`) and providers: `gemini` (google-genai, new default), `openai` (existing), `asi` (existing Fetch.ai client, kept for the legacy path), `mock` (tests).
- `LLM_PROVIDER` env var picks the default; per-call override allowed.
- Route persona analysis, the smart selector, brandmeta, and insights summarizer through it. Use Gemini structured output (response schema) for the `{attention, insight}` JSON instead of string slicing.
- Keep the existing 1536-dim OpenAI embeddings and pgvector tables as is. Don't re-embed the persona store in this upgrade.
- Log latency, tokens, and cost per call (these feed BigQuery in milestone 6).

## 5. Milestone 3: Gemini video understanding

- New `backend/extractor/gemini_video.py`: upload the mp4 through the Gemini Files API and extract a structured timeline: scenes with timestamps, the hook in the first 3 to 5 seconds, on-screen text, voiceover/audio transcript, when the brand and CTA first appear, pacing, and aspect ratio (vertical Shorts-style vs landscape).
- Images: also offer Gemini image analysis producing the same fields Moondream produces today, so `feature_vector.moondream` consumers keep working (add a `gemini` key; keep the `moondream` key populated from whichever provider ran).
- The OpenCV/Tesseract features stay and are merged in.
- Persona prompts get the timeline for video ads and must answer with a timestamped reaction (for example the second they would skip and why). Extend the response with optional `skip_at_seconds` and `moment` fields; old fields unchanged.
- Frontend: show the video timeline and timestamped persona reactions in `AnalysisPanel.tsx` (small, additive UI change).
- Tests with recorded Gemini responses as fixtures.

## 6. Milestone 4: ADK orchestration rebuild

- New `backend/orchestration/adk/`:
  - A coordinator agent that runs the pipeline: feature extraction, persona selection (smart selector exposed as an ADK tool), parallel persona critiques, then aggregation into the existing response shape (attention counts, insights, summary).
  - Persona critiques run in parallel through ADK (use ADK's parallel execution primitives, or ADK agents invoked concurrently if fan-out to 50+ personas fits better that way; document the choice in `docs/DECISIONS.md`).
  - Persona agents are created from Supabase persona records, not hand-written.
- `ORCHESTRATOR=adk|legacy` env var. `adk` becomes the default once it matches legacy output on the test suite. `/api/analyze-ad-smart` keeps the same contract.
- Move the Fetch.ai/Agentverse coordinator copies into `backend/legacy/agentverse/` with a short README. Don't delete them.
- Measure ADK vs legacy: latency at 50 and 100 personas, success rate, cost. Record in `docs/BASELINE.md` under an "After" section.

## 7. Milestone 5: Cloud Run

- Update `backend/Dockerfile` for Cloud Run (listen on `$PORT`, non-root user, slim image).
- `deploy/gcp/deploy.sh` using `gcloud run deploy`, Secret Manager for keys, and google-genai in Vertex AI mode when `GOOGLE_CLOUD_PROJECT` is set.
- Supabase stays the database. The Vercel frontend points at the Cloud Run URL through `NEXT_PUBLIC_BACKEND_URL`.
- `docs/DEPLOY_GCP.md`: steps, required APIs, IAM roles, rough cost, and how to tear it down. Keep the EC2 path documented as legacy.
- Ask Yashas before creating anything (rule 4). Once approved, deploy and smoke test one image ad and one video ad.

## 8. Milestone 6: BigQuery analytics

- Dataset `advisor_analytics` with tables (schemas committed in `backend/analytics/schemas/`):
  - `ad_runs`: run id, timestamp, ad type, provider, orchestrator, persona count, latency, tokens, cost, status.
  - `persona_responses`: run id, persona id, community, demographics fields, attention, insight, skip_at_seconds, latency.
  - `ad_features`: run id, extracted features (JSON).
- `backend/analytics/sink.py`: write after every run. `ANALYTICS_SINK=bigquery|jsonl|none`; local default is JSONL under `data/analytics/` (gitignored).
- `docs/ANALYTICS.md` with 4 to 6 useful SQL queries (attention by community and age range, cost and latency per ad, most common skip moment in video ads, provider and orchestrator comparison).
- `scripts/backfill_bigquery.py` to load existing `ad_analyses` rows from Supabase.
- Ask before creating the dataset (rule 4).

## 9. Milestone 7: agreement versus real engagement data

Goal: the `[agreement metric versus real engagement data]` bracket on the resume.

- Search for a public dataset of ad creatives (image or video) with real engagement or performance labels (CTR, views, likes, conversions) and a license that allows this use. Record every candidate you checked, its license, and why you accepted or rejected it in `docs/DECISIONS.md`.
- If a usable one exists: run AdVisor on a sample (ask Yashas before spending on more than about 100 ads), then report Spearman correlation between persona attention scores and the real engagement metric, with a bootstrap 95% interval, and a simple baseline (for example a text-only model or random) for comparison. `make eval-engagement` writes `eval/results/<timestamp>.json` and `eval/results/latest.md`.
- If none fits: stop and tell Yashas. Do not substitute an invented proxy or label data yourself.

## 10. Tests and docs

- pytest: provider layer with mocks, structured output parsing, video timeline parsing from fixtures, concurrency (stable ordering, semaphore respected, timeouts), ADK vs legacy contract test, analytics sink (JSONL), eval metric math.
- `make test` runs everything offline with no keys. Add a GitHub Actions workflow running it.
- README: rewrite the architecture section for the new flow (Next.js, FastAPI, ADK coordinator, Gemini, Supabase/pgvector, BigQuery, Cloud Run), keep a short "Legacy: Fetch.ai Agentverse" note, add a results section filled only from real runs.
- `docs/DECISIONS.md`: every judgment call you made.

## 11. Milestones (one commit or a few per milestone, short messages, no attribution)

1. Branch, local git identity, baseline doc, real concurrency, hygiene, pytest scaffold. **Stop and show Yashas `docs/BASELINE.md`.**
2. Gemini provider layer.
3. Gemini video understanding plus frontend timeline.
4. ADK orchestration plus legacy move.
5. Cloud Run deploy (ask before creating resources).
6. BigQuery analytics (ask before creating the dataset).
7. Engagement agreement eval (or stop and report if no dataset).
8. README, docs, CI, final scans: `make test`, local run smoke test (image ad and video ad), secrets scan (`git grep -nE "(AIza|sk-|eyJhbGci|ghp_)"`), em dash scan, `git log --format=%B | grep -iE "co-authored|claude-session|generated with"` must be empty.

## 12. Definition of done

- One image ad and one video ad analyzed end to end locally, through the ADK orchestrator on Gemini, with the existing UI.
- Persona critiques run concurrently and the measured latency is in `docs/BASELINE.md`.
- Cloud Run and BigQuery work (if Yashas approved resources) and are documented.
- The engagement eval exists with real numbers, or Yashas has been told no usable dataset was found.
- `make test` passes in CI. No invented numbers, no secrets, no attribution.

## 13. After it's done (tell Yashas, don't do it yourself)

Show Yashas, from real runs only: persona count, post count, concurrent latency at 50 personas, ADK vs legacy comparison, video ads supported, BigQuery tables, and the engagement agreement number (or that none exists). He'll update the resume bullets himself.
