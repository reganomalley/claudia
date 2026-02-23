"""Tests for check-git-hygiene.py — blocking + advisory git hygiene hook."""

import json

from conftest import make_pretool_input


class TestEnvFileBlocking:
    """Writing to .env should block."""

    def test_env_file_blocks(self, run_hook):
        data = make_pretool_input("Write", "/app/.env", "SECRET=abc123")
        code, _, stderr = run_hook("check-git-hygiene.py", data)
        assert code == 2
        assert ".env" in stderr

    def test_env_local_blocks(self, run_hook):
        data = make_pretool_input("Write", "/app/.env.local", "SECRET=abc123")
        code, _, stderr = run_hook("check-git-hygiene.py", data)
        assert code == 2

    def test_env_production_blocks(self, run_hook):
        data = make_pretool_input("Write", "/app/.env.production", "SECRET=abc123")
        code, _, stderr = run_hook("check-git-hygiene.py", data)
        assert code == 2

    def test_env_example_allowed(self, run_hook):
        data = make_pretool_input("Write", "/app/.env.example", "SECRET=placeholder")
        code, _, _ = run_hook("check-git-hygiene.py", data)
        assert code == 0

    def test_env_sample_allowed(self, run_hook):
        data = make_pretool_input("Write", "/app/.env.sample", "SECRET=placeholder")
        code, _, _ = run_hook("check-git-hygiene.py", data)
        assert code == 0

    def test_env_template_allowed(self, run_hook):
        data = make_pretool_input("Write", "/app/.env.template", "SECRET=placeholder")
        code, _, _ = run_hook("check-git-hygiene.py", data)
        assert code == 0

    def test_env_test_allowed(self, run_hook):
        data = make_pretool_input("Write", "/app/.env.test", "SECRET=placeholder")
        code, _, _ = run_hook("check-git-hygiene.py", data)
        assert code == 0

    def test_env_in_test_dir_allowed(self, run_hook):
        data = make_pretool_input("Write", "/app/tests/.env", "SECRET=abc")
        code, _, _ = run_hook("check-git-hygiene.py", data)
        assert code == 0

    def test_env_in_fixtures_dir_allowed(self, run_hook):
        data = make_pretool_input("Write", "/app/fixtures/.env", "SECRET=abc")
        code, _, _ = run_hook("check-git-hygiene.py", data)
        assert code == 0


class TestMergeConflictBlocking:
    """Merge conflict markers should block."""

    def test_left_marker_blocks(self, run_hook):
        data = make_pretool_input("Write", "/app/main.js", "<<<<<<< HEAD\nsome code")
        code, _, stderr = run_hook("check-git-hygiene.py", data)
        assert code == 2
        assert "conflict" in stderr.lower()

    def test_equals_marker_blocks(self, run_hook):
        data = make_pretool_input("Write", "/app/main.js", "some code\n=======\nother code")
        code, _, stderr = run_hook("check-git-hygiene.py", data)
        assert code == 2

    def test_right_marker_blocks(self, run_hook):
        data = make_pretool_input("Write", "/app/main.js", "some code\n>>>>>>> branch-name")
        code, _, stderr = run_hook("check-git-hygiene.py", data)
        assert code == 2

    def test_conflict_in_markdown_allowed(self, run_hook):
        """Markdown files can legitimately contain these characters."""
        data = make_pretool_input("Write", "/app/README.md", "<<<<<<< example\n=======\n>>>>>>>")
        code, _, _ = run_hook("check-git-hygiene.py", data)
        assert code == 0

    def test_conflict_in_txt_allowed(self, run_hook):
        data = make_pretool_input("Write", "/app/notes.txt", "<<<<<<< example")
        code, _, _ = run_hook("check-git-hygiene.py", data)
        assert code == 0


class TestBinaryFileAdvisory:
    """Binary file warnings are advisory only."""

    def test_zip_file_warns(self, run_hook):
        data = make_pretool_input("Write", "/app/data.zip", "binary content")
        code, stdout, _ = run_hook("check-git-hygiene.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "binary" in output["systemMessage"].lower() or "Binary" in output["systemMessage"]

    def test_exe_file_warns(self, run_hook):
        data = make_pretool_input("Write", "/app/tool.exe", "binary content")
        code, stdout, _ = run_hook("check-git-hygiene.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "systemMessage" in output

    def test_normal_file_no_warning(self, run_hook):
        data = make_pretool_input("Write", "/app/main.js", "const x = 1;")
        code, stdout, _ = run_hook("check-git-hygiene.py", data)
        assert code == 0
        assert stdout.strip() == ""
