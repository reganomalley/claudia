"""Tests for claudia-run-suggest.py — run suggestion detection hook."""

import json

from conftest import make_stop_input, setup_claudia_config, clear_stop_lock


class TestFileDetection:
    """File creation should trigger run suggestions."""

    def test_html_file_suggests_open(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("I've created index.html with the page layout.")
        code, stdout, _ = run_hook("claudia-run-suggest.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "open" in output.get("additionalContext", "").lower()

    def test_python_file_suggests_python3(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("I've created script.py with the data processing logic.")
        code, stdout, _ = run_hook("claudia-run-suggest.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "python3" in output.get("additionalContext", "")

    def test_js_file_suggests_node(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("I've created server.js with the Express setup.")
        code, stdout, _ = run_hook("claudia-run-suggest.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "node" in output.get("additionalContext", "")

    def test_ts_file_suggests_tsx(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("I've created app.ts with the TypeScript config.")
        code, stdout, _ = run_hook("claudia-run-suggest.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "tsx" in output.get("additionalContext", "")

    def test_sh_file_suggests_bash(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("I've created deploy.sh with the deployment script.")
        code, stdout, _ = run_hook("claudia-run-suggest.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "bash" in output.get("additionalContext", "")

    def test_package_json_suggests_npm_install(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("I've created package.json with your dependencies.")
        code, stdout, _ = run_hook("claudia-run-suggest.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "npm install" in output.get("additionalContext", "")


class TestGating:
    """Gate: beginner OR high proactivity."""

    def test_intermediate_moderate_silent(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="intermediate")
        data = make_stop_input("I've created script.py with the logic.")
        code, stdout, _ = run_hook("claudia-run-suggest.py", data)
        assert stdout.strip() == ""

    def test_intermediate_high_active(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="intermediate")
        data = make_stop_input("I've created script.py with the logic.")
        code, stdout, _ = run_hook("claudia-run-suggest.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "python3" in output.get("additionalContext", "")


class TestDedup:
    """Once per file type per session."""

    def test_dedup_same_type(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")

        data1 = make_stop_input("I've created app.py with the Flask server.")
        _, stdout1, _ = run_hook("claudia-run-suggest.py", data1)
        clear_stop_lock(tmp_path)

        data2 = make_stop_input("I've created utils.py with helper functions.")
        _, stdout2, _ = run_hook("claudia-run-suggest.py", data2)
        # Second .py file should be deduped
        assert stdout2.strip() == ""


class TestEmptyMessage:
    def test_empty_message(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_stop_input("")
        code, stdout, _ = run_hook("claudia-run-suggest.py", data)
        assert code == 0
        assert stdout.strip() == ""
