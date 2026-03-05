"""Acceptance tests for all bug fixes in the Claude Code Terminal Dashboard.

Each test verifies a specific bug fix works correctly.
"""
import json
import os
import sys
import tempfile
import time

import pytest

# Ensure dashboard package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# =============================================================================
# TEST 1: Active session polling no longer destroys focus
# =============================================================================

class TestFix1_SessionsEqual:
    """Verify _sessions_equal() method exists and change detection works."""

    def test_sessions_equal_method_exists(self):
        """_sessions_equal must exist on ActiveSessionsPane."""
        from dashboard.screens.active import ActiveSessionsPane
        assert hasattr(ActiveSessionsPane, '_sessions_equal'), \
            "_sessions_equal method does not exist on ActiveSessionsPane"

    def test_sessions_equal_same_sessions(self):
        """Identical session lists should be considered equal."""
        from dashboard.screens.active import ActiveSessionsPane
        from dashboard.data.sessions import ActiveSession

        # Create two identical session lists
        s1 = ActiveSession(
            tty="/dev/ttys001", pid=1234, status="working",
            project="myproj", branch="main", worktree="", cwd="/tmp",
            timestamp=time.time(),
        )
        s2 = ActiveSession(
            tty="/dev/ttys001", pid=1234, status="working",
            project="myproj", branch="main", worktree="", cwd="/tmp",
            timestamp=time.time(),
        )

        pane = ActiveSessionsPane.__new__(ActiveSessionsPane)
        assert pane._sessions_equal([s1], [s2]) is True

    def test_sessions_equal_different_sessions(self):
        """Different session lists should NOT be considered equal."""
        from dashboard.screens.active import ActiveSessionsPane
        from dashboard.data.sessions import ActiveSession

        s1 = ActiveSession(
            tty="/dev/ttys001", pid=1234, status="working",
            project="myproj", branch="main", worktree="", cwd="/tmp",
            timestamp=time.time(),
        )
        s2 = ActiveSession(
            tty="/dev/ttys002", pid=5678, status="attention",
            project="other", branch="dev", worktree="", cwd="/home",
            timestamp=time.time(),
        )

        pane = ActiveSessionsPane.__new__(ActiveSessionsPane)
        assert pane._sessions_equal([s1], [s2]) is False

    def test_sessions_equal_different_lengths(self):
        """Lists of different lengths should NOT be equal."""
        from dashboard.screens.active import ActiveSessionsPane
        from dashboard.data.sessions import ActiveSession

        s1 = ActiveSession(
            tty="/dev/ttys001", pid=1234, status="working",
            project="myproj", branch="main", worktree="", cwd="/tmp",
            timestamp=time.time(),
        )

        pane = ActiveSessionsPane.__new__(ActiveSessionsPane)
        assert pane._sessions_equal([s1], []) is False
        assert pane._sessions_equal([], [s1]) is False

    def test_sessions_equal_empty_lists(self):
        """Two empty lists should be equal."""
        from dashboard.screens.active import ActiveSessionsPane
        pane = ActiveSessionsPane.__new__(ActiveSessionsPane)
        assert pane._sessions_equal([], []) is True

    def test_refresh_sessions_skips_rebuild_when_equal(self):
        """Verify the _async_refresh method has the equality check.

        We verify this by inspecting the method source code contains
        the _sessions_equal check and the early return.
        """
        import inspect
        from dashboard.screens.active import ActiveSessionsPane
        source = inspect.getsource(ActiveSessionsPane._async_refresh)
        assert '_sessions_equal' in source, \
            "_async_refresh does not call _sessions_equal"
        assert 'return' in source.split('_sessions_equal')[1][:100], \
            "_async_refresh does not return early when sessions are equal"

    def test_refresh_sessions_saves_and_restores_focus(self):
        """Verify the _async_refresh method saves focused card ID before rebuild."""
        import inspect
        from dashboard.screens.active import ActiveSessionsPane
        source = inspect.getsource(ActiveSessionsPane._async_refresh)
        assert 'focused_id' in source, \
            "_async_refresh does not track focused card ID"
        # Verify it tries to restore focus after rebuild
        assert 'restore' in source.lower() or 'focus()' in source, \
            "_async_refresh does not restore focus after rebuild"


