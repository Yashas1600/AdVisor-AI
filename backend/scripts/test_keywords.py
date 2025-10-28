"""
Quick test to preview extracted keywords
"""
import json
import sys
from pathlib import Path
from collections import Counter

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from process_reddit_data import RedditDataProcessor

def preview_keywords():
    """Preview what keywords will be extracted"""
    processor = RedditDataProcessor()

    # Load data
    keywords_path = Path(__file__).parent.parent / "data" / "keywords.json"
    subreddits_path = Path(__file__).parent.parent / "data" / "subreddits.json"

    print("Loading data files...")
    with open(keywords_path, "r") as f:
        keywords_data = json.load(f)
    with open(subreddits_path, "r") as f:
        subreddits_data = json.load(f)

    # Combine all posts
    all_posts = keywords_data + subreddits_data
    valid_posts = [p for p in all_posts if "error" not in p]

    print(f"Loaded {len(valid_posts)} valid posts\n")

    # Extract keywords
    print("Extracting top 50 meaningful keywords...")
    keywords = processor.extract_top_keywords_from_posts(valid_posts, top_n=50)

    print(f"\nTop 50 Keywords:")
    print("=" * 60)
    for i, keyword in enumerate(keywords, 1):
        print(f"{i:2}. {keyword}")

    print("\n" + "=" * 60)
    print(f"Total unique keywords extracted: {len(keywords)}")

if __name__ == "__main__":
    preview_keywords()
