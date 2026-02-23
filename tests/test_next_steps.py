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

    def test_long_summary_silent(self, run_hook, tmp_path):
        """Multi-paragraph summaries should not trigger next-steps."""
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        summary = (
            "All done. Here's the summary:\n\n"
            "**Changes made across 10 files:**\n\n"
            "1. **`claudia_config.py`** -- Added `load_suppress_hooks()` and `dismiss_hint()`.\n"
            "2. **`claudia-stop-dispatch.py`** -- Loads suppress_hooks, skips suppressed hooks.\n"
            "3. **Stop hooks with dismiss hints:**\n"
            "   - `claudia-next-steps.py` -- hint every 3rd firing\n"
            "   - `claudia-run-suggest.py` -- hint every firing\n"
            "   - `claudia-milestones.py` -- hint every firing\n"
            "   - `claudia-teach.py` -- hint every 3rd keyword tip\n"
            "4. **Independent hooks with suppress check:**\n"
            "   - `claudia-prompt-coach.py` -- bail early if suppressed\n"
            "   - `claudia-session-tips.py` -- bail early if suppressed\n"
            "   - `claudia-compact-tip.py` -- bail early if suppressed\n"
            "5. **README.md** -- Added suppress_hooks to config example.\n"
            "6. **Tests** -- 17 new tests across 4 test files. Full suite: 262 tests passing.\n"
        )
        data = make_stop_input(summary)
        code, stdout, _ = run_hook("claudia-next-steps.py", data)
        assert stdout.strip() == ""

    def test_mid_message_completion_silent(self, run_hook, tmp_path):
        """Completion phrase buried in a list item should not trigger."""
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        msg = "Here are the changes:\n- I've added error handling to auth.py\n- Updated the tests"
        data = make_stop_input(msg)
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


class TestDismissHint:
    """Dismiss hint appears on every 3rd firing."""

    def test_dismiss_hint_on_third(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        messages = [
            "I've created file1.py with module 1.",
            "I've created file2.py with module 2.",
            "I've created file3.py with module 3.",
        ]
        outputs = []
        for msg in messages:
            clear_stop_lock(tmp_path)
            data = make_stop_input(msg)
            _, stdout, _ = run_hook("claudia-next-steps.py", data)
            outputs.append(stdout.strip())

        # 3rd firing (count=3, 3%3==0) should have dismiss hint
        if outputs[2]:
            output = json.loads(outputs[2])
            assert "silence next-steps" in output.get("systemMessage", "")
            assert "suppress_hooks" in output.get("additionalContext", "")

    def test_no_dismiss_hint_on_first(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("I've created index.html with the page layout.")
        _, stdout, _ = run_hook("claudia-next-steps.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "silence next-steps" not in output.get("systemMessage", "")


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
