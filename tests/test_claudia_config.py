"""Tests for claudia_config.py — shared configuration module."""

import hashlib
import json
import os
import sys

import pytest

# Import the module directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks", "scripts"))
import claudia_config


class TestResolveProject:
    """resolve_project() — git root detection, md5 key generation."""

    def test_git_repo_detected(self, tmp_path, monkeypatch):
        project = tmp_path / "myproject"
        project.mkdir()
        (project / ".git").mkdir()
        monkeypatch.chdir(project)
        monkeypatch.setenv("HOME", str(tmp_path))

        key, path = claudia_config.resolve_project()
        assert path == str(project)
        expected_key = hashlib.md5(str(project).encode()).hexdigest()[:8]
        assert key == expected_key

    def test_home_dir_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))

        key, path = claudia_config.resolve_project()
        assert key is None
        assert path is None

    def test_nested_dir_finds_parent_git(self, tmp_path, monkeypatch):
        project = tmp_path / "myproject"
        project.mkdir()
        (project / ".git").mkdir()
        subdir = project / "src" / "components"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)
        monkeypatch.setenv("HOME", str(tmp_path))

        key, path = claudia_config.resolve_project()
        assert path == str(project)

    def test_no_git_uses_cwd(self, tmp_path, monkeypatch):
        project = tmp_path / "myproject"
        project.mkdir()
        monkeypatch.chdir(project)
        monkeypatch.setenv("HOME", str(tmp_path))

        key, path = claudia_config.resolve_project()
        assert path == str(project)
        assert key is not None


class TestLoadUserConfig:
    """load_user_config() — config file loading, defaults."""

    def test_defaults_when_no_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.chdir(tmp_path)

        proactivity, experience = claudia_config.load_user_config()
        assert proactivity == "moderate"
        assert experience == "intermediate"

    def test_custom_proactivity(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.chdir(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "claudia.json").write_text(json.dumps({"proactivity": "high"}))

        proactivity, experience = claudia_config.load_user_config()
        assert proactivity == "high"

    def test_experience_from_context(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.chdir(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "claudia-context.json").write_text(
            json.dumps({"experience": "beginner"})
        )

        _, experience = claudia_config.load_user_config()
        assert experience == "beginner"

    def test_corrupt_config_returns_defaults(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.chdir(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "claudia.json").write_text("not json!!!")

        proactivity, experience = claudia_config.load_user_config()
        assert proactivity == "moderate"


class TestProjectContext:
    """load_project_context / save_project_context — read/write cycle."""

    def test_save_and_load(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        claudia_config.save_project_context(
            {"stack": {"frontend": "React"}, "experience": "beginner"},
            key="abc12345",
            path="/fake/project",
        )

        ctx = claudia_config.load_project_context(key="abc12345")
        assert ctx["stack"]["frontend"] == "React"
        assert ctx["experience"] == "beginner"
        assert ctx["project_key"] == "abc12345"

    def test_fallback_to_global(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.chdir(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "claudia-context.json").write_text(
            json.dumps({"experience": "advanced", "stack": {"lang": "Python"}})
        )

        ctx = claudia_config.load_project_context(key="nonexistent")
        assert ctx["experience"] == "advanced"

    def test_no_context_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.chdir(tmp_path)

        ctx = claudia_config.load_project_context(key="nonexistent")
        assert ctx == {}

    def test_save_without_key_writes_global(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.chdir(tmp_path)  # At home dir, so no project
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        claudia_config.save_project_context({"experience": "beginner"})

        global_path = claude_dir / "claudia-context.json"
        assert global_path.exists()
        data = json.loads(global_path.read_text())
        assert data["experience"] == "beginner"

    def test_save_updates_registry(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        claudia_config.save_project_context(
            {"name": "test-proj"},
            key="abc12345",
            path="/fake/project",
        )

        registry = claudia_config.load_registry()
        assert "abc12345" in registry["projects"]
        assert registry["projects"]["abc12345"]["path"] == "/fake/project"


class TestLoadRegistry:
    def test_empty_registry(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        registry = claudia_config.load_registry()
        assert registry == {"version": 1, "projects": {}}

    def test_existing_registry(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        reg = {"version": 1, "projects": {"key1": {"name": "proj", "path": "/p", "last_active": "x", "created": "x"}}}
        (claude_dir / "claudia-projects.json").write_text(json.dumps(reg))

        result = claudia_config.load_registry()
        assert "key1" in result["projects"]
