"""
Script to store Reddit post embeddings in Vector DB
Standalone script for testing/re-running just the embedding storage
"""
import json
import sys
import time
from pathlib import Path
from typing import List, Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from db import PersonaManager
from utils.openai_client import OpenAIClient


def store_post_embeddings(posts: List[Dict], max_posts: int = 100) -> int:
    """
    Store Reddit post embeddings in Vector DB

    Args:
        posts: List of Reddit posts
        max_posts: Maximum number of posts to process

    Returns:
        Number of embeddings stored
    """
    print("=" * 80)
    print("STORING REDDIT POST EMBEDDINGS")
    print("=" * 80)

    pm = PersonaManager()
    openai_client = OpenAIClient()

    stored_count = 0
    batch_embeddings = []

    # Filter posts with valid title AND community_name
    print("\n1. Filtering valid posts...")
    valid_posts = [
        p for p in posts
        if "error" not in p
        and p.get("title")
        and p.get("community_name")  # Must have community_name
    ][:max_posts]

    print(f"   ✓ Found {len(valid_posts)} valid posts with title and community_name")
    print(f"   Processing up to {max_posts} posts")

    if not valid_posts:
        print("\n❌ No valid posts found to process!")
        print("   Posts must have both 'title' and 'community_name' fields")
        return 0

    # Process in batches
    print(f"\n2. Generating embeddings and storing...")
    batch_size = 10
    total_batches = (len(valid_posts) - 1) // batch_size + 1

    for i in range(0, len(valid_posts), batch_size):
        batch = valid_posts[i : i + batch_size]
        batch_num = i // batch_size + 1

        try:
            print(f"\n   Batch {batch_num}/{total_batches} ({len(batch)} posts):")

            # Prepare texts for embedding
            texts = []
            valid_batch_posts = []

            for post in batch:
                community = post.get("community_name", "")
                # Additional safety check
                if not community:
                    print(f"     ⚠️  Skipping post with no community_name")
                    continue

                if not community.startswith("r/"):
                    community = f"r/{community}"

                title = post.get("title", "")
                description = post.get("description", "")
                text = f"{title}. {description[:200]}" if description else title

                texts.append(text)
                valid_batch_posts.append(post)

            if not texts:
                print(f"     ⚠️  No valid texts in batch, skipping")
                continue

            print(f"     Generating {len(texts)} embeddings...")
            # Generate embeddings in batch
            embeddings = openai_client.batch_generate_embeddings(texts)
            print(f"     ✓ Generated {len(embeddings)} embeddings")

            # Prepare data for batch insert
            for post, embedding, text in zip(valid_batch_posts, embeddings, texts):
                community = post.get("community_name", "")
                # Safety check again
                if not community:
                    continue
                if not community.startswith("r/"):
                    community = f"r/{community}"

                batch_embeddings.append(
                    {
                        "content_id": post.get("post_id", f"post_{i}"),
                        "content_type": "post",
                        "embedding": embedding,
                        "embedding_text": text[:500],  # Truncate very long texts
                        "community_name": community,
                        "metadata": {
                            "upvotes": post.get("num_upvotes", 0),
                            "num_comments": post.get("num_comments", 0),
                            "date_posted": post.get("date_posted"),
                            "url": post.get("url"),
                            "title": post.get("title", "")[:200],
                        },
                    }
                )

            print(f"     ✓ Prepared {len(batch_embeddings)} embeddings for storage")
            print(f"     Sample: {valid_batch_posts[0].get('title', '')[:60]}...")

            # Rate limit
            time.sleep(1)

        except Exception as e:
            print(f"     ✗ Error processing batch {batch_num}: {e}")
            import traceback
            traceback.print_exc()

    # Insert all embeddings at once
    print(f"\n3. Storing {len(batch_embeddings)} embeddings in database...")
    if batch_embeddings:
        try:
            pm.batch_store_reddit_embeddings(batch_embeddings)
            stored_count = len(batch_embeddings)
            print(f"   ✓ Successfully stored {stored_count} post embeddings")
        except Exception as e:
            print(f"   ✗ Error storing embeddings in database: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("   ⚠️  No embeddings to store")

    # Summary
    print("\n" + "=" * 80)
    print("EMBEDDING STORAGE COMPLETE!")
    print("=" * 80)
    print(f"Posts processed: {len(valid_posts)}")
    print(f"Embeddings stored: {stored_count}")
    print("=" * 80)

    return stored_count


def main():
    """Load Reddit data and store embeddings"""

    # Paths to data files
    data_dir = Path(__file__).parent.parent / "data"
    keywords_path = data_dir / "keywords.json"
    subreddits_path = data_dir / "subreddits.json"

    # Check if files exist
    if not keywords_path.exists():
        print(f"❌ Error: {keywords_path} not found")
        return

    if not subreddits_path.exists():
        print(f"❌ Error: {subreddits_path} not found")
        return

    # Load data
    print("\nLoading Reddit data files...")
    with open(keywords_path, "r") as f:
        keywords_data = json.load(f)
    print(f"  ✓ Loaded {len(keywords_data)} posts from keywords.json")

    with open(subreddits_path, "r") as f:
        subreddits_data = json.load(f)
    print(f"  ✓ Loaded {len(subreddits_data)} posts from subreddits.json")

    # Combine all posts
    all_posts = keywords_data + subreddits_data
    print(f"  ✓ Total posts: {len(all_posts)}")

    # Store embeddings
    store_post_embeddings(all_posts, max_posts=100)


if __name__ == "__main__":
    main()
