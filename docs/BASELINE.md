# Baseline Measurements

Measured from commit ed7b50b on `main`, before the Google upgrade work.

## Data counts

| Metric | Measured | Resume claim |
|--------|----------|--------------|
| Personas in Supabase | [TBD - run `SELECT count(*) FROM personas`] | 1,000 |
| Scraped posts (data files, not in repo) | ~10,043 across keywords.json + subreddits.json per CLAUDE.md | 10K+ |
| Unique communities | ~1,577 per CLAUDE.md (21 represented in persona DB) | 1,577 |

The persona count in the README says 932; the resume says 1,000. Actual count needs a live Supabase query.

## Sequential analysis latency (before concurrency fix)

The analysis loop in `backend/api/routes/analyze.py` (commit ed7b50b) ran persona LLM calls **sequentially** with a `time.sleep(0.2)` between each call.

| Parameter | Value |
|-----------|-------|
| Personas per run | 50 (default) |
| Model | gpt-4o-mini |
| Max tokens per call | 200 |
| Rate-limit sleep | 0.2 s between calls |
| Estimated wall time (50 personas) | ~60-90 s (0.2 s sleep + ~1-1.5 s API round trip each) |
| Concurrency | 1 (sequential) |

[TBD: actual timed run once backend is up with keys]

## After concurrency fix

Replaced the sequential loop with `asyncio.gather` + `AsyncOpenAI` + semaphore.

| Parameter | Value |
|-----------|-------|
| Concurrency (ADVISOR_CONCURRENCY) | 25 (default, configurable) |
| Per-persona timeout (PERSONA_TIMEOUT) | 30 s |
| Retries | none (fail with fallback "partial") |
| Result ordering | stable (sorted by original index) |
| Estimated wall time (50 personas) | [TBD - measure after running] |
| Speedup vs sequential | [TBD] |

## Tokens and cost per ad (50 personas)

| Item | Estimate |
|------|----------|
| System prompt tokens (per persona) | ~150 |
| User prompt tokens (per persona) | ~120 |
| Output tokens (per persona) | ~50 |
| Total tokens per ad (50 personas) | ~16,000 |
| GPT-4o-mini cost per ad | ~$0.003 (input $0.15/1M, output $0.60/1M) |
| Persona selection (1 call) | ~$0.001 |
| Total cost per ad | ~$0.004 |

## Hygiene issues fixed in Milestone 1

- Removed committed log files: `uagents_core.log`, `backend/agentverse_registration.log`
- Removed committed PDF: `cal hacks 25.pdf`
- Removed Supabase anon JWT from `VERCEL_DEPLOYMENT.md` (was in git history -- Yashas should consider rotating it)
- Removed hardcoded EC2 IP from `VERCEL_DEPLOYMENT.md`
- Fixed hardcoded `http://localhost:8000` in `app/api/extract/route.ts` and `app/api/brandmeta/route.ts` to use `NEXT_PUBLIC_BACKEND_URL`
- Added `.env.example` for both frontend and backend
- Cleaned up duplicate entries in `.gitignore`, added `*.log` pattern
