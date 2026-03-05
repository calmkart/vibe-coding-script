"""Tests for dashboard.utils.format module."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dashboard.utils.format import (
    format_age,
    format_duration,
    shorten_path,
    project_name_from_dir,
    format_tokens,
    format_filesize,
    format_date,
    format_cost,
    truncate_text,
    decode_project_path,
)


# ============================================================
# format_age tests
# ============================================================

class TestFormatAge:
    def test_just_now(self):
        result = format_age(time.time())
        assert "s ago" in result or result == "now" or result == "0s ago"

    def test_seconds_ago(self):
        result = format_age(time.time() - 30)
        assert "s ago" in result
        assert "30" in result or "29" in result or "31" in result

    def test_minutes_ago(self):
        result = format_age(time.time() - 300)  # 5 min
        assert "m ago" in result
        assert "5" in result

    def test_hours_ago(self):
        result = format_age(time.time() - 7200)  # 2 hours
        assert "h ago" in result
        assert "2" in result

    def test_days_ago(self):
        result = format_age(time.time() - 172800)  # 2 days
        assert "d ago" in result
        assert "2" in result

    def test_future_timestamp(self):
        """Future timestamps should return 'now'."""
        result = format_age(time.time() + 1000)
        assert result == "now"

    def test_boundary_59_seconds(self):
        result = format_age(time.time() - 59)
        assert "s ago" in result

    def test_boundary_60_seconds(self):
        result = format_age(time.time() - 60)
        assert "m ago" in result

    def test_boundary_3599_seconds(self):
        result = format_age(time.time() - 3599)
        assert "m ago" in result

    def test_boundary_3600_seconds(self):
        result = format_age(time.time() - 3600)
        assert "h ago" in result

    def test_boundary_86399_seconds(self):
        result = format_age(time.time() - 86399)
        assert "h ago" in result

    def test_boundary_86400_seconds(self):
        result = format_age(time.time() - 86400)
        assert "d ago" in result


# ============================================================
# format_duration tests
# ============================================================

class TestFormatDuration:
    def test_seconds(self):
        assert format_duration(30) == "30s"

    def test_minutes(self):
        result = format_duration(150)
        assert "2m" in result
        assert "30s" in result

    def test_hours(self):
        result = format_duration(7200)
        assert "2h" in result

    def test_days(self):
        result = format_duration(90000)
        assert "1d" in result

    def test_zero(self):
        assert format_duration(0) == "0s"


# ============================================================
# shorten_path tests
# ============================================================

class TestShortenPath:
    def test_home_replacement(self):
        home = os.path.expanduser("~")
        result = shorten_path(home + "/Desktop/project")
        assert result.startswith("~")
        assert "Desktop" in result

    def test_long_path_truncated(self):
        long_path = "/a" * 100
        result = shorten_path(long_path, max_len=30)
        assert len(result) <= 30
        assert "\u2026" in result

    def test_short_path_unchanged(self):
        result = shorten_path("/tmp/test", max_len=50)
        assert result == "/tmp/test"

    def test_empty_path(self):
        result = shorten_path("")
        assert result == ""


# ============================================================
# project_name_from_dir tests
# ============================================================

class TestProjectNameFromDir:
    def test_encoded_path(self):
        result = project_name_from_dir("-Users-calmp-Desktop-code-lepton")
        assert result == "lepton"

    def test_simple_name(self):
        result = project_name_from_dir("my-project")
        assert result == "project"  # splits on hyphen, takes last

    def test_single_component(self):
        result = project_name_from_dir("standalone")
        assert result == "standalone"

    def test_empty_string(self):
        result = project_name_from_dir("")
        assert result == ""

    def test_leading_hyphens_stripped(self):
        result = project_name_from_dir("-Users-test")
        assert result == "test"


# ============================================================
# format_tokens tests
# ============================================================

class TestFormatTokens:
    def test_small_numbers(self):
        assert format_tokens(0) == "0"
        assert format_tokens(999) == "999"

    def test_thousands(self):
        result = format_tokens(1000)
        assert "K" in result
        assert "1.0" in result

    def test_millions(self):
        result = format_tokens(1_500_000)
        assert "M" in result
        assert "1.5" in result

    def test_billions(self):
        result = format_tokens(2_500_000_000)
        assert "B" in result
        assert "2.5" in result

    def test_exact_boundary_1000(self):
        result = format_tokens(1000)
        assert "K" in result

    def test_exact_boundary_million(self):
        result = format_tokens(1_000_000)
        assert "M" in result

    def test_exact_boundary_billion(self):
        result = format_tokens(1_000_000_000)
        assert "B" in result


# ============================================================
# format_filesize tests
# ============================================================

class TestFormatFilesize:
    def test_bytes(self):
        result = format_filesize(500)
        assert "B" in result
        assert "500" in result

    def test_kilobytes(self):
        result = format_filesize(2048)
        assert "KB" in result

    def test_megabytes(self):
        result = format_filesize(5_242_880)
        assert "MB" in result
        assert "5.0" in result

    def test_gigabytes(self):
        result = format_filesize(2_147_483_648)
        assert "GB" in result

    def test_zero(self):
        assert format_filesize(0) == "0 B"


# ============================================================
# format_date tests
# ============================================================

class TestFormatDate:
    def test_iso_date(self):
        result = format_date("2024-01-15T14:30:00Z")
        assert "2024" in result
        assert "01" in result
        assert "15" in result

    def test_iso_date_no_z(self):
        result = format_date("2024-01-15T14:30:00")
        assert "2024" in result

    def test_invalid_date(self):
        result = format_date("not-a-date")
        assert isinstance(result, str)

    def test_empty_date(self):
        result = format_date("")
        assert result == "?"

    def test_none_date(self):
        result = format_date(None)
        assert result == "?"


# ============================================================
# format_cost tests
# ============================================================

class TestFormatCost:
    def test_large_cost(self):
        result = format_cost(150.5)
        assert "$" in result
        assert "150" in result or "151" in result

    def test_medium_cost(self):
        result = format_cost(5.50)
        assert "$5.50" in result

    def test_small_cost(self):
        result = format_cost(0.05)
        assert "$0.050" in result

    def test_tiny_cost(self):
        result = format_cost(0.005)
        assert "$0.005" in result or "$0.0050" in result

    def test_zero_cost(self):
        result = format_cost(0)
        assert "$" in result
        assert "0.0000" in result

    def test_precision_levels(self):
        # >= 100: no decimal
        assert "." not in format_cost(100.0).replace("$", "").replace(",", "")
        # >= 1: 2 decimal
        assert format_cost(1.5) == "$1.50"
        # >= 0.01: 3 decimal
        assert format_cost(0.05) == "$0.050"
        # < 0.01: 4 decimal
        assert format_cost(0.001) == "$0.0010"


# ============================================================
# truncate_text tests
# ============================================================

class TestTruncateText:
    def test_short_text(self):
        assert truncate_text("hello") == "hello"

    def test_long_text_truncated(self):
        long = "x" * 200
        result = truncate_text(long, max_len=50)
        assert len(result) <= 50
        assert "\u2026" in result

    def test_strips_xml_tags(self):
        result = truncate_text("<tag>hello</tag> world")
        assert "<tag>" not in result
        assert "hello" in result
        assert "world" in result

    def test_empty_text(self):
        assert truncate_text("") == ""

    def test_none_text(self):
        assert truncate_text(None) == ""

    def test_exact_max_len(self):
        text = "x" * 100
        result = truncate_text(text, max_len=100)
        assert result == text  # Should not truncate at exact boundary

    def test_one_over_max_len(self):
        text = "x" * 101
        result = truncate_text(text, max_len=100)
        assert len(result) == 100
        assert result[-1] == "\u2026"


# ============================================================
# decode_project_path tests
# ============================================================

class TestDecodeProjectPath:
    def test_encoded_path(self):
        result = decode_project_path("-Users-calmp-Desktop-code-lepton")
        assert result == "/Users/calmp/Desktop/code/lepton"

    def test_non_encoded_path(self):
        result = decode_project_path("plain-name")
        assert result == "plain-name"

    def test_root_level(self):
        result = decode_project_path("-tmp")
        assert result == "/tmp"

    def test_deep_path(self):
        result = decode_project_path("-a-b-c-d-e")
        assert result == "/a/b/c/d/e"
