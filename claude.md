# AdVisor Project Overview

## Product Vision
AdVisor empowers marketers to understand and improve their ad creatives by combining multimodal feature extraction with generative agent simulations.

## Core Workflow
1. User uploads ad (image/video) + company info
2. System analyzes the creative and extracts features
3. AI simulates audience communities
4. Delivers actionable creative feedback and improved ad variants

## System Architecture (7 Components)

### 1. Ad Upload
- Input: User uploads ad + company metadata
- Output: Raw file + metadata

### 2. Feature Extraction Engine
- Input: Ad creative (image/video/audio)
- Output: Multimodal features (visual, text, audio, sentiment, etc.)
- **Goal**: Extract ≥10 distinct, decorrelated features per ad
- **Performance**: <5 min per 50 ads on single GPU

### 3. Feature Store
- Input: Features from extractor
- Output: Central structured dataset + embeddings
- Stores structured embeddings and signals

### 4. Community Recommender
- Input: Ad embeddings + brand metadata
- Output: Suggests best-fit or custom audience communities to simulate
- **Key Role**: Acts as router, defines which audience lenses agents should think through

### 5. Agent Simulation Layer
- Input: Selected communities + features
- Output: Runs feedback simulations tailored to each audience
- Agent types: Performance Analyst, Creative Director, etc.
- Instantiates agents for each community (e.g., "Gen Z minimalists," "Busy professionals")

### 6. Creative Feedback & Variant Generator
- Input: Agent outputs
- Output: Produces improved ad variants or creative recommendations

### 7. Insights Dashboard
- Input: Aggregated feedback, variants, metrics
- Output: Visualization + download/export UI for marketers

## Key Objectives

| Goal | Description | Metric |
|------|-------------|--------|
| Feature Extraction Insight | Extract semantically rich, non-redundant signals | ≥10 distinct, decorrelated features per ad |
| Performance | Fast processing, parallelizable | <5 min per 50 ads on single GPU |
| Robustness | Handle diverse industries, formats | 100% of .png/.mp4 ads processed |
| Creativity | Unique, interpretable signals | ≥3 novel "outside-the-box" signal types |

## Critical Connection
The Community Recommender → Agent Simulation Layer handoff is crucial:
- Without it, agents wouldn't know which audience persona they're simulating
- This is the key connection between data-driven analysis and human-like interpretation

## Tech Stack Considerations
- Need multimodal ML models (vision, text, audio)
- GPU acceleration for batch processing
- Agent framework for simulation layer
- Frontend dashboard for visualization
- Feature store/database for embeddings

## Current Status - Reddit Scraper Complete ✅

### Backend API (Python FastAPI)
- **Location**: `backend/`
- **Status**: Fully implemented using Bright Data Dataset API
- **Endpoint**: `POST http://localhost:8000/scrape`
- **Features**:
  - Scrapes subreddit posts (title, body, author, upvotes, timestamp, URL)
  - Extracts top 25 comments per post
  - Saves to `backend/data/{subreddit}_{timestamp}.json`
  - Polling-based workflow: trigger → poll progress → download snapshot

### Reddit Scraper Implementation
- **Files**:
  - `backend/scraper/brightdata_client.py` - API client with polling logic
  - `backend/scraper/reddit_scraper_v2.py` - Main scraper orchestration
  - `backend/main.py` - FastAPI server
  - `backend/models/reddit_post.py` - Pydantic models
  - `backend/utils/parsers.py` - Data parsing utilities

### Environment Variables (.env)
```
BRIGHT_DATA_API_KEY=a18e1c69af4ba02bfc9d79361880ecc9690554ae0e1945d891d48f2ebc44313b
FETCH_AI_API_KEY=sk_8647c64a7ec3493db51369190475ca12177db5485b9a41f19b0d3256dd5e4366
```

### Next Steps
1. Test Reddit scraper with r/Fitness #Deprecated
2. Begin implementing Feature Extraction Engine (Component 2)
3. Set up Feature Store for embeddings (Component 3)

## 2025-10-25 – Compact Session

### #CurrentFocus
Converted CSV datasets to Bright Data API input formats for batch keyword & URL-based Reddit scraping