# =============================================================================
# TEST 2: _resolve_project_path handles non-existent directories
# =============================================================================

class TestFix2_ResolveProjectPath:
    """Verify _resolve_project_path handles non-existent directories gracefully."""

    def test_nonexistent_path_does_not_crash(self):
        """_resolve_project_path with nonexistent dir should NOT crash."""
        from dashboard.data.history import _resolve_project_path
        # This must not raise any exception
        result = _resolve_project_path("/nonexistent/path", "-Some-Dir")
        assert isinstance(result, str), "Should return a string"
        assert len(result) > 0, "Should return a non-empty string"

    def test_nonexistent_path_fallback_decoding(self):
        """Should fall back to decoding the dirname when directory doesn't exist."""
        from dashboard.data.history import _resolve_project_path
        result = _resolve_project_path("/nonexistent/path", "-Users-calmp-code")
        # The dash-encoded format: leading dash means starts with /
        assert result == "/Users/calmp/code", f"Got unexpected result: {result}"

    def test_load_project_sessions_nonexistent_returns_empty(self):
        """load_project_sessions with nonexistent project should return empty list, not crash.

        BUG FOUND: _load_from_jsonl_scan does os.listdir() on non-existent dir
        without checking existence first. _resolve_project_path is fixed but
        the downstream caller is not guarded.
        """
        from dashboard.data.history import load_project_sessions
        try:
            result = load_project_sessions("nonexistent-project-12345")
            assert isinstance(result, list), "Should return a list"
            assert len(result) == 0, f"Should return empty list, got {len(result)} items"
        except FileNotFoundError:
            pytest.fail(
                "REMAINING BUG: load_project_sessions crashes with FileNotFoundError "
                "when project directory does not exist. _load_from_jsonl_scan needs "
                "an os.path.isdir() guard before os.listdir()."
            )


# =============================================================================
# TEST 3: load_conversation with max_messages=0 returns empty
# =============================================================================

class TestFix3_MaxMessagesZero:
    """Verify load_conversation with max_messages=0 returns empty list."""

    def _create_test_jsonl(self):
        """Create a temp JSONL file with valid conversation data."""
        tmpfile = tempfile.NamedTemporaryFile(
            mode='w', suffix='.jsonl', delete=False
        )
        for i in range(5):
            msg = {
                "timestamp": f"2024-01-01T00:0{i}:00Z",
                "message": {
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": f"Test message {i}",
                },
                "uuid": f"uuid-{i}",
            }
            tmpfile.write(json.dumps(msg) + "\n")
        tmpfile.close()
        return tmpfile.name

    def test_max_messages_zero_returns_empty(self):
        """max_messages=0 must return empty list."""
        from dashboard.data.history import load_conversation
        path = self._create_test_jsonl()
        try:
            result = load_conversation(path, max_messages=0)
            assert result == [], f"Expected empty list, got {len(result)} items"
        finally:
            os.unlink(path)

    def test_max_messages_one_returns_exactly_one(self):
        """max_messages=1 must return exactly 1 message."""
        from dashboard.data.history import load_conversation
        path = self._create_test_jsonl()
        try:
            result = load_conversation(path, max_messages=1)
            assert len(result) == 1, f"Expected 1 message, got {len(result)}"
        finally:
            os.unlink(path)

    def test_max_messages_default_loads_all(self):
        """Default max_messages should load all messages."""
        from dashboard.data.history import load_conversation
        path = self._create_test_jsonl()
        try:
            result = load_conversation(path)
            assert len(result) == 5, f"Expected 5 messages, got {len(result)}"
        finally:
            os.unlink(path)

    def test_max_messages_negative_returns_empty(self):
        """max_messages=-1 should also return empty (negative is <= 0)."""
        from dashboard.data.history import load_conversation
        path = self._create_test_jsonl()
        try:
            result = load_conversation(path, max_messages=-1)
            assert result == [], f"Expected empty list, got {len(result)} items"
        finally:
            os.unlink(path)


