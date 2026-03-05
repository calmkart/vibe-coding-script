"""Tests for dashboard.utils.export module."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dashboard.utils.export import export_to_markdown, export_to_json


# ============================================================
# export_to_markdown tests
# ============================================================

class TestExportToMarkdown:
    def _sample_messages(self):
        return [
            {"role": "user", "content": "Hello, can you help me?", "timestamp": "2024-01-01T10:00:00Z"},
            {"role": "assistant", "content": "Of course! How can I help?", "timestamp": "2024-01-01T10:01:00Z"},
        ]

    def test_creates_file(self, tmp_path):
        output = str(tmp_path / "test.md")
        result = export_to_markdown(
            session_id="abc123",
            project_name="TestProject",
            git_branch="main",
            created="2024-01-01T10:00:00Z",
            messages=self._sample_messages(),
            output_path=output,
        )
        assert result == output
        assert os.path.exists(output)

    def test_markdown_content(self, tmp_path):
        output = str(tmp_path / "test.md")
        export_to_markdown(
            session_id="abc123",
            project_name="TestProject",
            git_branch="main",
            created="2024-01-01T10:00:00Z",
            messages=self._sample_messages(),
            output_path=output,
        )
        content = open(output).read()
        assert "# Claude Code Session" in content
        assert "abc123" in content
        assert "TestProject" in content
        assert "main" in content
        assert "## User" in content
        assert "## Assistant" in content
        assert "Hello, can you help me?" in content
        assert "Of course! How can I help?" in content

    def test_empty_messages(self, tmp_path):
        output = str(tmp_path / "empty.md")
        export_to_markdown(
            session_id="abc123",
            project_name="TestProject",
            git_branch="main",
            created="2024-01-01",
            messages=[],
            output_path=output,
        )
        content = open(output).read()
        assert "# Claude Code Session" in content
        assert "Messages:** 0" in content

    def test_tool_use_content(self, tmp_path):
        output = str(tmp_path / "tools.md")
        messages = [
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Let me check that file."},
                    {"type": "tool_use", "name": "read_file", "input": {"path": "/test.py"}},
                ],
                "timestamp": "2024-01-01T10:00:00Z",
            }
        ]
        export_to_markdown(
            session_id="abc123",
            project_name="TestProject",
            git_branch="main",
            created="2024-01-01",
            messages=messages,
            output_path=output,
        )
        content = open(output).read()
        assert "read_file" in content
        assert "Tool:" in content

    def test_thinking_content(self, tmp_path):
        output = str(tmp_path / "thinking.md")
        messages = [
            {
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": "Let me think about this..."},
                    {"type": "text", "text": "Here is my answer."},
                ],
                "timestamp": "2024-01-01T10:00:00Z",
            }
        ]
        export_to_markdown(
            session_id="abc123",
            project_name="TestProject",
            git_branch="main",
            created="2024-01-01",
            messages=messages,
            output_path=output,
        )
        content = open(output).read()
        assert "Thinking" in content
        assert "Here is my answer" in content

    def test_list_content_user(self, tmp_path):
        output = str(tmp_path / "list_user.md")
        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": "Multi-block user message"}],
                "timestamp": "2024-01-01T10:00:00Z",
            }
        ]
        export_to_markdown(
            session_id="abc123",
            project_name="TestProject",
            git_branch="main",
            created="2024-01-01",
            messages=messages,
            output_path=output,
        )
        content = open(output).read()
        assert "Multi-block user message" in content

    def test_creates_directory_if_needed(self, tmp_path):
        output = str(tmp_path / "subdir" / "nested" / "test.md")
        export_to_markdown(
            session_id="abc123",
            project_name="TestProject",
            git_branch="main",
            created="2024-01-01",
            messages=[],
            output_path=output,
        )
        assert os.path.exists(output)

    def test_large_tool_input_truncated(self, tmp_path):
        output = str(tmp_path / "large_tool.md")
        large_input = {"data": "x" * 2000}
        messages = [
            {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "name": "write_file", "input": large_input},
                ],
                "timestamp": "2024-01-01T10:00:00Z",
            }
        ]
        export_to_markdown(
            session_id="abc123",
            project_name="TestProject",
            git_branch="main",
            created="2024-01-01",
            messages=messages,
            output_path=output,
        )
        content = open(output).read()
        assert "[truncated]" in content


# ============================================================
# export_to_json tests
# ============================================================

class TestExportToJson:
    def _sample_messages(self):
        return [
            {"role": "user", "content": "Hello", "timestamp": "2024-01-01T10:00:00Z"},
            {"role": "assistant", "content": "Hi there", "timestamp": "2024-01-01T10:01:00Z"},
        ]

    def test_creates_file(self, tmp_path):
        output = str(tmp_path / "test.json")
        result = export_to_json(
            session_id="abc123",
            project_name="TestProject",
            git_branch="main",
            created="2024-01-01",
            messages=self._sample_messages(),
            output_path=output,
        )
        assert result == output
        assert os.path.exists(output)

    def test_valid_json(self, tmp_path):
        output = str(tmp_path / "test.json")
        export_to_json(
            session_id="abc123",
            project_name="TestProject",
            git_branch="main",
            created="2024-01-01",
            messages=self._sample_messages(),
            output_path=output,
        )
        with open(output) as f:
            data = json.load(f)

        assert data["session_id"] == "abc123"
        assert data["project"] == "TestProject"
        assert data["git_branch"] == "main"
        assert data["message_count"] == 2
        assert len(data["messages"]) == 2
        assert "exported" in data

    def test_empty_messages(self, tmp_path):
        output = str(tmp_path / "empty.json")
        export_to_json(
            session_id="abc123",
            project_name="TestProject",
            git_branch="main",
            created="2024-01-01",
            messages=[],
            output_path=output,
        )
        with open(output) as f:
            data = json.load(f)
        assert data["message_count"] == 0
        assert data["messages"] == []

    def test_creates_directory_if_needed(self, tmp_path):
        output = str(tmp_path / "subdir" / "test.json")
        export_to_json(
            session_id="abc123",
            project_name="TestProject",
            git_branch="main",
            created="2024-01-01",
            messages=[],
            output_path=output,
        )
        assert os.path.exists(output)

    def test_unicode_content(self, tmp_path):
        output = str(tmp_path / "unicode.json")
        messages = [
            {"role": "user", "content": "Hello \u4e16\u754c \U0001f30d", "timestamp": "t1"},
        ]
        export_to_json(
            session_id="abc123",
            project_name="TestProject",
            git_branch="main",
            created="2024-01-01",
            messages=messages,
            output_path=output,
        )
        with open(output, encoding="utf-8") as f:
            data = json.load(f)
        assert "\u4e16\u754c" in data["messages"][0]["content"]
        assert "\U0001f30d" in data["messages"][0]["content"]
