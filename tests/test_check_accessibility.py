"""Tests for check-accessibility.py — a11y pattern detection hook."""

import json

from conftest import make_pretool_input


class TestA11yPatterns:
    """Each a11y issue should trigger a warning."""

    def test_img_without_alt(self, run_hook):
        data = make_pretool_input("Write", "/app/page.html", '<img src="photo.jpg">')
        code, stdout, _ = run_hook("check-accessibility.py", data)
        assert code == 0
        output = json.loads(stdout)
        assert "alt" in output["systemMessage"].lower()

    def test_img_with_alt_ok(self, run_hook):
        data = make_pretool_input("Write", "/app/page.html", '<img src="photo.jpg" alt="A photo">')
        code, stdout, _ = run_hook("check-accessibility.py", data)
        assert code == 0
        # Should not warn about missing alt
        if stdout.strip():
            output = json.loads(stdout)
            assert "alt" not in output["systemMessage"].lower() or "without alt" not in output["systemMessage"].lower()

    def test_positive_tabindex(self, run_hook):
        data = make_pretool_input("Write", "/app/page.jsx", '<div tabIndex="5">')
        code, stdout, _ = run_hook("check-accessibility.py", data)
        output = json.loads(stdout)
        assert "tabIndex" in output["systemMessage"] or "tab" in output["systemMessage"].lower()

    def test_anchor_without_href(self, run_hook):
        data = make_pretool_input("Write", "/app/page.html", '<a onClick={handleClick}>Click</a>')
        code, stdout, _ = run_hook("check-accessibility.py", data)
        output = json.loads(stdout)
        assert "href" in output["systemMessage"].lower() or "Anchor" in output["systemMessage"]

    def test_autofocus_detected(self, run_hook):
        data = make_pretool_input("Write", "/app/page.tsx", '<input autoFocus />')
        code, stdout, _ = run_hook("check-accessibility.py", data)
        output = json.loads(stdout)
        assert "autoFocus" in output["systemMessage"] or "autofocus" in output["systemMessage"].lower()

    def test_empty_heading(self, run_hook):
        data = make_pretool_input("Write", "/app/page.html", '<h1></h1>')
        code, stdout, _ = run_hook("check-accessibility.py", data)
        output = json.loads(stdout)
        assert "heading" in output["systemMessage"].lower()


class TestFileFiltering:
    """Only HTML/JSX/Vue/Svelte files should be checked."""

    def test_js_file_ignored(self, run_hook):
        data = make_pretool_input("Write", "/app/main.js", '<img src="photo.jpg">')
        code, stdout, _ = run_hook("check-accessibility.py", data)
        assert stdout.strip() == ""

    def test_py_file_ignored(self, run_hook):
        data = make_pretool_input("Write", "/app/main.py", '<img src="photo.jpg">')
        code, stdout, _ = run_hook("check-accessibility.py", data)
        assert stdout.strip() == ""

    def test_vue_file_checked(self, run_hook):
        data = make_pretool_input("Write", "/app/Page.vue", '<img src="photo.jpg">')
        code, stdout, _ = run_hook("check-accessibility.py", data)
        output = json.loads(stdout)
        assert "alt" in output["systemMessage"].lower()

    def test_svelte_file_checked(self, run_hook):
        data = make_pretool_input("Write", "/app/Page.svelte", '<img src="photo.jpg">')
        code, stdout, _ = run_hook("check-accessibility.py", data)
        output = json.loads(stdout)
        assert "alt" in output["systemMessage"].lower()

    def test_astro_file_checked(self, run_hook):
        data = make_pretool_input("Write", "/app/page.astro", '<img src="photo.jpg">')
        code, stdout, _ = run_hook("check-accessibility.py", data)
        output = json.loads(stdout)
        assert "alt" in output["systemMessage"].lower()


class TestTestFileSkipping:
    def test_test_file_skipped(self, run_hook):
        data = make_pretool_input("Write", "/app/page.test.tsx", '<img src="photo.jpg">')
        code, stdout, _ = run_hook("check-accessibility.py", data)
        assert stdout.strip() == ""

    def test_spec_file_skipped(self, run_hook):
        data = make_pretool_input("Write", "/app/page.spec.jsx", '<img src="photo.jpg">')
        code, stdout, _ = run_hook("check-accessibility.py", data)
        assert stdout.strip() == ""

    def test_test_dir_skipped(self, run_hook):
        data = make_pretool_input("Write", "/app/tests/page.html", '<img src="photo.jpg">')
        code, stdout, _ = run_hook("check-accessibility.py", data)
        assert stdout.strip() == ""
