from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from scraper.reddit_scraper_v2 import RedditScraperV2
from models.reddit_post import SubredditScrapeRequest, SubredditScrapeResponse

# Import persona agent router
from api.persona_agents import router as agents_router

# Import extract and brandmeta routers
from api.routes.extract import router as extract_router
from api.routes.brandmeta import router as brandmeta_router
from api.routes.analyze import router as analyze_router
from api.routes.health_check import router as health_router
from api.routes.moondream_diagnostic import router as moondream_router
from api.routes.personas import router as personas_router
from api.routes.insights import router as insights_router

# Load environment variables from parent directory
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

app = FastAPI(
    title="AdVisor API",
    description="API for Reddit scraping and AI-powered persona agents",
    version="3.0.0"
)

# CORS middleware for frontend and external services
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scraper = RedditScraperV2()

# Include persona agent routes
app.include_router(agents_router)

# Include extract and brandmeta routes
app.include_router(extract_router)
app.include_router(brandmeta_router)
app.include_router(analyze_router)
app.include_router(health_router)
app.include_router(moondream_router)
app.include_router(personas_router)
app.include_router(insights_router)


@app.get("/")
async def root():
    return {
        "message": "AdVisor API",
        "version": "3.0.0",
        "endpoints": {
            "/scrape": "POST - Scrape a subreddit",
            "/health": "GET - Health check",
            "/extract": "POST - Extract features from ad creative (file blob upload)",
            "/brandmeta": "POST - Get brand metadata",
            "/api/analyze-ad-smart": "POST - Smart ad analysis with persona selection",
            "/agents/personas": "GET - List available personas",
            "/agents/chat": "POST - Chat with a persona agent",
            "/agents/analyze-ad": "POST - Get ad feedback from a persona",
            "/agents/analyze-ad-multi": "POST - Get ad feedback from multiple personas",
            "/docs": "GET - Interactive API documentation"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/scrape", response_model=SubredditScrapeResponse)
async def scrape_subreddit(request: SubredditScrapeRequest):
    """
    Scrape posts from a subreddit and save to JSON file.

    Args:
        request: SubredditScrapeRequest containing:
            - subreddit_url: URL of the subreddit (e.g., "https://reddit.com/r/python")
            - max_posts: Maximum number of posts to scrape (default: 25)

    Returns:
        SubredditScrapeResponse with scraped posts
    """
    try:
        # Extract subreddit name from URL
        subreddit_name = request.subreddit_url.rstrip('/').split('/')[-1]

        # Scrape the subreddit
        posts = await scraper.scrape_subreddit(
            request.subreddit_url,
            max_posts=request.max_posts,
            sort_by=request.sort_by,
            sort_by_time=request.sort_by_time,
            keyword=request.keyword
        )

        # Create response
        response = SubredditScrapeResponse(
            subreddit=subreddit_name,
            posts=posts,
            total_posts=len(posts)
        )

        # Save to JSON file with format: subreddit_timestamp.json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{subreddit_name}_{timestamp}.json"
        filepath = os.path.join("data", filename)

        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)

        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(response.model_dump(), f, indent=2, ensure_ascii=False)

        print(f"✓ Saved scraped data to: {filepath}")

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error scraping subreddit: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
