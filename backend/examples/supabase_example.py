"""
Example usage of Supabase client for AdVisor project
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config import get_client


def example_insert_reddit_post():
    """Example: Insert a Reddit post into Supabase"""
    supabase = get_client()

    # Example post data
    post_data = {
        "post_id": "t3_abc123",
        "title": "Example Reddit Post",
        "url": "https://www.reddit.com/r/example/comments/abc123/",
        "author": "example_user",
        "community": "example",
        "upvotes": 100,
        "num_comments": 25,
        "content": "This is an example post",
        "created_at": "2025-10-25T00:00:00Z"
    }

    # Insert into table (adjust table name as needed)
    response = supabase.table('reddit_posts').insert(post_data).execute()
    print(f"Inserted: {response.data}")


def example_query_posts():
    """Example: Query Reddit posts from Supabase"""
    supabase = get_client()

    # Query posts with filters
    response = supabase.table('reddit_posts') \
        .select("*") \
        .gte('upvotes', 50) \
        .limit(10) \
        .execute()

    print(f"Found {len(response.data)} posts with 50+ upvotes")
    return response.data


def example_insert_author_profile():
    """Example: Insert author profile data"""
    supabase = get_client()

    profile_data = {
        "username": "example_user",
        "profile_url": "https://www.reddit.com/user/example_user/",
        "scraped_at": "2025-10-25T00:00:00Z"
    }

    response = supabase.table('author_profiles').insert(profile_data).execute()
    print(f"Inserted profile: {response.data}")


def example_upsert_features():
    """Example: Upsert (insert or update) extracted features"""
    supabase = get_client()

    features_data = {
        "post_id": "t3_abc123",
        "sentiment_score": 0.85,
        "emotion_tags": ["joy", "excitement"],
        "visual_features": {"colors": ["blue", "white"], "objects": ["person", "car"]},
        "audio_features": None,
        "text_complexity": 0.72,
        "extracted_at": "2025-10-25T00:00:00Z"
    }

    response = supabase.table('post_features') \
        .upsert(features_data, on_conflict='post_id') \
        .execute()

    print(f"Upserted features: {response.data}")


if __name__ == '__main__':
    print("Supabase SDK Examples\n")

    try:
        # Uncomment to test specific examples
        # example_insert_reddit_post()
        # example_query_posts()
        # example_insert_author_profile()
        # example_upsert_features()

        print("Examples ready to run. Uncomment function calls to test.")

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. Set SUPABASE_URL and SUPABASE_KEY in your .env file")
        print("2. Created the necessary tables in your Supabase project")
