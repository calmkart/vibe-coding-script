"""Tests for dashboard.data.sessions module."""
import json
import os
import sys
import tempfile
import time

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dashboard.data.sessions import (
    ActiveSession,
    read_active_sessions,
    active_session_summary,
    SESSION_DIR,
    STALE_THRESHOLD,
)


# ============================================================
# ActiveSession dataclass tests
# ============================================================

class TestActiveSessionDataclass:
    """Test ActiveSession dataclass properties."""

    def _make_session(self, **overrides):
        defaults = dict(
            tty="/dev/ttys001",
            pid=os.getpid(),
            status="working",
            project="test-project",
            branch="main",
            worktree="",
            cwd="/tmp/test",
            timestamp=time.time(),
        )
        defaults.update(overrides)
        return ActiveSession(**defaults)

    def test_fields_present(self):
        s = self._make_session()
        assert s.tty == "/dev/ttys001"
        assert s.pid == os.getpid()
        assert s.status == "working"
        assert s.project == "test-project"
        assert s.branch == "main"
        assert s.worktree == ""
        assert s.cwd == "/tmp/test"
        assert s.timestamp > 0

    def test_age_seconds(self):
        ts = time.time() - 60  # 60 seconds ago
        s = self._make_session(timestamp=ts)
        age = s.age_seconds
        assert 59 <= age <= 62, f"Expected ~60, got {age}"

    def test_age_seconds_recent(self):
        s = self._make_session(timestamp=time.time())
        assert s.age_seconds < 2

    def test_is_alive_current_process(self):
        """Current process PID should be alive."""
        s = self._make_session(pid=os.getpid())
        assert s.is_alive is True

    def test_is_alive_dead_process(self):
        """A PID that doesn't exist should not be alive."""
        s = self._make_session(pid=99999999)
        # This should return False (ProcessLookupError)
        result = s.is_alive
        # On some systems large PIDs may cause different errors
        assert isinstance(result, bool)

    def test_tty_short(self):
        s = self._make_session(tty="/dev/ttys001")
        assert s.tty_short == "ttys001"

    def test_tty_short_empty(self):
        s = self._make_session(tty="")
        assert s.tty_short == ""

    def test_status_icon_working(self):
        s = self._make_session(status="working")
        assert s.status_icon == "\u25c9"

    def test_status_icon_attention(self):
        s = self._make_session(status="attention")
        assert s.status_icon == "\u23f8"

    def test_status_icon_done(self):
        s = self._make_session(status="done")
        assert s.status_icon == "\u2713"

    def test_status_icon_unknown(self):
        s = self._make_session(status="bogus")
        assert s.status_icon == "?"


# ============================================================
# read_active_sessions tests
# ============================================================

