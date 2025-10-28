"""
Process Reddit data from keywords.json and subreddits.json
Enriches with OpenAI GPT and stores in Knowledge Graph + Vector DB
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Set
from collections import Counter
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from db import PersonaManager, KnowledgeGraph, VectorStore
from utils.openai_client import OpenAIClient


class RedditDataProcessor:
    """
    Process Reddit scraped data and populate KG + Vector DB
    """

    def __init__(self):
        self.pm = PersonaManager()
        self.kg = KnowledgeGraph()
        self.vs = VectorStore()
        self.openai = OpenAIClient()

        # Track created entities to avoid duplicates
        self.created_communities = {}  # name -> id
        self.created_interests = {}  # label -> id
        self.created_personas = {}  # name -> id

    # ========================================================================
    # COMMUNITY EXTRACTION & ENRICHMENT
    # ========================================================================

    def extract_communities_from_posts(self, posts: List[Dict]) -> Dict[str, List[str]]:
        """
        Extract unique communities and sample posts for each

        Returns:
            Dict mapping community_name -> list of post titles
        """
        community_posts = {}

        for post in posts:
            if "error" in post or "community_name" not in post:
                continue

            community = post.get("community_name", "")
            if not community:
                continue

            # Normalize community name
            if not community.startswith("r/"):
                community = f"r/{community}"

            if community not in community_posts:
                community_posts[community] = []

            # Collect sample post titles
            title = post.get("title", "")
            if title and len(community_posts[community]) < 20:
                community_posts[community].append(title)

        return community_posts

    def create_enriched_community(self, community_name: str, sample_posts: List[str]) -> str:
        """
        Create community in KG with GPT enrichment and embedding

        Returns:
            community_id
        """
        # Check if already exists
        existing = self.kg.get_community_by_name(community_name)
        if existing:
            print(f"  ✓ Community {community_name} already exists")
            return existing["id"]

        print(f"  Enriching community: {community_name}")

        try:
            # Use GPT to generate community profile
            profile = self.openai.generate_community_summary(
                community_name=community_name, sample_posts=sample_posts
            )

            # Create description text for embedding
            description_text = f"{community_name}: {profile['description']}. Audience: {profile['audience_type']}. Tone: {profile['tone']}."

            # Generate embedding
            embedding = self.openai.generate_embedding(description_text)

            # Create community in KG + Vector DB
            community = self.pm.create_community_full(
                name=community_name,
                description=profile["description"],
                embedding=embedding,
                platform="reddit",
                activity_level=profile.get("activity_level", "medium"),
                topic_categories=profile.get("topic_categories", []),
            )

            print(f"  ✓ Created community: {community_name} (ID: {community['id']})")
            return community["id"]

        except Exception as e:
            print(f"  ✗ Error creating community {community_name}: {e}")
            # Fallback: create basic community
            community = self.kg.create_community(
                name=community_name,
                platform="reddit",
                description=f"Community for {community_name}",
            )
            return community["id"] if community else None

    # ========================================================================
    # INTEREST EXTRACTION
    # ========================================================================

    def extract_top_keywords_from_posts(self, posts: List[Dict], top_n: int = 50) -> List[str]:
        """
        Extract meaningful keywords from post titles
        Filters out common stopwords and Reddit-specific jargon

        Returns:
            List of top meaningful keywords
        """
        word_counts = Counter()

        # Comprehensive stopwords list (common words + Reddit jargon)
        stopwords = {
            # Common English stopwords
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
            "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
            "did", "will", "would", "should", "could", "may", "might", "can", "this", "that", "these",
            "those", "i", "you", "he", "she", "it", "we", "they", "what", "which", "who", "when",
            "where", "why", "how", "my", "your", "me", "from", "just", "so", "not", "all", "any",
            "about", "after", "also", "am", "as", "because", "before", "both", "by", "come", "each",
            "even", "get", "give", "go", "her", "him", "his", "if", "into", "let", "make", "more",
            "most", "much", "no", "now", "only", "other", "out", "over", "said", "see", "than",
            "them", "then", "there", "their", "up", "use", "very", "want", "way", "well", "went",
            "while", "who", "with", "yes", "yet", "some", "such", "take", "tell", "than", "them",
            "then", "there", "these", "they", "thing", "think", "time", "two", "under", "until",

            # Time/quantity words (too generic)
            "years", "year", "months", "month", "weeks", "week", "days", "day", "hours", "hour",
            "ago", "old", "first", "second", "last", "next", "many", "few", "lot", "lots",

            # Reddit-specific jargon
            "aita", "tifu", "update", "edit", "deleted", "removed", "post", "posts", "reddit",
            "redditor", "redditors", "comment", "comments", "thread", "subreddit", "upvote",
            "downvote", "karma", "meta", "throwaway",

            # Vague/generic verbs and actions
            "dont", "doesnt", "didnt", "wont", "cant", "wasnt", "werent", "isnt", "arent",
            "need", "needs", "needed", "know", "knows", "knew", "like", "liked", "likes",
            "got", "get", "gets", "getting", "made", "make", "makes", "making", "told", "tell",
            "asked", "ask", "asks", "said", "says", "say", "saying", "trying", "tried", "try",
            "going", "goes", "went", "doing", "done", "having", "found", "find", "finds",
            "finding", "told", "telling", "tells", "taken", "takes", "took", "given", "gives",
            "gave", "started", "start", "starts", "starting", "stopped", "stop", "stops",
            "wanted", "wants", "wanting",

            # Generic pronouns/possessives
            "someone", "anyone", "everyone", "something", "anything", "everything", "somebody",
            "anybody", "everybody", "mine", "yours", "hers", "ours", "theirs",

            # Generic descriptors/adverbs
            "people", "person", "today", "every", "never", "always", "really", "actually",
            "still", "finally", "better", "through", "without", "during", "please", "youre",
            "heres", "thats", "whats", "theres", "things", "thing", "watch", "story",
            "aitah",  # Another AITA variant
            "since", "instead", "right", "wrong", "called", "around", "later", "share",
            "almost", "again", "personal", "myself", "working", "taking", "final",
            "match",  # Too generic
        }

        for post in posts:
            if "error" in post or "title" not in post:
                continue

            title = post.get("title", "").lower()
            words = title.split()

            for word in words:
                # Clean word - only alphanumeric
                word = "".join(char for char in word if char.isalnum())

                # Filter criteria:
                # - Must be at least 5 characters (more meaningful)
                # - Not in stopwords list
                # - Must contain at least one vowel (filter acronyms/abbreviations)
                # - Not purely numeric
                if (len(word) >= 5 and
                    word not in stopwords and
                    any(c in word for c in 'aeiou') and
                    not word.isdigit()):
                    word_counts[word] += 1

        return [word for word, count in word_counts.most_common(top_n)]

    def create_interests_from_keywords(self, keywords: List[str], max_interests: int = 30) -> List[str]:
        """
        Create interests in KG from keywords (batched)

        Returns:
            List of interest IDs
        """
        interest_ids = []

        print(f"\nGenerating {min(max_interests, len(keywords))} interests from top keywords...")

        # Process in batches
        batch_size = 5
        for i in range(0, min(max_interests, len(keywords)), batch_size):
            batch_keywords = keywords[i : i + batch_size]

            for keyword in batch_keywords:
                # Check if already exists
                existing_interests = self.kg.list_interests()
                existing_labels = {int["label"].lower() for int in existing_interests}

                if keyword.lower() in existing_labels:
                    print(f"  ✓ Interest '{keyword}' already exists")
                    continue

                try:
                    # Use GPT to generate interests
                    interests_data = self.openai.generate_interests_from_keyword(keyword, count=1)

                    for interest_data in interests_data:
                        interest = self.kg.create_interest(
                            label=interest_data["label"],
                            category=interest_data.get("category", "topic"),
                            description=interest_data.get("description", ""),
                            keywords=interest_data.get("keywords", [keyword]),
                        )

                        if interest:
                            interest_ids.append(interest["id"])
                            print(f"  ✓ Created interest: {interest_data['label']}")

                except Exception as e:
                    print(f"  ✗ Error creating interest for '{keyword}': {e}")

                # Rate limit
                time.sleep(0.5)

        return interest_ids

    # ========================================================================
    # PERSONA GENERATION
    # ========================================================================

    def generate_personas_for_community(
        self, community_name: str, community_id: str, sample_posts: List[str], personas_per_community: int = 50
    ) -> List[str]:
        """
        Generate and store personas for a single community
        Commits to database immediately after completion

        Args:
            community_name: Name of the community (e.g., "r/Fitness")
            community_id: Database ID of the community
            sample_posts: Sample post titles from the community
            personas_per_community: Number of diverse personas to generate

        Returns:
            List of persona IDs created
        """
        persona_ids = []

        try:
            # Extract main topic from community name
            topic = community_name.replace("r/", "").replace("_", " ")

            print(f"\n  Processing {community_name} - generating {personas_per_community} diverse personas...")

            # Generate personas in batches of 10 to avoid timeouts
            batch_size = 10
            num_batches = (personas_per_community + batch_size - 1) // batch_size

            all_personas = []
            for batch_idx in range(num_batches):
                batch_count = min(batch_size, personas_per_community - len(all_personas))
                print(f"    Batch {batch_idx + 1}/{num_batches}: Generating {batch_count} personas...")

                personas_batch = self.openai.generate_diverse_personas_batch(
                    keyword=topic,
                    sample_posts=sample_posts,
                    count=batch_count
                )

                all_personas.extend(personas_batch)
                print(f"    ✓ Generated {batch_count} personas (total: {len(all_personas)}/{personas_per_community})")

                # Small delay between batches
                time.sleep(1)

            # Create embeddings for all personas
            print(f"    Creating embeddings for {len(all_personas)} personas...")
            summary_texts = [
                f"{p['summary']} Interests: {topic}. Pain points: {', '.join(p.get('pain_points', [])[:3])}."
                for p in all_personas
            ]

            embeddings = self.openai.batch_generate_embeddings(summary_texts)
            print(f"    ✓ Created {len(embeddings)} embeddings")

            # Create each persona in database
            print(f"    Storing personas in database...")
            print("    " + "=" * 76)
            personas_created = 0
            for idx, (persona_data, embedding) in enumerate(zip(all_personas, embeddings), 1):
                # Display persona details
                print(f"\n    PERSONA #{idx}/{len(all_personas)}: {persona_data['name']}")
                print(f"    {'-' * 76}")
                print(f"    📋 Summary: {persona_data['summary'][:100]}...")

                demographics = persona_data.get("demographics", {})
                print(f"    👤 Demographics:")
                print(f"       Age: {demographics.get('age', 'N/A')}, "
                      f"Gender: {demographics.get('gender', 'N/A')}, "
                      f"Income: {demographics.get('income_level', 'N/A')}")

                psychographics = persona_data.get("psychographics", {})
                values = psychographics.get("values", [])
                if values:
                    print(f"    🧠 Values: {', '.join(values[:3])}")

                pain_points = persona_data.get("pain_points", [])
                if pain_points:
                    print(f"    ⚡ Pain Points: {pain_points[0][:80]}...")

                motivations = persona_data.get("motivations", [])
                if motivations:
                    print(f"    🎯 Motivations: {motivations[0][:80]}...")

                persona = self.pm.create_persona_full(
                    name=persona_data["name"],
                    summary=persona_data["summary"],
                    embedding=embedding,
                    demographics=demographics,
                    psychographics=psychographics,
                    pain_points=pain_points,
                    motivations=motivations,
                    communities=[{
                        "community_id": community_id,
                        "relevance_score": 0.9,
                        "context": f"Active in {community_name}"
                    }] if community_id else [],
                )

                persona_ids.append(persona["id"])
                self.created_personas[persona_data["name"]] = persona["id"]
                personas_created += 1
                print(f"    ✅ Stored (ID: {persona['id']})")

            print("    " + "=" * 76)
            print(f"  ✓ Committed {personas_created} personas to database for {community_name}")

        except Exception as e:
            print(f"  ✗ Error generating personas for {community_name}: {e}")
            import traceback
            traceback.print_exc()

        return persona_ids

    # ========================================================================
    # CONTENT EMBEDDING STORAGE
    # ========================================================================

    def store_post_embeddings(self, posts: List[Dict], max_posts: int = 100) -> int:
        """
        Store Reddit post embeddings in Vector DB

        Returns:
            Number of embeddings stored
        """
        print(f"\nStoring post embeddings (max {max_posts})...")

        stored_count = 0
        batch_embeddings = []

        # Filter posts with valid title AND community_name
        valid_posts = [
            p for p in posts
            if "error" not in p
            and p.get("title")
            and p.get("community_name")  # Must have community_name
        ][:max_posts]

        print(f"  Found {len(valid_posts)} valid posts with title and community_name")

        # Process in batches
        batch_size = 10
        for i in range(0, len(valid_posts), batch_size):
            batch = valid_posts[i : i + batch_size]

            try:
                # Prepare texts for embedding
                texts = []
                for post in batch:
                    community = post.get("community_name", "")
                    # Additional safety check
                    if community and not community.startswith("r/"):
                        community = f"r/{community}"
                    elif not community:
                        continue  # Skip if still None

                    text = f"{post.get('title', '')}. {post.get('description', '')[:200]}"
                    texts.append(text)

                # Generate embeddings in batch
                embeddings = self.openai.batch_generate_embeddings(texts)

                # Prepare data for batch insert
                for post, embedding, text in zip(batch, embeddings, texts):
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
                            "embedding_text": text,
                            "community_name": community,
                            "metadata": {
                                "upvotes": post.get("num_upvotes", 0),
                                "num_comments": post.get("num_comments", 0),
                                "date_posted": post.get("date_posted"),
                                "url": post.get("url"),
                            },
                        }
                    )

                print(f"  ✓ Processed batch {i // batch_size + 1}/{(len(valid_posts) - 1) // batch_size + 1}")

                # Rate limit
                time.sleep(1)

            except Exception as e:
                print(f"  ✗ Error processing batch {i // batch_size + 1}: {e}")
                import traceback
                traceback.print_exc()

        # Insert all embeddings at once
        if batch_embeddings:
            try:
                self.pm.batch_store_reddit_embeddings(batch_embeddings)
                stored_count = len(batch_embeddings)
                print(f"  ✓ Stored {stored_count} post embeddings")
            except Exception as e:
                print(f"  ✗ Error storing embeddings: {e}")

        return stored_count

    # ========================================================================
    # MAIN PROCESSING PIPELINE
    # ========================================================================

    def process_json_files(
        self,
        keywords_path: str,
        subreddits_path: str,
        max_communities: int = 20,
        personas_per_community: int = 50,
        max_interests: int = 30,
        max_posts_to_embed: int = 100,
    ):
        """
        Main processing pipeline

        Args:
            keywords_path: Path to keywords.json
            subreddits_path: Path to subreddits.json
            max_communities: Maximum communities to process
            personas_per_community: Number of personas to generate per community
            max_interests: Maximum interests to create
            max_posts_to_embed: Maximum posts to store embeddings for
        """
        print("=" * 80)
        print("REDDIT DATA PROCESSING PIPELINE")
        print("=" * 80)

        # Load data
        print("\n1. Loading data files...")
        with open(keywords_path, "r") as f:
            keywords_data = json.load(f)
        with open(subreddits_path, "r") as f:
            subreddits_data = json.load(f)

        # Combine all posts
        all_posts = keywords_data + subreddits_data
        valid_posts = [p for p in all_posts if "error" not in p]

        print(f"  ✓ Loaded {len(valid_posts)} valid posts from {len(all_posts)} total")

        # Step 2: Extract communities
        print("\n2. Extracting and enriching communities...")
        community_posts = self.extract_communities_from_posts(valid_posts)
        print(f"  Found {len(community_posts)} unique communities")

        # Step 3: Extract keywords and create interests (before personas)
        print("\n3. Extracting keywords and creating interests...")
        top_keywords = self.extract_top_keywords_from_posts(valid_posts, top_n=50)
        print(f"  Extracted top {len(top_keywords)} keywords: {top_keywords[:10]}...")

        interest_ids = self.create_interests_from_keywords(top_keywords, max_interests=max_interests)
        print(f"  ✓ Created {len(interest_ids)} interests")

        # Step 4: Process each community individually (create community + personas)
        print(f"\n4. Processing top {max_communities} communities with {personas_per_community} personas each...")
        sorted_communities = sorted(community_posts.items(), key=lambda x: len(x[1]), reverse=True)

        all_persona_ids = []
        for idx, (community_name, sample_posts) in enumerate(sorted_communities[:max_communities], 1):
            print(f"\n[Community {idx}/{max_communities}] {community_name}")

            # Create enriched community first
            community_id = self.create_enriched_community(community_name, sample_posts)
            if community_id:
                self.created_communities[community_name] = community_id

            # Generate personas for this community and commit to DB
            if community_id:
                persona_ids = self.generate_personas_for_community(
                    community_name=community_name,
                    community_id=community_id,
                    sample_posts=sample_posts,
                    personas_per_community=personas_per_community
                )
                all_persona_ids.extend(persona_ids)
                print(f"  ✓ Progress: {len(all_persona_ids)}/{max_communities * personas_per_community} total personas created")

            time.sleep(1)  # Rate limit

        print(f"\n  ✓ All communities processed: {len(all_persona_ids)} total personas created")

        # Step 5: Store post embeddings
        stored_count = self.store_post_embeddings(valid_posts, max_posts=max_posts_to_embed)

        # Summary
        print("\n" + "=" * 80)
        print("PROCESSING COMPLETE!")
        print("=" * 80)
        print(f"Communities created: {len(self.created_communities)}")
        print(f"Interests created: {len(interest_ids)}")
        print(f"Personas created: {len(all_persona_ids)}")
        print(f"Post embeddings stored: {stored_count}")
        print("=" * 80)


def main():
    """Run the processing pipeline"""
    processor = RedditDataProcessor()

    # Paths
    keywords_path = Path(__file__).parent.parent / "data" / "keywords.json"
    subreddits_path = Path(__file__).parent.parent / "data" / "subreddits.json"

    # Process
    processor.process_json_files(
        keywords_path=str(keywords_path),
        subreddits_path=str(subreddits_path),
        max_communities=20,           # Process top 20 communities
        personas_per_community=50,    # Generate 50 personas PER community
        max_interests=30,             # Create 30 interests
        max_posts_to_embed=100,       # Store 100 post embeddings
    )
    # Total personas: 20 communities × 50 personas = 1,000 personas


if __name__ == "__main__":
    main()
