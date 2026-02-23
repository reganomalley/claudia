"""Tests for check-practices.py — anti-pattern detection hook."""

import json

from conftest import make_pretool_input, setup_claudia_config


class TestAntiPatternDetection:
    """Each anti-pattern should trigger a warning."""

    def test_eval_detected(self, run_hook):
        data = make_pretool_input("Write", "/app/main.js", "var x = eval('1+1');")
        code, stdout, _ = run_hook("check-practices.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "eval()" in output["systemMessage"]

    def test_console_log_detected(self, run_hook):
        data = make_pretool_input("Write", "/app/main.js", "console.log('debug');")
        code, stdout, _ = run_hook("check-practices.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "console.log" in output["systemMessage"]

    def test_empty_catch_detected(self, run_hook):
        data = make_pretool_input("Write", "/app/main.js", "try { x() } catch(e) { }")
        code, stdout, _ = run_hook("check-practices.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "Empty catch" in output["systemMessage"]

    def test_http_url_detected(self, run_hook):
        data = make_pretool_input("Write", "/app/config.js", 'url = "http://example.com/api"')
        code, stdout, _ = run_hook("check-practices.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "HTTP" in output["systemMessage"]

    def test_http_localhost_allowed(self, run_hook):
        data = make_pretool_input("Write", "/app/config.js", 'url = "http://localhost:3000"')
        code, stdout, _ = run_hook("check-practices.py", data)
        assert code == 0
        assert stdout.strip() == ""

    def test_sql_injection_detected(self, run_hook):
        data = make_pretool_input("Write", "/app/db.js", '"SELECT * FROM users WHERE id = " + req.params.id')
        code, stdout, _ = run_hook("check-practices.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "SQL" in output["systemMessage"]

    def test_document_write_detected(self, run_hook):
        data = make_pretool_input("Write", "/app/main.js", "document.write('<h1>hi</h1>')")
        code, stdout, _ = run_hook("check-practices.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "document.write" in output["systemMessage"]

    def test_innerhtml_detected(self, run_hook):
        data = make_pretool_input("Write", "/app/main.js", 'el.innerHTML = userInput;')
        code, stdout, _ = run_hook("check-practices.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "innerHTML" in output["systemMessage"]

    def test_todo_detected(self, run_hook):
        data = make_pretool_input("Write", "/app/main.js", "// TODO: fix this later")
        code, stdout, _ = run_hook("check-practices.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "TODO" in output["systemMessage"]

    def test_chmod_777_detected(self, run_hook):
        data = make_pretool_input("Write", "/app/setup.sh", "chmod 777 /var/data")
        code, stdout, _ = run_hook("check-practices.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "chmod 777" in output["systemMessage"]

    def test_ssl_disabled_detected(self, run_hook):
        data = make_pretool_input("Write", "/app/req.py", "requests.get(url, verify=False)")
        code, stdout, _ = run_hook("check-practices.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "SSL" in output["systemMessage"]


class TestTestFileSkipping:
    """Test files should skip console.log and TODO warnings."""

    def test_console_log_allowed_in_test_files(self, run_hook):
        data = make_pretool_input("Write", "/app/main.test.js", "console.log('test output');")
        code, stdout, _ = run_hook("check-practices.py", data)
        assert code == 0
        # Should not warn about console.log in test files
        if stdout.strip():
            output = json.loads(stdout)
            assert "console.log" not in output.get("systemMessage", "")

    def test_todo_allowed_in_test_files(self, run_hook):
        data = make_pretool_input("Write", "/app/main.spec.js", "// TODO: add more tests")
        code, stdout, _ = run_hook("check-practices.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "TODO" not in output.get("systemMessage", "")


class TestDedup:
    """Same warning not repeated for same file+pattern."""

    def test_dedup_same_file_pattern(self, run_hook):
        data = make_pretool_input("Write", "/app/main.js", "var x = eval('1+1');")
        code1, stdout1, _ = run_hook("check-practices.py", data)
        assert json.loads(stdout1)  # First time: warning

        code2, stdout2, _ = run_hook("check-practices.py", data)
        assert code2 == 0
        assert stdout2.strip() == ""  # Second time: deduped


class TestEdgeCases:
    """Empty/missing content and tool type filtering."""

    def test_empty_content_exits_clean(self, run_hook):
        data = make_pretool_input("Write", "/app/main.js", "")
        code, stdout, _ = run_hook("check-practices.py", data)
        assert code == 0
        assert stdout.strip() == ""

    def test_non_write_tool_ignored(self, run_hook):
        data = {"session_id": "test", "tool_name": "Read", "tool_input": {"file_path": "/app/main.js"}}
        code, stdout, _ = run_hook("check-practices.py", data)
        assert code == 0
        assert stdout.strip() == ""

    def test_edit_tool_scans_new_string(self, run_hook):
        data = make_pretool_input("Edit", "/app/main.js", new_string="var x = eval('bad');")
        code, stdout, _ = run_hook("check-practices.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "eval()" in output["systemMessage"]

    def test_multiedit_scans_all_edits(self, run_hook):
        data = make_pretool_input(
            "MultiEdit", "/app/main.js",
            edits=[{"new_string": "eval('a')"}, {"new_string": "document.write('b')"}]
        )
        code, stdout, _ = run_hook("check-practices.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "eval()" in output["systemMessage"]
        assert "document.write" in output["systemMessage"]

    def test_output_is_valid_json(self, run_hook):
        data = make_pretool_input("Write", "/app/main.js", "eval('bad')")
        code, stdout, _ = run_hook("check-practices.py", data)
        output = json.loads(stdout)
        assert "systemMessage" in output

    def test_invalid_json_stdin_exits_clean(self, run_hook, hook_env):
        """Malformed stdin should exit 0 gracefully."""
        import subprocess, sys, os
        script = os.path.join(os.path.dirname(__file__), "..", "hooks", "scripts", "check-practices.py")
        result = subprocess.run(
            [sys.executable, script],
            input="not json at all",
            capture_output=True, text=True, env=hook_env,
        )
        assert result.returncode == 0
