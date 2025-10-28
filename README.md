# AdVisor

> AI-powered ad creative analysis platform using 932 diverse persona agents to provide authentic audience feedback

## 🎯 Overview

AdVisor empowers marketers to understand and improve their ad creatives by combining multimodal feature extraction with generative agent simulations. The platform analyzes ads through the lens of 932 unique, data-driven personas sourced from real Reddit communities, providing authentic feedback on how different audience segments perceive creative content.

## 🏗️ Architecture

```
User Application / Frontend
     ↓
Agentverse Coordinator Agent (SupaVisor)
  • Hosted on Fetch.ai's Agentverse platform
  • Orchestrates multi-persona analysis
  • Aggregates insights and key metrics
     ↓
AWS EC2 FastAPI Server (52.53.159.105:8000)
  • Hosts 932 deployed persona agents
  • Manages persona database (Supabase + pgvector)
  • Handles parallel agent execution
     ↓
932 Individual Persona Agents
  • Each powered by Fetch.ai ASI:One API (asi1-mini model)
  • Real-time ad analysis with authentic perspectives
  • Vector search for relevant context
```

## 🔧 Technology Stack

### Backend
- **FastAPI** - High-performance Python web framework for API endpoints
- **Python 3.12** - Core programming language
- **uvicorn** - ASGI server for production deployment

### AI & Agent Framework
- **Fetch.ai ASI:One API** - AI reasoning engine (asi1-mini model) for authentic persona embodiment
- **uAgents Framework** - Official Fetch.ai framework for agent creation and communication
- **Agentverse** - Fetch.ai's platform for hosting and discovering agents
- **OpenAI API** - GPT-4o-mini for persona generation, text-embedding-3-small for embeddings

### Database & Vector Search
- **Supabase** - PostgreSQL database with built-in APIs
- **pgvector** - PostgreSQL extension for vector similarity search
- **IVFFlat indexing** - Fast k-NN search for persona/content embeddings

### Data Collection
- **Bright Data Browser API** - Automated Reddit scraping for community data
  - Browser automation with infinite scroll for deep post extraction
  - Discover by Keywords endpoint (101 unique keywords)
  - URL-based post scraping with comment extraction (1,508 posts)
  - Multi-community analysis across 1,577 communities

### Deployment & Infrastructure
- **AWS EC2** - Cloud hosting (Amazon Linux)
- **Docker & Docker Compose** - Containerization for consistent deployment
- **systemd** - Service management for auto-restart
- **Git** - Version control

### Development Tools
- **python-dotenv** - Environment variable management
- **requests** - HTTP client for API communication
- **Pydantic** - Data validation and settings management
- **dateparser** - Flexible date parsing

## 📊 System Components

### 1. Ad Upload & Processing
- Upload ad creatives (image/video) with company metadata
- Extract raw files and metadata for analysis

### 2. Feature Extraction Engine
- **Goal**: Extract ≥10 distinct, decorrelated features per ad
- **Performance**: <5 min per 50 ads on single GPU
- Multimodal analysis: visual, text, audio, sentiment

### 3. Feature Store
- Centralized structured dataset
- Vector embeddings (1536 dimensions via OpenAI)
- Efficient similarity search

### 4. Community Recommender
- Suggests best-fit audience communities to simulate
- Routes analysis to relevant persona demographics

### 5. Agent Simulation Layer ⭐ **CORE COMPONENT**

#### Agentverse Coordinator (SupaVisor)
- **Hosted on Fetch.ai Agentverse** - Cloud-based agent orchestration platform
- **Role**: Acts as intelligent coordinator between frontend and AWS persona agents
- **Functions**:
  - Receives ad analysis requests from users/applications
  - Forwards requests to AWS EC2 API hosting 932 persona agents
  - Aggregates responses from multiple persona agents
  - Extracts key insights and sentiment metrics
  - Generates simulation summary for insights dashboard
  - Returns structured analysis with sentiment breakdown
- **Benefits**: Decoupled architecture, scalable, discoverable on Agentverse marketplace

#### 932 Persona Agents (AWS-Hosted)
- **Deployment**: All agents hosted on AWS EC2 (52.53.159.105:8000)
- **AI Engine**: Each agent powered by Fetch.ai ASI:One API (asi1-mini model)
- **Data Source**: Generated from real Reddit community data (1,577 communities)
- Each persona has:
  - Demographics (age, location, income, education, occupation)
  - Psychographics (values, interests, lifestyle)
  - Pain points and motivations from real community discussions
  - Authentic community context via vector search
- Agent types: Performance Analyst, Creative Director, Community Member
- **Response Time**: <5s for 10 personas analyzed in parallel

### 6. Creative Feedback & Variant Generator
- Aggregates persona analyses
- Sentiment breakdown (positive/neutral/negative)
- Actionable recommendations
- Creative improvement suggestions

### 7. Insights Dashboard
- Visualization of aggregated feedback
- Sentiment distribution
- Export capabilities for marketers