# =============================================================================
# TEST 4: load_conversation handles binary files
# =============================================================================

class TestFix4_BinaryFileHandling:
    """Verify load_conversation does not crash on binary files."""

    def test_binary_file_does_not_crash(self):
        """Calling load_conversation on a binary file must not raise."""
        from dashboard.data.history import load_conversation
        # Create a temp binary file
        tmpfile = tempfile.NamedTemporaryFile(
            suffix='.jsonl', delete=False, mode='wb'
        )
        tmpfile.write(bytes(range(256)) * 10)  # 2560 bytes of binary data
        tmpfile.close()

        try:
            result = load_conversation(tmpfile.name)
            assert isinstance(result, list), "Should return a list"
            # It's OK if the list is empty - just shouldn't crash
        finally:
            os.unlink(tmpfile.name)

    def test_binary_file_with_null_bytes(self):
        """File with null bytes should be handled gracefully."""
        from dashboard.data.history import load_conversation
        tmpfile = tempfile.NamedTemporaryFile(
            suffix='.jsonl', delete=False, mode='wb'
        )
        tmpfile.write(b'\x00' * 1000)
        tmpfile.close()

        try:
            result = load_conversation(tmpfile.name)
            assert isinstance(result, list), "Should return a list"
        finally:
            os.unlink(tmpfile.name)

    def test_mixed_binary_and_valid_json(self):
        """File with some binary and some valid JSON should parse what it can."""
        from dashboard.data.history import load_conversation
        tmpfile = tempfile.NamedTemporaryFile(
            suffix='.jsonl', delete=False, mode='wb'
        )
        # Write some garbage then a valid message
        tmpfile.write(b'\x89PNG\r\n\x1a\n garbage\n')
        valid_msg = json.dumps({
            "timestamp": "2024-01-01T00:00:00Z",
            "message": {"role": "user", "content": "hello"},
            "uuid": "test-uuid",
        })
        tmpfile.write(valid_msg.encode('utf-8') + b'\n')
        tmpfile.write(b'\xff\xfe binary trailing data\n')
        tmpfile.close()

        try:
            result = load_conversation(tmpfile.name)
            assert isinstance(result, list), "Should return a list"
            # Should have parsed the valid line
            assert len(result) >= 1, "Should have parsed at least the valid JSON line"
        finally:
            os.unlink(tmpfile.name)


# =============================================================================
# TEST 5: Escape from conversation tracks origin tab
# =============================================================================

class TestFix5_ConversationOrigin:
    """Verify conversation origin tracking for back navigation."""

    def test_conversation_origin_attribute_exists(self):
        """ClaudeDashboard must have _conversation_origin attribute."""
        from dashboard.app import ClaudeDashboard
        app = ClaudeDashboard.__new__(ClaudeDashboard)
        # The attribute is set in __init__
        # Let's verify by inspecting __init__
        import inspect
        source = inspect.getsource(ClaudeDashboard.__init__)
        assert '_conversation_origin' in source, \
            "_conversation_origin not initialized in __init__"

    def test_conversation_origin_default_is_tab_history(self):
        """Default _conversation_origin should be 'tab-history'."""
        import inspect
        from dashboard.app import ClaudeDashboard
        source = inspect.getsource(ClaudeDashboard.__init__)
        assert '"tab-history"' in source or "'tab-history'" in source, \
            "_conversation_origin default is not 'tab-history'"

    def test_active_handler_sets_origin_to_tab_active(self):
        """on_active_sessions_pane_view_conversation must set origin to tab-active."""
        import inspect
        from dashboard.app import ClaudeDashboard
        source = inspect.getsource(ClaudeDashboard.on_active_sessions_pane_view_conversation)
        assert '"tab-active"' in source or "'tab-active'" in source, \
            "on_active_sessions_pane_view_conversation does not set origin to 'tab-active'"

    def test_history_handler_sets_origin_to_tab_history(self):
        """on_session_browser_pane_view_conversation must set origin to tab-history."""
        import inspect
        from dashboard.app import ClaudeDashboard
        source = inspect.getsource(ClaudeDashboard.on_session_browser_pane_view_conversation)
        assert '"tab-history"' in source or "'tab-history'" in source, \
            "on_session_browser_pane_view_conversation does not set origin to 'tab-history'"

    def test_go_back_uses_conversation_origin(self):
        """on_conversation_pane_go_back must use self._conversation_origin."""
        import inspect
        from dashboard.app import ClaudeDashboard
        source = inspect.getsource(ClaudeDashboard.on_conversation_pane_go_back)
        assert '_conversation_origin' in source, \
            "on_conversation_pane_go_back does not use _conversation_origin"


