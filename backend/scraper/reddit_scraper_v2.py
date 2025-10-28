from typing import List
from models.reddit_post import RedditPost, Comment
from utils.parsers import parse_upvotes, clean_text
from scraper.brightdata_client import BrightDataClient


class RedditScraperV2:
    """Reddit scraper using Bright Data Dataset API"""

    def __init__(self):
        self.client = BrightDataClient()

    async def scrape_subreddit(
        self,
        subreddit_url: str,
        max_posts: int = 25,
        sort_by: str = "Top",
        sort_by_time: str = "Today",
        keyword: str = ""
    ) -> List[RedditPost]:
        """
        Scrape posts from a subreddit using Bright Data's Dataset API.

        Args:
            subreddit_url: URL of the subreddit
            max_posts: Maximum number of posts to scrape
            sort_by: Sort method (Hot, Top, New, Rising)
            sort_by_time: Time filter (Today, This Week, This Month, All Time)
            keyword: Optional keyword filter

        Returns:
            List of RedditPost objects
        """
        print(f"Scraping {subreddit_url} via Bright Data API...")

        # Get posts from Bright Data
        posts_data = await self.client.scrape_subreddit(
            subreddit_url=subreddit_url,
            max_posts=max_posts,
            sort_by=sort_by,
            sort_by_time=sort_by_time,
            keyword=keyword
        )

        print(f"✓ Retrieved {len(posts_data)} posts from API")

        reddit_posts = []

        for idx, post_data in enumerate(posts_data):
            try:
                print(f"Processing post {idx + 1}/{len(posts_data)}: {post_data.get('title', '')[:50]}...")

                # Get full post URL
                post_url = post_data.get('url', '')

                # Scrape comments for this post
                comments = await self._scrape_post_comments(post_url)

                # Create RedditPost object
                reddit_post = RedditPost(
                    title=clean_text(post_data.get('title', '')),
                    body=clean_text(post_data.get('description', '') or ''),
                    author=clean_text(post_data.get('user_posted', 'unknown')),
                    upvotes=parse_upvotes(str(post_data.get('num_upvotes', 0))),
                    timestamp=post_data.get('date_posted', ''),
                    comments=comments[:25],
                    url=post_url
                )

                reddit_posts.append(reddit_post)
                print(f"✓ Processed with {len(comments)} comments")

            except Exception as e:
                print(f"✗ Error processing post: {e}")
                continue

        return reddit_posts

    async def _scrape_post_comments(self, post_url: str) -> List[Comment]:
        """
        Scrape comments from a specific post.

        Args:
            post_url: URL of the Reddit post

        Returns:
            List of Comment objects
        """
        try:
            # Get comments from Bright Data
            comments_data = await self.client.scrape_comments(
                post_url=post_url,
                days_back=365,
                load_all_replies=True,
                comment_limit=25
            )

            if not comments_data:
                return []

            # The API returns a single object with a 'replies' field
            # But we want top-level comments, not just replies
            # The comment_data itself IS a comment, and it has replies
            comments = []

            # If there's a main comment
            if comments_data.get('comment'):
                main_comment = Comment(
                    author=clean_text(comments_data.get('user_posted', 'unknown')),
                    body=clean_text(comments_data.get('comment', '')),
                    upvotes=parse_upvotes(str(comments_data.get('num_upvotes', 0))),
                    timestamp=comments_data.get('date_posted', '')
                )
                comments.append(main_comment)

            # Add replies as separate comments
            replies = comments_data.get('replies', [])
            for reply_data in replies[:24]:  # Max 24 more to keep total at 25
                try:
                    comment = Comment(
                        author=clean_text(reply_data.get('user_replying', 'unknown')),
                        body=clean_text(reply_data.get('reply', '')),
                        upvotes=parse_upvotes(str(reply_data.get('num_upvotes', 0))),
                        timestamp=reply_data.get('date_of_reply', '')
                    )
                    comments.append(comment)
                except Exception as e:
                    print(f"Error parsing comment: {e}")
                    continue

            return comments

        except Exception as e:
            print(f"Error scraping comments for {post_url}: {e}")
            return []
