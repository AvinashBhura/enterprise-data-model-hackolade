"""Repository-level rules from spec 0001."""

import csv
import io
import re
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from support import REPO

import install_hackolade_config as installer  # noqa: E402  (tools/ is on sys.path via support)
from edm.checks import CHECKS, Context  # noqa: E402
from edm.model import load_models  # noqa: E402
from edm.rules import Rules  # noqa: E402

# Spec 0001, requirement 2: folders that must explain themselves.
README_FOLDERS = [
    "src", "src/01_foundation", "src/01_foundation/common", "src/02_domain", "src/02_domain/_shared",
    "src/03_process", "src/03_process/_core", "src/04_application", "src/04_application/_shared",
    "tools", "config", "hackolade", "specs", "tests", "ci", "docs/decisions", "src/02_domain/HR",
]


class TestRepository(unittest.TestCase):
    def test_every_required_folder_has_a_readme(self):
        missing = [f for f in README_FOLDERS if not (REPO / f / "README.md").is_file()]
        self.assertEqual(missing, [])

    def test_every_model_folder_has_a_readme(self):
        missing = sorted({p.parent.relative_to(REPO).as_posix() for p in (REPO / "src").rglob("*.hck.json")
                          if not (p.parent / "README.md").is_file()})
        self.assertEqual(missing, [])

    def test_rules_file_has_every_section(self):
        rules = Rules.load(REPO)
        for section in ("scope", "layers", "metadata", "foundation", "naming", "type_map", "base_types",
                        "enums", "polymorphic_references", "deviations", "format"):
            self.assertIn(section, rules.raw, section)
        self.assertTrue(all(isinstance(w, str) for w in rules.section("naming")["reserved_words"]))

    def test_real_repository_passes_all_checks(self):
        rules = Rules.load(REPO)
        ctx = Context(REPO, rules, load_models(REPO, rules))
        violations = [str(v) for name in CHECKS for v in CHECKS[name](ctx)]
        self.assertEqual(violations, [])

    def test_no_old_schema_language_left_in_code(self):
        word = "link" + "ml"  # spelled in parts so this file passes the same search (spec 0001, criterion 2)
        hits = []
        for folder in ("src", "tools", "tests"):
            for p in (REPO / folder).rglob("*"):
                if p.is_file() and p.suffix in (".py", ".json", ".yaml", ".md"):
                    if word in p.read_text(encoding="utf-8", errors="ignore").lower():
                        hits.append(p.relative_to(REPO).as_posix())
        self.assertEqual(hits, [])

    def test_glossary_csv_matches_glossary_page(self):
        page = (REPO / "docs/architecture/glossary.md").read_text(encoding="utf-8")
        terms_on_page = re.findall(r"^\*\*(.+?)\*\* — ", page, re.M)
        with open(REPO / "hackolade/glossary/edm-glossary.csv", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual([r["Term"] for r in rows], terms_on_page)
        self.assertEqual(len({r["Term_ID"] for r in rows}), len(rows))


class TestModelFiles(unittest.TestCase):
    def test_internal_references_resolve(self):
        """Every model file's relationships, keys, derivations and links resolve (D12)."""
        script = REPO / "migration" / "validate_structure.py"
        if not script.exists():
            self.skipTest("migration/ has been removed")
        import importlib.util
        import json
        spec = importlib.util.spec_from_file_location("validate_structure", script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        problems = []
        for f in sorted((REPO / "src").rglob("*.hck.json")):
            problems += [f"{f.name}: {p}" for p in mod.integrity(f, json.loads(f.read_text(encoding="utf-8")))]
        self.assertEqual(problems, [])


class TestAIAssets(unittest.TestCase):
    """Spec 0006, acceptance criteria 5 and 6."""

    def test_skills_have_front_matter(self):
        skills = sorted((REPO / ".claude" / "skills").glob("*/SKILL.md"))
        self.assertGreaterEqual(len(skills), 3)
        for path in skills:
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), path)
            front = text.split("---\n")[1]
            self.assertRegex(front, r"(?m)^name: " + re.escape(path.parent.name) + r"\s*$", path)
            self.assertRegex(front, r"(?m)^description: \S", path)

    def test_agents_have_front_matter(self):
        agents = sorted((REPO / ".claude" / "agents").glob("*.md"))
        self.assertEqual([a.stem for a in agents],
                         ["application-modeller", "governance-checker", "model-reviewer", "spec-author"])
        for path in agents:
            front = path.read_text(encoding="utf-8").split("---\n")[1]
            self.assertRegex(front, r"(?m)^name: " + path.stem + r"\s*$")
            self.assertRegex(front, r"(?m)^description: \S")

    def test_no_old_schema_language_in_ai_assets(self):
        word = "link" + "ml"
        paths = [REPO / "AGENTS.md", REPO / "CLAUDE.md"]
        for folder in (".github", ".claude"):
            paths += [p for p in (REPO / folder).rglob("*") if p.is_file()]
        hits = [p.relative_to(REPO).as_posix() for p in paths
                if word in p.read_text(encoding="utf-8", errors="ignore").lower()]
        self.assertEqual(hits, [])


class TestHackoladeConfigInstaller(unittest.TestCase):
    def setUp(self):
        self.options = Path(tempfile.mkdtemp(prefix="hk-options-"))

    def tearDown(self):
        shutil.rmtree(self.options, ignore_errors=True)

    def run_installer(self, *args):
        out = io.StringIO()
        with redirect_stdout(out):
            installer.main(["--options", str(self.options), *args])
        return out.getvalue()

    def test_dry_run_writes_nothing(self):
        out = self.run_installer()
        self.assertIn("Dry run", out)
        self.assertEqual(list(self.options.iterdir()), [])

    def test_force_backs_up_and_applies(self):
        target = self.options / "Polyglot/customProperties/properties_pane/entity_level/entityLevelConfig.json"
        target.parent.mkdir(parents=True)
        target.write_text("[]", encoding="utf-8")
        out = self.run_installer("--force")
        self.assertIn("Backed up 1 file(s)", out)
        self.assertNotEqual(target.read_text(encoding="utf-8"), "[]")
        backups = list(self.options.glob("edm-backup-*/Polyglot/customProperties/properties_pane/entity_level/entityLevelConfig.json"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), "[]")
        self.assertIn("0 file(s) to add or change", self.run_installer())


if __name__ == "__main__":
    unittest.main()
