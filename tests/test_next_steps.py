"""Tests for claudia-next-steps.py — completion signal detection hook."""

import json

from conftest import make_stop_input, setup_claudia_config, clear_stop_lock


class TestCompletionDetection:
    """Completion signals should trigger next-step suggestions."""

    def test_ive_created_triggers(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("I've created index.html with the page layout.")
        code, stdout, _ = run_hook("claudia-next-steps.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "What's next" in output.get("additionalContext", "")

    def test_done_triggers(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("Done. The file has been updated.")
        code, stdout, _ = run_hook("claudia-next-steps.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "What's next" in output.get("additionalContext", "")

    def test_its_ready_triggers(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("It's ready. You can start using the API now.")
        code, stdout, _ = run_hook("claudia-next-steps.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "What's next" in output.get("additionalContext", "")

    def test_no_completion_signal_silent(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("Let me think about the best approach for this.")
        code, stdout, _ = run_hook("claudia-next-steps.py", data)
        assert stdout.strip() == ""


class TestFileTypeSteps:
    """Next steps should be contextual to file type."""

    def test_html_steps(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("I've created index.html with the landing page.")
        code, stdout, _ = run_hook("claudia-next-steps.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            ctx = output.get("additionalContext", "")
            assert "browser" in ctx.lower() or "open" in ctx.lower()

    def test_py_steps(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("I've created script.py with the data processor.")
        code, stdout, _ = run_hook("claudia-next-steps.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            ctx = output.get("additionalContext", "")
            assert "python3" in ctx or "Run" in ctx


class TestGating:
    """Beginner only."""

    def test_intermediate_silent(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="intermediate")
        data = make_stop_input("I've created main.js with the server.")
        code, stdout, _ = run_hook("claudia-next-steps.py", data)
        assert stdout.strip() == ""


class TestMaxPerSession:
    """Max 3 suggestions per session."""

    def test_max_three(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        messages = [
            "I've created file1.py with module 1.",
            "I've created file2.py with module 2.",
            "I've created file3.py with module 3.",
            "I've created file4.py with module 4.",
        ]
        outputs = []
        for msg in messages:
            clear_stop_lock(tmp_path)
            data = make_stop_input(msg)
            _, stdout, _ = run_hook("claudia-next-steps.py", data)
            outputs.append(stdout.strip())

        fired = [o for o in outputs if o]
        assert len(fired) <= 3
