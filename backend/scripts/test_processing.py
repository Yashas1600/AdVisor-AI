"""
Quick test script for Reddit data processing
Tests OpenAI integration and small-scale processing
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.openai_client import OpenAIClient


def test_openai_connection():
    """Test OpenAI API connection"""
    print("\n" + "=" * 60)
    print("TEST 1: OpenAI Connection")
    print("=" * 60)

    try:
        client = OpenAIClient()
        print("✓ OpenAI client initialized")

        # Test basic generation
        response = client.generate_response("Say 'Hello from GPT!'", max_tokens=20)
        print(f"✓ GPT Response: {response}")

        # Test embedding
        embedding = client.generate_embedding("Test text for embedding")
        print(f"✓ Embedding generated: {len(embedding)} dimensions")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_persona_generation():
    """Test persona generation from keyword"""
    print("\n" + "=" * 60)
    print("TEST 2: Persona Generation")
    print("=" * 60)

    try:
        client = OpenAIClient()

        persona_data = client.generate_persona_from_keyword(
            keyword="fitness", related_terms=["gym", "protein", "workout"]
        )

        print(f"✓ Generated persona: {persona_data['name']}")
        print(f"  Summary: {persona_data['summary'][:100]}...")
        print(f"  Demographics: {persona_data.get('demographics', {})}")
        print(f"  Pain points: {persona_data.get('pain_points', [])[:2]}")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_community_enrichment():
    """Test community summary generation"""
    print("\n" + "=" * 60)
    print("TEST 3: Community Enrichment")
    print("=" * 60)

    try:
        client = OpenAIClient()

        sample_posts = [
            "What protein powder do you recommend?",
            "Best budget gym for students?",
            "How to stay motivated?",
        ]

        community_data = client.generate_community_summary(community_name="r/Fitness", sample_posts=sample_posts)

        print(f"✓ Generated community profile for r/Fitness")
        print(f"  Description: {community_data['description']}")
        print(f"  Topics: {community_data.get('topic_categories', [])}")
        print(f"  Audience: {community_data.get('audience_type', 'N/A')}")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_interest_generation():
    """Test interest generation"""
    print("\n" + "=" * 60)
    print("TEST 4: Interest Generation")
    print("=" * 60)

    try:
        client = OpenAIClient()

        interests = client.generate_interests_from_keyword(keyword="protein", count=2)

        print(f"✓ Generated {len(interests)} interests:")
        for interest in interests:
            print(f"  - {interest['label']}: {interest.get('description', 'N/A')[:80]}...")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_batch_embeddings():
    """Test batch embedding generation"""
    print("\n" + "=" * 60)
    print("TEST 5: Batch Embeddings")
    print("=" * 60)

    try:
        client = OpenAIClient()

        texts = [
            "Best protein powder for muscle building",
            "Budget gym memberships for college students",
            "How to stay motivated at the gym",
        ]

        embeddings = client.batch_generate_embeddings(texts)

        print(f"✓ Generated {len(embeddings)} embeddings")
        print(f"  Each embedding: {len(embeddings[0])} dimensions")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("REDDIT DATA PROCESSING - TEST SUITE")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("OpenAI Connection", test_openai_connection()))
    results.append(("Persona Generation", test_persona_generation()))
    results.append(("Community Enrichment", test_community_enrichment()))
    results.append(("Interest Generation", test_interest_generation()))
    results.append(("Batch Embeddings", test_batch_embeddings()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Ready to process Reddit data.")
        print("\nNext step: Run 'python scripts/process_reddit_data.py'")
    else:
        print("\n⚠️  Some tests failed. Check your .env file and API keys.")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
