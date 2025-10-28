# Persona Agent System for AdVisor

## Overview

The Persona Agent System creates AI-powered agents for each persona in the AdVisor platform. Each agent can:
- **Reason** from their persona's perspective
- **Retrieve** relevant information from Elasticsearch
- **Analyze** ad creatives and provide feedback
- **Chat** interactively with users

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Persona Agent                        │
│  ┌──────────────────────────────────────────────┐  │
│  │  Persona Context (Demographics, Psycho-      │  │
│  │  graphics, Pain Points, Motivations)         │  │
│  └──────────────────────────────────────────────┘  │
│                       ↓                              │
│  ┌──────────────────────────────────────────────┐  │
│  │  Information Retrieval                        │  │
│  │  - Search similar communities (vector)       │  │
│  │  - Find relevant content (k-NN)              │  │
│  │  - Discover similar personas                 │  │
│  └──────────────────────────────────────────────┘  │
│                       ↓                              │
│  ┌──────────────────────────────────────────────┐  │
│  │  LLM Reasoning (GPT-4o-mini)                 │  │
│  │  - Generate contextual responses             │  │
│  │  - Analyze ad creatives                      │  │
│  │  - Provide persona-specific insights         │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Core Components

### 1. PersonaAgent

Represents a single persona as an intelligent agent.

**Key Methods**:
- `get_context()` - Returns formatted persona context
- `retrieve_relevant_content(query)` - Searches Elasticsearch for relevant info
- `retrieve_similar_personas()` - Finds personas with similar embeddings
- `chat(message)` - Interactive chat from persona's perspective
- `analyze_ad_creative(ad_description)` - Provides ad feedback

**Example Usage**:

```python
from agents import PersonaAgent

# Create agent for a persona
agent = PersonaAgent(persona_id="abc-123")

# Chat with the agent
result = agent.chat("What are your thoughts on fitness apps?")
print(result['response'])

# Analyze an ad
analysis = agent.analyze_ad_creative("""
    A fitness app showing busy professionals working out during lunch.
    Tagline: "5-minute workouts that fit your schedule."
""")
print(analysis['analysis'])
```

### 2. PersonaAgentManager

Manages multiple persona agents and orchestrates multi-persona analysis.

**Key Methods**:
- `list_available_personas()` - Lists all personas that can become agents
- `get_agent(persona_id)` - Gets/creates an agent (with caching)
- `multi_persona_analysis(ad_description)` - Gets feedback from multiple personas

**Example Usage**:

```python
from agents import PersonaAgentManager

manager = PersonaAgentManager()

# List available personas
personas = manager.list_available_personas()
print(f"Found {len(personas)} personas")

# Multi-persona ad analysis
analyses = manager.multi_persona_analysis(
    ad_description="Ad for a productivity app...",
    num_personas=5
)

for analysis in analyses:
    print(f"{analysis['persona_name']}: {analysis['analysis'][:100]}...")
```

## FastAPI Endpoints

### List Available Personas

```http
GET /agents/personas
```

**Response**:
```json
[
  {
    "id": "persona-id-123",
    "name": "Corporate Warriors 25-34",
    "summary": "Young professionals navigating the corporate world..."
  }
]
```

### Chat with Persona

```http
POST /agents/chat
Content-Type: application/json

{
  "persona_id": "persona-id-123",
  "message": "What are your thoughts on remote work?",
  "include_retrieval": true
}
```

**Response**:
```json
{
  "persona_name": "Corporate Warriors 25-34",
  "persona_summary": "Young professionals...",
  "response": "As a Corporate Warrior, remote work presents...",
  "retrieved_context": [
    {
      "type": "community",
      "name": "r/WorkFromHome",
      "description": "Community for remote workers...",
      "score": 0.89
    }
  ]
}
```

### Analyze Ad (Single Persona)

```http
POST /agents/analyze-ad
Content-Type: application/json

{
  "ad_description": "Fitness app for busy professionals with 5-minute workouts",
  "persona_id": "persona-id-123"
}
```

**Response**:
```json
{
  "persona_name": "Corporate Warriors 25-34",
  "persona_summary": "Young professionals...",
  "demographics": {
    "age_range": "25-34",
    "income_level": "middle",
    "occupation": "professional"
  },
  "analysis": "1. Initial Reaction: Positive...\n2. Resonating Elements:..."
}
```

### Analyze Ad (Multiple Personas)

```http
POST /agents/analyze-ad-multi
Content-Type: application/json

{
  "ad_description": "Fitness app for busy professionals",
  "num_personas": 5
}
```

**Response**: Array of `PersonaAnalysis` objects

### Get Persona Context

```http
GET /agents/persona/{persona_id}/context
```

**Response**:
```json
{
  "persona_id": "persona-id-123",
  "context": "You are Corporate Warriors 25-34, a persona representing...",
  "persona_data": {
    "name": "Corporate Warriors 25-34",
    "demographics": {...},
    "psychographics": {...},
    "pain_points": [...],
    "motivations": [...]
  }
}
```

### Find Similar Personas

```http
GET /agents/persona/{persona_id}/similar?k=3
```

**Response**:
```json
{
  "persona_id": "persona-id-123",
  "persona_name": "Corporate Warriors 25-34",
  "similar_personas": [
    {
      "name": "Ambitious Entrepreneurs 25-34",
      "summary": "Business owners navigating...",
      "similarity_score": 0.87
    }
  ]
}
```

