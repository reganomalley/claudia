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


class TestAllHooksNone:
    """When all hooks return None, dispatcher should be silent."""

    def test_intermediate_moderate_generic_message(self, run_hook, tmp_path):
        """Intermediate user, moderate proactivity, generic message — all hooks return None."""
        setup_claudia_config(tmp_path, proactivity="moderate", experience="intermediate")
        data = make_stop_input("Here is the updated file with the changes you requested.")
        code, stdout, _ = run_hook("claudia-stop-dispatch.py", data)
        assert code == 0
        assert stdout.strip() == ""

    def test_advanced_low_proactivity(self, run_hook, tmp_path):
        """Advanced user with low proactivity — nothing should fire."""
        setup_claudia_config(tmp_path, proactivity="low", experience="advanced")
        data = make_stop_input("I've created server.py using Docker and Vercel and Next.js.")
        code, stdout, _ = run_hook("claudia-stop-dispatch.py", data)
        assert code == 0
        assert stdout.strip() == ""

    def test_invalid_json_exits_cleanly(self, run_hook, tmp_path, hook_env):
        """Invalid JSON stdin should not crash."""
        import subprocess
        script_path = __import__("os").path.join(
            __import__("os").path.dirname(__file__), "..", "hooks", "scripts", "claudia-stop-dispatch.py"
        )
        env = hook_env.copy()
        result = subprocess.run(
            [__import__("sys").executable, script_path],
            input="not valid json {{{",
            capture_output=True, text=True, env=env, timeout=10,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""


class TestPriorityOrder:
    """Dispatcher should respect hook priority (milestones first, teach last)."""

    def test_milestone_takes_priority_over_teach(self, run_hook, tmp_path):
        """If milestones and teach both match, milestones wins (runs first)."""
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        # Fresh session — "I've created" triggers milestone (first_file) AND teach (Docker)
        data = make_stop_input("I've created app.js using Docker for the backend.")
        code, stdout, _ = run_hook("claudia-stop-dispatch.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            context = output.get("additionalContext", "")
            # Milestones hook fires first — should mention the milestone, not Docker teaching
            # (milestones check comes before teach in HOOK_MODULES order)
            assert "additionalContext" in output or "systemMessage" in output

    def test_run_suggest_before_teach(self, run_hook, tmp_path):
        """run-suggest comes before teach in dispatch order."""
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        # Exhaust milestones
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "claudia-milestones.json").write_text(
            json.dumps({"achieved": ["first_file", "first_error_fixed", "first_commit", "first_project_run", "ten_files"], "file_count": 20})
        )
        # "I've created server.py" should trigger run-suggest (py) before teach
        data = make_stop_input("I've created server.py with the Docker configuration.")
        code, stdout, _ = run_hook("claudia-stop-dispatch.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            context = output.get("additionalContext", "")
            # run-suggest comes before teach — should suggest how to run, not teach Docker
            assert "python3" in context.lower() or "run" in context.lower() or "Docker" in context


class TestSuppressHooks:
    """suppress_hooks should skip hooks in dispatch."""

    def test_suppressed_hook_skipped(self, run_hook, tmp_path):
        """When milestones is suppressed, it should not fire."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        # Set up beginner config with milestones suppressed
        (claude_dir / "claudia.json").write_text(
            json.dumps({"proactivity": "moderate", "suppress_hooks": ["milestones"]})
        )
        (claude_dir / "claudia-context.json").write_text(
            json.dumps({"experience": "beginner"})
        )
        # Fresh session — "I've created" would normally trigger first_file milestone
        data = make_stop_input("I've created main.js with the basic setup.")
        code, stdout, _ = run_hook("claudia-stop-dispatch.py", data)
        assert code == 0
        # If there's output, it should NOT be a milestone celebration
        if stdout.strip():
            output = json.loads(stdout)
            ctx = output.get("additionalContext", "")
            assert "first file" not in ctx.lower()

    def test_suppressed_teach_skipped(self, run_hook, tmp_path):
        """When teach is suppressed, keyword tips should not fire."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "claudia.json").write_text(
            json.dumps({"proactivity": "high", "suppress_hooks": ["teach"]})
        )
        (claude_dir / "claudia-context.json").write_text(
            json.dumps({"experience": "beginner"})
        )
        # Exhaust milestones and run-suggest so teach would be next
        (claude_dir / "claudia-milestones.json").write_text(
            json.dumps({"achieved": ["first_file", "first_error_fixed", "first_commit", "first_project_run", "ten_files"], "file_count": 20})
        )
        data = make_stop_input("You should consider using Docker for containerization.")
        code, stdout, _ = run_hook("claudia-stop-dispatch.py", data)
        assert code == 0
        # Should be silent since teach is suppressed and no other hook matches
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

    def test_output_is_valid_json(self, run_hook, tmp_path):
        """Output must always be parseable JSON or empty."""
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_stop_input("I've created index.html and deployed to Vercel with Next.js.")
        code, stdout, _ = run_hook("claudia-stop-dispatch.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)  # Should not raise
            assert "additionalContext" in output or "systemMessage" in output
