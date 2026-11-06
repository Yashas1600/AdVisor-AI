"""Shared fixtures for AdVisor tests.

The backend has deep import chains (supabase, openai, etc.) that aren't
installed in the test environment. We mock these at the sys.modules level
before any backend code is imported.
"""
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---- Module-level mocks for heavy dependencies ----
# These must be set BEFORE any backend module is imported.

_MOCK_MODULES = [
    "supabase",
    "moondream",
    "cv2",
    "pytesseract",
    "sklearn",
    "sklearn.cluster",
    "dateparser",
    "postgrest",
    "dotenv",
]

for mod_name in _MOCK_MODULES:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Set env vars early so singletons don't blow up
os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key")
os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "fake-supabase-key")

# Mock the db and config module trees to prevent Supabase client creation
mock_supabase_client_mod = MagicMock()
mock_supabase_client_mod.supabase_client = MagicMock()
sys.modules["db.supabase_client"] = mock_supabase_client_mod

mock_config_mod = MagicMock()
sys.modules["config.supabase_client"] = mock_config_mod
sys.modules["config"] = mock_config_mod

mock_db = MagicMock()
sys.modules["db"] = mock_db

# Mock the openai_client singleton module (uses httpx, not the openai package)
mock_openai_client_mod = MagicMock()
sys.modules["utils.openai_client"] = mock_openai_client_mod

# Mock fetchai client
sys.modules["utils.fetchai_client"] = MagicMock()


@pytest.fixture
def mock_env(monkeypatch):
    """Set required env vars for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key")
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "fake-supabase-key")
    monkeypatch.setenv("ADVISOR_CONCURRENCY", "5")
    monkeypatch.setenv("PERSONA_TIMEOUT", "5")


@pytest.fixture
def sample_feature_vector():
    """Minimal feature vector matching the API contract."""
    return {
        "moondream": {
            "summary": "A fitness ad showing a person running",
            "caption": "Get fit today",
            "cta": "Sign up now",
            "keywords": ["fitness", "running", "health"],
            "target_audience": "18-35 health-conscious adults",
        },
        "features": {
            "color": {
                "palette_hex": ["#FF5733", "#33FF57", "#3357FF"],
                "colorfulness": 0.65,
            },
            "layout": {
                "aspect_ratio": "16:9",
                "whitespace_ratio": 0.3,
            },
        },
    }


@pytest.fixture
def sample_personas():
    """List of fake persona records matching Supabase shape."""
    return [
        {
            "id": f"persona-{i:03d}",
            "name": f"Test Persona {i}",
            "summary": f"A test persona number {i}",
            "demographics": {"age_range": "18-24", "income_level": "middle"},
            "psychographics": {"values": ["health", "adventure"]},
            "pain_points": ["lack of time", "budget constraints"],
            "motivations": ["self-improvement", "social validation"],
        }
        for i in range(50)
    ]
