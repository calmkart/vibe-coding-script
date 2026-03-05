"""Tests for dashboard.data.search module."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dashboard.data.search import (
    SearchResult,
    search_conversations,
    _extract_text,
    _extract_match_context,
)


class TestSearchConversations:
    """Test full-text search across conversations."""

    def test_returns_list(self):
        result = search_conversations("test")
        assert isinstance(result, list)

    def test_empty_query_returns_empty(self):
        result = search_conversations("")
        assert result == []

    def test_none_query_returns_empty(self):
        result = search_conversations(None)
        assert result == []

    def test_results_are_search_result_instances(self):
        result = search_conversations("the")
        for r in result:
            assert isinstance(r, SearchResult)

    def test_max_results_respected(self):
        result = search_conversations("the", max_results=3)
        assert len(result) <= 3

    def test_max_results_one(self):
        result = search_conversations("the", max_results=1)
        assert len(result) <= 1

    def test_search_result_fields(self):
        result = search_conversations("the", max_results=5)
        if result:
            r = result[0]
            assert r.session_id, "session_id should not be empty"
            assert r.project_name, "project_name should not be empty"
            assert r.jsonl_path, "jsonl_path should not be empty"
            assert r.role in ("user", "assistant")
            assert r.content_preview, "content_preview should not be empty"
            assert r.match_line >= 1

    def test_results_sorted_by_timestamp_desc(self):
        result = search_conversations("the", max_results=20)
        if len(result) >= 2:
            timestamps = [r.timestamp for r in result if r.timestamp]
            if len(timestamps) >= 2:
                assert timestamps == sorted(timestamps, reverse=True)

    def test_project_filter(self):
        result = search_conversations("the", project_filter="nonexistent-project-xyz")
        assert result == []

    def test_handles_missing_projects_dir(self, monkeypatch):
        import dashboard.data.search as mod
        monkeypatch.setattr(mod, "PROJECTS_DIR", "/nonexistent/path")
        result = mod.search_conversations("test")
        assert result == []

    def test_with_temp_files(self, tmp_path):
        """Test search against controlled temp files."""
        import dashboard.data.search as mod

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()

        lines = [
            json.dumps({
                "sessionId": "sess-1",
                "timestamp": "2024-01-01T10:00:00Z",
                "message": {"role": "user", "content": "Find this unique needle text"},
            }),
            json.dumps({
                "sessionId": "sess-1",
                "timestamp": "2024-01-01T10:01:00Z",
                "message": {"role": "assistant", "content": "Response without match"},
            }),
        ]
        with open(project_dir / "sess-1.jsonl", "w") as f:
            f.write("\n".join(lines) + "\n")

        orig_dir = mod.PROJECTS_DIR
        mod.PROJECTS_DIR = str(tmp_path)
        try:
            result = mod.search_conversations("unique needle")
            assert len(result) == 1
            assert result[0].role == "user"
            assert "unique needle" in result[0].content_preview.lower()
        finally:
            mod.PROJECTS_DIR = orig_dir


class TestExtractText:
    """Test _extract_text helper."""

    def test_string_content(self):
        assert _extract_text("hello world") == "hello world"

    def test_list_with_text_blocks(self):
        content = [
            {"type": "text", "text": "Hello"},
            {"type": "text", "text": "World"},
        ]
        result = _extract_text(content)
        assert "Hello" in result
        assert "World" in result

    def test_list_with_tool_use(self):
        content = [
            {"type": "tool_use", "name": "read_file"},
        ]
        result = _extract_text(content)
        assert "read_file" in result

    def test_empty_list(self):
        assert _extract_text([]) == ""

    def test_non_string_non_list(self):
        result = _extract_text(42)
        assert result == "42"

    def test_none_content(self):
        result = _extract_text(None)
        assert result == "None"


class TestExtractMatchContext:
    """Test _extract_match_context helper."""

    def test_basic_context(self):
        text = "This is a long text with a needle in the middle of it."
        result = _extract_match_context(text, "needle", context_chars=10)
        assert "needle" in result

    def test_no_match(self):
        text = "Some text without the search term"
        result = _extract_match_context(text, "xyznonexistent")
        # Should return truncated text
        assert len(result) <= 161  # 160 + possible ellipsis

    def test_match_at_start(self):
        text = "needle at the very beginning of the text"
        result = _extract_match_context(text, "needle", context_chars=10)
        assert result.startswith("needle")

    def test_match_at_end(self):
        text = "text ending with the needle"
        result = _extract_match_context(text, "needle", context_chars=10)
        assert "needle" in result

    def test_ellipsis_added(self):
        text = "a" * 50 + "needle" + "b" * 50
        result = _extract_match_context(text, "needle", context_chars=10)
        # Should have ellipsis on both sides
        assert "\u2026" in result
