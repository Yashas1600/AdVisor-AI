"""Tests for the LLM provider abstraction layer."""

import os
import pytest

# Ensure mock provider is available without real API keys
os.environ.setdefault("LLM_PROVIDER", "mock")


def test_import_interface():
    from llm.interface import LLMProvider
    assert LLMProvider is not None


def test_import_router():
    from llm.router import get_provider
    assert callable(get_provider)


def test_mock_provider_via_router():
    from llm.router import get_provider
    provider = get_provider("mock")
    from llm.mock import MockProvider
    assert isinstance(provider, MockProvider)


@pytest.mark.asyncio
async def test_mock_generate_json():
    from llm.mock import MockProvider
    p = MockProvider(default_attention="ignore", default_insight="Test insight")
    result = await p.generate_json("sys", "usr", {"type": "object"})
    assert result["attention"] == "ignore"
    assert result["insight"] == "Test insight"
    assert len(p.calls) == 1


@pytest.mark.asyncio
async def test_mock_generate_text():
    from llm.mock import MockProvider
    p = MockProvider(default_insight="hello world")
    result = await p.generate_text("sys", "usr")
    assert result == "hello world"


@pytest.mark.asyncio
async def test_mock_analyze_image_with_schema():
    from llm.mock import MockProvider
    p = MockProvider()
    result = await p.analyze_image(b"\x00", "image/png", "describe", schema={"type": "object"})
    assert isinstance(result, dict)
    assert "description" in result


@pytest.mark.asyncio
async def test_mock_analyze_image_without_schema():
    from llm.mock import MockProvider
    p = MockProvider(default_insight="a cat")
    result = await p.analyze_image(b"\x00", "image/png", "describe")
    assert result == "a cat"


@pytest.mark.asyncio
async def test_mock_analyze_video():
    from llm.mock import MockProvider
    p = MockProvider()
    result = await p.analyze_video("/tmp/fake.mp4", "describe", schema={"type": "object"})
    assert isinstance(result, dict)


def test_unknown_provider_raises():
    from llm.router import get_provider
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_provider("nonexistent_provider_xyz")


def test_llm_package_exports():
    from llm import LLMProvider, get_provider
    assert LLMProvider is not None
    assert callable(get_provider)
