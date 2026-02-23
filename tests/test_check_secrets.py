"""Tests for check-secrets.py — secret detection blocking hook."""

import json

from conftest import make_pretool_input


class TestSecretDetection:
    """Each secret pattern should trigger exit 2."""

    def test_aws_access_key(self, run_hook):
        data = make_pretool_input("Write", "/app/config.js", 'key = "AKIAIOSFODNN7EXAMPLE"')
        code, _, stderr = run_hook("check-secrets.py", data)
        assert code == 2
        assert "AWS" in stderr

    def test_openai_key(self, run_hook):
        data = make_pretool_input("Write", "/app/config.js", 'key = "sk-1234567890abcdefghijklmn"')
        code, _, stderr = run_hook("check-secrets.py", data)
        assert code == 2
        assert "secret key" in stderr.lower() or "OpenAI" in stderr or "Stripe" in stderr

    def test_github_pat(self, run_hook):
        data = make_pretool_input("Write", "/app/config.js", 'token = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"')
        code, _, stderr = run_hook("check-secrets.py", data)
        assert code == 2
        assert "GitHub" in stderr

    def test_github_oauth(self, run_hook):
        data = make_pretool_input("Write", "/app/config.js", 'token = "gho_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"')
        code, _, stderr = run_hook("check-secrets.py", data)
        assert code == 2
        assert "GitHub" in stderr

    def test_gitlab_pat(self, run_hook):
        data = make_pretool_input("Write", "/app/config.js", 'token = "glpat-abcdefghijklmnopqrstuv"')
        code, _, stderr = run_hook("check-secrets.py", data)
        assert code == 2
        assert "GitLab" in stderr

    def test_slack_token(self, run_hook):
        data = make_pretool_input("Write", "/app/config.js", 'token = "xoxb-abc123def456"')
        code, _, stderr = run_hook("check-secrets.py", data)
        assert code == 2
        assert "Slack" in stderr

    def test_private_key(self, run_hook):
        data = make_pretool_input("Write", "/app/key.pem", "-----BEGIN RSA PRIVATE KEY-----")
        code, _, stderr = run_hook("check-secrets.py", data)
        assert code == 2
        assert "Private key" in stderr or "key" in stderr.lower()

    def test_private_key_no_type(self, run_hook):
        data = make_pretool_input("Write", "/app/key.pem", "-----BEGIN PRIVATE KEY-----")
        code, _, stderr = run_hook("check-secrets.py", data)
        assert code == 2

    def test_hardcoded_password(self, run_hook):
        data = make_pretool_input("Write", "/app/config.js", 'password = "mysuperpassword123"')
        code, _, stderr = run_hook("check-secrets.py", data)
        assert code == 2
        assert "password" in stderr.lower()

    def test_hardcoded_secret(self, run_hook):
        data = make_pretool_input("Write", "/app/config.js", 'secret = "abcdef1234567890"')
        code, _, stderr = run_hook("check-secrets.py", data)
        assert code == 2
        assert "secret" in stderr.lower()

    def test_api_key_hardcoded(self, run_hook):
        data = make_pretool_input("Write", "/app/config.js", 'api_key = "abcdef1234567890abcd"')
        code, _, stderr = run_hook("check-secrets.py", data)
        assert code == 2
        assert "API key" in stderr or "api" in stderr.lower()

    def test_mongodb_uri(self, run_hook):
        data = make_pretool_input("Write", "/app/config.js", 'uri = "mongodb://admin:password@host.com"')
        code, _, stderr = run_hook("check-secrets.py", data)
        assert code == 2
        assert "MongoDB" in stderr

    def test_mongodb_srv_uri(self, run_hook):
        data = make_pretool_input("Write", "/app/config.js", 'uri = "mongodb+srv://admin:password@host.com"')
        code, _, stderr = run_hook("check-secrets.py", data)
        assert code == 2
        assert "MongoDB" in stderr

    def test_postgres_uri(self, run_hook):
        data = make_pretool_input("Write", "/app/config.js", 'uri = "postgresql://user:pass@host.com"')
        code, _, stderr = run_hook("check-secrets.py", data)
        assert code == 2
        assert "PostgreSQL" in stderr

    def test_mysql_uri(self, run_hook):
        data = make_pretool_input("Write", "/app/config.js", 'uri = "mysql://user:pass@host.com"')
        code, _, stderr = run_hook("check-secrets.py", data)
        assert code == 2
        assert "MySQL" in stderr