# =============================================================================
# TEST 6: Search is now wired up
# =============================================================================

class TestFix6_SearchWiredUp:
    """Verify search functionality is wired up correctly."""

    def test_search_screen_class_exists(self):
        """SearchScreen class must exist in app module."""
        from dashboard.app import SearchScreen
        assert SearchScreen is not None

    def test_search_screen_is_modal(self):
        """SearchScreen must be a ModalScreen."""
        from dashboard.app import SearchScreen
        from textual.screen import ModalScreen
        assert issubclass(SearchScreen, ModalScreen), \
            "SearchScreen is not a subclass of ModalScreen"

    def test_search_screen_has_input_handler(self):
        """SearchScreen must have on_input_submitted handler."""
        from dashboard.app import SearchScreen
        assert hasattr(SearchScreen, 'on_input_submitted'), \
            "SearchScreen does not have on_input_submitted handler"

    def test_search_screen_calls_search_conversations(self):
        """SearchScreen.on_input_submitted must call search_conversations."""
        import inspect
        from dashboard.app import SearchScreen
        source = inspect.getsource(SearchScreen.on_input_submitted)
        assert 'search_conversations' in source, \
            "on_input_submitted does not call search_conversations"

    def test_search_conversations_function_exists(self):
        """search_conversations function must exist in data/search.py."""
        from dashboard.data.search import search_conversations
        assert callable(search_conversations)

    def test_search_conversations_empty_query_returns_empty(self):
        """Empty query should return empty results."""
        from dashboard.data.search import search_conversations
        result = search_conversations("")
        assert result == [], f"Expected empty list for empty query, got {len(result)} items"

    def test_search_conversations_nonexistent_query(self):
        """A query that matches nothing should return empty list, not crash."""
        from dashboard.data.search import search_conversations
        result = search_conversations("xyzzy_nonexistent_query_12345_unique")
        assert isinstance(result, list)

    def test_app_has_search_action(self):
        """ClaudeDashboard must have action_search method."""
        from dashboard.app import ClaudeDashboard
        assert hasattr(ClaudeDashboard, 'action_search'), \
            "ClaudeDashboard does not have action_search"

    def test_app_search_action_opens_search_screen(self):
        """action_search should open SearchScreen."""
        import inspect
        from dashboard.app import ClaudeDashboard
        source = inspect.getsource(ClaudeDashboard.action_search)
        assert 'SearchScreen' in source, \
            "action_search does not reference SearchScreen"


# =============================================================================
# TEST 7: Delete confirmation tracks session ID
# =============================================================================

