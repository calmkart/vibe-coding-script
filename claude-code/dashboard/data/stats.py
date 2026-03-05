"""Stats-cache.json reader for usage statistics."""
from __future__ import annotations

import json
import os
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
    """Load and parse ~/.claude/stats-cache.json."""
    if not os.path.exists(STATS_PATH):
        return UsageStats()

    try:
        with open(STATS_PATH) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return UsageStats()

    stats = UsageStats(
        total_sessions=data.get("totalSessions", 0),
        total_messages=data.get("totalMessages", 0),
        first_session_date=data.get("firstSessionDate", ""),
    )

    # Longest session
    longest = data.get("longestSession", {})
    stats.longest_session_id = longest.get("sessionId", "")
    stats.longest_session_messages = longest.get("messageCount", 0)
    stats.longest_session_duration = longest.get("duration", 0) / 1000  # ms to seconds

    # Daily activity
    for entry in data.get("dailyActivity", []):
        stats.daily_activity.append(DailyActivity(
            date=entry.get("date", ""),
            message_count=entry.get("messageCount", 0),
            session_count=entry.get("sessionCount", 0),
            tool_call_count=entry.get("toolCallCount", 0),
        ))

    # Daily model tokens
    for entry in data.get("dailyModelTokens", []):
        stats.daily_tokens.append(DailyTokens(
            date=entry.get("date", ""),
            tokens_by_model=entry.get("tokensByModel", {}),
        ))

    # Model usage
    for model, usage in data.get("modelUsage", {}).items():
        stats.model_usage[model] = ModelUsage(
            model=model,
            input_tokens=usage.get("inputTokens", 0),
            output_tokens=usage.get("outputTokens", 0),
            cache_read_tokens=usage.get("cacheReadInputTokens", 0),
            cache_creation_tokens=usage.get("cacheCreationInputTokens", 0),
            cost_usd=usage.get("costUSD", 0),
            web_search_requests=usage.get("webSearchRequests", 0),
        )

    # Hour counts
    for hour_str, count in data.get("hourCounts", {}).items():
        try:
            stats.hour_counts[int(hour_str)] = count
        except ValueError:
            pass

    return stats
