"""Tests for check-deps.py — deprecated package detection hook."""

import json

from conftest import make_pretool_input


class TestPackageDetection:
    """Known problematic packages should trigger warnings."""

    def test_request_deprecated(self, run_hook):
        content = '{"dependencies": {"request": "^2.88.0"}}'
        data = make_pretool_input("Write", "/app/package.json", content)
        code, stdout, _ = run_hook("check-deps.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "request" in output["systemMessage"]
        assert "Deprecated" in output["systemMessage"]

    def test_moment_detected(self, run_hook):
        content = '{"dependencies": {"moment": "^2.29.0"}}'
        data = make_pretool_input("Write", "/app/package.json", content)
        code, stdout, _ = run_hook("check-deps.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "moment" in output["systemMessage"]

    def test_lodash_detected(self, run_hook):
        content = '{"dependencies": {"lodash": "^4.17.0"}}'
        data = make_pretool_input("Write", "/app/package.json", content)
        code, stdout, _ = run_hook("check-deps.py", data)
        output = json.loads(stdout)
        assert "lodash" in output["systemMessage"]

    def test_colors_compromised(self, run_hook):
        content = '{"dependencies": {"colors": "^1.4.0"}}'
        data = make_pretool_input("Write", "/app/package.json", content)
        code, stdout, _ = run_hook("check-deps.py", data)
        output = json.loads(stdout)
        assert "colors" in output["systemMessage"]
        assert "compromised" in output["systemMessage"].lower() or "supply chain" in output["systemMessage"].lower()

    def test_faker_sabotaged(self, run_hook):
        content = '{"dependencies": {"faker": "^5.0.0"}}'
        data = make_pretool_input("Write", "/app/package.json", content)
        code, stdout, _ = run_hook("check-deps.py", data)
        output = json.loads(stdout)
        assert "faker" in output["systemMessage"]

    def test_is_odd_trivial(self, run_hook):
        content = '{"dependencies": {"is-odd": "^3.0.0"}}'
        data = make_pretool_input("Write", "/app/package.json", content)
        code, stdout, _ = run_hook("check-deps.py", data)
        output = json.loads(stdout)
        assert "is-odd" in output["systemMessage"]

    def test_gulp_legacy(self, run_hook):
        content = '{"devDependencies": {"gulp": "^4.0.0"}}'
        data = make_pretool_input("Write", "/app/package.json", content)
        code, stdout, _ = run_hook("check-deps.py", data)
        output = json.loads(stdout)
        assert "gulp" in output["systemMessage"]

    def test_tslint_deprecated(self, run_hook):
        content = '{"devDependencies": {"tslint": "^6.0.0"}}'
        data = make_pretool_input("Write", "/app/package.json", content)
        code, stdout, _ = run_hook("check-deps.py", data)
        output = json.loads(stdout)
        assert "tslint" in output["systemMessage"]

    def test_multiple_bad_deps(self, run_hook):
        content = '{"dependencies": {"request": "^2.0", "moment": "^2.0"}}'
        data = make_pretool_input("Write", "/app/package.json", content)
        code, stdout, _ = run_hook("check-deps.py", data)
        output = json.loads(stdout)
        assert "request" in output["systemMessage"]
        assert "moment" in output["systemMessage"]


class TestFileFiltering:
    """Only package.json files should be checked."""

    def test_non_package_json_ignored(self, run_hook):
        data = make_pretool_input("Write", "/app/config.json", '{"request": "^2.0"}')
        code, stdout, _ = run_hook("check-deps.py", data)
        assert code == 0
        assert stdout.strip() == ""

    def test_js_file_ignored(self, run_hook):
        data = make_pretool_input("Write", "/app/main.js", '"request"')
        code, stdout, _ = run_hook("check-deps.py", data)
        assert code == 0
        assert stdout.strip() == ""


class TestDedup:
    def test_dedup_same_package(self, run_hook):
        content = '{"dependencies": {"request": "^2.88.0"}}'
        data = make_pretool_input("Write", "/app/package.json", content)
        _, stdout1, _ = run_hook("check-deps.py", data)
        assert json.loads(stdout1)

        _, stdout2, _ = run_hook("check-deps.py", data)
        assert stdout2.strip() == ""


class TestCleanDeps:
    def test_safe_packages_no_warning(self, run_hook):
        content = '{"dependencies": {"express": "^4.0.0", "uuid": "^9.0.0"}}'
        data = make_pretool_input("Write", "/app/package.json", content)
        code, stdout, _ = run_hook("check-deps.py", data)
        assert code == 0
        assert stdout.strip() == ""
