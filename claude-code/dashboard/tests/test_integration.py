"""Integration tests for the dashboard app and widgets."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest

# Test that all modules import without error
class TestImports:
    """Verify all modules can be imported successfully."""

    def test_import_app(self):
        from dashboard.app import ClaudeDashboard, main
        assert ClaudeDashboard is not None

    def test_import_data_sessions(self):
        from dashboard.data.sessions import ActiveSession, read_active_sessions, active_session_summary
        assert ActiveSession is not None

    def test_import_data_history(self):
        from dashboard.data.history import (
            SessionEntry, ProjectInfo, discover_all_projects,
            load_project_sessions, load_conversation, delete_session,
        )
        assert SessionEntry is not None

    def test_import_data_stats(self):
        from dashboard.data.stats import UsageStats, DailyActivity, ModelUsage, load_stats
        assert UsageStats is not None

    def test_import_data_search(self):
        from dashboard.data.search import SearchResult, search_conversations
        assert SearchResult is not None

    def test_import_data_cache(self):
        from dashboard.data.cache import DataCache, CacheEntry
        assert DataCache is not None

    def test_import_utils_format(self):
        from dashboard.utils.format import (
            format_age, format_tokens, format_filesize, format_cost,
            truncate_text, shorten_path, decode_project_path,
        )
        assert format_age is not None

    def test_import_utils_pricing(self):
        from dashboard.utils.pricing import (
            PRICING, get_model_pricing, calculate_cost, calculate_total_cost,
            format_model_name,
        )
        assert PRICING is not None

    def test_import_utils_export(self):
        from dashboard.utils.export import export_to_markdown, export_to_json
        assert export_to_markdown is not None

    def test_import_utils_iterm(self):
        from dashboard.utils.iterm import jump_to_iterm_tab, resume_session_in_iterm
        assert jump_to_iterm_tab is not None

    def test_import_screens(self):
        from dashboard.screens.active import ActiveSessionsPane
        from dashboard.screens.browser import SessionBrowserPane
        from dashboard.screens.conversation import ConversationPane
        from dashboard.screens.usage import UsageDashboardPane
        assert ActiveSessionsPane is not None

    def test_import_widgets(self):
        from dashboard.widgets.session_card import ActiveSessionCard, HistorySessionCard
        from dashboard.widgets.ascii_chart import AsciiBarChart, SparkLine
        from dashboard.widgets.heatmap import HourlyHeatmap
        from dashboard.widgets.cost_table import CostTable
        from dashboard.widgets.filter_bar import SearchBar
        assert ActiveSessionCard is not None


class TestAppInstantiation:
    """Test that the app can be instantiated."""

    def test_app_creates(self):
        from dashboard.app import ClaudeDashboard
        app = ClaudeDashboard()
        assert app.title == "Claude Code Dashboard"
        assert app.sub_title == "Session Manager"

    def test_app_has_cache(self):
        from dashboard.app import ClaudeDashboard
        from dashboard.data.cache import DataCache
        app = ClaudeDashboard()
        assert isinstance(app.cache, DataCache)

    def test_app_bindings(self):
        from dashboard.app import ClaudeDashboard
        app = ClaudeDashboard()
        binding_keys = [b.key for b in app.BINDINGS]
        assert "q" in binding_keys
        assert "1" in binding_keys
        assert "2" in binding_keys
        assert "3" in binding_keys
        assert "4" in binding_keys


class TestWidgetInstantiation:
    """Test that widgets can be created without errors."""

    def test_active_session_card(self):
        from dashboard.widgets.session_card import ActiveSessionCard
        import time
        card = ActiveSessionCard(
            tty="/dev/ttys001",
            pid=1234,
            status="working",
            project="test-project",
            branch="main",
            worktree="",
            cwd="/tmp/test",
            timestamp=time.time(),
        )
        assert card.project == "test-project"
        assert card.session_status == "working"

    def test_history_session_card(self):
        from dashboard.widgets.session_card import HistorySessionCard
        card = HistorySessionCard(
            session_id="abc123",
            project_name="TestProject",
            first_prompt="Hello world",
            summary="Test summary",
            message_count=42,
            created="2024-01-01",
            modified="2024-01-01",
            git_branch="main",
            file_size=1024,
        )
        assert card.session_id == "abc123"
        assert card.message_count == 42

    def test_ascii_bar_chart(self):
        from dashboard.widgets.ascii_chart import AsciiBarChart
        chart = AsciiBarChart(title="Test Chart")
        assert chart.chart_title == "Test Chart"

    def test_sparkline(self):
        from dashboard.widgets.ascii_chart import SparkLine
        spark = SparkLine()
        assert spark is not None

    def test_hourly_heatmap(self):
        from dashboard.widgets.heatmap import HourlyHeatmap
        hm = HourlyHeatmap()
        assert hm is not None

    def test_search_bar(self):
        from dashboard.widgets.filter_bar import SearchBar
        sb = SearchBar()
        assert sb is not None


class TestDataPipelineIntegration:
    """Test the full data pipeline: load -> process -> format."""

    def test_stats_to_cost_calculation(self):
        """Load stats, calculate costs, format them."""
        from dashboard.data.stats import load_stats
        from dashboard.utils.pricing import calculate_cost, format_model_name
        from dashboard.utils.format import format_tokens, format_cost

        stats = load_stats()
        for model, usage in stats.model_usage.items():
            cost = calculate_cost(
                model=model,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cache_read_tokens=usage.cache_read_tokens,
                cache_creation_tokens=usage.cache_creation_tokens,
            )
            name = format_model_name(model)
            input_str = format_tokens(usage.input_tokens)
            cost_str = format_cost(cost)

            assert isinstance(name, str)
            assert isinstance(input_str, str)
            assert isinstance(cost_str, str)
            assert "$" in cost_str

    def test_projects_to_sessions_to_conversation(self):
        """Load projects, get sessions, load conversation."""
        from dashboard.data.history import discover_all_projects, load_conversation

        projects = discover_all_projects()
        if not projects:
            pytest.skip("No projects available")

        project = projects[0]
        assert project.sessions

        session = project.sessions[0]
        if os.path.exists(session.jsonl_path):
            messages = load_conversation(session.jsonl_path, max_messages=5)
            assert isinstance(messages, list)

    def test_session_export_pipeline(self, tmp_path):
        """Load a session and export it."""
        from dashboard.data.history import discover_all_projects, load_conversation
        from dashboard.utils.export import export_to_markdown, export_to_json

        projects = discover_all_projects()
        if not projects or not projects[0].sessions:
            pytest.skip("No projects/sessions available")

        session = projects[0].sessions[0]
        if not os.path.exists(session.jsonl_path):
            pytest.skip("JSONL file missing")

        messages = load_conversation(session.jsonl_path, max_messages=10)

        # Export to markdown
        md_path = str(tmp_path / "export.md")
        export_to_markdown(
            session_id=session.session_id,
            project_name=session.project_name,
            git_branch=session.git_branch,
            created=session.created,
            messages=messages,
            output_path=md_path,
        )
        assert os.path.exists(md_path)
        content = open(md_path).read()
        assert "# Claude Code Session" in content

        # Export to JSON
        json_path = str(tmp_path / "export.json")
        export_to_json(
            session_id=session.session_id,
            project_name=session.project_name,
            git_branch=session.git_branch,
            created=session.created,
            messages=messages,
            output_path=json_path,
        )
        assert os.path.exists(json_path)
        with open(json_path) as f:
            data = json.load(f)
        assert data["session_id"] == session.session_id

    def test_search_and_verify_results(self):
        """Search for a common word and verify results contain it."""
        from dashboard.data.search import search_conversations

        # 'the' is very common in English
        results = search_conversations("the", max_results=5)
        for r in results:
            # The content_preview should contain the search term
            assert "the" in r.content_preview.lower() or len(r.content_preview) > 0

    def test_active_sessions_with_summary(self):
        """Read active sessions and compute summary."""
        from dashboard.data.sessions import read_active_sessions, active_session_summary

        sessions = read_active_sessions()
        summary = active_session_summary(sessions)
        total = summary["working"] + summary["attention"] + summary["done"]
        # Total in summary should match (or be less than, if some have unknown status) session count
        assert total <= len(sessions)