class TestFileSkipping:
    """Test/example files should be skipped."""

    def test_test_file_skipped(self, run_hook):
        data = make_pretool_input("Write", "/app/test_config.js", 'key = "AKIAIOSFODNN7EXAMPLE"')
        code, _, _ = run_hook("check-secrets.py", data)
        assert code == 0

    def test_spec_file_skipped(self, run_hook):
        data = make_pretool_input("Write", "/app/config.spec.js", 'key = "AKIAIOSFODNN7EXAMPLE"')
        code, _, _ = run_hook("check-secrets.py", data)
        assert code == 0

    def test_fixture_file_skipped(self, run_hook):
        data = make_pretool_input("Write", "/app/fixture_data.js", 'key = "AKIAIOSFODNN7EXAMPLE"')
        code, _, _ = run_hook("check-secrets.py", data)
        assert code == 0

    def test_example_file_skipped(self, run_hook):
        data = make_pretool_input("Write", "/app/config.example.js", 'key = "AKIAIOSFODNN7EXAMPLE"')
        code, _, _ = run_hook("check-secrets.py", data)
        assert code == 0

    def test_markdown_file_skipped(self, run_hook):
        data = make_pretool_input("Write", "/app/README.md", 'key = "AKIAIOSFODNN7EXAMPLE"')
        code, _, _ = run_hook("check-secrets.py", data)
        assert code == 0

    def test_mock_file_skipped(self, run_hook):
        data = make_pretool_input("Write", "/app/mock_auth.js", 'key = "AKIAIOSFODNN7EXAMPLE"')
        code, _, _ = run_hook("check-secrets.py", data)
        assert code == 0

    def test_sample_file_skipped(self, run_hook):
        data = make_pretool_input("Write", "/app/config.sample.js", 'key = "AKIAIOSFODNN7EXAMPLE"')
        code, _, _ = run_hook("check-secrets.py", data)
        assert code == 0


class TestDedup:
    """Second hit on same file+type should exit 0."""

    def test_dedup_second_hit(self, run_hook):
        data = make_pretool_input("Write", "/app/config.js", 'key = "AKIAIOSFODNN7EXAMPLE"')
        code1, _, _ = run_hook("check-secrets.py", data)
        assert code1 == 2

        code2, _, _ = run_hook("check-secrets.py", data)
        assert code2 == 0


class TestCleanContent:
    """Clean content should exit 0."""

    def test_clean_content(self, run_hook):
        data = make_pretool_input("Write", "/app/main.js", 'const x = 42;')
        code, stdout, stderr = run_hook("check-secrets.py", data)
        assert code == 0

    def test_empty_content(self, run_hook):
        data = make_pretool_input("Write", "/app/main.js", "")
        code, _, _ = run_hook("check-secrets.py", data)
        assert code == 0

    def test_invalid_json_exits_clean(self, run_hook, hook_env):
        import subprocess, sys, os
        script = os.path.join(os.path.dirname(__file__), "..", "hooks", "scripts", "check-secrets.py")
        result = subprocess.run(
            [sys.executable, script],
            input="not json at all",
            capture_output=True, text=True, env=hook_env,
        )
        assert result.returncode == 0


class TestToolTypes:
    """All tool types extract content correctly."""

    def test_edit_scans_new_string(self, run_hook):
        data = make_pretool_input("Edit", "/app/config.js", new_string='key = "AKIAIOSFODNN7EXAMPLE"')
        code, _, stderr = run_hook("check-secrets.py", data)
        assert code == 2

    def test_multiedit_scans_all(self, run_hook):
        data = make_pretool_input(
            "MultiEdit", "/app/config.js",
            edits=[{"new_string": 'key = "AKIAIOSFODNN7EXAMPLE"'}]
        )
        code, _, stderr = run_hook("check-secrets.py", data)
        assert code == 2

    def test_non_write_tool_ignored(self, run_hook):
        data = {"session_id": "test", "tool_name": "Read", "tool_input": {"file_path": "/app/config.js"}}
        code, _, _ = run_hook("check-secrets.py", data)
        assert code == 0
