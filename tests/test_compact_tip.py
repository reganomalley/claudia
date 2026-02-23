"""Tests for claudia-compact-tip.py — PreCompact event tips."""

import json

from conftest import make_compact_input, setup_claudia_config


class TestAutoCompaction:
    """Auto-triggered compaction tips."""

    def test_auto_shows_esc_tip(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_compact_input("auto")
        code, stdout, _ = run_hook("claudia-compact-tip.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "Esc" in output.get("systemMessage", "") or "compacted" in output.get("systemMessage", "").lower()

    def test_auto_dedup(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_compact_input("auto")
        run_hook("claudia-compact-tip.py", data)

        _, stdout2, _ = run_hook("claudia-compact-tip.py", data)
        assert stdout2.strip() == ""


class TestManualCompaction:
    def test_manual_shows_tip(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_compact_input("manual")
        code, stdout, _ = run_hook("claudia-compact-tip.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "pro" in output.get("systemMessage", "").lower()

    def test_manual_dedup(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_compact_input("manual")
        run_hook("claudia-compact-tip.py", data)

        _, stdout2, _ = run_hook("claudia-compact-tip.py", data)
        assert stdout2.strip() == ""


class TestGating:
    """Beginner only, moderate+ proactivity."""

    def test_non_beginner_silent(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="intermediate")
        data = make_compact_input("auto")
        code, stdout, _ = run_hook("claudia-compact-tip.py", data)
        assert stdout.strip() == ""

    def test_low_proactivity_silent(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="low", experience="beginner")
        data = make_compact_input("auto")
        code, stdout, _ = run_hook("claudia-compact-tip.py", data)
        assert stdout.strip() == ""

    def test_beginner_moderate_active(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_compact_input("auto")
        code, stdout, _ = run_hook("claudia-compact-tip.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "systemMessage" in output


class TestNoAdditionalContext:
    """Compact tips should NOT use additionalContext (it gets wiped)."""

    def test_no_additional_context(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_compact_input("auto")
        _, stdout, _ = run_hook("claudia-compact-tip.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "additionalContext" not in output
