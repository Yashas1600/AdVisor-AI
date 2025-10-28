"""
Quick test script for Persona Agent API
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_list_personas():
    """Test listing available personas"""
    print("\n" + "=" * 80)
    print("TEST: List Available Personas")
    print("=" * 80)

    response = requests.get(f"{BASE_URL}/agents/personas")
    if response.status_code == 200:
        personas = response.json()
        print(f"✓ Found {len(personas)} personas")
        for i, persona in enumerate(personas[:5], 1):
            print(f"{i}. {persona['name']}")
            print(f"   {persona['summary'][:80]}...")
        return personas[0]["id"] if personas else None
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
        return None


def test_chat(persona_id):
    """Test chatting with a persona"""
    print("\n" + "=" * 80)
    print("TEST: Chat with Persona")
    print("=" * 80)

    data = {
        "persona_id": persona_id,
        "message": "What are your thoughts on productivity apps?",
        "include_retrieval": True
    }

    response = requests.post(f"{BASE_URL}/agents/chat", json=data)
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Response from: {result['persona_name']}")
        print(f"\n{result['response'][:300]}...\n")
        if result['retrieved_context']:
            print(f"Retrieved {len(result['retrieved_context'])} context items")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)


def test_analyze_ad(persona_id):
    """Test ad analysis"""
    print("\n" + "=" * 80)
    print("TEST: Analyze Ad Creative")
    print("=" * 80)

    ad = """
    A productivity app for remote workers featuring:
    - AI-powered task prioritization
    - Automated meeting scheduling
    - Focus time blocking
    - Team collaboration tools

    Tagline: "Work smarter, not harder. Let AI optimize your day."

    Visual: Professional working from a coffee shop with laptop
    """

    data = {
        "ad_description": ad,
        "persona_id": persona_id
    }

    response = requests.post(f"{BASE_URL}/agents/analyze-ad", json=data)
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Analysis from: {result['persona_name']}")
        print(f"\n{result['analysis'][:400]}...\n")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)


def test_multi_persona_analysis():
    """Test multi-persona ad analysis"""
    print("\n" + "=" * 80)
    print("TEST: Multi-Persona Ad Analysis")
    print("=" * 80)

    ad = """
    Email marketing platform for small businesses:
    - Drag-and-drop email builder
    - Automated campaigns
    - A/B testing
    - Analytics dashboard

    Tagline: "Professional email marketing made simple"
    """

    data = {
        "ad_description": ad,
        "num_personas": 3
    }

    response = requests.post(f"{BASE_URL}/agents/analyze-ad-multi", json=data)
    if response.status_code == 200:
        results = response.json()
        print(f"✓ Got {len(results)} persona analyses\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['persona_name']}")
            print(f"   {result['analysis'][:150]}...\n")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)


def test_get_context(persona_id):
    """Test getting persona context"""
    print("\n" + "=" * 80)
    print("TEST: Get Persona Context")
    print("=" * 80)

    response = requests.get(f"{BASE_URL}/agents/persona/{persona_id}/context")
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Context for persona {persona_id}")
        print(f"\n{result['context'][:400]}...\n")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)


def test_similar_personas(persona_id):
    """Test finding similar personas"""
    print("\n" + "=" * 80)
    print("TEST: Find Similar Personas")
    print("=" * 80)

    response = requests.get(f"{BASE_URL}/agents/persona/{persona_id}/similar?k=3")
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Similar to: {result['persona_name']}\n")
        for persona in result['similar_personas']:
            print(f"- {persona['name']} (similarity: {persona['similarity_score']:.3f})")
            print(f"  {persona['summary'][:80]}...\n")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)


def main():
    print("\n" + "=" * 80)
    print("PERSONA AGENT API TEST SUITE")
    print("=" * 80)
    print("\nMake sure the API server is running:")
    print("  cd backend && uvicorn main:app --reload\n")

    try:
        # Test 1: List personas
        persona_id = test_list_personas()

        if not persona_id:
            print("\n✗ No personas found. Run migration first.")
            return

        # Test 2: Chat
        test_chat(persona_id)

        # Test 3: Single persona ad analysis
        test_analyze_ad(persona_id)

        # Test 4: Multi-persona analysis
        test_multi_persona_analysis()

        # Test 5: Get context
        test_get_context(persona_id)

        # Test 6: Similar personas
        test_similar_personas(persona_id)

        print("\n" + "=" * 80)
        print("✓ ALL TESTS COMPLETED")
        print("=" * 80)

    except requests.exceptions.ConnectionError:
        print("\n✗ Connection Error: Make sure the API server is running")
        print("  Run: cd backend && uvicorn main:app --reload")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