## How Persona Agents Work

### 1. Context Building

Each agent constructs a rich context from the persona's:
- **Demographics**: Age, gender, income, education, occupation, location
- **Psychographics**: Values, lifestyle, personality traits
- **Pain Points**: Key challenges and frustrations
- **Motivations**: What drives them
- **Interests & Communities**: Topics and spaces they care about

### 2. Information Retrieval

When a query is made, the agent:
1. Generates an embedding for the query using OpenAI
2. Searches Elasticsearch for:
   - Similar communities (vector search)
   - Relevant content (k-NN on embeddings)
3. Includes retrieved context in the LLM prompt

### 3. LLM Reasoning

The agent uses GPT-4o-mini to:
- Interpret the query from the persona's perspective
- Incorporate retrieved information
- Generate authentic responses based on persona characteristics
- Provide specific feedback rooted in pain points and motivations

### 4. Response Generation

Responses include:
- The persona's authentic perspective
- References to retrieved context when relevant
- Specific suggestions based on persona characteristics
- Engagement likelihood ratings (for ad analysis)

## Use Cases

### 1. Ad Creative Testing

Test ad concepts with diverse personas before production:

```python
manager = PersonaAgentManager()

ad = """
Email marketing SaaS for small businesses.
Features: automated campaigns, A/B testing, analytics.
Tagline: "Marketing automation made simple."
"""

# Get feedback from 10 different personas
analyses = manager.multi_persona_analysis(ad, num_personas=10)

# Aggregate insights
positive_reactions = sum(1 for a in analyses if "positive" in a['analysis'].lower())
print(f"{positive_reactions}/10 personas had positive reactions")
```

### 2. Persona Discovery

Find which personas are similar to your target audience:

```python
target_persona_id = "corporate-warrior-123"
agent = manager.get_agent(target_persona_id)

similar = agent.retrieve_similar_personas(k=5)
print("Target similar personas for this campaign:")
for p in similar:
    print(f"- {p['name']} (similarity: {p['similarity_score']:.2f})")
```

### 3. Interactive Research

Chat with personas to understand their perspectives:

```python
agent = manager.get_agent("millennial-parent-456")

# Ask about pain points
result = agent.chat("What's your biggest challenge with meal planning?")
print(result['response'])

# Get community context
print("Retrieved from:", [c['name'] for c in result['retrieved_context']])
```

### 4. Campaign Optimization

Iterate on ad copy based on persona feedback:

```python
versions = [
    "Version A: 'Save time with AI-powered automation'",
    "Version B: 'Focus on what matters. Let AI handle the rest'",
    "Version C: 'Automate your workflow in 5 minutes'"
]

for version in versions:
    analysis = manager.multi_persona_analysis(version, num_personas=5)
    avg_engagement = sum(
        int(a['analysis'].split('10')[0][-1])
        for a in analysis if '/10' in a['analysis']
    ) / len(analysis)
    print(f"{version}: Avg engagement {avg_engagement}/10")
```

## Integration with Main App

Add to your FastAPI app:

```python
from fastapi import FastAPI
from api.persona_agents import router as agents_router

app = FastAPI()

# Include persona agent endpoints
app.include_router(agents_router)

# Now available at:
# - GET  /agents/personas
# - POST /agents/chat
# - POST /agents/analyze-ad
# - POST /agents/analyze-ad-multi
# - GET  /agents/persona/{id}/context
# - GET  /agents/persona/{id}/similar
```

## Performance Considerations

### Caching

Agents are cached in `PersonaAgentManager.agents` dict:
- First access: ~500ms (load from Elasticsearch)
- Subsequent access: ~1ms (from cache)

### Retrieval Speed

- Vector search on communities: ~50-100ms
- Vector search on content: ~100-200ms
- Total retrieval: ~150-300ms

### LLM Response Time

- Simple chat: ~2-3 seconds
- Ad analysis: ~5-7 seconds
- Multi-persona (5): ~25-35 seconds (can be parallelized)

### Optimization Tips

1. **Batch operations**: Use `multi_persona_analysis()` instead of individual calls
2. **Disable retrieval**: Set `include_retrieval=False` for faster responses
3. **Limit personas**: Start with 3-5 personas for quick feedback
4. **Cache agents**: Reuse `PersonaAgentManager` instance across requests

## Testing

Run the demo script:

```bash
cd backend
python agents/persona_agent.py
```

This will:
1. List available personas
2. Create an agent for the first persona
3. Test chat with retrieval
4. Test ad analysis
5. Run multi-persona analysis

## Current Limitations

1. **No conversation history**: Each chat is stateless (can be added)
2. **English only**: LLM is optimized for English
3. **Retrieval quality**: Depends on Elasticsearch data quality
4. **Cost**: Each chat/analysis costs ~$0.001-0.002 in OpenAI fees

## Future Enhancements

- [ ] Conversation memory for multi-turn chats
- [ ] Parallel execution for multi-persona analysis
- [ ] Streaming responses for real-time feedback
- [ ] Custom retrieval strategies per persona
- [ ] A/B testing framework integration
- [ ] Sentiment analysis on responses
- [ ] Persona agent fine-tuning based on community data
