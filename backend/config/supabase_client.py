"""
Supabase client configuration and initialization
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
def get_supabase_client() -> Client:
    """
    Create and return a Supabase client instance

    Returns:
        Client: Authenticated Supabase client

    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_KEY are not set
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "Missing Supabase credentials. "
            "Please set SUPABASE_URL and SUPABASE_KEY in your .env file"
        )

    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Singleton instance
_supabase_client: Client = None

def get_client() -> Client:
    """
    Get or create a singleton Supabase client instance

    Returns:
        Client: Shared Supabase client instance
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = get_supabase_client()
    return _supabase_client
