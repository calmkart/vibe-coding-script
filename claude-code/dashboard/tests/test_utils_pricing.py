"""Tests for dashboard.utils.pricing module."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dashboard.utils.pricing import (
    PRICING,
    DEFAULT_PRICING,
    get_model_pricing,
    calculate_cost,
    calculate_total_cost,
    format_model_name,
)


# ============================================================
# get_model_pricing tests
# ============================================================

class TestGetModelPricing:
    def test_exact_match_opus(self):
        result = get_model_pricing("claude-opus-4-6")
        assert result == PRICING["claude-opus-4-6"]

    def test_exact_match_sonnet(self):
        result = get_model_pricing("claude-sonnet-4-6")
        assert result == PRICING["claude-sonnet-4-6"]

    def test_exact_match_haiku(self):
        result = get_model_pricing("claude-haiku-4-5-20251001")
        assert result == PRICING["claude-haiku-4-5-20251001"]

    def test_prefix_match(self):
        """Model with suffix should match via prefix."""
        result = get_model_pricing("claude-opus-4-6[1m]")
        assert result == PRICING["claude-opus-4-6"]

    def test_keyword_haiku(self):
        result = get_model_pricing("some-unknown-haiku-model")
        assert result == PRICING["claude-haiku-4-5-20251001"]

    def test_keyword_sonnet(self):
        result = get_model_pricing("some-unknown-sonnet-model")
        assert result == PRICING["claude-sonnet-4-6"]

    def test_unknown_model_returns_default(self):
        result = get_model_pricing("completely-unknown-model-xyz")
        assert result == DEFAULT_PRICING

    def test_all_known_models_have_required_keys(self):
        for model, pricing in PRICING.items():
            assert "input" in pricing, f"{model} missing 'input'"
            assert "output" in pricing, f"{model} missing 'output'"
            assert "cache_read" in pricing, f"{model} missing 'cache_read'"
            assert "cache_creation" in pricing, f"{model} missing 'cache_creation'"

    def test_default_pricing_has_required_keys(self):
        assert "input" in DEFAULT_PRICING
        assert "output" in DEFAULT_PRICING
        assert "cache_read" in DEFAULT_PRICING
        assert "cache_creation" in DEFAULT_PRICING

    def test_prices_are_positive(self):
        for model, pricing in PRICING.items():
            for key, value in pricing.items():
                assert value >= 0, f"{model}.{key} = {value} is negative"


# ============================================================
# calculate_cost tests
# ============================================================

class TestCalculateCost:
    def test_zero_tokens(self):
        result = calculate_cost("claude-opus-4-6")
        assert result == 0.0

    def test_input_only(self):
        result = calculate_cost("claude-opus-4-6", input_tokens=1_000_000)
        assert result == 15.0  # $15 per million input tokens

    def test_output_only(self):
        result = calculate_cost("claude-opus-4-6", output_tokens=1_000_000)
        assert result == 75.0  # $75 per million output tokens

    def test_cache_read(self):
        result = calculate_cost("claude-opus-4-6", cache_read_tokens=1_000_000)
        assert result == 1.5  # $1.50 per million cache read tokens

    def test_cache_creation(self):
        result = calculate_cost("claude-opus-4-6", cache_creation_tokens=1_000_000)
        assert result == 18.75

    def test_combined_cost(self):
        result = calculate_cost(
            "claude-opus-4-6",
            input_tokens=100_000,
            output_tokens=50_000,
            cache_read_tokens=200_000,
            cache_creation_tokens=10_000,
        )
        expected = (
            100_000 * 15.0 / 1_000_000  # 1.5
            + 50_000 * 75.0 / 1_000_000  # 3.75
            + 200_000 * 1.50 / 1_000_000  # 0.30
            + 10_000 * 18.75 / 1_000_000  # 0.1875
        )
        assert abs(result - expected) < 0.001

    def test_sonnet_cheaper_than_opus(self):
        opus_cost = calculate_cost("claude-opus-4-6", input_tokens=1_000_000)
        sonnet_cost = calculate_cost("claude-sonnet-4-6", input_tokens=1_000_000)
        assert sonnet_cost < opus_cost

    def test_haiku_cheapest(self):
        haiku_cost = calculate_cost("claude-haiku-4-5-20251001", input_tokens=1_000_000)
        sonnet_cost = calculate_cost("claude-sonnet-4-6", input_tokens=1_000_000)
        assert haiku_cost < sonnet_cost


# ============================================================
# calculate_total_cost tests
# ============================================================

class TestCalculateTotalCost:
    def test_empty_dict(self):
        assert calculate_total_cost({}) == 0.0

    def test_single_model(self):
        usage = {
            "claude-opus-4-6": {
                "inputTokens": 1_000_000,
                "outputTokens": 0,
                "cacheReadInputTokens": 0,
                "cacheCreationInputTokens": 0,
            }
        }
        result = calculate_total_cost(usage)
        assert result == 15.0

    def test_multiple_models(self):
        usage = {
            "claude-opus-4-6": {
                "inputTokens": 1_000_000,
                "outputTokens": 0,
            },
            "claude-sonnet-4-6": {
                "inputTokens": 1_000_000,
                "outputTokens": 0,
            },
        }
        result = calculate_total_cost(usage)
        assert result == 15.0 + 3.0  # opus + sonnet input costs

    def test_missing_fields_default_to_zero(self):
        usage = {
            "claude-opus-4-6": {}  # All fields missing
        }
        result = calculate_total_cost(usage)
        assert result == 0.0


# ============================================================
# format_model_name tests
# ============================================================

class TestFormatModelName:
    def test_opus(self):
        assert format_model_name("claude-opus-4-6") == "Opus 4.6"

    def test_opus_with_suffix(self):
        assert format_model_name("claude-opus-4-6[1m]") == "Opus 4.6"

    def test_sonnet(self):
        assert format_model_name("claude-sonnet-4-6") == "Sonnet 4.6"

    def test_haiku(self):
        assert format_model_name("claude-haiku-4-5-20251001") == "Haiku 4.5"

    def test_unknown_model(self):
        result = format_model_name("gpt-4-turbo")
        assert result == "gpt-4-turbo"  # Returned as-is

    def test_opus_45(self):
        assert format_model_name("claude-opus-4-5-20251101") == "Opus 4.5"

    def test_sonnet_45(self):
        assert format_model_name("claude-sonnet-4-5-20251022") == "Sonnet 4.5"