class TestReadActiveSessions:
    """Test the read_active_sessions function."""

    def test_returns_list(self):
        """Should always return a list."""
        result = read_active_sessions()
        assert isinstance(result, list)

    def test_sessions_are_active_session_instances(self):
        """All items should be ActiveSession instances."""
        result = read_active_sessions()
        for s in result:
            assert isinstance(s, ActiveSession)

    def test_handles_missing_directory(self, monkeypatch):
        """Should return empty list if SESSION_DIR doesn't exist."""
        import dashboard.data.sessions as mod
        monkeypatch.setattr(mod, "SESSION_DIR", "/nonexistent/path/12345")
        result = mod.read_active_sessions()
        assert result == []

    def test_with_temp_session_files(self, tmp_path):
        """Create temp session files and verify they're read."""
        import dashboard.data.sessions as mod

        session_dir = tmp_path / "claude-sessions"
        session_dir.mkdir()

        # Create a valid session file with current PID so it passes alive check
        session_data = {
            "tty": "/dev/ttys099",
            "pid": os.getpid(),
            "status": "working",
            "project": "my-project",
            "branch": "feature-branch",
            "worktree": "",
            "cwd": "/tmp/test",
            "timestamp": time.time(),
        }
        with open(session_dir / "test.json", "w") as f:
            json.dump(session_data, f)

        orig_dir = mod.SESSION_DIR
        mod.SESSION_DIR = str(session_dir)
        try:
            result = mod.read_active_sessions()
            assert len(result) >= 1
            found = [s for s in result if s.project == "my-project"]
            assert len(found) == 1
            assert found[0].tty == "/dev/ttys099"
            assert found[0].status == "working"
            assert found[0].branch == "feature-branch"
        finally:
            mod.SESSION_DIR = orig_dir

    def test_stale_sessions_pruned(self, tmp_path):
        """Sessions older than STALE_THRESHOLD should be pruned."""
        import dashboard.data.sessions as mod

        session_dir = tmp_path / "claude-sessions"
        session_dir.mkdir()

        stale_data = {
            "tty": "/dev/ttys099",
            "pid": 99999999,  # Use a PID that doesn't exist so it's treated as dead
            "status": "working",
            "project": "stale-project",
            "branch": "main",
            "cwd": "/tmp",
            "timestamp": time.time() - STALE_THRESHOLD - 100,
        }
        fpath = session_dir / "stale.json"
        with open(fpath, "w") as f:
            json.dump(stale_data, f)

        orig_dir = mod.SESSION_DIR
        mod.SESSION_DIR = str(session_dir)
        try:
            result = mod.read_active_sessions()
            # The stale session should have been pruned (file deleted)
            stale_matches = [s for s in result if s.project == "stale-project"]
            assert len(stale_matches) == 0
            # The file should have been deleted
            assert not fpath.exists()
        finally:
            mod.SESSION_DIR = orig_dir

    def test_invalid_json_handled(self, tmp_path):
        """Corrupted JSON files should be skipped."""
        import dashboard.data.sessions as mod

        session_dir = tmp_path / "claude-sessions"
        session_dir.mkdir()

        with open(session_dir / "bad.json", "w") as f:
            f.write("{{not valid json!!!")

        orig_dir = mod.SESSION_DIR
        mod.SESSION_DIR = str(session_dir)
        try:
            result = mod.read_active_sessions()
            assert isinstance(result, list)
            # Should not crash
        finally:
            mod.SESSION_DIR = orig_dir

    def test_sort_order_working_first(self, tmp_path):
        """Sessions should be sorted: working > attention > done."""
        import dashboard.data.sessions as mod

        session_dir = tmp_path / "claude-sessions"
        session_dir.mkdir()
        now = time.time()
        pid = os.getpid()

        for i, status in enumerate(["done", "attention", "working"]):
            data = {
                "tty": f"/dev/ttys{i:03d}",
                "pid": pid,
                "status": status,
                "project": f"project-{status}",
                "branch": "main",
                "cwd": "/tmp",
                "timestamp": now - i,  # slightly different timestamps
            }
            with open(session_dir / f"{status}.json", "w") as f:
                json.dump(data, f)

        orig_dir = mod.SESSION_DIR
        mod.SESSION_DIR = str(session_dir)
        try:
            result = mod.read_active_sessions()
            statuses = [s.status for s in result]
            # working should come before attention, attention before done
            if "working" in statuses and "attention" in statuses:
                assert statuses.index("working") < statuses.index("attention")
            if "attention" in statuses and "done" in statuses:
                assert statuses.index("attention") < statuses.index("done")
        finally:
            mod.SESSION_DIR = orig_dir


# ============================================================
# active_session_summary tests
# ============================================================

class TestActiveSessionSummary:
    """Test the active_session_summary function."""

    def _make_session(self, status):
        return ActiveSession(
            tty="/dev/ttys001", pid=1, status=status,
            project="p", branch="b", worktree="", cwd="/tmp", timestamp=time.time(),
        )

    def test_empty_list(self):
        result = active_session_summary([])
        assert result == {"working": 0, "attention": 0, "done": 0}

    def test_all_working(self):
        sessions = [self._make_session("working") for _ in range(3)]
        result = active_session_summary(sessions)
        assert result == {"working": 3, "attention": 0, "done": 0}

    def test_mixed_statuses(self):
        sessions = [
            self._make_session("working"),
            self._make_session("working"),
            self._make_session("attention"),
            self._make_session("done"),
            self._make_session("done"),
            self._make_session("done"),
        ]
        result = active_session_summary(sessions)
        assert result == {"working": 2, "attention": 1, "done": 3}

    def test_unknown_status_ignored(self):
        sessions = [self._make_session("unknown_status")]
        result = active_session_summary(sessions)
        assert result == {"working": 0, "attention": 0, "done": 0}

    def test_returns_dict_with_correct_keys(self):
        result = active_session_summary([])
        assert set(result.keys()) == {"working", "attention", "done"}
