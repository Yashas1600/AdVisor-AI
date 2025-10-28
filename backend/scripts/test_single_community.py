"""
Test script to process a single community and display persona details
"""
import json
import sys
from pathlib import Path
from typing import List, Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from db import PersonaManager, KnowledgeGraph, VectorStore
from utils.openai_client import OpenAIClient


class SingleCommunityTest:
    """
    Test processing for a single community
    """

    def __init__(self):
        self.pm = PersonaManager()
        self.kg = KnowledgeGraph()
        self.vs = VectorStore()
        self.openai = OpenAIClient()

    def process_single_community(
        self, community_name: str, sample_posts: List[str], num_personas: int = 5
    ):
        """
        Process a single community and display all details

        Args:
            community_name: Name of the community (e.g., "r/Fitness")
            sample_posts: Sample post titles from the community
            num_personas: Number of personas to generate (default: 5 for testing)
        """
        print("=" * 80)
        print(f"TESTING SINGLE COMMUNITY: {community_name}")
        print("=" * 80)

        # Step 1: Create enriched community (or retrieve if exists)
        print(f"\n1. Creating/retrieving enriched community profile...")
        print(f"   Community: {community_name}")
        print(f"   Sample posts ({len(sample_posts)}):")
        for i, post in enumerate(sample_posts[:5], 1):
            print(f"     {i}. {post}")

        try:
            # Check if community already exists
            existing_community = self.kg.get_community_by_name(community_name)

            if existing_community:
                print(f"\n   ℹ️  Community already exists in database!")
                print(f"     Database ID: {existing_community['id']}")
                print(f"     Description: {existing_community.get('description', 'N/A')}")
                print(f"     Platform: {existing_community.get('platform', 'N/A')}")
                print(f"     Activity Level: {existing_community.get('activity_level', 'N/A')}")

                community_id = existing_community["id"]
            else:
                # Generate community profile with GPT
                profile = self.openai.generate_community_summary(
                    community_name=community_name, sample_posts=sample_posts
                )

                print(f"\n   ✓ Community Profile Generated:")
                print(f"     Description: {profile['description']}")
                print(f"     Audience Type: {profile['audience_type']}")
                print(f"     Tone: {profile['tone']}")
                print(f"     Activity Level: {profile.get('activity_level', 'medium')}")
                print(f"     Topic Categories: {', '.join(profile.get('topic_categories', []))}")

                # Create description for embedding
                description_text = f"{community_name}: {profile['description']}. Audience: {profile['audience_type']}. Tone: {profile['tone']}."

                # Generate embedding
                embedding = self.openai.generate_embedding(description_text)
                print(f"     Embedding dimension: {len(embedding)}")

                # Create community in database
                community = self.pm.create_community_full(
                    name=community_name,
                    description=profile["description"],
                    embedding=embedding,
                    platform="reddit",
                    activity_level=profile.get("activity_level", "medium"),
                    topic_categories=profile.get("topic_categories", []),
                )

                community_id = community["id"]
                print(f"     Database ID: {community_id}")

        except Exception as e:
            print(f"   ✗ Error creating community: {e}")
            import traceback
            traceback.print_exc()
            return

        # Step 2: Generate personas
        print(f"\n2. Generating {num_personas} diverse personas...")

        try:
            # Extract topic from community name
            topic = community_name.replace("r/", "").replace("_", " ")

            # Generate personas using GPT
            personas_data = self.openai.generate_diverse_personas_batch(
                keyword=topic, sample_posts=sample_posts, count=num_personas
            )

            print(f"   ✓ Generated {len(personas_data)} personas")

            # Create embeddings
            summary_texts = [
                f"{p['summary']} Interests: {topic}. Pain points: {', '.join(p.get('pain_points', [])[:3])}."
                for p in personas_data
            ]

            embeddings = self.openai.batch_generate_embeddings(summary_texts)
            print(f"   ✓ Created {len(embeddings)} embeddings")

        except Exception as e:
            print(f"   ✗ Error generating personas: {e}")
            import traceback
            traceback.print_exc()
            return

        # Step 3: Store personas and display details
        print(f"\n3. Storing personas in database and displaying details...")
        print("=" * 80)

        persona_ids = []
        for idx, (persona_data, embedding) in enumerate(zip(personas_data, embeddings), 1):
            print(f"\n{'=' * 80}")
            print(f"PERSONA #{idx}: {persona_data['name']}")
            print(f"{'=' * 80}")

            # Display full persona details
            print(f"\n📋 SUMMARY:")
            print(f"   {persona_data['summary']}")

            print(f"\n👤 DEMOGRAPHICS:")
            demographics = persona_data.get("demographics", {})
            for key, value in demographics.items():
                print(f"   {key.replace('_', ' ').title()}: {value}")

            print(f"\n🧠 PSYCHOGRAPHICS:")
            psychographics = persona_data.get("psychographics", {})
            for key, value in psychographics.items():
                if isinstance(value, list):
                    print(f"   {key.replace('_', ' ').title()}:")
                    for item in value:
                        print(f"     • {item}")
                else:
                    print(f"   {key.replace('_', ' ').title()}: {value}")

            print(f"\n⚡ PAIN POINTS:")
            for pain_point in persona_data.get("pain_points", []):
                print(f"   • {pain_point}")

            print(f"\n🎯 MOTIVATIONS:")
            for motivation in persona_data.get("motivations", []):
                print(f"   • {motivation}")

            print(f"\n🔢 EMBEDDING:")
            print(f"   Dimension: {len(embedding)}")
            print(f"   First 5 values: {embedding[:5]}")

            # Store in database
            try:
                persona = self.pm.create_persona_full(
                    name=persona_data["name"],
                    summary=persona_data["summary"],
                    embedding=embedding,
                    demographics=demographics,
                    psychographics=psychographics,
                    pain_points=persona_data.get("pain_points", []),
                    motivations=persona_data.get("motivations", []),
                    communities=[
                        {
                            "community_id": community_id,
                            "relevance_score": 0.9,
                            "context": f"Active in {community_name}",
                        }
                    ],
                )

                persona_ids.append(persona["id"])
                print(f"\n✅ STORED IN DATABASE:")
                print(f"   Database ID: {persona['id']}")
                print(f"   Created at: {persona.get('created_at', 'N/A')}")

            except Exception as e:
                print(f"\n❌ ERROR STORING PERSONA: {e}")
                import traceback
                traceback.print_exc()

        # Summary
        print("\n" + "=" * 80)
        print("TEST COMPLETE!")
        print("=" * 80)
        print(f"Community: {community_name}")
        print(f"Community ID: {community_id}")
        print(f"Personas created: {len(persona_ids)}")
        print(f"Persona IDs: {persona_ids}")
        print("=" * 80)


