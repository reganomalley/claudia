"""Tests for suppress_topics feature in claudia-teach.py."""

import json

from conftest import make_stop_input, setup_claudia_config, clear_stop_lock


def _setup_with_suppress(tmp_path, suppress_topics, proactivity="high", experience="beginner"):
    """Set up config with suppress_topics list."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(exist_ok=True)

    config = {"proactivity": proactivity, "suppress_topics": suppress_topics}
    (claude_dir / "claudia.json").write_text(json.dumps(config))

    context = {"experience": experience}
    (claude_dir / "claudia-context.json").write_text(json.dumps(context))


class TestSuppressTopicsKeyword:
    """Suppressing a keyword name skips that keyword."""

    def test_suppressed_keyword_skipped(self, run_hook, tmp_path):
        _setup_with_suppress(tmp_path, ["Netlify"])
        data = make_stop_input("Deploy this on Netlify.")
        data["suppress_topics"] = ["Netlify"]
        code, stdout, _ = run_hook("claudia-teach.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "Netlify" not in output.get("additionalContext", "")

    def test_unsuppressed_keyword_still_fires(self, run_hook, tmp_path):
        _setup_with_suppress(tmp_path, ["Netlify"])
        data = make_stop_input("Deploy this on Vercel.")
        data["suppress_topics"] = ["Netlify"]
        code, stdout, _ = run_hook("claudia-teach.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "Vercel" in output.get("additionalContext", "")


class TestSuppressTopicsCategory:
    """Suppressing a category name skips all keywords in that category."""

    def test_category_suppresses_all_keywords(self, run_hook, tmp_path):
        _setup_with_suppress(tmp_path, ["hosting"])
        data = make_stop_input("Deploy this on Vercel or Netlify or Railway.")
        data["suppress_topics"] = ["hosting"]
        code, stdout, _ = run_hook("claudia-teach.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            ctx = output.get("additionalContext", "")
            assert "Vercel" not in ctx
            assert "Netlify" not in ctx
            assert "Railway" not in ctx


class TestSuppressCaseInsensitive:
    """Matching should be case-insensitive."""

    def test_lowercase_suppresses_titlecase(self, run_hook, tmp_path):
        _setup_with_suppress(tmp_path, ["netlify"])
        data = make_stop_input("Deploy this on Netlify.")
        data["suppress_topics"] = ["netlify"]
        code, stdout, _ = run_hook("claudia-teach.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "Netlify" not in output.get("additionalContext", "")

    def test_uppercase_suppresses(self, run_hook, tmp_path):
        _setup_with_suppress(tmp_path, ["HOSTING"])
        data = make_stop_input("Deploy this on Vercel.")
        data["suppress_topics"] = ["HOSTING"]
        code, stdout, _ = run_hook("claudia-teach.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "Vercel" not in output.get("additionalContext", "")


class TestSuppressEmpty:
    """Empty suppress_topics should change nothing."""

    def test_empty_list_no_effect(self, run_hook, tmp_path):
        _setup_with_suppress(tmp_path, [])
        data = make_stop_input("Deploy this on Vercel.")
        data["suppress_topics"] = []
        code, stdout, _ = run_hook("claudia-teach.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "Vercel" in output.get("additionalContext", "")

    def test_missing_key_no_effect(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_stop_input("Deploy this on Vercel.")
        # No suppress_topics key at all
        code, stdout, _ = run_hook("claudia-teach.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "Vercel" in output.get("additionalContext", "")


class TestDismissHint:
    """Every teach tip should include a dismiss hint."""

    def test_dismiss_hint_in_output(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_stop_input("Deploy this on Vercel.")
        code, stdout, _ = run_hook("claudia-teach.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            ctx = output.get("additionalContext", "")
            assert "suppress_topics" in ctx
            assert "claudia.json" in ctx