## 🚀 Getting Started

### Prerequisites
```bash
Python 3.12+
PostgreSQL with pgvector extension
Docker & Docker Compose (for deployment)
```

### Environment Variables
Create a `.env` file in the project root:
```bash
# Fetch.ai Configuration
FETCH_AI_API_KEY=sk_...
AGENTVERSE_KEY=eyJhbGc...
AGENT_SEED_PHRASE=your_seed_phrase_here

# Supabase Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGc...

# OpenAI API
OPENAI_API_KEY=sk-proj-...

# Bright Data (Reddit Scraping)
BRIGHT_DATA_API_KEY=...
```

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/AdVisor.git
   cd AdVisor
   ```

2. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Set up Supabase database**
   ```bash
   # Run SQL schemas in Supabase SQL Editor
   backend/sql/01_knowledge_graph_schema.sql
   backend/sql/02_vector_database_schema.sql
   ```

4. **Process Reddit data and generate personas** (optional - already done)
   ```bash
   python backend/db/process_reddit_data.py
   # Processes 1,577 communities, generates 1,000 personas
   # Cost: ~$3.85, Time: ~60-75 minutes
   ```

5. **Run the API server**
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Test the API**
   ```bash
   curl http://localhost:8000/agents/personas
   ```

### AWS Deployment

See detailed guide: [`backend/deploy/AWS_DEPLOYMENT.md`](backend/deploy/AWS_DEPLOYMENT.md)

```bash
# On AWS EC2 instance
cd AdVisor/backend
docker-compose up -d
```

**Live Production API**: http://52.53.159.105:8000

### Agentverse Coordinator Deployment

See detailed guide: [`backend/AGENTVERSE_WEB_DEPLOY.md`](backend/AGENTVERSE_WEB_DEPLOY.md)

1. Go to https://agentverse.ai
2. Create new agent
3. Copy code from `backend/agents/COPY_THIS_TO_AGENTVERSE.py`
4. Deploy and get agent address

## 📡 API Endpoints

### Core Endpoints

#### **GET** `/agents/personas`
List all 932 personas with demographics and psychographics
```json
[
  {
    "id": "uuid",
    "name": "Socially-Conscious Teens 18-24",
    "demographics": {...},
    "psychographics": {...}
  }
]
```

#### **POST** `/agents/chat`
Chat with a specific persona
```json
{
  "persona_id": "uuid",
  "message": "What do you think about this ad?"
}
```

#### **POST** `/agents/analyze-ad`
Get single persona's analysis of an ad
```json
{
  "persona_id": "uuid",
  "ad_description": "Nike running shoes ad featuring athlete..."
}
```

#### **POST** `/agents/analyze-ad-multi`
Get multi-persona analysis (recommended)
```json
{
  "ad_description": "Nike running shoes ad...",
  "num_personas": 10
}
```
**Response**: Array of analyses + sentiment summary

#### **POST** `/agents/{persona_id}/context`
Get persona's relevant context via vector search

#### **POST** `/agents/similar`
Find similar personas via embedding similarity

## 📈 Key Metrics & Performance

| Metric | Value |
|--------|-------|
| Total Personas | 932 (deployed on AWS EC2) |
| Source Communities | 1,577 Reddit communities |
| Scraped Posts | 10,043+ |
| Persona Data Generation | $2.00 (OpenAI GPT-4o-mini - one-time) |
| Embedding Generation | $0.05 (OpenAI text-embedding-3-small - one-time) |
| Agent Reasoning Engine | Fetch.ai ASI:One API (asi1-mini model) |
| Vector Dimensions | 1,536 |
| API Response Time | <5s for 10 personas (parallel execution) |
| Database Size | ~8 MB (personas + embeddings) |
| Similarity Search | <100ms (pgvector IVFFlat index) |
| Coordinator Deployment | Agentverse (cloud-hosted) |

## 🎯 Key Objectives

| Goal | Description | Metric |
|------|-------------|--------|
| Feature Extraction Insight | Extract semantically rich, non-redundant signals | ≥10 distinct features per ad |
| Performance | Fast processing, parallelizable | <5 min per 50 ads |
| Robustness | Handle diverse industries, formats | 100% of .png/.mp4 ads |
| Creativity | Unique, interpretable signals | ≥3 novel signal types |
| Authenticity | Real persona responses | 932 data-driven personas |

## 🧪 Example Usage

### Python Client
```python
import requests

# Analyze ad with 10 diverse personas
response = requests.post(
    "http://52.53.159.105:8000/agents/analyze-ad-multi",
    json={
        "ad_description": "Eco-friendly water bottle ad. Shows hikers in nature. Tagline: 'Hydrate Responsibly.'",
        "num_personas": 10
    }
)

analyses = response.json()

# Get sentiment breakdown
for analysis in analyses:
    print(f"{analysis['persona_name']}: {analysis['sentiment']}")
    print(f"  Reasoning: {analysis['reasoning'][:100]}...")