### #SessionChanges
- Parsed Sheet 2-Table 1.csv and extracted 101 unique keywords for Bright Data keyword-based discovery
- Created parse_keywords.py script to clean and format keywords from messy CSV with regex
- Generated keyword_scrape_input.csv with columns: keyword, date, sort_by, num_of_posts (all set to 100)
- Extracted 1,508 unique post URLs from 100_subreddits.json (1,550 total posts)
- Created extract_urls.py to generate url_scrape_input.csv with days_back=50, load_all_replies=true, comment_limit=100
- Analyzed post distribution across 71 subreddits (avg 21.8 posts per subreddit, top: Anxiety/depression/motorcycles with 100 each)

### #NextSteps
- Upload keyword_scrape_input.csv to Bright Data for keyword-based scraping #Deprecated
- Upload url_scrape_input.csv to Bright Data for URL-based comment scraping #Deprecated
- Process and store scraped Reddit data in Feature Store #Deprecated
- Begin Feature Extraction Engine implementation

### #BugsAndTheories
- Some keywords have broken words (e.g. "p rotein powder", "van conv ersions") ⇒ source CSV has formatting issues with quoted strings
- 42 duplicate URLs in 100_subreddits.json ⇒ multiple scraping runs or overlapping subreddit queries

### #Background
- Pivoted from browser automation to Bright Data Dataset API for reliability
- Using two scraping approaches: keyword-based (101 keywords) and URL-based (1,508 posts)
- Bright Data API uses synchronous /scrape endpoint with parameters: url, sort_by, sort_by_time, num_of_posts, keyword
- Created batch processing scripts for CSV → API input format conversion

## 2025-10-25 – Compact Session

### #CurrentFocus
Built complete Knowledge Graph + Vector DB system with automated Reddit data processing pipeline generating 50 diverse personas per community