class TestFix7_DeleteConfirmation:
    """Verify delete uses a modal confirmation dialog."""

    def test_delete_action_uses_modal(self):
        """action_delete_session must use DeleteConfirmScreen modal."""
        import inspect
        from dashboard.screens.browser import SessionBrowserPane
        source = inspect.getsource(SessionBrowserPane.action_delete_session)
        assert 'DeleteConfirmScreen' in source, \
            "action_delete_session does not use DeleteConfirmScreen modal"

    def test_delete_confirm_screen_exists(self):
        """DeleteConfirmScreen must be defined."""
        from dashboard.screens.browser import DeleteConfirmScreen
        assert DeleteConfirmScreen is not None

    def test_delete_action_references_session_id(self):
        """action_delete_session must reference session_id."""
        import inspect
        from dashboard.screens.browser import SessionBrowserPane
        source = inspect.getsource(SessionBrowserPane.action_delete_session)
        assert 'session_id' in source or 'session.session_id' in source, \
            "action_delete_session does not reference session_id"

    def test_delete_action_has_callback(self):
        """action_delete_session must use a callback for the modal result."""
        import inspect
        from dashboard.screens.browser import SessionBrowserPane
        source = inspect.getsource(SessionBrowserPane.action_delete_session)
        assert 'callback' in source, \
            "action_delete_session does not use a callback"

    def test_confirm_screen_has_escape_binding(self):
        """DeleteConfirmScreen must have Escape to cancel."""
        from dashboard.screens.browser import DeleteConfirmScreen
        binding_keys = [b.key for b in DeleteConfirmScreen.BINDINGS]
        assert 'escape' in binding_keys, \
            "DeleteConfirmScreen missing escape binding"


# =============================================================================
# TEST 8: Usage dashboard shows empty state
# =============================================================================

class TestFix8_UsageEmptyState:
    """Verify usage dashboard handles missing stats gracefully."""

    def test_render_dashboard_handles_none_stats(self):
        """_render_dashboard should not crash when _stats is None."""
        import inspect
        from dashboard.screens.usage import UsageDashboardPane
        source = inspect.getsource(UsageDashboardPane._render_dashboard)
        # Must check for None/empty stats before accessing attributes
        assert 'not self._stats' in source or 'self._stats is None' in source, \
            "_render_dashboard does not check for missing stats"

    def test_empty_state_message_displayed(self):
        """When stats are None, should display an informative empty state."""
        import inspect
        from dashboard.screens.usage import UsageDashboardPane
        source = inspect.getsource(UsageDashboardPane._render_dashboard)
        # After the None check, there should be an early return or message
        assert 'No usage data' in source or 'no usage' in source.lower() or '0' in source, \
            "No empty state message found in _render_dashboard"

    def test_empty_state_shows_zero_values(self):
        """Empty state should show 0 for sessions, messages, cost."""
        import inspect
        from dashboard.screens.usage import UsageDashboardPane
        source = inspect.getsource(UsageDashboardPane._render_dashboard)
        # Check it sets card values to zero/NA
        null_check_block = source.split('not self._stats')[0:2]
        assert len(null_check_block) > 1, "Could not find the null check block"
        after_null_check = source.split('not self._stats')[1].split('return')[0]
        assert '$0.00' in after_null_check or 'N/A' in after_null_check or '0' in after_null_check, \
            "Empty state does not show zero/NA values"


# =============================================================================
# TEST 9: Low contrast text fixed
# =============================================================================