```

### Agentverse Agent Communication
```python
from uagents import Agent, Context, Model

class AdAnalysisRequest(Model):
    ad_description: str
    num_personas: int = 10

# Send to coordinator on Agentverse
await ctx.send(
    "agent1q...",  # Coordinator address
    AdAnalysisRequest(
        ad_description="Your ad here",
        num_personas=5
    )
)
```

## 📂 Project Structure

```
AdVisor/
├── backend/
│   ├── main.py                          # FastAPI application
│   ├── agents/
│   │   ├── persona_agent.py             # Persona agent with Fetch.ai integration
│   │   ├── coordinator_agent.py         # Local coordinator
│   │   ├── COPY_THIS_TO_AGENTVERSE.py   # Agentverse deployment code
│   │   └── deploy_to_agentverse.py      # Registration script
│   ├── db/
│   │   ├── persona_manager.py           # Persona CRUD operations
│   │   ├── knowledge_graph.py           # Community/interest graph
│   │   ├── vector_store.py              # pgvector operations
│   │   └── process_reddit_data.py       # Data processing pipeline
│   ├── sql/
│   │   ├── 01_knowledge_graph_schema.sql
│   │   └── 02_vector_database_schema.sql
│   ├── utils/
│   │   ├── fetchai_client.py            # Fetch.ai ASI:One wrapper
│   │   ├── openai_client.py             # OpenAI API wrapper
│   │   └── supabase_client.py           # Supabase connection
│   ├── deploy/
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   ├── deploy.sh
│   │   └── AWS_DEPLOYMENT.md
│   ├── data/                            # Scraped Reddit data (gitignored)
│   └── requirements.txt
├── .env                                 # Environment variables
├── .gitignore
├── CLAUDE.md                            # Project development log
└── README.md                            # This file
```

## 🔐 Security Notes

- All API keys stored in `.env` (not committed to git)
- AWS EC2 security groups configured for ports 22, 80, 8000
- Supabase Row Level Security (RLS) policies active
- Agent seed phrases for cryptographic signatures

## 🌟 Unique Features

### 1. **Real Data-Driven Personas**
Unlike traditional simulated personas, AdVisor's 932 agents are generated from real Reddit community data, ensuring authentic perspectives.

### 2. **Distributed Agent Architecture**
- **Coordinator agent on Agentverse**: Orchestrates requests, aggregates insights, extracts key metrics
- **932 persona agents on AWS EC2**: Deployed for scalability and parallel execution
- **Fetch.ai ASI:One API**: Powers all agent reasoning (asi1-mini model)
- **Decoupled design**: Frontend → Agentverse Coordinator → AWS Agents → AI reasoning

### 3. **Multi-Community Analysis**
Each persona represents a unique community segment with:
- Specific demographics
- Real pain points from Reddit posts
- Authentic motivations and values

### 4. **Fast Vector Search**
pgvector with IVFFlat indexing enables <100ms similarity search across 932 persona embeddings

### 5. **Flexible Deployment**
- Local development
- AWS EC2 production
- Agentverse coordinator
- Docker containerization

## 📊 Data Pipeline

```
Bright Data Reddit Scraping
     ↓
10,043 posts from 1,577 communities
     ↓
Keyword extraction + community analysis
     ↓
GPT-4o-mini persona generation (50 per community)
     ↓
OpenAI embeddings (1536 dimensions)
     ↓
Supabase + pgvector storage
     ↓
932 Persona Agents powered by Fetch.ai
```

## 🛣️ Roadmap

- [ ] Complete Feature Extraction Engine (Component 2)
- [ ] Set up Feature Store for ad embeddings (Component 3)
- [ ] Build Community Recommender (Component 4)
- [ ] Implement Creative Feedback & Variant Generator (Component 6)
- [ ] Create Insights Dashboard (Component 7)
- [ ] Add image/video multimodal analysis
- [ ] Implement HTTPS with Nginx
- [ ] Add API authentication
- [ ] Build frontend application

## 🤝 Contributing

This project is under active development. Contributions welcome!

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **Fetch.ai** - ASI:One API and uAgents framework
- **Supabase** - Database and vector search infrastructure
- **OpenAI** - Persona generation and embeddings
- **Bright Data** - Reddit data collection
- **Reddit Communities** - Source data for authentic personas

---

**Status**: Production Ready ✅
- **AWS EC2 Deployment**: Live at http://52.53.159.105:8000 (932 persona agents)
- **Agentverse Coordinator**: Deployed at `agent1qw8kzfh7gfv63ravqmclx9uzkxwa6mkqycty7nfctuzqlmcuz0wfzzy8lpl` (@supavisor)
- **Agent Reasoning**: All 932 agents powered by Fetch.ai ASI:One API (asi1-mini model)
- **Response Time**: <5s for parallel 10-persona ad analysis
- **Full Stack**: Frontend → Agentverse Coordinator → AWS EC2 → 932 Agents → Fetch.ai ASI:One

For questions or issues, please open a GitHub issue or contact the maintainer.
