"""Shared fixtures for Claudia hook tests."""

import json
import os
import subprocess
import sys
import tempfile

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "hooks", "scripts")


@pytest.fixture
def tmp_claude_dir(tmp_path):
    """Temp directory that stands in for ~/.claude/."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    return claude_dir


@pytest.fixture
def hook_env(tmp_path):
    """Environment dict with HOME pointed at tmp_path so state files land there."""
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    return env


def _run_hook(script_name, stdin_data, env, timeout=10):
    """Run a hook script as a subprocess with JSON on stdin.

    Returns (exit_code, stdout, stderr).
    """
    ext = os.path.splitext(script_name)[1]
    script_path = os.path.join(SCRIPTS_DIR, script_name)

    if ext == ".sh":
        cmd = ["bash", script_path]
    else:
        cmd = [sys.executable, script_path]

    result = subprocess.run(
        cmd,
        input=json.dumps(stdin_data),
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )
    return result.returncode, result.stdout, result.stderr


@pytest.fixture
def run_hook(hook_env):
    """Fixture that returns a callable to run hook scripts."""
    def _run(script_name, stdin_data, env_overrides=None):
        env = hook_env.copy()
        if env_overrides:
            env.update(env_overrides)
        return _run_hook(script_name, stdin_data, env)
    return _run


def make_pretool_input(tool_name, file_path, content=None, new_string=None,
                       edits=None, session_id="test-session"):
    """Build PreToolUse JSON input."""
    tool_input = {"file_path": file_path}
    if tool_name == "Write":
        tool_input["content"] = content or ""
    elif tool_name == "Edit":
        tool_input["new_string"] = new_string or content or ""
    elif tool_name == "MultiEdit":
        tool_input["edits"] = edits or [{"new_string": content or ""}]
    return {
        "session_id": session_id,
        "tool_name": tool_name,
        "tool_input": tool_input,
    }


def make_stop_input(message, session_id="test-session"):
    """Build Stop event JSON input."""
    return {
        "session_id": session_id,
        "last_assistant_message": message,
    }


def make_session_input(source, session_id="test-session"):
    """Build SessionStart JSON input."""
    return {
        "session_id": session_id,
        "source": source,
    }


def make_compact_input(trigger, session_id="test-session"):
    """Build PreCompact JSON input."""
    return {
        "session_id": session_id,
        "trigger": trigger,
    }


def make_prompt_input(prompt, session_id="test-session"):
    """Build UserPromptSubmit JSON input."""
    return {
        "session_id": session_id,
        "prompt": prompt,
    }


def setup_claudia_config(tmp_path, proactivity="moderate", experience="intermediate"):
    """Create fake claudia config files in the temp HOME directory."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(exist_ok=True)

    # Proactivity config
    config = {"proactivity": proactivity}
    (claude_dir / "claudia.json").write_text(json.dumps(config))

    # Experience via global context
    context = {"experience": experience}
    (claude_dir / "claudia-context.json").write_text(json.dumps(context))


def clear_stop_lock(tmp_path, session_id="test-session"):
    """Remove the per-turn stop lock so the next Stop hook can fire."""
    lock_file = tmp_path / ".claude" / f"claudia_stop_lock_{session_id}.tmp"
    if lock_file.exists():
        lock_file.unlink()
