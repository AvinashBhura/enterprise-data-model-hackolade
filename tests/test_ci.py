"""Tests for the CI helpers in ci/ (spec 0006)."""

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "ci" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestSpecGate(unittest.TestCase):
    def setUp(self):
        self.gate = load("spec_gate").gate
        self.status = {"0003": "Approved (2026-10-12)", "0007": "Draft"}.get

    def test_docs_only_change_needs_no_spec(self):
        self.assertTrue(self.gate("Fix typo", ["docs/index.md"], self.status)[0])

    def test_model_change_without_spec_fails(self):
        ok, msg = self.gate("Add interview fields", ["src/02_domain/HR/x.hck.json"], self.status)
        self.assertFalse(ok)
        self.assertIn("name its spec", msg)

    def test_model_change_with_approved_spec_passes(self):
        self.assertTrue(self.gate("[0003] Add interview fields", ["src/a.hck.json"], self.status)[0])

    def test_draft_or_unknown_spec_fails(self):
        self.assertFalse(self.gate("[0007] New rule", ["config/edm-rules.yaml"], self.status)[0])
        self.assertFalse(self.gate("[0099] New rule", ["tools/x.py"], self.status)[0])


class TestDeltaAndPlugins(unittest.TestCase):
    def test_delta_empty_and_summary(self):
        delta = load("delta")
        tmp = Path(tempfile.mkdtemp())
        (tmp / "empty.json").write_text(json.dumps({"collections": [], "relationships": []}))
        (tmp / "full.json").write_text(json.dumps({"collections": [{"collectionName": "Candidate"}]}))
        self.assertEqual(delta.main(["--empty", str(tmp / "empty.json")]), 0)
        self.assertEqual(delta.main(["--empty", str(tmp / "full.json")]), 1)
        out = io.StringIO()
        with redirect_stdout(out):
            delta.main(["--summary", str(tmp / "full.json"), "--title", "TA"])
        self.assertIn("entity `Candidate`", out.getvalue())

    def test_plugin_versions(self):
        check = load("check_plugins")
        tmp = Path(tempfile.mkdtemp())
        (tmp / "plugins.txt").write_text("# comment\nPostgreSQL 0.2.53\n")
        for text, expected in (("  PostgreSQL: 0.2.60, commit: x\n", 0), ("  PostgreSQL: 0.2.9, commit: x\n", 1),
                               ("  Oracle: 1.0.0\n", 1)):
            old = sys.stdin
            sys.stdin = io.StringIO(text)
            try:
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(check.main([str(tmp / "plugins.txt")]), expected, text)
            finally:
                sys.stdin = old


if __name__ == "__main__":
    unittest.main()
