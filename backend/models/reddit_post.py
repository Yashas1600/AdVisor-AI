from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Comment(BaseModel):
    author: str
    body: str
    upvotes: int
    timestamp: str


class RedditPost(BaseModel):
    title: str
    body: Optional[str]
    author: str
    upvotes: int
    timestamp: str
    comments: List[Comment]
    url: str


class SubredditScrapeRequest(BaseModel):
    subreddit_url: str
    max_posts: int = 25
    sort_by: str = "Top"  # Hot, New, Top, Rising
    sort_by_time: str = "Today"  # Today, This Week, This Month, All Time
    keyword: str = ""


class SubredditScrapeResponse(BaseModel):
    subreddit: str
    posts: List[RedditPost]
    total_posts: int
