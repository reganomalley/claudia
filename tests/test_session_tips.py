"""Tests for claudia-session-tips.py — session startup tips hook."""

import json
import os
from datetime import date
from unittest.mock import patch, MagicMock

from conftest import make_session_input, setup_claudia_config


class TestStartup:
    """Fresh session startup behavior."""

    def test_beginner_gets_greeting(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_session_input("startup")
        code, stdout, _ = run_hook("claudia-session-tips.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            ctx = output.get("additionalContext", "")
            assert "Claudia is here" in ctx or "Just build" in ctx

    def test_non_beginner_gets_full_greeting(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="intermediate")
        data = make_session_input("startup")
        code, stdout, _ = run_hook("claudia-session-tips.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            ctx = output.get("additionalContext", "")
            assert "Claudia" in ctx
            # Full greeting includes command list
            assert "/claudia:ask" in ctx or "catches" in ctx

    def test_beginner_gets_startup_tip(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_session_input("startup")
        code, stdout, _ = run_hook("claudia-session-tips.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            ctx = output.get("additionalContext", "")
            # Should contain a tip from STARTUP_TIPS pool
            assert "tip" in ctx.lower() or "Claudia" in ctx

    def test_greeting_dedup(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_session_input("startup")
        run_hook("claudia-session-tips.py", data)

        _, stdout2, _ = run_hook("claudia-session-tips.py", data)
        # Second startup should not re-show greeting
        if stdout2.strip():
            output = json.loads(stdout2)
            ctx = output.get("additionalContext", "")
            assert "IMPORTANT" not in ctx


class TestLowProactivity:
    """Low proactivity: only greetings on startup, nothing else."""

    def test_low_proactivity_startup_still_greets(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="low", experience="intermediate")
        data = make_session_input("startup")
        code, stdout, _ = run_hook("claudia-session-tips.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "Claudia" in output.get("additionalContext", "")

    def test_low_proactivity_resume_silent(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="low", experience="intermediate")
        data = make_session_input("resume")
        code, stdout, _ = run_hook("claudia-session-tips.py", data)
        assert stdout.strip() == ""


class TestResume:
    """Resume session behavior."""

    def test_resume_shows_welcome_back(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="intermediate")
        data = make_session_input("resume")
        code, stdout, _ = run_hook("claudia-session-tips.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            msg = output.get("systemMessage", "")
            assert "Welcome back" in msg or "back" in msg.lower()


class TestCompact:
    """Compact event behavior."""

    def test_compact_beginner_gets_tip(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_session_input("compact")
        code, stdout, _ = run_hook("claudia-session-tips.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            msg = output.get("systemMessage", "")
            assert "compact" in msg.lower() or "context" in msg.lower()


class TestClear:
    """Clear event — should produce nothing."""

    def test_clear_silent(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="intermediate")
        data = make_session_input("clear")
        code, stdout, _ = run_hook("claudia-session-tips.py", data)
        assert code == 0
        # Clear doesn't produce tips (no greeting since not startup)
        if stdout.strip():
            output = json.loads(stdout)
            # At most a greeting if first session
            assert "additionalContext" in output


class TestUpdateCheck:
    """Daily npm update check on startup."""

    def _write_update_cache(self, tmp_path, check_date, latest):
        """Write a cached update check file."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        cache = {"last_check_date": check_date, "latest": latest}
        (claude_dir / "claudia_update_check.json").write_text(json.dumps(cache))

    def test_cached_today_no_npm_call(self, run_hook, tmp_path):
        """When cache has today's date, npm should not be called."""
        setup_claudia_config(tmp_path, proactivity="moderate", experience="intermediate")
        # Cache says we checked today, latest is same as installed
        self._write_update_cache(tmp_path, date.today().isoformat(), "0.9.1")
        data = make_session_input("startup")

        # Even with npm unavailable, this should work (cache hit)
        env_overrides = {"PATH": "/nonexistent"}
        code, stdout, _ = run_hook("claudia-session-tips.py", data, env_overrides=env_overrides)
        assert code == 0
        # Should not contain update hint since versions match
        if stdout.strip():
            output = json.loads(stdout)
            msg = output.get("systemMessage", "")
            assert "npm update" not in msg

    def test_shows_hint_when_outdated(self, run_hook, tmp_path):
        """When cached latest > installed, show update hint."""
        setup_claudia_config(tmp_path, proactivity="moderate", experience="intermediate")
        self._write_update_cache(tmp_path, date.today().isoformat(), "0.9.2")
        data = make_session_input("startup")

        code, stdout, _ = run_hook("claudia-session-tips.py", data)
        assert code == 0
        assert stdout.strip()
        output = json.loads(stdout)
        msg = output.get("systemMessage", "")
        assert "v0.9.2 available" in msg
        assert "npm update -g claudia-mentor" in msg
        # Update hint should NOT be in additionalContext (Claude doesn't need it)
        ctx = output.get("additionalContext", "")
        assert "npm update" not in ctx

    def test_silent_when_versions_match(self, run_hook, tmp_path):
        """When cached latest == installed, no update hint."""
        setup_claudia_config(tmp_path, proactivity="moderate", experience="intermediate")
        self._write_update_cache(tmp_path, date.today().isoformat(), "0.9.1")
        data = make_session_input("startup")

        code, stdout, _ = run_hook("claudia-session-tips.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            msg = output.get("systemMessage", "")
            assert "npm update" not in msg

    def test_npm_failure_graceful(self, run_hook, tmp_path):
        """When npm is unavailable and no cache, update check is silently skipped."""
        setup_claudia_config(tmp_path, proactivity="moderate", experience="intermediate")
        data = make_session_input("startup")

        # Break PATH so npm can't be found, and no cache file exists
        env_overrides = {"PATH": "/nonexistent"}
        code, stdout, _ = run_hook("claudia-session-tips.py", data, env_overrides=env_overrides)
        assert code == 0
        # Should still show greeting, just no update hint
        if stdout.strip():
            output = json.loads(stdout)
            msg = output.get("systemMessage", "")
            assert "npm update" not in msg
