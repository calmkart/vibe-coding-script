"""Usage statistics computed from actual session data.

Primary source: JSONL session files via discover_all_projects().
Secondary source: ~/.claude/stats-cache.json (for hourly heatmap data only,
since hour-of-day info is not easily derived from session metadata).
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional


STATS_PATH = os.path.expanduser("~/.claude/stats-cache.json")


@dataclass
class DailyActivity:
    date: str
    message_count: int
    session_count: int
    tool_call_count: int


@dataclass
class DailyTokens:
    date: str
    tokens_by_model: Dict[str, int]

    @property
    def total_tokens(self) -> int:
        return sum(self.tokens_by_model.values())


@dataclass
class ModelUsage:
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    cost_usd: float
    web_search_requests: int


@dataclass
class UsageStats:
    total_sessions: int = 0
    total_messages: int = 0
    first_session_date: str = ""
    longest_session_id: str = ""
    longest_session_messages: int = 0
    longest_session_duration: float = 0
    daily_activity: List[DailyActivity] = field(default_factory=list)
    daily_tokens: List[DailyTokens] = field(default_factory=list)
    model_usage: Dict[str, ModelUsage] = field(default_factory=dict)
    hour_counts: Dict[int, int] = field(default_factory=dict)


def load_stats() -> UsageStats:
    """Build usage stats from actual session data (JSONL files).

    This is the ground truth — it scans all sessions via
    discover_all_projects() which already computes per-session
    token usage and estimated cost.

    The stats-cache.json is only used for hourly heatmap data.
    """
    from .history import discover_all_projects

    projects = discover_all_projects()

    stats = UsageStats()

    # Aggregators
    model_agg: Dict[str, dict] = {}  # model -> {input, output, cache_read, cache_create}
    daily_agg: Dict[str, dict] = {}  # date -> {messages, sessions}
    daily_tokens_agg: Dict[str, Dict[str, int]] = {}  # date -> {model -> tokens}

    for project in projects:
        for s in project.sessions:
            stats.total_sessions += 1
            stats.total_messages += s.message_count

            # Track longest session
            if s.message_count > stats.longest_session_messages:
                stats.longest_session_messages = s.message_count
                stats.longest_session_id = s.session_id

            # First session date
            date_str = (s.created or s.modified or "")[:10]
            if date_str:
                if not stats.first_session_date or date_str < stats.first_session_date:
                    stats.first_session_date = date_str

            # Daily activity
            if date_str:
                day = daily_agg.setdefault(date_str, {"messages": 0, "sessions": 0})
                day["messages"] += s.message_count
                day["sessions"] += 1

            # Model usage aggregation
            model = s.primary_model
            if model and s.total_output_tokens > 0:
                agg = model_agg.setdefault(model, {
                    "input": 0, "output": 0, "cache_read": 0, "cache_create": 0,
                })
                agg["input"] += s.total_input_tokens
                agg["output"] += s.total_output_tokens
                agg["cache_read"] += s.total_cache_read
                agg["cache_create"] += s.total_cache_create

                # Daily tokens by model
                if date_str:
                    dt = daily_tokens_agg.setdefault(date_str, {})
                    dt[model] = dt.get(model, 0) + s.total_input_tokens + s.total_output_tokens

    # Build daily activity list (sorted)
    for date_str in sorted(daily_agg):
        day = daily_agg[date_str]
        stats.daily_activity.append(DailyActivity(
            date=date_str,
            message_count=day["messages"],
            session_count=day["sessions"],
            tool_call_count=0,
        ))

    # Build daily tokens list (sorted)
    for date_str in sorted(daily_tokens_agg):
        stats.daily_tokens.append(DailyTokens(
            date=date_str,
            tokens_by_model=daily_tokens_agg[date_str],
        ))

    # Build model usage
    from ..utils.pricing import calculate_cost
    for model, agg in model_agg.items():
        cost = calculate_cost(
            model=model,
            input_tokens=agg["input"],
            output_tokens=agg["output"],
            cache_read_tokens=agg["cache_read"],
            cache_creation_tokens=agg["cache_create"],
        )
        stats.model_usage[model] = ModelUsage(
            model=model,
            input_tokens=agg["input"],
            output_tokens=agg["output"],
            cache_read_tokens=agg["cache_read"],
            cache_creation_tokens=agg["cache_create"],
            cost_usd=cost,
            web_search_requests=0,
        )

    # Hour counts — use stats-cache.json for this (can't derive from session metadata)
    stats.hour_counts = _load_hour_counts()

    return stats


def _load_hour_counts() -> Dict[int, int]:
    """Load hourly distribution from stats-cache.json (best available source)."""
    if not os.path.exists(STATS_PATH):
        return {}
    try:
        with open(STATS_PATH) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

    counts = {}
    for hour_str, count in data.get("hourCounts", {}).items():
        try:
            counts[int(hour_str)] = count
        except ValueError:
            pass
    return counts
