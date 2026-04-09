"""Tests for _image_analysis module."""

import pytest

from _image_analysis import (
    analyze_image_bytes,
    compute_visual_hash,
    image_coverage_ratio,
    image_dominant_color_ratio,
    image_file_size_key,
    image_page_dimensions,
    image_visual_key,
    is_background_candidate,
)


# ---------------------------------------------------------------------------
# compute_visual_hash
# ---------------------------------------------------------------------------

class TestComputeVisualHash:
    def test_returns_none_for_empty(self):
        assert compute_visual_hash([]) is None

    def test_returns_hex_string(self):
        result = compute_visual_hash([100, 200, 50, 150])
        assert result is not None
        assert isinstance(result, str)
        # Should be zero-padded hex
        int(result, 16)  # Should not raise

    def test_all_same_values(self):
        result = compute_visual_hash([128, 128, 128, 128])
        assert result is not None

    def test_deterministic(self):
        samples = [10, 20, 30, 40, 50, 60, 70, 80]
        assert compute_visual_hash(samples) == compute_visual_hash(samples)

    def test_different_inputs_different_hashes(self):
        a = compute_visual_hash([0, 0, 0, 255, 255, 255, 0, 0])
        b = compute_visual_hash([255, 255, 255, 0, 0, 0, 255, 255])
        assert a != b

    def test_padded_to_16_chars(self):
        # With small samples the numeric value is small, should still be padded
        result = compute_visual_hash([0, 1])
        assert result is not None
        assert len(result) == 16

    def test_single_sample(self):
        result = compute_visual_hash([42])
        assert result is not None


# ---------------------------------------------------------------------------
# analyze_image_bytes — pymupdf unavailable path
# ---------------------------------------------------------------------------

class TestAnalyzeImageBytes:
    def test_returns_empty_when_pymupdf_unavailable(self, monkeypatch):
        import _image_analysis
        monkeypatch.setattr(_image_analysis, "pymupdf", None)
        assert analyze_image_bytes(b"\x00\x01\x02") == {}

    def test_returns_empty_for_invalid_bytes(self):
        # Even if pymupdf is available, garbage bytes should return {}
        result = analyze_image_bytes(b"not-an-image")
        # Result is either {} (pymupdf fails) or a dict with keys
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# image_file_size_key
# ---------------------------------------------------------------------------

class TestImageFileSizeKey:
    def test_returns_int(self):
        assert image_file_size_key({"file_size": 1024}) == 1024

    def test_coerces_float(self):
        assert image_file_size_key({"file_size": 1024.5}) == 1024

    def test_returns_none_when_missing(self):
        assert image_file_size_key({}) is None

    def test_returns_none_when_none(self):
        assert image_file_size_key({"file_size": None}) is None

    def test_coerces_string(self):
        assert image_file_size_key({"file_size": "2048"}) == 2048


# ---------------------------------------------------------------------------
# image_visual_key
# ---------------------------------------------------------------------------

class TestImageVisualKey:
    def test_returns_string(self):
        assert image_visual_key({"visual_hash": "abc123"}) == "abc123"

    def test_returns_none_when_missing(self):
        assert image_visual_key({}) is None

    def test_returns_none_when_empty_string(self):
        assert image_visual_key({"visual_hash": ""}) is None

    def test_returns_none_when_none(self):
        assert image_visual_key({"visual_hash": None}) is None

    def test_coerces_to_str(self):
        assert image_visual_key({"visual_hash": 123}) == "123"


# ---------------------------------------------------------------------------
# image_coverage_ratio
# ---------------------------------------------------------------------------

class TestImageCoverageRatio:
    def test_returns_float(self):
        assert image_coverage_ratio({"coverage_ratio": 0.75}) == 0.75

    def test_returns_none_when_missing(self):
        assert image_coverage_ratio({}) is None

    def test_returns_none_when_none(self):
        assert image_coverage_ratio({"coverage_ratio": None}) is None

    def test_coerces_int(self):
        assert image_coverage_ratio({"coverage_ratio": 1}) == 1.0
        assert isinstance(image_coverage_ratio({"coverage_ratio": 1}), float)


# ---------------------------------------------------------------------------
# image_dominant_color_ratio
# ---------------------------------------------------------------------------

class TestImageDominantColorRatio:
    def test_returns_float(self):
        assert image_dominant_color_ratio({"dominant_color_ratio": 0.9}) == 0.9

    def test_returns_none_when_missing(self):
        assert image_dominant_color_ratio({}) is None

    def test_returns_none_when_none(self):
        assert image_dominant_color_ratio({"dominant_color_ratio": None}) is None


# ---------------------------------------------------------------------------
# image_page_dimensions
# ---------------------------------------------------------------------------

