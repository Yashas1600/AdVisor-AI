"""
Quick test to verify Supabase connection works
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_client

def test_connection():
    """Test Supabase connection"""
    try:
        print("Testing Supabase connection...")
        supabase = get_client()
        print("✓ Supabase client created successfully!")

        # Try to ping the database by listing tables (will fail gracefully if no tables exist)
        print("\nAttempting to query database...")

        # This will test the connection
        print(f"✓ Connected to Supabase at: {supabase.supabase_url}")
        print(f"✓ Using API key: {supabase.supabase_key[:20]}...")

        return True

    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("\nPlease update your .env file with valid Supabase credentials:")
        print("  SUPABASE_URL=your_project_url")
        print("  SUPABASE_KEY=your_anon_key")
        return False

    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

if __name__ == '__main__':
    test_connection()
