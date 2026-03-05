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
        """Missing stats-cache.json only affects hour_counts; session data comes from JSONL."""
        import dashboard.data.stats as mod
        monkeypatch.setattr(mod, "STATS_PATH", "/nonexistent/stats.json")
        result = mod.load_stats()
        assert isinstance(result, UsageStats)
        # Stats are computed from real session data, so they may be non-zero
        assert result.hour_counts == {}  # hour_counts comes from cache file

    def test_handles_corrupt_stats_file(self, tmp_path):
        """Corrupt stats-cache.json only affects hour_counts."""
        import dashboard.data.stats as mod
        corrupt_file = tmp_path / "corrupt-stats.json"
        corrupt_file.write_text("not valid json {{{")
        orig_path = mod.STATS_PATH
        mod.STATS_PATH = str(corrupt_file)
        try:
            result = mod.load_stats()
            assert isinstance(result, UsageStats)
            assert result.hour_counts == {}
        finally:
            mod.STATS_PATH = orig_path

    def test_hour_counts_from_cache(self, tmp_path):
        """Hour counts are loaded from stats-cache.json."""
        import dashboard.data.stats as mod

        data = {"hourCounts": {"9": 10, "14": 20, "22": 5}}

        stats_file = tmp_path / "stats.json"
        with open(stats_file, "w") as f:
            json.dump(data, f)

        orig_path = mod.STATS_PATH
        mod.STATS_PATH = str(stats_file)
        try:
            result = mod.load_stats()
            assert result.hour_counts == {9: 10, 14: 20, 22: 5}
        finally:
            mod.STATS_PATH = orig_path

    def test_stats_computed_from_sessions(self):
        """Stats are computed from actual session data (not cache file)."""
        import dashboard.data.stats as mod
        result = mod.load_stats()
        # Should have real data from JSONL files
        assert result.total_sessions >= 0
        assert isinstance(result.daily_activity, list)
        assert isinstance(result.daily_tokens, list)
        assert isinstance(result.model_usage, dict)
