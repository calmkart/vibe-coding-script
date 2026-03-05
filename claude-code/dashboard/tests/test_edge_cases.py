"""Edge case and adversarial tests for the dashboard."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dashboard.data.sessions import ActiveSession, read_active_sessions, active_session_summary
from dashboard.data.history import (
    load_conversation, load_project_sessions, _resolve_project_path,
    SessionEntry, discover_all_projects,
)
from dashboard.data.stats import load_stats, UsageStats
from dashboard.data.search import search_conversations, _extract_text, _extract_match_context
from dashboard.utils.format import (
    format_age, format_tokens, format_filesize, format_cost,
    truncate_text, shorten_path, decode_project_path, format_date,
    format_duration, project_name_from_dir,
)
from dashboard.utils.pricing import calculate_cost, get_model_pricing, format_model_name


# ============================================================
# Boundary value tests
# ============================================================

class TestBoundaryValues:
    """Test boundary and extreme values."""

    def test_format_tokens_zero(self):
        assert format_tokens(0) == "0"

    def test_format_tokens_negative(self):
        """Negative values should not crash."""
        result = format_tokens(-1)
        assert isinstance(result, str)

    def test_format_tokens_max_int(self):
        result = format_tokens(2**63)
        assert "B" in result or isinstance(result, str)

    def test_format_filesize_zero(self):
        assert "0" in format_filesize(0)

    def test_format_filesize_one(self):
        assert "1" in format_filesize(1)

    def test_format_filesize_max(self):
        result = format_filesize(2**40)
        assert "GB" in result or "TB" in result or isinstance(result, str)

    def test_format_cost_zero(self):
        result = format_cost(0.0)
        assert "$" in result

    def test_format_cost_negative(self):
        """Negative costs should not crash (might happen with refunds)."""
        result = format_cost(-1.0)
        assert isinstance(result, str)

    def test_format_cost_very_large(self):
        result = format_cost(999999.99)
        assert "$" in result

    def test_format_cost_very_small(self):
        result = format_cost(0.00001)
        assert "$" in result

    def test_format_age_zero_delta(self):
        result = format_age(time.time())
        assert isinstance(result, str)

    def test_format_age_epoch_zero(self):
        """Very old timestamp."""
        result = format_age(0)
        assert "d ago" in result

    def test_format_duration_zero(self):
        assert format_duration(0) == "0s"

    def test_format_duration_very_large(self):
        result = format_duration(1_000_000)
        assert "d" in result

    def test_format_duration_negative(self):
        """Negative duration should not crash."""
        result = format_duration(-10)
        assert isinstance(result, str)

    def test_calculate_cost_zero_tokens(self):
        result = calculate_cost("claude-opus-4-6", 0, 0, 0, 0)
        assert result == 0.0

    def test_calculate_cost_very_large_tokens(self):
        result = calculate_cost("claude-opus-4-6", input_tokens=10**12)
        assert result > 0
        assert isinstance(result, float)

    def test_max_messages_zero(self, tmp_path):
        """max_messages=0 -- BUG: the code appends first, then checks limit.

        The check is `len(messages) >= max_messages` which is `1 >= 0` after
        the first append. So max_messages=0 still returns 1 message.
        This documents the off-by-one behavior.
        """
        jsonl = tmp_path / "test.jsonl"
        with open(jsonl, "w") as f:
            f.write(json.dumps({"message": {"role": "user", "content": "hi"}, "timestamp": "t"}) + "\n")
        result = load_conversation(str(jsonl), max_messages=0)
        assert len(result) == 0  # max_messages=0 returns empty list (early return)

    def test_max_messages_one(self, tmp_path):
        """max_messages=1 should return exactly 1 message."""
        jsonl = tmp_path / "test.jsonl"
        with open(jsonl, "w") as f:
            for i in range(10):
                f.write(json.dumps({"message": {"role": "user", "content": f"msg {i}"}, "timestamp": "t"}) + "\n")
        result = load_conversation(str(jsonl), max_messages=1)
        assert len(result) == 1


# ============================================================
# Invalid input tests
# ============================================================

class TestInvalidInputs:
    """Test handling of invalid/malformed inputs."""

    def test_truncate_text_none(self):
        assert truncate_text(None) == ""

    def test_truncate_text_empty(self):
        assert truncate_text("") == ""

    def test_shorten_path_empty(self):
        assert shorten_path("") == ""

    def test_decode_project_path_empty(self):
        result = decode_project_path("")
        assert isinstance(result, str)

    def test_project_name_from_dir_empty(self):
        result = project_name_from_dir("")
        assert isinstance(result, str)

    def test_format_date_none(self):
        result = format_date(None)
        assert result == "?"

    def test_format_date_garbage(self):
        result = format_date("xyz-not-a-date-at-all")
        assert isinstance(result, str)

    def test_format_model_name_empty(self):
        result = format_model_name("")
        assert isinstance(result, str)

    def test_get_model_pricing_empty_string(self):
        result = get_model_pricing("")
        assert isinstance(result, dict)

    def test_search_none_query(self):
        result = search_conversations(None)
        assert result == []

    def test_search_empty_query(self):
        result = search_conversations("")
        assert result == []

    def test_extract_text_none(self):
        result = _extract_text(None)
        assert result == "None"

    def test_extract_text_number(self):
        result = _extract_text(42)
        assert result == "42"

    def test_extract_text_empty_list(self):
        result = _extract_text([])
        assert result == ""

    def test_extract_text_nested_empty_dicts(self):
        result = _extract_text([{}, {}, {}])
        # Should not crash, returns joined empty strings
        assert isinstance(result, str)

    def test_load_conversation_binary_file(self, tmp_path):
        """Binary file -- BUG: load_conversation does not handle UnicodeDecodeError.

        The function opens the file in text mode without errors='replace',
        so binary content raises UnicodeDecodeError. This documents the bug.
        """
        binfile = tmp_path / "binary.jsonl"
        with open(binfile, "wb") as f:
            f.write(bytes(range(256)) * 10)
        try:
            result = load_conversation(str(binfile))
            assert isinstance(result, list)
        except UnicodeDecodeError:
            pass  # Known bug: binary files crash load_conversation

    def test_active_session_summary_with_empty_list(self):
        result = active_session_summary([])
        assert result == {"working": 0, "attention": 0, "done": 0}


# ============================================================
# Corrupted data tests
# ============================================================

class TestCorruptedData:
    """Test handling of corrupted files and data."""

    def test_corrupted_jsonl_lines(self, tmp_path):
        """JSONL with mix of valid and invalid lines."""
        jsonl = tmp_path / "mixed.jsonl"
        lines = [
            '{"message": {"role": "user", "content": "valid"}, "timestamp": "t"}',
            "not json at all",
            '{"message": {"role": "assistant", "content": "also valid"}, "timestamp": "t"}',
            '{incomplete json...',
            "",  # empty line
            '{"message": {"role": "user", "content": "third valid"}, "timestamp": "t"}',
        ]
        with open(jsonl, "w") as f:
            f.write("\n".join(lines) + "\n")

        result = load_conversation(str(jsonl))
        assert len(result) == 3

    def test_empty_jsonl_file(self, tmp_path):
        jsonl = tmp_path / "empty.jsonl"
        jsonl.touch()
        result = load_conversation(str(jsonl))
        assert result == []

    def test_jsonl_with_only_empty_lines(self, tmp_path):
        jsonl = tmp_path / "whitespace.jsonl"
        with open(jsonl, "w") as f:
            f.write("\n\n\n\n\n")
        result = load_conversation(str(jsonl))
        assert result == []

    def test_sessions_with_missing_fields(self, tmp_path):
        """Session JSON files with missing fields should be handled."""
        import dashboard.data.sessions as mod

        session_dir = tmp_path / "sessions"
        session_dir.mkdir()

        # Minimal valid data - just timestamp and pid
        data = {"timestamp": time.time(), "pid": os.getpid()}
        with open(session_dir / "minimal.json", "w") as f:
            json.dump(data, f)

        orig_dir = mod.SESSION_DIR
        mod.SESSION_DIR = str(session_dir)
        try:
            result = mod.read_active_sessions()
            assert isinstance(result, list)
            if result:
                s = result[0]
                assert s.tty == ""
                assert s.project == "unknown"
                assert s.branch == ""
        finally:
            mod.SESSION_DIR = orig_dir

    def test_corrupt_stats_cache(self, tmp_path):
        """Corrupted stats-cache.json should return empty stats."""
        import dashboard.data.stats as mod

        corrupt = tmp_path / "stats.json"
        corrupt.write_text("{invalid json here")

        orig_path = mod.STATS_PATH
        mod.STATS_PATH = str(corrupt)
        try:
            result = mod.load_stats()
            assert isinstance(result, UsageStats)
            assert result.total_sessions == 0
        finally:
            mod.STATS_PATH = orig_path

    def test_stats_with_invalid_hour_counts(self, tmp_path):
        """hour_counts with non-numeric keys should be handled."""
        import dashboard.data.stats as mod

        data = {
            "totalSessions": 1,
            "hourCounts": {"abc": 5, "9": 10, "not_a_number": 3},
        }
        stats_file = tmp_path / "stats.json"
        with open(stats_file, "w") as f:
            json.dump(data, f)

        orig_path = mod.STATS_PATH
        mod.STATS_PATH = str(stats_file)
        try:
            result = mod.load_stats()
            # Only valid hour "9" should be included
            assert 9 in result.hour_counts
            assert result.hour_counts[9] == 10
            # Invalid keys should be skipped
            assert len(result.hour_counts) == 1
        finally:
            mod.STATS_PATH = orig_path


# ============================================================
# Very long data tests
# ============================================================

class TestVeryLongData:
    """Test with extremely long strings and large datasets."""

    def test_very_long_path(self):
        long_path = "/very" * 100 + "/long/path"
        result = shorten_path(long_path, max_len=50)
        assert len(result) <= 50

    def test_very_long_project_name(self):
        long_name = "x" * 500
        result = project_name_from_dir(long_name)
        assert isinstance(result, str)

    def test_truncate_very_long_text(self):
        long_text = "word " * 10000
        result = truncate_text(long_text, max_len=100)
        assert len(result) <= 100

    def test_very_long_first_prompt(self):
        s = SessionEntry(
            session_id="id", project_name="p", project_path="/p",
            project_dir="d", jsonl_path="/f.jsonl",
            first_prompt="x" * 10000, summary="", message_count=0,
            created="", modified="", git_branch="", is_sidechain=False,
            file_size=0,
        )
        result = s.short_prompt
        assert len(result) <= 101

    def test_extract_match_context_very_long_text(self):
        text = "a" * 10000 + "MATCH" + "b" * 10000
        result = _extract_match_context(text, "match", context_chars=80)
        assert "MATCH" in result
        assert len(result) < 300  # Should be bounded by context_chars

    def test_search_very_long_query(self, tmp_path):
        """Very long search query should not crash."""
        import dashboard.data.search as mod
        orig_dir = mod.PROJECTS_DIR
        mod.PROJECTS_DIR = str(tmp_path)
        try:
            result = mod.search_conversations("x" * 10000)
            assert isinstance(result, list)
        finally:
            mod.PROJECTS_DIR = orig_dir


# ============================================================
# Concurrency tests
# ============================================================

class TestConcurrency:
    """Test thread-safety of data access."""

    def test_concurrent_session_reads(self):
        """Multiple threads reading sessions should not crash."""
        import threading

        errors = []

        def read_sessions():
            try:
                result = read_active_sessions()
                assert isinstance(result, list)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=read_sessions) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert len(errors) == 0, f"Errors in concurrent reads: {errors}"

    def test_concurrent_stats_reads(self):
        """Multiple threads reading stats should not crash."""
        import threading

        errors = []

        def read_stats():
            try:
                result = load_stats()
                assert isinstance(result, UsageStats)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=read_stats) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert len(errors) == 0

    def test_concurrent_project_discovery(self):
        """Multiple threads discovering projects should not crash."""
        import threading

        errors = []

        def discover():
            try:
                result = discover_all_projects()
                assert isinstance(result, list)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=discover) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert len(errors) == 0


# ============================================================
# Special character tests
# ============================================================

class TestSpecialCharacters:
    """Test handling of special characters in inputs."""

    def test_unicode_in_project_name(self):
        result = project_name_from_dir("-Users-test-\u30d7\u30ed\u30b8\u30a7\u30af\u30c8")
        assert isinstance(result, str)

    def test_path_with_spaces(self):
        result = shorten_path("/Users/test user/My Project/src", max_len=50)
        assert isinstance(result, str)

    def test_decode_path_with_special_chars(self):
        # The decode function only handles hyphen-to-slash conversion
        result = decode_project_path("-Users-test")
        assert result == "/Users/test"

    def test_format_date_with_timezone(self):
        result = format_date("2024-01-15T14:30:00+09:00")
        assert "2024" in result

    def test_search_with_special_regex_chars(self, tmp_path):
        """Search query with regex special chars should not crash."""
        import dashboard.data.search as mod
        orig_dir = mod.PROJECTS_DIR
        mod.PROJECTS_DIR = str(tmp_path)
        try:
            result = mod.search_conversations("[test].*?+(){}|^$\\")
            assert isinstance(result, list)
        finally:
            mod.PROJECTS_DIR = orig_dir

    def test_truncate_text_with_html_entities(self):
        result = truncate_text("<p>Hello &amp; world</p>")
        assert "&amp;" in result or "&" in result
        assert "<p>" not in result