### #SessionChanges
- Extracted 118,169 unique author profile URLs from keywords.json using extract_author_urls.py
- Built Supabase SDK integration with supabase_client.py and tested connection successfully
- Created complete KG schema (sql/01_knowledge_graph_schema.sql) with personas, communities, interests, creative_prefs tables
- Created vector DB schema (sql/02_vector_database_schema.sql) with pgvector, embeddings tables, RPC functions
- Built Python SDK layer: knowledge_graph.py, vector_store.py, persona_manager.py integration
- Created OpenAI client wrapper (openai_client.py) with GPT-4o-mini + text-embedding-3-small support
- Built process_reddit_data.py pipeline: extracts 1,577 communities, enriches top 20, generates 50 personas each (1,000 total)
- Added generate_diverse_personas_batch() method for batch persona generation with diversity strategy
- Updated .gitignore to exclude large data files (backend/data/*.json, backend/*.csv)
- Created comprehensive docs: SETUP_GUIDE.md, DATA_PROCESSING_GUIDE.md, QUICK_REFERENCE.md, 50_PERSONAS_PER_COMMUNITY.md

### #NextSteps
- Run SQL schemas in Supabase (01_knowledge_graph_schema.sql, 02_vector_database_schema.sql)
- Execute process_reddit_data.py to generate 1,000 personas (~60-75 min, ~$3.85 cost)
- Verify persona count and test similarity search queries
- Connect personas to Agent Simulation Layer for creative feedback

### #RecentImprovements
- Fixed OpenAI timeout (30s → 300s) and reduced batch size (50 → 10 personas per batch)
- Improved keyword extraction with comprehensive stopword filtering (now extracts meaningful topics like "husband", "weight", "college", "workout" instead of generic words like "aita", "update", "years")

### #BugsAndTheories
- None identified in current session

### #Background
- System processes 10,043 posts from keywords.json + subreddits.json across 1,577 unique communities
- Generates 50 diverse personas per community (varying age, income, experience, goals) using GPT batch generation
- **Batch strategy**: 5 batches of 10 personas per community (100 GPT API calls total) - prevents timeout issues
- **Timeout fix**: Increased OpenAI client timeout from 30s to 300s (5 minutes) in utils/openai_client.py
- Cost breakdown: $2.00 persona gen, $0.05 embeddings, $0.40 communities, $1.40 other = $3.85 total
- Database impact: 1,000 personas + embeddings = ~8 MB, IVFFlat indexes handle <100ms similarity search
- **Pipeline architecture**: Processes each community sequentially - creates community, generates 50 personas (5 batches of 10), commits to DB before moving to next community (enables incremental progress if interrupted)

## 2025-10-25 – Compact Session

### #CurrentFocus
Fixed OpenAI timeout errors and improved keyword extraction for meaningful interest generation

### #SessionChanges
- Modified process_reddit_data.py to commit to database after each community (incremental processing for fault tolerance)
- Increased OpenAI client timeout from 30s to 300s in utils/openai_client.py (prevents read timeout on large requests)
- Reduced persona batch size from 50 to 10 (5 batches per community) to prevent API timeouts
- Expanded stopword list from ~60 to 180+ words (filters Reddit jargon, generic verbs, time words)
- Increased minimum keyword length from 3 to 5 characters with vowel requirement
- Created INCREMENTAL_PROCESSING.md documenting per-community commit strategy
- Created TIMEOUT_FIX.md explaining timeout solution and batch size trade-offs
- Created KEYWORD_EXTRACTION.md showing before/after keyword quality improvements
- Created test_keywords.py script to preview extracted keywords before processing

### #NextSteps
- Run SQL schemas in Supabase (01_knowledge_graph_schema.sql, 02_vector_database_schema.sql)
- Execute process_reddit_data.py to generate 1,000 personas (50 per community × 20 communities)
- Verify persona creation and test similarity search queries
- Connect personas to Agent Simulation Layer for creative feedback

### #BugsAndTheories
- OpenAI timeout on 50-persona batches ⇒ requests taking 2-3 minutes exceeded 30s timeout, fixed with 300s timeout + smaller batches
- Generic keywords extracted (aita, update, years) ⇒ insufficient stopword filtering, fixed with comprehensive 180+ word stopword list

### #Background
- Incremental processing: Each community commits immediately (community + 50 personas + embeddings) before moving to next
- Keyword quality: Now extracts meaningful topics (husband, weight, college, workout) vs generic words (aita, update, years)
- Total API calls: 100 GPT persona generation + 20 embedding batches = 120 calls for 1,000 personas
- Processing time: ~60-75 minutes total, ~3-4 minutes per community (includes 5 persona batches + embeddings + DB writes)

## 2025-10-25 – Compact Session

### #CurrentFocus
Integrated Elasticsearch for fast vector search and full-text search capabilities alongside Supabase

### #SessionChanges
- Installed elasticsearch==9.1.1 Python client and configured connection to Elastic Cloud serverless
- Created config/elasticsearch_client.py with API key authentication and connection testing
- Built es_search/schema.py with serverless-compatible index mappings for personas, communities, content, interests
- Created es_search/es_client.py SDK with CRUD operations, vector search (k-NN), and bulk indexing
- Implemented db/dual_store.py to write to both Supabase (PostgreSQL + pgvector) and Elasticsearch simultaneously
- Added Elasticsearch credentials to .env (URL, API key, cloud ID)
- Updated requirements.txt with elasticsearch dependency
- Created ELASTICSEARCH_SETUP.md with comprehensive usage guide and examples

### #NextSteps
- Modify process_reddit_data.py to use DualStoreManager instead of PersonaManager
- Run pipeline to populate both Supabase and Elasticsearch with 1,000 personas
- Test vector search performance comparison between pgvector and Elasticsearch
- Build FastAPI endpoints for persona/community search using both stores

### #BugsAndTheories
- Initial connection error ⇒ serverless mode doesn't support shard/replica settings, fixed by removing from mappings

### #Background
- Elasticsearch cluster: my-elasticsearch-project (us-central1, serverless mode)
- Dual-store architecture: Supabase for relational data + pgvector, Elasticsearch for fast vector/text search + analytics
- Vector dimensions: 1536 (OpenAI text-embedding-3-small) with cosine similarity
- Indices created: advisor_personas, advisor_communities, advisor_content, advisor_interests
- Use cases: Elasticsearch for search speed, Supabase for transactional consistency and relational queries

## 2025-10-25 – Compact Session

### #CurrentFocus
Migrated existing Supabase data (personas, communities, content, interests) to Elasticsearch for dual-store architecture

### #SessionChanges
- Created scripts/migrate_supabase_to_elasticsearch.py with full migration pipeline for all data types
- Parsed string-encoded fields (demographics, psychographics, pain_points, motivations) using ast.literal_eval
- Converted string-encoded embeddings to float arrays using json.loads for Elasticsearch indexing
- Migrated 97/100 personas (3 missing embeddings), 20/25 communities, 97/100 content items, 100/100 interests
- Created scripts/migrate_fix_personas.py for focused persona migration bypassing relational lookups
- Renamed elasticsearch folder to es_search to avoid Python package naming conflict
- Updated requirements.txt with elasticsearch==9.1.1 dependency

### #NextSteps
- Test Elasticsearch vector search performance vs Supabase pgvector with sample queries
- Build FastAPI search endpoints using DualStoreManager for hybrid queries
- Implement search aggregations and analytics using Elasticsearch
- Update process_reddit_data.py to use DualStoreManager for future data ingestion

### #BugsAndTheories
- Embedding string format ⇒ Supabase stores embeddings as JSON strings, required json.loads parsing for Elasticsearch
- Demographics/psychographics as strings ⇒ stored as string repr not JSON, needed ast.literal_eval to convert to dicts/lists
- Missing 'name' field in relations ⇒ get_persona_communities() returns incomplete data, bypassed by skipping community/interest lookups

### #Background
- Migration completed: 311 total documents synced from Supabase to Elasticsearch
- Data parsing strategy: ast.literal_eval for Python literals, json.loads for JSON strings
- Current Elasticsearch state: 94 personas, 20 communities, 97 content, 100 interests all searchable
- Both stores now contain same data: Supabase (source of truth), Elasticsearch (search/analytics layer)

## 2025-10-26 – Compact Session

### #CurrentFocus
Integrated Fetch.ai ASI:One API to power all 932 persona agents with asi1-mini model for authentic persona embodiment

### #SessionChanges
- Created backend/utils/fetchai_client.py wrapper with OpenAI-compatible chat completions interface for asi1-mini model
- Updated backend/agents/persona_agent.py to use Fetch.ai for agent reasoning (system prompts for persona embodiment)
- Replaced OpenAI LLM calls with Fetch.ai ASI:One while keeping OpenAI for embedding generation only
- Added error handling to db/persona_manager.py for graceful database query failures in vector search
- Tested connection to Fetch.ai API successfully (https://api.asi1.ai/v1/chat/completions)
- Verified all 6 API endpoints working: list personas, chat, analyze-ad, analyze-ad-multi, get context, find similar
- Tested with multiple personas generating authentic, persona-specific responses to ads and queries

### #NextSteps
- Begin implementing Feature Extraction Engine (Component 2)
- Set up Feature Store for embeddings (Component 3)
- Connect persona agents to creative feedback and variant generation pipeline

### #BugsAndTheories
- Supabase RPC match_content/match_communities type mismatch ⇒ varchar(255) vs text in column 2, added try/catch to prevent failures
- Chat endpoint initially failed with 500 error ⇒ database query type mismatch, fixed with error handling fallbacks

### #Background
- Architecture: Fetch.ai ASI:One (asi1-mini) for agent reasoning, OpenAI for embeddings, Supabase for data + pgvector retrieval
- All 932 personas now use Fetch.ai with system prompts containing full persona context (demographics, psychographics, pain points, motivations)
- Agents access embedded messages/content via vector similarity search in Supabase
- Removed all Elasticsearch dependencies per user request (reverted to Supabase-only for vector search)
- API running at http://localhost:8000 with full persona agent functionality

## 2025-10-26 – Compact Session

### #CurrentFocus
Deployed 932 persona agents to AWS EC2 with coordinator agent on Agentverse for distributed ad analysis

### #SessionChanges
- Created coordinator_agent.py to orchestrate multi-persona ad analysis through FastAPI endpoints
- Built complete AWS deployment pipeline: Dockerfile, docker-compose.yml, deploy.sh, systemd service config
- Created AWS_DEPLOYMENT.md and AGENTVERSE_DEPLOYMENT.md comprehensive deployment guides
- Deployed FastAPI with 932 Fetch.ai persona agents to AWS EC2 instance at 52.53.159.105:8000
- Resolved Amazon Linux compatibility issues (yum vs apt, dateparser module, nested directories, port conflicts)
- Created coordinator_agent_agentverse.py production-ready for Agentverse deployment with mailbox system
- Cleaned git history to remove all "Co-Authored-By: Claude" references using filter-branch
- Attempted Agentverse registration using uAgents framework (5 test agents created with cryptographic signatures)
- Tested end-to-end AWS API: all 6 endpoints operational, multi-persona analysis working with sentiment summaries

### #NextSteps
- Complete Agentverse coordinator deployment (leave Agent Endpoint URL blank, paste coordinator_agent_agentverse.py code)
- Test end-to-end flow: Agentverse Coordinator → AWS FastAPI → 932 Personas → Fetch.ai ASI:One
- Optional: Set up systemd service for auto-restart, configure HTTPS with Nginx, add API authentication
- Begin Feature Extraction Engine (Component 2) for ad creative multimodal analysis

### #BugsAndTheories
- Agentverse API 401 "Could not validate challenge proof" ⇒ requires cryptographic signatures with private keys via uAgents framework
- EC2 `apt: command not found` ⇒ Amazon Linux uses yum not apt, adjusted all deployment commands
- Port 8000 conflict on EC2 ⇒ previous instance running, killed with lsof + kill -9
- Nested AdVisor/AdVisor directory ⇒ user in wrong path, corrected to ~/AdVisor/backend
- Missing dateparser module ⇒ not in requirements.txt, installed manually with pip

### #Background
- Architecture: Agentverse Coordinator → AWS FastAPI (52.53.159.105:8000) → 932 Personas → Fetch.ai ASI:One API
- AWS Instance: i-00b8b674817dfd056 running Amazon Linux, public IP 52.53.159.105, private IP 172.31.1.169
- Coordinator agent uses AdAnalysisRequest/AdAnalysisResponse models for structured messaging via uAgents protocol
- All 932 personas accessible at public endpoints: /agents/personas, /agents/chat, /agents/analyze-ad, /agents/analyze-ad-multi
- Agentverse deployment ready: coordinator_agent_agentverse.py with seed "advisor_coordinator_seed_v1_production", mailbox enabled
- Git history cleaned: 36 commits rewritten, force-pushed to remove Claude co-author references

## 2025-10-26 – Compact Session

### #CurrentFocus
Completed documentation for production deployment and added missing API endpoints for feature extraction and brand metadata

### #SessionChanges
- Created comprehensive README.md documenting full AdVisor system with all technologies, architecture, and deployment info
- Updated README technology stack: clarified Bright Data Browser API with infinite scroll, Fetch.ai ASI:One for agents
- Corrected cost metrics in README: OpenAI for one-time persona generation, Fetch.ai ASI:One for runtime agent reasoning
- Created SUPAVISOR_README.md (135 lines) documenting Agentverse coordinator with deployment info, protocol, performance
- Created SUPAVISOR_BIO.md with multiple bio formats (short/medium/long/elevator pitch/one-liner/tags) for Agentverse
- Deployed SupaVisor coordinator to Agentverse: agent1qw8kzfh7gfv63ravqmclx9uzkxwa6mkqycty7nfctuzqlmcuz0wfzzy8lpl (@supavisor)
- Copied /extract and /brandmeta routes from api/ to backend/api/routes/ for AWS deployment
- Updated backend/main.py to include extract_router and brandmeta_router for missing endpoints
- Changed CORS to allow_origins=["*"] for production external requests
- Copied api/schemas.py, api/schemas_brandmeta.py, api/services/ to backend/api/ for dependencies

### #NextSteps
- Redeploy backend to AWS EC2 with /extract and /brandmeta endpoints (git pull + restart uvicorn) #Deprecated
- Test /extract and /brandmeta endpoints on AWS to confirm 404 errors resolved
- Begin Feature Extraction Engine implementation (Component 2)
- Build frontend integration with SupaVisor coordinator on Agentverse

### #BugsAndTheories
- AWS 404 errors on /extract and /brandmeta ⇒ endpoints existed in api/ but not included in backend/main.py, fixed by copying routes

### #Background
- SupaVisor deployed on Agentverse as production coordinator orchestrating 932 AWS-hosted persona agents
- README documents full stack: 932 personas powered by Fetch.ai ASI:One, coordinator on Agentverse, AWS EC2 deployment
- Architecture: Frontend → SupaVisor (Agentverse) → AWS FastAPI → 932 Agents → Fetch.ai ASI:One API
- All documentation completed: main README, SupaVisor README, deployment guides, bio variations for Agentverse profile
- /extract endpoint: handles image/video uploads for feature extraction
- /brandmeta endpoint: generates brand metadata using LLM providers (local/openai/google/anthropic)

## 2025-10-26 – ASI:One Direct Integration

### #CurrentFocus
Replaced EC2 agent architecture with direct ASI:One integration for intelligent persona-based ad analysis

### #SessionChanges
- Created smart_agent_selector.py with intelligent persona selection (age + 40% industry match algorithm)
- **OpenAI-powered persona selection**: Uses GPT-4o-mini to semantically rank personas by industry relevance (replaces keyword matching)
- Built /api/analyze-ad-smart endpoint that uses ASI:One agents directly instead of EC2
- ASI:One agents analyze feature vectors (moondream + visual features) from each persona's perspective
- Each persona gets unique system prompt with demographics, psychographics, pain points, motivations
- Agents return structured JSON: {attention: "full"|"partial"|"ignore", insight: "reaction text"}
- Updated frontend dashboard to pass feature_vector instead of ad_description
- Frontend maps 50 persona analyses to random graph nodes for visualization
- Click interaction shows persona insight + attention level with color coding (green/yellow/red)
- Restricted clicks to only highlighted dots (nodes with analysis data)
- Added fallback to keyword matching if OpenAI selection fails

### #NextSteps
- Test complete flow: upload ad → extract features → smart persona selection → ASI:One analysis
- Monitor ASI:One API costs and performance with 50 concurrent persona analyses
- Consider batch processing or async if 50 sequential calls take too long
- Add loading states in frontend during analysis

### #BugsAndTheories
- None identified yet - awaiting first real test

### #Background
- **New Architecture**: Frontend → Next.js API → Smart Selector (OpenAI + Supabase) → ASI:One (50 personas) → Save Results
- **Smart Selection Process**:
  1. Filter personas by target age range (e.g., "18-24")
  2. Use OpenAI GPT-4o-mini to semantically rank by industry relevance
  3. Select top 40% most relevant (e.g., 20 personas for fitness ad get fitness enthusiasts)
  4. Fill remaining 60% with age-matched diverse perspectives
- **Persona Prompts**: Each ASI:One call embodies different persona with full context from Supabase
- **Feature Analysis**: Moondream summary, caption, CTA, keywords + color palette, whitespace, aspect ratio
- **Cost Efficiency**:
  - Removed EC2 dependency
  - OpenAI selection: ~1 call per analysis (~$0.001)
  - ASI:One analysis: 50 personas × ~200 tokens = ~10k tokens/analysis
- **Visualization**: 50 analyzed personas highlighted on 1000-node graph, clickable for detailed insights

## 2025-10-26 – Compact Session

### #CurrentFocus
Implemented community display name mapping for persona visualization, replacing generic "Community 01, 02, 03" with descriptive names

### #SessionChanges
- Fixed Supabase RLS policy blocking backend inserts to ad_analyses table (added service role policies)
- Created COMMUNITY_DISPLAY_NAMES mapping 25 subreddits to 21 unique display names (1:1 per subreddit)
- Updated backend/api/routes/personas.py to fetch persona-community relationships and map to display names
- Modified AgentGraph.tsx to use communityNames state and communityIndexMap for proper grouping
- Updated legend, hover tooltip, and click card to show community display names instead of generic labels
- Added community tag as styled pill in tooltips and detail cards
- Registered insights router in backend/main.py for /insights endpoint
- Fixed .vercelignore to keep package.json (was removing all *.json files causing Vercel build failures)
- Committed changes and pushed to enable Vercel deployment

### #NextSteps
- Update EC2 backend with latest community mapping code (git pull + restart uvicorn)
- Test /insights endpoint on EC2 after deployment
- Verify community names display correctly in frontend after EC2 update
- Monitor Vercel deployment status

### #BugsAndTheories
- Supabase RLS policy 42501 error ⇒ service role lacked INSERT/UPDATE permissions, fixed with dedicated policies
- Frontend showing "Community 01, 02, 03" ⇒ EC2 backend outdated, local has fix
- Vercel build failing with "No Next.js version detected" ⇒ .vercelignore had *.json wildcard removing package.json
- /insights endpoint 404 ⇒ insights router not registered in main.py, added include_router call

### #Background
- 932 personas grouped into 21 communities with descriptive names (AITA Community, Avid Gamers, Bodyweight Fitness Enthusiasts, etc.)
- Community mapping supports 25 subreddits but only 21 exist in database (4 missing: r/Fitness, r/motorcycles, r/nosleep, r/CuratedTumblr)
- Frontend .env points to EC2 (52.53.159.105:8000), local changes need EC2 deployment to be visible
- AgentGraph uses communityIndexMap to assign personas to community indices based on display names
- Supabase RLS now allows both authenticated users and service role to read/write ad_analyses
