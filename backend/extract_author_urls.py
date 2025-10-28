import json
import csv
from pathlib import Path

def extract_profile_urls(json_file_path, output_csv_path):
    """
    Extract all unique user profile URLs from keywords.json
    and save them to a CSV file with format: url,keyword (keyword blank)
    """
    profile_urls = set()

    print(f"Reading {json_file_path}...")

    # Read the large JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Processing {len(data)} posts...")

    # Iterate through all posts
    for post in data:
        # Skip error entries
        if 'error' in post:
            continue

        # Get user_posted (author of the post)
        if 'user_posted' in post and post['user_posted']:
            user = post['user_posted']
            if user != '[deleted]':
                profile_url = f"https://www.reddit.com/user/{user}/"
                profile_urls.add(profile_url)

        # Get user_url from comments
        if 'comments' in post and post['comments']:
            for comment in post['comments']:
                # Check user_url field
                if 'user_url' in comment and comment['user_url']:
                    url = comment['user_url']
                    # Skip invalid/undefined URLs
                    if 'undefined' not in url and 'reddit.com/user/' in url:
                        profile_urls.add(url)

                # Also check user_commenting to build URL
                if 'user_commenting' in comment and comment['user_commenting']:
                    user = comment['user_commenting']
                    if user != '[deleted]':
                        profile_url = f"https://www.reddit.com/user/{user}/"
                        profile_urls.add(profile_url)

                # Process nested replies recursively
                if 'replies' in comment and comment['replies']:
                    process_replies(comment['replies'], profile_urls)

    # Sort URLs for consistency
    sorted_urls = sorted(list(profile_urls))

    print(f"Found {len(sorted_urls)} unique profile URLs")

    # Write to CSV
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['url', 'keyword'])

        for url in sorted_urls:
            writer.writerow([url, ''])  # keyword is blank

    print(f"Saved to {output_csv_path}")
    return len(sorted_urls)

def process_replies(replies, profile_urls):
    """Recursively process nested comment replies"""
    for reply in replies:
        if 'user_url' in reply and reply['user_url']:
            url = reply['user_url']
            if 'undefined' not in url and 'reddit.com/user/' in url:
                profile_urls.add(url)

        if 'user_commenting' in reply and reply['user_commenting']:
            user = reply['user_commenting']
            if user != '[deleted]':
                profile_url = f"https://www.reddit.com/user/{user}/"
                profile_urls.add(profile_url)

        if 'replies' in reply and reply['replies']:
            process_replies(reply['replies'], profile_urls)

if __name__ == '__main__':
    json_file = Path('data/keywords.json')
    output_file = Path('author_profile_urls.csv')

    count = extract_profile_urls(json_file, output_file)
    print(f"\n✓ Extracted {count} unique author profile URLs")
