"""Tests for dashboard.data.stats module."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dashboard.data.stats import (
    UsageStats,
    DailyActivity,
    DailyTokens,
    ModelUsage,
    load_stats,
    STATS_PATH,
)


class TestLoadStats:
    """Test loading stats from stats-cache.json."""

    def test_returns_usage_stats(self):
        result = load_stats()
        assert isinstance(result, UsageStats)

    def test_total_sessions_positive(self):
        """Real stats should have some sessions."""
        result = load_stats()
        if os.path.exists(STATS_PATH):
            assert result.total_sessions > 0

    def test_total_messages_positive(self):
        result = load_stats()
        if os.path.exists(STATS_PATH):
            assert result.total_messages > 0

    def test_daily_activity_is_list(self):
        result = load_stats()
        assert isinstance(result.daily_activity, list)
        for a in result.daily_activity:
            assert isinstance(a, DailyActivity)

    def test_daily_activity_fields(self):
        result = load_stats()
        if result.daily_activity:
            a = result.daily_activity[0]
            assert a.date, "date should not be empty"
            assert isinstance(a.message_count, int)
            assert isinstance(a.session_count, int)
            assert isinstance(a.tool_call_count, int)

    def test_model_usage_populated(self):
        result = load_stats()
        if os.path.exists(STATS_PATH):
            assert len(result.model_usage) > 0

    def test_model_usage_fields(self):
        result = load_stats()
        for model, usage in result.model_usage.items():
            assert isinstance(usage, ModelUsage)
            assert isinstance(usage.input_tokens, int)
            assert isinstance(usage.output_tokens, int)
            assert isinstance(usage.cache_read_tokens, int)
            assert isinstance(usage.cache_creation_tokens, int)
            assert isinstance(usage.cost_usd, (int, float))

    def test_hour_counts_valid_hours(self):
        result = load_stats()
        for hour in result.hour_counts:
            assert 0 <= hour <= 23, f"Invalid hour: {hour}"

    def test_daily_tokens_total(self):
        result = load_stats()
        for dt in result.daily_tokens:
            assert isinstance(dt, DailyTokens)
            assert isinstance(dt.total_tokens, int)
            assert dt.total_tokens >= 0

    def test_handles_missing_stats_file(self, monkeypatch):
        import dashboard.data.stats as mod
        monkeypatch.setattr(mod, "STATS_PATH", "/nonexistent/stats.json")
        result = mod.load_stats()
        assert isinstance(result, UsageStats)
        assert result.total_sessions == 0
        assert result.total_messages == 0
        assert result.daily_activity == []

    def test_handles_corrupt_stats_file(self, tmp_path):
        import dashboard.data.stats as mod
        corrupt_file = tmp_path / "corrupt-stats.json"
        corrupt_file.write_text("not valid json {{{")
        orig_path = mod.STATS_PATH
        mod.STATS_PATH = str(corrupt_file)
        try:
            result = mod.load_stats()
            assert isinstance(result, UsageStats)
            assert result.total_sessions == 0
        finally:
            mod.STATS_PATH = orig_path

    def test_with_synthetic_data(self, tmp_path):
        """Test with known synthetic data."""
        import dashboard.data.stats as mod

        data = {
            "totalSessions": 42,
            "totalMessages": 500,
            "firstSessionDate": "2024-01-01T00:00:00Z",
            "longestSession": {
                "sessionId": "long-session",
                "messageCount": 200,
                "duration": 3600000,  # 1 hour in ms
            },
            "dailyActivity": [
                {"date": "2024-01-01", "messageCount": 10, "sessionCount": 2, "toolCallCount": 5},
            ],
            "dailyModelTokens": [
                {"date": "2024-01-01", "tokensByModel": {"claude-opus-4-6": 1000}},
            ],
            "modelUsage": {
                "claude-opus-4-6": {
                    "inputTokens": 100000,
                    "outputTokens": 50000,
                    "cacheReadInputTokens": 20000,
                    "cacheCreationInputTokens": 10000,
                    "costUSD": 5.50,
                    "webSearchRequests": 3,
                },
            },
            "hourCounts": {"9": 10, "14": 20, "22": 5},
        }

        stats_file = tmp_path / "stats.json"
        with open(stats_file, "w") as f:
            json.dump(data, f)

        orig_path = mod.STATS_PATH
        mod.STATS_PATH = str(stats_file)
        try:
            result = mod.load_stats()
            assert result.total_sessions == 42
            assert result.total_messages == 500
            assert result.first_session_date == "2024-01-01T00:00:00Z"
            assert result.longest_session_id == "long-session"
            assert result.longest_session_messages == 200
            assert result.longest_session_duration == 3600.0  # converted to seconds
            assert len(result.daily_activity) == 1
            assert result.daily_activity[0].message_count == 10
            assert len(result.daily_tokens) == 1
            assert result.daily_tokens[0].total_tokens == 1000
            assert "claude-opus-4-6" in result.model_usage
            mu = result.model_usage["claude-opus-4-6"]
            assert mu.input_tokens == 100000
            assert mu.output_tokens == 50000
            assert mu.cache_read_tokens == 20000
            assert mu.cache_creation_tokens == 10000
            assert mu.web_search_requests == 3
            assert result.hour_counts == {9: 10, 14: 20, 22: 5}
        finally:
            mod.STATS_PATH = orig_path
