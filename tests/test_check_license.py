"""Tests for check-license.py — copyleft license detection hook."""

import json

from conftest import make_pretool_input


class TestCopyleftDetection:
    """Copyleft packages should trigger warnings."""

    def test_readline_gpl(self, run_hook):
        content = '{"dependencies": {"readline": "^1.0.0"}}'
        data = make_pretool_input("Write", "/app/package.json", content)
        code, stdout, _ = run_hook("check-license.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "readline" in output["systemMessage"]
        assert "GPL" in output["systemMessage"]

    def test_mongodb_sspl(self, run_hook):
        content = '{"dependencies": {"mongodb": "^6.0.0"}}'
        data = make_pretool_input("Write", "/app/package.json", content)
        code, stdout, _ = run_hook("check-license.py", data)
        output = json.loads(stdout)
        assert "mongodb" in output["systemMessage"]
        assert "SSPL" in output["systemMessage"]

    def test_grafana_agpl(self, run_hook):
        content = '{"dependencies": {"grafana": "^10.0.0"}}'
        data = make_pretool_input("Write", "/app/package.json", content)
        code, stdout, _ = run_hook("check-license.py", data)
        output = json.loads(stdout)
        assert "grafana" in output["systemMessage"]
        assert "AGPL" in output["systemMessage"]

    def test_minio_agpl(self, run_hook):
        content = '{"dependencies": {"minio": "^7.0.0"}}'
        data = make_pretool_input("Write", "/app/package.json", content)
        code, stdout, _ = run_hook("check-license.py", data)
        output = json.loads(stdout)
        assert "minio" in output["systemMessage"]

    def test_safe_package_no_warning(self, run_hook):
        """Packages with alternative=None (like mongoose) should not warn."""
        content = '{"dependencies": {"mongoose": "^7.0.0"}}'
        data = make_pretool_input("Write", "/app/package.json", content)
        code, stdout, _ = run_hook("check-license.py", data)
        assert code == 0
        # mongoose has alternative=None, should be skipped
        if stdout.strip():
            output = json.loads(stdout)
            assert "mongoose" not in output.get("systemMessage", "")


class TestFileFiltering:
    def test_non_package_json_ignored(self, run_hook):
        data = make_pretool_input("Write", "/app/config.json", '{"readline": "^1.0"}')
        code, stdout, _ = run_hook("check-license.py", data)
        assert stdout.strip() == ""


class TestDedup:
    def test_dedup_same_package(self, run_hook):
        content = '{"dependencies": {"mongodb": "^6.0.0"}}'
        data = make_pretool_input("Write", "/app/package.json", content)
        _, stdout1, _ = run_hook("check-license.py", data)
        assert json.loads(stdout1)

        _, stdout2, _ = run_hook("check-license.py", data)
        assert stdout2.strip() == ""
