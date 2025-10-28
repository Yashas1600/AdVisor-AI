"""
Analyze posts per subreddit in 100_subreddits.json
"""
import json
import re
from collections import Counter
from pathlib import Path

# Read the JSON file
json_file = Path(__file__).parent / "100_subreddits.json"

print("Reading 100_subreddits.json...")
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total posts: {len(data)}")

# Extract subreddit from each post URL
subreddit_counts = Counter()

for item in data:
    if isinstance(item, dict) and 'url' in item:
        url = item['url']
        # Extract subreddit from URL like: https://www.reddit.com/r/SUBREDDIT/comments/...
        match = re.search(r'/r/([^/]+)/', url)
        if match:
            subreddit = match.group(1)
            subreddit_counts[subreddit] += 1

print(f"\nTotal unique subreddits: {len(subreddit_counts)}")
print(f"\nPosts per subreddit:")
print("-" * 50)

# Sort by count descending
for subreddit, count in subreddit_counts.most_common():
    print(f"{subreddit:30} {count:4} posts")

print("-" * 50)
print(f"\nAverage posts per subreddit: {len(data) / len(subreddit_counts):.1f}")
