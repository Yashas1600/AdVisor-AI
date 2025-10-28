"""
Register all persona agents to Fetch.ai Agentverse
Makes them discoverable and accessible on the Agentverse platform
"""
import sys
from pathlib import Path
import json
from typing import List, Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from db.persona_manager import PersonaManager
from utils.agentverse_client import AgentverseClient


def register_all_personas_to_agentverse(
    base_endpoint: str = "http://localhost:8000",
    limit: int = None,
    save_results: bool = True
):
    """
    Register all personas as agents on Agentverse

    Args:
        base_endpoint: Base URL for agent API endpoints
        limit: Optional limit on number of personas to register (for testing)
        save_results: Whether to save results to JSON file
    """
    print("=" * 80)
    print("AGENTVERSE AGENT REGISTRATION")
    print("=" * 80)
    print()

    # Initialize clients
    print("1. Initializing clients...")
    pm = PersonaManager()
    av_client = AgentverseClient()
    print("   ✓ PersonaManager initialized")
    print("   ✓ AgentverseClient initialized")
    print()

    # Get all personas
    print("2. Fetching personas from Supabase...")
    personas = pm.list_personas(limit=1000)

    if limit:
        personas = personas[:limit]

    print(f"   ✓ Found {len(personas)} personas to register")
    print()

    # Prepare persona data for registration
    persona_list = []
    for p in personas:
        if p.get("id"):
            persona_list.append({
                "id": str(p.get("id")),
                "name": p.get("name", "Unknown"),
                "summary": p.get("summary", "")
            })

    print(f"3. Registering {len(persona_list)} agents to Agentverse...")
    print(f"   Base endpoint: {base_endpoint}")
    print(f"   Agent type: custom")
    print()

    # Register agents
    results = av_client.batch_register_personas(
        personas=persona_list,
        base_endpoint=base_endpoint
    )

    # Count successes and failures
    successes = sum(1 for r in results if r.get("success"))
    failures = len(results) - successes

    print()
    print("=" * 80)
    print("REGISTRATION SUMMARY")
    print("=" * 80)
    print(f"Total personas: {len(results)}")
    print(f"✓ Successful:   {successes}")
    print(f"✗ Failed:       {failures}")
    print()

    # Show failed registrations
    if failures > 0:
        print("Failed registrations:")
        for r in results:
            if not r.get("success"):
                print(f"  - {r.get('persona_name')} ({r.get('persona_id', 'unknown')[:8]}...)")
                if r.get("error"):
                    print(f"    Error: {r.get('error')}")
        print()

    # Save results
    if save_results:
        output_file = Path(__file__).parent.parent / "data" / "agentverse_registrations.json"
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"✓ Results saved to: {output_file}")
        print()

    # Show sample registered agents
    print("Sample registered agents:")
    for r in results[:5]:
        if r.get("success"):
            print(f"  - {r.get('persona_name')}")
            print(f"    Address: {r.get('agent_address')}")
            print(f"    ID: {r.get('persona_id')[:8]}...")
            print()

    print("=" * 80)
    print("✓ REGISTRATION COMPLETED")
    print("=" * 80)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Register persona agents to Agentverse")
    parser.add_argument(
        "--endpoint",
        type=str,
        default="http://localhost:8000",
        help="Base URL for agent API endpoints (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of agents to register (for testing)"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to JSON file"
    )

    args = parser.parse_args()

    # Run registration
    results = register_all_personas_to_agentverse(
        base_endpoint=args.endpoint,
        limit=args.limit,
        save_results=not args.no_save
    )

    # Exit with error code if any failed
    failed_count = sum(1 for r in results if not r.get("success"))
    sys.exit(1 if failed_count > 0 else 0)
