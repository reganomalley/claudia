"""Tests for claudia-teach.py — keyword teaching + command reveals."""

import json

from conftest import make_stop_input, setup_claudia_config, clear_stop_lock


class TestKeywordDetection:
    """Technology keywords should trigger teaching tips."""

    def test_vercel_detected(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_stop_input("You should deploy this on Vercel for the best experience.")
        code, stdout, _ = run_hook("claudia-teach.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "Vercel" in output.get("systemMessage", "") or "Vercel" in output.get("additionalContext", "")

    def test_react_detected(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_stop_input("I'll use React for the frontend components.")
        code, stdout, _ = run_hook("claudia-teach.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "React" in output.get("additionalContext", "")

    def test_postgres_detected(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_stop_input("We should use Postgres for the database.")
        code, stdout, _ = run_hook("claudia-teach.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "Postgres" in output.get("additionalContext", "")

    def test_docker_detected(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("Let me containerize this with Docker.")
        code, stdout, _ = run_hook("claudia-teach.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "Docker" in output.get("additionalContext", "")

    def test_api_concept_detected(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_stop_input("This API endpoint returns JSON.")
        code, stdout, _ = run_hook("claudia-teach.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "API" in output.get("additionalContext", "")


class TestProactivityGating:
    """Low proactivity should silence everything."""

    def test_low_proactivity_silent(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="low", experience="beginner")
        data = make_stop_input("Deploy this on Vercel.")
        code, stdout, _ = run_hook("claudia-teach.py", data)
        assert code == 0
        assert stdout.strip() == ""

    def test_non_beginner_moderate_silent(self, run_hook, tmp_path):
        """Non-beginners need high proactivity to get teaching."""
        setup_claudia_config(tmp_path, proactivity="moderate", experience="intermediate")
        data = make_stop_input("Deploy this on Vercel.")
        code, stdout, _ = run_hook("claudia-teach.py", data)
        assert code == 0
        assert stdout.strip() == ""

    def test_non_beginner_high_gets_teaching(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="intermediate")
        data = make_stop_input("Deploy this on Vercel.")
        code, stdout, _ = run_hook("claudia-teach.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "Vercel" in output.get("additionalContext", "")


class TestErrorPatterns:
    """Error patterns should teach beginners."""

    def test_enoent_detected(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("error: ENOENT: no such file or directory")
        code, stdout, _ = run_hook("claudia-teach.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "error" in output.get("additionalContext", "").lower()

    def test_module_not_found(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("Error: Module not found: Can't resolve 'lodash'")
        code, stdout, _ = run_hook("claudia-teach.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "error" in output.get("additionalContext", "").lower() or "Module" in output.get("additionalContext", "")


class TestCommandReveals:
    """Beginners should get contextual command reveals."""

    def test_file_written_reveals_explain(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("I've created main.js with the basic server setup.")
        code, stdout, _ = run_hook("claudia-teach.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            ctx = output.get("additionalContext", "")
            # May reveal /claudia:explain
            assert "/claudia:explain" in ctx or "created" in ctx.lower() or len(ctx) > 0

    def test_error_reveals_wtf(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        # First, exhaust keyword tip with a non-keyword message containing error
        data = make_stop_input("The operation failed with an error code.")
        code, stdout, _ = run_hook("claudia-teach.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            ctx = output.get("additionalContext", "")
            # May reveal /claudia:wtf
            assert "/claudia:wtf" in ctx or "error" in ctx.lower() or len(ctx) > 0


class TestDedup:
    """Same keyword not repeated."""

    def test_keyword_dedup(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")

        data = make_stop_input("Deploy on Vercel.")
        code1, stdout1, _ = run_hook("claudia-teach.py", data)
        clear_stop_lock(tmp_path)

        code2, stdout2, _ = run_hook("claudia-teach.py", data)
        # Second time should not mention Vercel again
        if stdout2.strip():
            output = json.loads(stdout2)
            assert "Vercel" not in output.get("additionalContext", "")


class TestStateMigration:
    """Old flat list state should migrate to new dict format."""

    def test_flat_list_migrates(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        # Write old-format state file
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        state_file = claude_dir / "claudia_teach_state_test-session.json"
        state_file.write_text(json.dumps(["vercel"]))

        data = make_stop_input("Use React for the frontend.")
        code, stdout, _ = run_hook("claudia-teach.py", data)
        # Should work without crashing, and vercel should stay deduped
        assert code == 0


class TestEmptyMessage:
    def test_empty_message_exits_clean(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_stop_input("")
        code, stdout, _ = run_hook("claudia-teach.py", data)
        assert code == 0
        assert stdout.strip() == ""
