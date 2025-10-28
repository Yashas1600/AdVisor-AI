import os
import httpx
import asyncio
from typing import List, Dict, Any


class BrightDataClient:
    """Client for Bright Data Reddit Dataset API"""

    def __init__(self):
        self.api_key = os.getenv("BRIGHT_DATA_API_KEY")
        self.base_url = "https://api.brightdata.com/datasets/v3"
        self.subreddit_dataset_id = "gd_lvz8ah06191smkebj4"
        self.comments_dataset_id = "gd_lvzdpsdlw09j6t702"

    async def scrape_subreddit(
        self,
        subreddit_url: str,
        max_posts: int = 25,
        sort_by: str = "Top",
        sort_by_time: str = "Today",
        keyword: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Scrape posts from a subreddit using Bright Data's discover_by subreddit_url API.

        API Doc: Discover by subreddit URL allows sorting (new, top, hot) and filtering.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Build input payload according to API spec
        input_obj = {
            "url": subreddit_url,
            "sort_by": sort_by,
            "sort_by_time": sort_by_time,
            "num_of_posts": max_posts,
            "keyword": keyword
        }

        payload = {
            "input": [input_obj]
        }

        # Step 1: Trigger the scrape using synchronous scrape endpoint
        scrape_url = f"{self.base_url}/scrape?dataset_id={self.subreddit_dataset_id}&include_errors=true&type=discover_new&discover_by=subreddit_url&format=json"

        async with httpx.AsyncClient(timeout=600.0) as client:
            print(f"Scraping {subreddit_url}...")
            print(f"Parameters: sort_by={sort_by}, num_of_posts={max_posts}")

            response = await client.post(scrape_url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()

            if isinstance(data, list):
                print(f"✓ Successfully scraped {len(data)} posts")
                return data
            else:
                print(f"Unexpected response format: {type(data)}")
                print(f"Response: {data}")
                return []

    async def scrape_comments(
        self,
        post_url: str,
        days_back: int = 365,
        load_all_replies: bool = True,
        comment_limit: int = 25
    ) -> Dict[str, Any]:
        """
        Scrape comments from a specific Reddit post using Comments API.

        API Doc: Collect by URL allows filtering by days_back and comment limits.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Build input according to API spec
        input_obj = {
            "url": post_url,
            "load_all_replies": load_all_replies
        }

        # Add optional parameters
        if days_back:
            input_obj["days_back"] = days_back
        if comment_limit:
            input_obj["comment_limit"] = comment_limit

        payload = {
            "input": [input_obj]
        }

        # Use synchronous scrape endpoint
        scrape_url = f"{self.base_url}/scrape?dataset_id={self.comments_dataset_id}&include_errors=true&format=json"

        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(scrape_url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()

            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return None