def main():
    """Run the single community test"""

    # Load data to get a real community example
    data_dir = Path(__file__).parent.parent / "data"
    keywords_path = data_dir / "keywords.json"

    # Check if data files exist
    if not keywords_path.exists():
        print(f"❌ Error: {keywords_path} not found")
        print("Please ensure Reddit data files exist in backend/data/")
        return

    # Load posts
    with open(keywords_path, "r") as f:
        posts = json.load(f)

    # Extract a community with good sample posts
    communities = {}
    for post in posts:
        if "error" in post or "community_name" not in post:
            continue

        community = post.get("community_name", "")
        if not community:
            continue

        if not community.startswith("r/"):
            community = f"r/{community}"

        if community not in communities:
            communities[community] = []

        title = post.get("title", "")
        if title and len(communities[community]) < 20:
            communities[community].append(title)

    # Find community with most posts
    if not communities:
        print("❌ Error: No valid communities found in data")
        return

    sorted_communities = sorted(communities.items(), key=lambda x: len(x[1]), reverse=True)
    test_community_name, test_sample_posts = sorted_communities[0]

    print(f"\nFound {len(communities)} communities in data")
    print(f"Testing with: {test_community_name} ({len(test_sample_posts)} sample posts)")

    # Run test
    tester = SingleCommunityTest()
    tester.process_single_community(
        community_name=test_community_name,
        sample_posts=test_sample_posts,
        num_personas=5,  # Generate 5 personas for testing
    )


if __name__ == "__main__":
    main()
