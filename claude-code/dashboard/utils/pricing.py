"""Anthropic pricing constants and cost calculator."""
from __future__ import annotations

from typing import Dict


# Anthropic pricing per million tokens (as of March 2026)
PRICING = {
    "claude-opus-4-6": {
        "input": 15.0,
        "output": 75.0,
        "cache_read": 1.50,
        "cache_creation": 18.75,
    },
    "claude-opus-4-5-20251101": {
        "input": 15.0,
        "output": 75.0,
        "cache_read": 1.50,
        "cache_creation": 18.75,
    },
    "claude-sonnet-4-6": {
        "input": 3.0,
        "output": 15.0,
        "cache_read": 0.30,
        "cache_creation": 3.75,
    },
    "claude-sonnet-4-5-20251022": {
        "input": 3.0,
        "output": 15.0,
        "cache_read": 0.30,
        "cache_creation": 3.75,
    },
    "claude-haiku-4-5-20251001": {
        "input": 0.80,
        "output": 4.0,
        "cache_read": 0.08,
        "cache_creation": 1.0,
    },
}

# Fallback pricing for unknown models
DEFAULT_PRICING = {
    "input": 15.0,
    "output": 75.0,
    "cache_read": 1.50,
    "cache_creation": 18.75,
}


def get_model_pricing(model: str) -> Dict[str, float]:
    """Get pricing for a model, with fallback."""
    # Try exact match first
    if model in PRICING:
        return PRICING[model]
    # Try prefix match (e.g. "claude-opus-4-6" matches "claude-opus-4-6[1m]")
    for key in PRICING:
        if model.startswith(key) or key.startswith(model):
            return PRICING[key]
    # Guess based on model name keywords
    model_lower = model.lower()
    if "haiku" in model_lower:
        return PRICING["claude-haiku-4-5-20251001"]
    elif "sonnet" in model_lower:
        return PRICING["claude-sonnet-4-6"]
    return DEFAULT_PRICING


def calculate_cost(
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_read_tokens: int = 0,
    cache_creation_tokens: int = 0,
) -> float:
    """Calculate estimated cost in USD from token counts."""
    prices = get_model_pricing(model)
    cost = (
        input_tokens * prices["input"] / 1_000_000
        + output_tokens * prices["output"] / 1_000_000
        + cache_read_tokens * prices["cache_read"] / 1_000_000
        + cache_creation_tokens * prices["cache_creation"] / 1_000_000
    )
    return cost


def calculate_total_cost(model_usage: Dict[str, dict]) -> float:
    """Calculate total cost across all models from stats-cache modelUsage data."""
    total = 0.0
    for model, usage in model_usage.items():
        total += calculate_cost(
            model=model,
            input_tokens=usage.get("inputTokens", 0),
            output_tokens=usage.get("outputTokens", 0),
            cache_read_tokens=usage.get("cacheReadInputTokens", 0),
            cache_creation_tokens=usage.get("cacheCreationInputTokens", 0),
        )
    return total


def format_model_name(model: str) -> str:
    """Shorten model name for display."""
    replacements = {
        "claude-opus-4-6": "Opus 4.6",
        "claude-opus-4-5-20251101": "Opus 4.5",
        "claude-sonnet-4-6": "Sonnet 4.6",
        "claude-sonnet-4-5-20251022": "Sonnet 4.5",
        "claude-haiku-4-5-20251001": "Haiku 4.5",
    }
    for key, short in replacements.items():
        if model.startswith(key) or key.startswith(model):
            return short
    return model
