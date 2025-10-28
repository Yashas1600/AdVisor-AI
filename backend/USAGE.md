# How to Use the Reddit Scraper API

## Start the Server

```bash
cd backend
python main.py
```

Server runs at: **http://localhost:8000**

## Scrape r/Fitness

### Using curl:

```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "subreddit_url": "https://www.reddit.com/r/Fitness/",
    "max_posts": 25
  }'
```

### Using Python requests:

```python
import requests

response = requests.post('http://localhost:8000/scrape', json={
    'subreddit_url': 'https://www.reddit.com/r/Fitness/',
    'max_posts': 25
})

data = response.json()
print(f"Scraped {data['total_posts']} posts")
```

### From Next.js frontend:

```typescript
const response = await fetch('http://localhost:8000/scrape', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    subreddit_url: 'https://www.reddit.com/r/Fitness/',
    max_posts: 25
  })
});

const data = await response.json();
console.log(`Scraped ${data.total_posts} posts`);
```

## Where Does the Data Go?

**Two places:**

1. **API Response** - Returns JSON directly in the response
2. **Saved File** - Automatically saves to `backend/data/` with format:
   - `Fitness_20241025_143022.json`
   - Format: `{subreddit}_{timestamp}.json`

## File Location

All scraped data is saved to:
```
backend/data/
├── Fitness_20241025_143022.json
├── python_20241025_150030.json
└── ...
```

The `data/` folder is git-ignored so scraped data won't be committed.

## Interactive Docs

Visit these URLs when the server is running:
- **Swagger UI**: http://localhost:8000/docs
- **API Info**: http://localhost:8000/