class TestFix9_LowContrast:
    """Verify no remaining #555 or #666 in style/widget files."""

    @pytest.mark.parametrize("filepath", [
        "/Users/calmp/Desktop/code/vibe-coding-script/claude-code/dashboard/styles/dashboard.tcss",
        "/Users/calmp/Desktop/code/vibe-coding-script/claude-code/dashboard/widgets/session_card.py",
        "/Users/calmp/Desktop/code/vibe-coding-script/claude-code/dashboard/screens/active.py",
        "/Users/calmp/Desktop/code/vibe-coding-script/claude-code/dashboard/screens/conversation.py",
    ])
    def test_no_555_color(self, filepath):
        """No #555 color values should remain."""
        if not os.path.exists(filepath):
            pytest.skip(f"File not found: {filepath}")
        with open(filepath) as f:
            content = f.read()
        # Check for #555 as a color value (not part of a longer hex like #555555)
        import re
        matches = re.findall(r'#555(?![0-9a-fA-F])', content)
        assert len(matches) == 0, \
            f"Found {len(matches)} instances of #555 in {os.path.basename(filepath)}"

    @pytest.mark.parametrize("filepath", [
        "/Users/calmp/Desktop/code/vibe-coding-script/claude-code/dashboard/styles/dashboard.tcss",
        "/Users/calmp/Desktop/code/vibe-coding-script/claude-code/dashboard/widgets/session_card.py",
        "/Users/calmp/Desktop/code/vibe-coding-script/claude-code/dashboard/screens/active.py",
        "/Users/calmp/Desktop/code/vibe-coding-script/claude-code/dashboard/screens/conversation.py",
    ])
    def test_no_666_color(self, filepath):
        """No #666 color values should remain."""
        if not os.path.exists(filepath):
            pytest.skip(f"File not found: {filepath}")
        with open(filepath) as f:
            content = f.read()
        import re
        matches = re.findall(r'#666(?![0-9a-fA-F])', content)
        assert len(matches) == 0, \
            f"Found {len(matches)} instances of #666 in {os.path.basename(filepath)}"

    def test_uses_777_or_888(self):
        """Files should use #777 or #888 for subdued text instead."""
        files_to_check = [
            "/Users/calmp/Desktop/code/vibe-coding-script/claude-code/dashboard/styles/dashboard.tcss",
            "/Users/calmp/Desktop/code/vibe-coding-script/claude-code/dashboard/widgets/session_card.py",
            "/Users/calmp/Desktop/code/vibe-coding-script/claude-code/dashboard/screens/active.py",
            "/Users/calmp/Desktop/code/vibe-coding-script/claude-code/dashboard/screens/conversation.py",
        ]
        found_777_or_888 = False
        for filepath in files_to_check:
            if os.path.exists(filepath):
                with open(filepath) as f:
                    content = f.read()
                if '#777' in content or '#888' in content:
                    found_777_or_888 = True
                    break
        assert found_777_or_888, "Neither #777 nor #888 found in any of the checked files"


# =============================================================================
# TEST 10: Project name truncation
# =============================================================================

class TestFix10_ProjectNameTruncation:
    """Verify project names > 24 chars are truncated with ellipsis."""

    def test_truncation_logic_in_source(self):
        """_rebuild_project_list must truncate names > 24 chars."""
        import inspect
        from dashboard.screens.browser import SessionBrowserPane
        source = inspect.getsource(SessionBrowserPane._mount_project_list)
        assert '24' in source or 'truncat' in source.lower(), \
            "No truncation at 24 chars found in _rebuild_project_list"

    def test_truncation_uses_ellipsis(self):
        """Truncation should use an ellipsis character."""
        import inspect
        from dashboard.screens.browser import SessionBrowserPane
        source = inspect.getsource(SessionBrowserPane._mount_project_list)
        # Should use unicode ellipsis (literal or escaped) or '...'
        assert '\u2026' in source or '\\u2026' in source or '...' in source, \
            "No ellipsis character found in _rebuild_project_list"

    def test_short_names_not_truncated(self):
        """Names <= 24 chars should NOT be truncated."""
        import inspect
        from dashboard.screens.browser import SessionBrowserPane
        source = inspect.getsource(SessionBrowserPane._mount_project_list)
        # The logic should be: if len > 24 then truncate, else keep as-is
        assert 'len(' in source and '24' in source, \
            "Truncation logic does not check length against 24"


# =============================================================================
# TEST 11: Overview cards height
# =============================================================================