class TestImagePageDimensions:
    def test_returns_tuple(self):
        assert image_page_dimensions({"page_width": 612, "page_height": 792}) == (612.0, 792.0)

    def test_returns_none_tuple_when_width_missing(self):
        assert image_page_dimensions({"page_height": 792}) == (None, None)

    def test_returns_none_tuple_when_height_missing(self):
        assert image_page_dimensions({"page_width": 612}) == (None, None)

    def test_returns_none_tuple_when_both_missing(self):
        assert image_page_dimensions({}) == (None, None)

    def test_returns_none_tuple_when_width_none(self):
        assert image_page_dimensions({"page_width": None, "page_height": 792}) == (None, None)

    def test_coerces_to_float(self):
        w, h = image_page_dimensions({"page_width": 612, "page_height": 792})
        assert isinstance(w, float)
        assert isinstance(h, float)


# ---------------------------------------------------------------------------
# is_background_candidate
# ---------------------------------------------------------------------------

def _make_image(**overrides) -> dict:
    """Helper to create a test image dict with sensible defaults."""
    base = {
        "page": 1,
        "coverage_ratio": 0.8,
        "page_width": 612,
        "page_height": 792,
        "width": 600,
        "height": 780,
        "x": 0,
        "y": 0,
    }
    base.update(overrides)
    return base


_DEFAULT_POLICY = {
    "background_min_coverage_ratio": 0.6,
    "background_min_text_tokens": 80,
    "background_edge_margin_ratio": 0.08,
    "background_edge_min_area_ratio": 0.18,
    "background_edge_min_span_ratio": 0.7,
}

_STATS_ENOUGH_TEXT = {1: {"text_tokens": 100, "char_count": 500}}
_STATS_LOW_TEXT = {1: {"text_tokens": 10, "char_count": 50}}


class TestIsBackgroundCandidate:
    def test_high_coverage_is_candidate(self):
        image = _make_image(coverage_ratio=0.8)
        assert is_background_candidate(image, _STATS_ENOUGH_TEXT, _DEFAULT_POLICY) is True

    def test_no_coverage_ratio_not_candidate(self):
        image = _make_image(coverage_ratio=None)
        assert is_background_candidate(image, _STATS_ENOUGH_TEXT, _DEFAULT_POLICY) is False

    def test_low_text_tokens_not_candidate(self):
        image = _make_image(coverage_ratio=0.8)
        assert is_background_candidate(image, _STATS_LOW_TEXT, _DEFAULT_POLICY) is False

    def test_missing_page_stats_not_candidate(self):
        image = _make_image(coverage_ratio=0.8)
        assert is_background_candidate(image, {}, _DEFAULT_POLICY) is False

    def test_edge_touching_medium_coverage_is_candidate(self):
        # Coverage below 0.6 but touches edge with sufficient span
        image = _make_image(
            coverage_ratio=0.3,
            x=0, y=0,
            width=500, height=600,
            page_width=612, page_height=792,
        )
        assert is_background_candidate(image, _STATS_ENOUGH_TEXT, _DEFAULT_POLICY) is True

    def test_no_edge_touch_medium_coverage_not_candidate(self):
        # Coverage below 0.6, not touching any edge
        image = _make_image(
            coverage_ratio=0.3,
            x=100, y=100,
            width=200, height=200,
            page_width=612, page_height=792,
        )
        assert is_background_candidate(image, _STATS_ENOUGH_TEXT, _DEFAULT_POLICY) is False

    def test_missing_position_fields_not_candidate(self):
        # Coverage below threshold, missing x/y
        image = _make_image(coverage_ratio=0.3, x=None, y=None)
        assert is_background_candidate(image, _STATS_ENOUGH_TEXT, _DEFAULT_POLICY) is False

    def test_small_span_not_candidate(self):
        # Touches edge but small span ratio
        image = _make_image(
            coverage_ratio=0.2,
            x=0, y=300,
            width=100, height=50,
            page_width=612, page_height=792,
        )
        assert is_background_candidate(image, _STATS_ENOUGH_TEXT, _DEFAULT_POLICY) is False

    def test_custom_policy_thresholds(self):
        policy = {**_DEFAULT_POLICY, "background_min_coverage_ratio": 0.9}
        image = _make_image(coverage_ratio=0.8)
        # 0.8 < 0.9 so not via coverage path, but still touches edge with enough span
        result = is_background_candidate(image, _STATS_ENOUGH_TEXT, policy)
        # Should still pass via edge path since x=0 touches left edge
        assert result is True

    def test_zero_text_tokens_threshold(self):
        policy = {**_DEFAULT_POLICY, "background_min_text_tokens": 0}
        image = _make_image(coverage_ratio=0.8)
        assert is_background_candidate(image, _STATS_LOW_TEXT, policy) is True
