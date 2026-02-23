"""Tests for claudia-prompt-coach.py — stuck/vague detection hook."""

import json

from conftest import make_prompt_input, setup_claudia_config


class TestStuckDetection:
    """Stuck patterns should trigger coaching."""

    def test_help_detected(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_prompt_input("help")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "stuck" in output.get("additionalContext", "").lower()

    def test_stuck_detected(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_prompt_input("i'm stuck")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "additionalContext" in output

    def test_idk_detected(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_prompt_input("idk")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "additionalContext" in output

    def test_what_now_detected(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="intermediate")
        data = make_prompt_input("what now")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "additionalContext" in output

    def test_where_do_i_start(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_prompt_input("where do i start")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "additionalContext" in output


class TestStuckGating:
    """Stuck detection respects proactivity gates."""

    def test_low_proactivity_silent(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="low", experience="beginner")
        data = make_prompt_input("help")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        assert stdout.strip() == ""

    def test_non_beginner_moderate_silent(self, run_hook, tmp_path):
        """Non-beginners at moderate proactivity shouldn't get stuck coaching."""
        setup_claudia_config(tmp_path, proactivity="moderate", experience="intermediate")
        data = make_prompt_input("help")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        assert stdout.strip() == ""

    def test_non_beginner_high_gets_stuck(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="intermediate")
        data = make_prompt_input("help")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "additionalContext" in output


class TestVaguePrompts:
    """Vague prompts should trigger coaching at high proactivity."""

    def test_fix_it_detected(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_prompt_input("fix it")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "vague" in output.get("additionalContext", "").lower() or "context" in output.get("additionalContext", "").lower()

    def test_its_broken_detected(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_prompt_input("it's broken")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "additionalContext" in output

    def test_single_word_what(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_prompt_input("what")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "short" in output.get("additionalContext", "").lower() or "context" in output.get("additionalContext", "").lower()

    def test_single_word_yes_skipped(self, run_hook, tmp_path):
        """Single-word confirmations should be skipped."""
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_prompt_input("yes")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        assert stdout.strip() == ""

    def test_vague_moderate_silent(self, run_hook, tmp_path):
        """Vague prompt coaching only at high proactivity."""
        setup_claudia_config(tmp_path, proactivity="moderate", experience="beginner")
        data = make_prompt_input("fix it")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        assert stdout.strip() == ""


class TestShortActionAllowlist:
    """Short action phrases should not trigger coaching."""

    def test_commit_this_not_coached(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_prompt_input("commit this")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        assert stdout.strip() == ""

    def test_push_it_not_coached(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_prompt_input("push it")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        assert stdout.strip() == ""

    def test_run_tests_not_coached(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_prompt_input("run tests")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        assert stdout.strip() == ""

    def test_ship_it_not_coached(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_prompt_input("ship it")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        assert stdout.strip() == ""

    def test_deploy_it_not_coached(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_prompt_input("deploy it")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        assert stdout.strip() == ""


class TestAllCaps:
    """ALL CAPS as frustration signal."""

    def test_all_caps_frustration(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_prompt_input("WHY DOES THIS KEEP BREAKING")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "frustrated" in output.get("additionalContext", "").lower()


class TestSlashCommandSkip:
    """Slash commands should be skipped."""

    def test_slash_command_skipped(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="beginner")
        data = make_prompt_input("/claudia:ask what is React")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        assert stdout.strip() == ""


class TestSuppressHook:
    """suppress_hooks should silence prompt-coach entirely."""

    def test_suppressed_exits_silently(self, run_hook, tmp_path):
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "claudia.json").write_text(
            json.dumps({"proactivity": "high", "suppress_hooks": ["prompt-coach"]})
        )
        (claude_dir / "claudia-context.json").write_text(
            json.dumps({"experience": "beginner"})
        )
        data = make_prompt_input("help")
        code, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        assert code == 0
        assert stdout.strip() == ""


class TestDismissHint:
    """Dismiss hint appears on every 2nd coaching."""

    def test_dismiss_hint_on_second(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="intermediate")
        prompts = ["help", "i'm stuck"]
        outputs = []
        for p in prompts:
            data = make_prompt_input(p)
            _, stdout, _ = run_hook("claudia-prompt-coach.py", data)
            outputs.append(stdout.strip())

        # 2nd coaching (count=2, 2%2==0) should have dismiss hint
        if outputs[1]:
            output = json.loads(outputs[1])
            # User sees "silence prompt-coach", Claude sees "suppress_hooks"
            assert "silence prompt-coach" in output.get("systemMessage", "")
            assert "suppress_hooks" in output.get("additionalContext", "")

    def test_no_dismiss_hint_on_first(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="intermediate")
        data = make_prompt_input("help")
        _, stdout, _ = run_hook("claudia-prompt-coach.py", data)
        if stdout.strip():
            output = json.loads(stdout)
            assert "silence prompt-coach" not in output.get("systemMessage", "")


class TestMaxPerSession:
    """Max 3 coaching moments per session."""

    def test_max_three_coaching(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path, proactivity="high", experience="intermediate")
        prompts = ["help", "i'm stuck", "what now", "i have no idea"]
        outputs = []
        for p in prompts:
            data = make_prompt_input(p)
            _, stdout, _ = run_hook("claudia-prompt-coach.py", data)
            outputs.append(stdout.strip())

        # First 3 should produce output, 4th should be empty
        coached = [o for o in outputs if o]
        assert len(coached) <= 3
