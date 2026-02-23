"""Tests for check-dockerfile.py — Dockerfile anti-pattern detection hook."""

import json

from conftest import make_pretool_input


class TestDockerfilePatterns:
    """Each Dockerfile anti-pattern should trigger a warning."""

    def test_running_as_root(self, run_hook):
        data = make_pretool_input("Write", "/app/Dockerfile", "FROM node:18\nUSER root\nRUN npm install")
        code, stdout, _ = run_hook("check-dockerfile.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "root" in output["systemMessage"].lower()

    def test_large_base_image(self, run_hook):
        data = make_pretool_input("Write", "/app/Dockerfile", "FROM ubuntu:22.04\nRUN apt-get update")
        code, stdout, _ = run_hook("check-dockerfile.py", data)
        output = json.loads(stdout)
        assert "base image" in output["systemMessage"].lower() or "Large" in output["systemMessage"]

    def test_latest_tag(self, run_hook):
        data = make_pretool_input("Write", "/app/Dockerfile", "FROM node:latest\nRUN npm install")
        code, stdout, _ = run_hook("check-dockerfile.py", data)
        output = json.loads(stdout)
        assert "latest" in output["systemMessage"].lower()

    def test_apt_without_no_install_recommends(self, run_hook):
        data = make_pretool_input("Write", "/app/Dockerfile", "FROM node:18\nRUN apt-get install python3")
        code, stdout, _ = run_hook("check-dockerfile.py", data)
        output = json.loads(stdout)
        assert "no-install-recommends" in output["systemMessage"]

    def test_copy_all(self, run_hook):
        data = make_pretool_input("Write", "/app/Dockerfile", "FROM node:18\nCOPY . /app\nRUN npm install")
        code, stdout, _ = run_hook("check-dockerfile.py", data)
        output = json.loads(stdout)
        assert "COPY" in output["systemMessage"] or "context" in output["systemMessage"].lower()

    def test_npm_install_no_production(self, run_hook):
        data = make_pretool_input("Write", "/app/Dockerfile", "FROM node:18\nRUN npm install")
        code, stdout, _ = run_hook("check-dockerfile.py", data)
        output = json.loads(stdout)
        assert "npm" in output["systemMessage"].lower() or "production" in output["systemMessage"].lower()

    def test_secret_in_env(self, run_hook):
        data = make_pretool_input("Write", "/app/Dockerfile", "FROM node:18\nENV API_KEY=sk-abc123")
        code, stdout, _ = run_hook("check-dockerfile.py", data)
        output = json.loads(stdout)
        assert "secret" in output["systemMessage"].lower() or "Secret" in output["systemMessage"]

    def test_expose_ssh(self, run_hook):
        data = make_pretool_input("Write", "/app/Dockerfile", "FROM node:18\nEXPOSE 22")
        code, stdout, _ = run_hook("check-dockerfile.py", data)
        output = json.loads(stdout)
        assert "SSH" in output["systemMessage"]

    def test_chmod_777(self, run_hook):
        data = make_pretool_input("Write", "/app/Dockerfile", "FROM node:18\nRUN chmod 777 /app")
        code, stdout, _ = run_hook("check-dockerfile.py", data)
        output = json.loads(stdout)
        assert "777" in output["systemMessage"]


class TestMultiStageDetection:
    """Multi-stage build detection only on Write with >200 chars."""

    def test_missing_multistage_on_full_write(self, run_hook):
        content = "FROM node:18-alpine\n" + "RUN echo 'line'\n" * 20  # >200 chars
        data = make_pretool_input("Write", "/app/Dockerfile", content)
        code, stdout, _ = run_hook("check-dockerfile.py", data)
        output = json.loads(stdout)
        assert "multi-stage" in output["systemMessage"].lower()

    def test_multistage_present_no_warning(self, run_hook):
        content = "FROM node:18-alpine AS builder\nRUN npm ci\n" + "RUN echo 'line'\n" * 20
        data = make_pretool_input("Write", "/app/Dockerfile", content)
        code, stdout, _ = run_hook("check-dockerfile.py", data)
        # Should not warn about multi-stage if AS is present
        if stdout.strip():
            output = json.loads(stdout)
            assert "multi-stage" not in output["systemMessage"].lower()

    def test_short_write_no_multistage_warning(self, run_hook):
        data = make_pretool_input("Write", "/app/Dockerfile", "FROM node:18-alpine\nRUN npm ci")
        code, stdout, _ = run_hook("check-dockerfile.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "multi-stage" not in output["systemMessage"].lower()

    def test_edit_no_multistage_check(self, run_hook):
        content = "FROM node:18-alpine\n" + "RUN echo 'line'\n" * 20
        data = make_pretool_input("Edit", "/app/Dockerfile", new_string=content)
        code, stdout, _ = run_hook("check-dockerfile.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "multi-stage" not in output["systemMessage"].lower()


class TestFileFiltering:
    """Only Dockerfile-like files should be checked."""

    def test_non_dockerfile_ignored(self, run_hook):
        data = make_pretool_input("Write", "/app/main.js", "FROM ubuntu:latest")
        code, stdout, _ = run_hook("check-dockerfile.py", data)
        assert stdout.strip() == ""

    def test_dockerfile_dot_prod(self, run_hook):
        data = make_pretool_input("Write", "/app/Dockerfile.prod", "FROM node:latest")
        code, stdout, _ = run_hook("check-dockerfile.py", data)
        output = json.loads(stdout)
        assert "latest" in output["systemMessage"]

    def test_custom_dockerfile(self, run_hook):
        data = make_pretool_input("Write", "/app/build.dockerfile", "FROM node:latest")
        code, stdout, _ = run_hook("check-dockerfile.py", data)
        output = json.loads(stdout)
        assert "latest" in output["systemMessage"]
