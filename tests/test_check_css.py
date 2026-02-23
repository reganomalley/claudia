"""Tests for check-css.py — CSS anti-pattern detection."""

import json

from conftest import make_pretool_input, setup_claudia_config


class TestImportantDetection:
    def test_important_warns(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path)
        data = make_pretool_input("Write", "src/style.css", "color: red !important;")
        code, stdout, _ = run_hook("check-css.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "!important" in output.get("systemMessage", "")

    def test_important_in_tsx(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path)
        content = 'const Foo = styled.div`color: red !important;`'
        data = make_pretool_input("Write", "src/Foo.tsx", content)
        code, stdout, _ = run_hook("check-css.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "!important" in output.get("systemMessage", "")


class TestZIndexDetection:
    def test_high_z_index_warns(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path)
        data = make_pretool_input("Write", "src/modal.css", ".modal { z-index: 9999; }")
        code, stdout, _ = run_hook("check-css.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "z-index" in output.get("systemMessage", "")

    def test_normal_z_index_no_warn(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path)
        data = make_pretool_input("Write", "src/nav.css", ".nav { z-index: 10; }")
        code, stdout, _ = run_hook("check-css.py", data)
        assert code == 0
        assert stdout.strip() == ""


class TestHardcodedColors:
    def test_hardcoded_color_warns(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path)
        data = make_pretool_input("Write", "src/button.css", ".btn { color: #ff0000; }")
        code, stdout, _ = run_hook("check-css.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "Hardcoded color" in output.get("systemMessage", "")

    def test_theme_file_skips_color_warning(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path)
        data = make_pretool_input("Write", "src/theme.css", ":root { --primary: #ff0000; }")
        code, stdout, _ = run_hook("check-css.py", data)
        assert code == 0
        # Should not warn about hardcoded colors in theme files
        if stdout.strip():
            output = json.loads(stdout)
            assert "Hardcoded color" not in output.get("systemMessage", "")

    def test_global_css_skips_color_warning(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path)
        data = make_pretool_input("Write", "src/styles/global.css", ":root { --brand: #d70000; }")
        code, stdout, _ = run_hook("check-css.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "Hardcoded color" not in output.get("systemMessage", "")


class TestFloatDetection:
    def test_float_warns(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path)
        data = make_pretool_input("Write", "src/layout.css", ".sidebar { float: left; }")
        code, stdout, _ = run_hook("check-css.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "Float" in output.get("systemMessage", "")


class TestUniversalReset:
    def test_universal_reset_warns(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path)
        data = make_pretool_input("Write", "src/reset.css", "* { margin: 0; padding: 0; }")
        code, stdout, _ = run_hook("check-css.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "Universal selector" in output.get("systemMessage", "")


class TestFileFiltering:
    def test_non_css_file_ignored(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path)
        data = make_pretool_input("Write", "src/utils.py", "important = True")
        code, stdout, _ = run_hook("check-css.py", data)
        assert code == 0
        assert stdout.strip() == ""

    def test_js_file_without_styles_ignored(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path)
        data = make_pretool_input("Write", "src/utils.jsx", "const x = 1;")
        code, stdout, _ = run_hook("check-css.py", data)
        assert code == 0
        assert stdout.strip() == ""

    def test_scss_file_detected(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path)
        data = make_pretool_input("Write", "src/app.scss", ".foo { color: red !important; }")
        code, stdout, _ = run_hook("check-css.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "!important" in output.get("systemMessage", "")


class TestDedup:
    def test_same_pattern_same_file_deduped(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path)
        data = make_pretool_input("Write", "src/a.css", "color: red !important;")
        run_hook("check-css.py", data)
        # Second time, same file — should be silent
        code, stdout, _ = run_hook("check-css.py", data)
        assert code == 0
        assert stdout.strip() == ""

    def test_same_pattern_different_file_not_deduped(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path)
        data1 = make_pretool_input("Write", "src/a.css", "color: red !important;")
        run_hook("check-css.py", data1)
        # Different file — should still warn
        data2 = make_pretool_input("Write", "src/b.css", "color: blue !important;")
        code, stdout, _ = run_hook("check-css.py", data2)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "!important" in output.get("systemMessage", "")


class TestEditTool:
    def test_edit_tool_detected(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path)
        data = make_pretool_input("Edit", "src/style.css", new_string="z-index: 99999;")
        code, stdout, _ = run_hook("check-css.py", data)
        assert code == 0
        if stdout.strip():
            output = json.loads(stdout)
            assert "z-index" in output.get("systemMessage", "")

    def test_empty_content_silent(self, run_hook, tmp_path):
        setup_claudia_config(tmp_path)
        data = make_pretool_input("Write", "src/style.css", "")
        code, stdout, _ = run_hook("check-css.py", data)
        assert code == 0
        assert stdout.strip() == ""
