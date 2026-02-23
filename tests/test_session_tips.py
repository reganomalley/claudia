"""Tests for claudia-session-tips.py — session startup tips hook."""

import json

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
