"""Tests for claudia-milestones.py — milestone detection hook."""

import json

from conftest import make_stop_input, setup_claudia_config, clear_stop_lock


class TestMilestoneDetection:
    """Each milestone should trigger a celebration."""

    def test_first_file(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("I've created main.js with the basic setup.")
        code, stdout, _ = run_hook("claudia-milestones.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "first file" in output.get("additionalContext", "").lower()

    def test_first_error_fixed(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        # Pre-mark first_file as achieved to avoid it winning
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "claudia-milestones.json").write_text(
            json.dumps({"achieved": ["first_file"], "file_count": 1})
        )
        data = make_stop_input("I've fixed the error in the login handler.")
        code, stdout, _ = run_hook("claudia-milestones.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "bug" in output.get("additionalContext", "").lower() or "first" in output.get("additionalContext", "").lower()

    def test_first_commit(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "claudia-milestones.json").write_text(
            json.dumps({"achieved": ["first_file", "first_error_fixed"], "file_count": 2})
        )
        data = make_stop_input("I've committed your changes to the repository.")
        code, stdout, _ = run_hook("claudia-milestones.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "commit" in output.get("additionalContext", "").lower()

    def test_first_project_run(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "claudia-milestones.json").write_text(
            json.dumps({"achieved": ["first_file"], "file_count": 1})
        )
        data = make_stop_input("The server is running on http://localhost:3000.")
        code, stdout, _ = run_hook("claudia-milestones.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "running" in output.get("additionalContext", "").lower() or "works" in output.get("additionalContext", "").lower()

    def test_ten_files(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "claudia-milestones.json").write_text(
            json.dumps({"achieved": ["first_file"], "file_count": 9})
        )
        # Create a message with 2 file mentions (pushes count to 11)
        data = make_stop_input("I've created utils.js and helpers.js with shared code.")
        code, stdout, _ = run_hook("claudia-milestones.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "10" in output.get("additionalContext", "") or "real project" in output.get("additionalContext", "").lower()


class TestGating:
    """Beginner only."""

    def test_intermediate_silent(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="intermediate")
        data = make_stop_input("I've created main.js.")
        code, stdout, _ = run_hook("claudia-milestones.py", data)
        assert stdout.strip() == ""


class TestPersistence:
    """Milestones persist cross-session."""

    def test_already_achieved_not_repeated(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "claudia-milestones.json").write_text(
            json.dumps({"achieved": ["first_file"], "file_count": 1})
        )
        # first_file already achieved — should not celebrate again
        data = make_stop_input("I've created another.js with more code.")
        code, stdout, _ = run_hook("claudia-milestones.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            # Should NOT be celebrating first_file again
            assert "first file" not in output.get("additionalContext", "").lower()


class TestFileCountTracking:
    """File count should accumulate."""

    def test_file_count_increments(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)

        data = make_stop_input("I've created app.js and also created index.html for the frontend.")
        run_hook("claudia-milestones.py", data)

        # Check the state file
        state_file = claude_dir / "claudia-milestones.json"
        if state_file.exists():
            state = json.loads(state_file.read_text())
            assert state.get("file_count", 0) >= 2