class TestFix11_OverviewCardsHeight:
    """Verify .overview-grid uses height: auto not height: 5."""

    def test_overview_grid_height_auto_in_tcss(self):
        """dashboard.tcss .overview-grid should use height: auto."""
        tcss_path = "/Users/calmp/Desktop/code/vibe-coding-script/claude-code/dashboard/styles/dashboard.tcss"
        with open(tcss_path) as f:
            content = f.read()
        # Find the .overview-grid block
        import re
        # Look for .overview-grid { ... height: auto ... }
        grid_match = re.search(r'\.overview-grid\s*\{([^}]+)\}', content)
        assert grid_match, ".overview-grid not found in dashboard.tcss"
        grid_block = grid_match.group(1)
        assert 'height: auto' in grid_block, \
            f".overview-grid does not have 'height: auto'. Found: {grid_block.strip()}"

    def test_overview_grid_not_height_5(self):
        """dashboard.tcss .overview-grid should NOT use height: 5."""
        tcss_path = "/Users/calmp/Desktop/code/vibe-coding-script/claude-code/dashboard/styles/dashboard.tcss"
        with open(tcss_path) as f:
            content = f.read()
        import re
        grid_match = re.search(r'\.overview-grid\s*\{([^}]+)\}', content)
        assert grid_match, ".overview-grid not found"
        grid_block = grid_match.group(1)
        assert 'height: 5' not in grid_block, \
            ".overview-grid still uses 'height: 5' (BUG NOT FIXED)"

    def test_overview_grid_height_auto_in_usage_py(self):
        """UsageDashboardPane DEFAULT_CSS should also use height: auto for overview-grid."""
        import inspect
        from dashboard.screens.usage import UsageDashboardPane
        # Check the DEFAULT_CSS
        css = UsageDashboardPane.DEFAULT_CSS
        if 'overview-grid' in css:
            assert 'height: auto' in css, \
                "UsageDashboardPane DEFAULT_CSS overview-grid does not use 'height: auto'"


# =============================================================================
# TEST 12: Full app integration test
# =============================================================================

class TestFix12_Integration:
    """Full app integration test - app starts without errors."""

    def test_app_instantiates(self):
        """ClaudeDashboard can be instantiated without error."""
        from dashboard.app import ClaudeDashboard
        app = ClaudeDashboard()
        assert app is not None
        assert app.TITLE == "Claude Code Dashboard"

    def test_app_has_all_four_tabs(self):
        """App compose should yield 4 TabPanes."""
        import inspect
        from dashboard.app import ClaudeDashboard
        source = inspect.getsource(ClaudeDashboard.compose)
        assert 'tab-active' in source, "Missing Active tab"
        assert 'tab-history' in source, "Missing History tab"
        assert 'tab-usage' in source, "Missing Usage tab"
        assert 'tab-conversation' in source, "Missing Conversation tab"

    def test_app_has_refresh_action(self):
        """App must have action_refresh_all method."""
        from dashboard.app import ClaudeDashboard
        assert hasattr(ClaudeDashboard, 'action_refresh_all')

    def test_app_has_search_binding(self):
        """App must have '/' bound to search."""
        from dashboard.app import ClaudeDashboard
        bindings = ClaudeDashboard.BINDINGS
        slash_binding = [b for b in bindings if b.key == 'slash']
        assert len(slash_binding) > 0, "No '/' (slash) binding found"

    def test_all_pane_classes_importable(self):
        """All pane classes must be importable."""
        from dashboard.screens.active import ActiveSessionsPane
        from dashboard.screens.browser import SessionBrowserPane
        from dashboard.screens.usage import UsageDashboardPane
        from dashboard.screens.conversation import ConversationPane
        assert ActiveSessionsPane is not None
        assert SessionBrowserPane is not None
        assert UsageDashboardPane is not None
        assert ConversationPane is not None

    def test_data_modules_importable(self):
        """All data modules must be importable."""
        from dashboard.data.history import load_conversation, discover_all_projects
        from dashboard.data.search import search_conversations
        from dashboard.data.sessions import read_active_sessions
        from dashboard.data.stats import load_stats
        from dashboard.data.cache import DataCache
        assert callable(load_conversation)
        assert callable(discover_all_projects)
        assert callable(search_conversations)
        assert callable(read_active_sessions)
        assert callable(load_stats)


# =============================================================================
# Run all tests when executed directly
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
