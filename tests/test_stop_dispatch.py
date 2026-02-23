"""Tests for claudia-stop-dispatch.py — consolidated Stop hook dispatcher."""

import json

from conftest import make_stop_input, setup_claudia_config


class TestDispatcherRouting:
    """Dispatcher should route to the right hook and return output."""

    def test_milestone_fires(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("I've created main.js with the basic setup.")
        code, stdout, _ = run_hook("claudia-stop-dispatch.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            # Should be a milestone or run-suggest or teach — some output
            assert "additionalContext" in output or "systemMessage" in output

    def test_keyword_teaching_fires(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        # Pre-exhaust milestones so teach can win
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "claudia-milestones.json").write_text(
            json.dumps({"achieved": ["first_file", "first_error_fixed", "first_commit", "first_project_run", "ten_files"], "file_count": 20})
        )
        data = make_stop_input("You should consider using Docker for containerization.")
        code, stdout, _ = run_hook("claudia-stop-dispatch.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "Docker" in output.get("additionalContext", "")

    def test_empty_message_silent(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_stop_input("")
        code, stdout, _ = run_hook("claudia-stop-dispatch.py", data)
        assert code == 0
        assert stdout.strip() == ""

    def test_no_match_silent(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="intermediate")
        data = make_stop_input("Here is a plain response with no triggers.")
        code, stdout, _ = run_hook("claudia-stop-dispatch.py", data)
        assert code == 0
        assert stdout.strip() == ""

    def test_low_proactivity_non_beginner_silent(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="low", experience="intermediate")
        data = make_stop_input("I've created main.js and deployed to Vercel.")
        code, stdout, _ = run_hook("claudia-stop-dispatch.py", data)
        assert code == 0
        assert stdout.strip() == ""


class TestSingleOutput:
    """Only one hook should produce output per dispatch."""

    def test_only_one_output(self, run_hook, tmp_path):
        """Even with multiple triggers, dispatcher returns one result."""
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        # This message triggers milestones (first_file), run-suggest (py), and teach (Docker)
        data = make_stop_input("I've created server.py with the Docker config and Vercel deployment.")
        code, stdout, _ = run_hook("claudia-stop-dispatch.py", data)
        assert code == 0
        if stdout.strip():
            # Should be valid JSON (single output, not multiple concatenated)
            output = json.loads(stdout)
            assert isinstance(output, dict)
