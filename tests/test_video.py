"""
Tests for Gemini video understanding, image analysis, and persona prompt integration.
Uses recorded fixtures instead of live API calls.
"""
import json
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

# Allow imports from backend/
BACKEND_DIR = str(Path(__file__).resolve().parent.parent / "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

# Set dummy env vars before any imports try to read them
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("OPENAI_API_KEY", "test-key")

# Mock heavy dependencies that aren't installed in test env
_MOCK_MODULES = [
    "supabase", "supabase.client", "supabase.lib", "supabase.lib.client_options",
    "moondream", "dotenv",
]
for mod in _MOCK_MODULES:
    if mod not in sys.modules:
        sys.modules[mod] = mock.MagicMock()

# Make supabase.create_client return a MagicMock
sys.modules["supabase"].create_client = mock.MagicMock(return_value=mock.MagicMock())

# Mock config module to prevent supabase import chain
_config_mock = mock.MagicMock()
_config_mock.get_client = mock.MagicMock(return_value=None)
_config_mock.get_supabase_client = mock.MagicMock(return_value=None)
sys.modules.setdefault("config", _config_mock)
sys.modules.setdefault("config.supabase_client", _config_mock)


# ---------------------------------------------------------------------------
# 1. VideoTimeline parsing from fixture
# ---------------------------------------------------------------------------

class TestVideoTimelineParsing:
    def setup_method(self):
        with open(FIXTURES_DIR / "gemini_video_response.json") as f:
            self.raw = json.load(f)

    def test_parse_timeline(self):
        from extractor.gemini_video import VideoTimeline
        timeline = VideoTimeline.model_validate(self.raw)
        assert len(timeline.scenes) == 5
        assert timeline.duration_seconds == 28.0
        assert timeline.pacing == "fast"
        assert timeline.aspect_ratio == "landscape"

    def test_scenes_have_timestamps(self):
        from extractor.gemini_video import VideoTimeline
        timeline = VideoTimeline.model_validate(self.raw)
        for scene in timeline.scenes:
            assert scene.end_seconds > scene.start_seconds
            assert isinstance(scene.description, str)
            assert len(scene.description) > 0

    def test_hook_present(self):
        from extractor.gemini_video import VideoTimeline
        timeline = VideoTimeline.model_validate(self.raw)
        assert len(timeline.hook) > 0
        assert "shoe" in timeline.hook.lower() or "lace" in timeline.hook.lower()

    def test_on_screen_text(self):
        from extractor.gemini_video import VideoTimeline
        timeline = VideoTimeline.model_validate(self.raw)
        assert len(timeline.on_screen_text) == 4
        assert timeline.on_screen_text[0].text == "PUSH YOUR LIMITS"

    def test_brand_and_cta_timestamps(self):
        from extractor.gemini_video import VideoTimeline
        timeline = VideoTimeline.model_validate(self.raw)
        assert timeline.brand_first_appearance == 16.5
        assert timeline.cta_first_appearance == 23.0

    def test_transcript_present(self):
        from extractor.gemini_video import VideoTimeline
        timeline = VideoTimeline.model_validate(self.raw)
        assert "FuelMax" in timeline.transcript

    def test_merge_with_opencv_features(self):
        from extractor.gemini_video import VideoTimeline, merge_with_opencv_features
        timeline = VideoTimeline.model_validate(self.raw)
        opencv = {"video": {"motion_intensity": 0.5, "cuts_per_min": 12.0}}
        merged = merge_with_opencv_features(timeline, opencv)
        assert "gemini_timeline" in merged
        assert merged["video"]["motion_intensity"] == 0.5
        assert merged["gemini_timeline"]["duration_seconds"] == 28.0


# ---------------------------------------------------------------------------
# 2. Gemini image response parsing
# ---------------------------------------------------------------------------

class TestGeminiImageParsing:
    def setup_method(self):
        with open(FIXTURES_DIR / "gemini_image_response.json") as f:
            self.raw = json.load(f)

    def test_matches_moondream_schema(self):
        """Gemini image output has the same keys as moondream."""
        expected_keys = {"summary", "caption", "brand", "product_category",
                         "extracted_text", "keywords", "cta", "target_audience"}
        assert set(self.raw.keys()) == expected_keys

    def test_keywords_are_list(self):
        assert isinstance(self.raw["keywords"], list)
        assert len(self.raw["keywords"]) >= 3

    def test_product_category(self):
        assert self.raw["product_category"] == "fitness"


# ---------------------------------------------------------------------------
# 3. Persona prompt includes timeline for video ads
# ---------------------------------------------------------------------------

class TestPersonaPromptVideoIntegration:
    def setup_method(self):
        with open(FIXTURES_DIR / "gemini_video_response.json") as f:
            self.timeline = json.load(f)

    def test_build_ad_prompt_with_timeline(self):
        from api.routes.analyze import _build_ad_prompt
        feature_vector = {
            "moondream": {
                "summary": "FuelMax energy drink ad",
                "caption": "Runner in the city",
                "cta": "Order now",
                "keywords": ["fitness", "energy"],
                "target_audience": "18-35 males",
            },
            "features": {
                "color": {"palette_hex": ["#FF0000", "#00FF00"], "colorfulness": 45.2},
                "layout": {"aspect_ratio": 1.78, "whitespace_ratio": 0.15},
            },
            "gemini_timeline": self.timeline,
        }
        prompt = _build_ad_prompt(feature_vector)

        assert "VIDEO TIMELINE" in prompt
        assert "28.0s" in prompt
        assert "fast" in prompt
        assert "Hook" in prompt
        assert "PUSH YOUR LIMITS" in prompt
        assert "fuelmax.com" in prompt.lower() or "FuelMax" in prompt

    def test_build_ad_prompt_without_timeline(self):
        from api.routes.analyze import _build_ad_prompt
        feature_vector = {
            "moondream": {"summary": "An image ad", "caption": "", "cta": "", "keywords": [], "target_audience": ""},
            "features": {"color": {"palette_hex": [], "colorfulness": 0}, "layout": {"aspect_ratio": 1.0, "whitespace_ratio": 0}},
        }
        prompt = _build_ad_prompt(feature_vector)
        assert "VIDEO TIMELINE" not in prompt
        assert "skip" not in prompt.lower()

    def test_prompt_includes_scene_descriptions(self):
        from api.routes.analyze import _build_ad_prompt
        feature_vector = {
            "moondream": {"summary": "test", "caption": "", "cta": "", "keywords": [], "target_audience": ""},
            "features": {"color": {"palette_hex": [], "colorfulness": 0}, "layout": {"aspect_ratio": 1.0, "whitespace_ratio": 0}},
            "gemini_timeline": self.timeline,
        }
        prompt = _build_ad_prompt(feature_vector)
        assert "runner" in prompt.lower()
        assert "hilltop" in prompt.lower()


# ---------------------------------------------------------------------------
# 4. Response schema includes skip_at_seconds and moment for video
# ---------------------------------------------------------------------------

class TestVideoResponseFields:
    def test_persona_result_has_video_fields(self):
        from api.routes.analyze import PersonaAnalysisResult
        result = PersonaAnalysisResult(
            persona_id="abc",
            persona_name="Test User",
            insight="Great ad",
            attention="full",
            skip_at_seconds=None,
            moment="The sunrise hilltop reveal at 15s",
        )
        assert result.skip_at_seconds is None
        assert result.moment == "The sunrise hilltop reveal at 15s"

    def test_persona_result_with_skip(self):
        from api.routes.analyze import PersonaAnalysisResult
        result = PersonaAnalysisResult(
            persona_id="xyz",
            persona_name="Bored Viewer",
            insight="Lost interest quickly",
            attention="ignore",
            skip_at_seconds=5.0,
            moment=None,
        )
        assert result.skip_at_seconds == 5.0
        assert result.moment is None

    def test_persona_result_backward_compat(self):
        """Old-style results without video fields still parse."""
        from api.routes.analyze import PersonaAnalysisResult
        result = PersonaAnalysisResult(
            persona_id="old",
            persona_name="Image Viewer",
            insight="Nice image",
            attention="partial",
        )
        assert result.skip_at_seconds is None
        assert result.moment is None


# ---------------------------------------------------------------------------
# 5. ExtractResponse schema includes gemini fields
# ---------------------------------------------------------------------------

class TestExtractResponseSchema:
    def test_gemini_fields_optional(self):
        from api.schemas import ExtractResponse, MediaInfo, ExtractFeatures
        resp = ExtractResponse(
            ad_id="test",
            media=MediaInfo(modality="image", width=100, height=100),
            features=ExtractFeatures(
                color={"colorfulness": 1.0, "mean_bgr": [0, 0, 0], "std_bgr": [0, 0, 0], "palette_hex": ["#000"] * 5},
                layout={"aspect_ratio": 1.0, "whitespace_ratio": 0.0},
            ),
        )
        assert resp.gemini is None
        assert resp.gemini_timeline is None

    def test_gemini_timeline_in_response(self):
        from api.schemas import ExtractResponse, MediaInfo, ExtractFeatures, GeminiTimeline
        timeline = GeminiTimeline(
            scenes=[],
            hook="test hook",
            duration_seconds=30.0,
            pacing="fast",
        )
        resp = ExtractResponse(
            ad_id="test",
            media=MediaInfo(modality="video", width=1920, height=1080, duration_ms=30000, fps=30.0),
            features=ExtractFeatures(
                color={"colorfulness": 1.0, "mean_bgr": [0, 0, 0], "std_bgr": [0, 0, 0], "palette_hex": ["#000"] * 5},
                layout={"aspect_ratio": 1.78, "whitespace_ratio": 0.1},
            ),
            gemini_timeline=timeline,
        )
        assert resp.gemini_timeline is not None
        assert resp.gemini_timeline.hook == "test hook"
        assert resp.gemini_timeline.duration_seconds == 30.0
