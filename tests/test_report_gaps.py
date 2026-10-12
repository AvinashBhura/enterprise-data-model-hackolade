"""Fixture tests for tools/report_gaps.py (spec 0005, acceptance criterion 5)."""

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from support import attr, enum_attr  # noqa: F401  (support puts tools/ on sys.path)

import report_gaps  # noqa: E402

DOMAIN = {
    "modelName": "TalentAcquisition",
    "collections": [{
        "collectionName": "JobApplication",
        "properties": [
            attr("entity_id", pattern="^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}"),
            attr("application_id"),
            attr("applied_date", "string", "date"),
            attr("screening_score", "numeric", "number"),
            enum_attr("stage", ["SCREEN", "INTERVIEW", "OFFER"]),
        ],
    }],
}


def column(name, type_="string", child="char", mode="varchar", maps_to=None, **extra):
    c = {"name": name, "code": name, "type": type_, "childType": child, "mode": mode}
    if maps_to:
        c["edmMapsTo"] = maps_to
    c.update(extra)
    return c


def app(columns, table_maps_to="TalentAcquisition.JobApplication"):
    t = {"collectionName": "applications", "code": "applications", "properties": columns}
    if table_maps_to:
        t["edmMapsTo"] = table_maps_to.split(".", 1)[1]
    return {"modelName": "LegacyATS", "collections": [t,
            {"collectionName": "audit_log", "code": "audit_log", "properties": [column("id")]}]}


class TestReportGaps(unittest.TestCase):
    def test_fully_mapped_table_has_only_the_unmapped_audit_table(self):
        cols = [column("id", "string", "uuid", None, "JobApplication.entity_id"),
                column("app_no", maps_to="JobApplication.application_id"),
                column("applied_on", "string", "datetime", "date", "JobApplication.applied_date"),
                column("score", "numeric", "numeric", "numeric", "JobApplication.screening_score"),
                column("stage", maps_to="JobApplication.stage", enum=["SCREEN", "INTERVIEW", "OFFER"])]
        r = report_gaps.report(app(cols), [DOMAIN])
        self.assertEqual(r.unmapped_tables, ["`audit_log`"])
        self.assertEqual(r.unmapped_columns, ["`audit_log.id`"])
        self.assertEqual((r.mismatches, r.missing, r.bad_mappings), ([], [], []))

    def test_type_enum_and_missing_attribute_gaps(self):
        cols = [column("id", maps_to="JobApplication.entity_id"),                      # text, not uuid
                column("applied_on", maps_to="JobApplication.applied_date"),           # text, not date
                column("stage", maps_to="JobApplication.stage", enum=["SCREEN", "HIRED"]),
                column("legacy_flag"),                                                 # unmapped
                column("owner", maps_to="JobApplication.owner")]                       # no such attribute
        r = report_gaps.report(app(cols), [DOMAIN])
        self.assertEqual(len(r.mismatches), 3, r.mismatches)
        self.assertTrue(any("extra ['HIRED']" in m for m in r.mismatches))
        self.assertIn("`applications.legacy_flag`", r.unmapped_columns)
        self.assertEqual(len(r.bad_mappings), 1)
        self.assertEqual(sorted(r.missing), ["`JobApplication.application_id`", "`JobApplication.screening_score`"])

    def test_cli_writes_markdown_and_can_fail(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "app.json").write_text(json.dumps(app([column("x")])), encoding="utf-8")
        (tmp / "dom.json").write_text(json.dumps(DOMAIN), encoding="utf-8")
        (tmp / "delta.json").write_text(json.dumps({"collections": [{"collectionName": "applications"}]}),
                                        encoding="utf-8")
        with redirect_stdout(StringIO()):
            code = report_gaps.main(["--model", str(tmp / "app.json"), "--domain", str(tmp / "dom.json"),
                                     "--delta", str(tmp / "delta.json"), "--out", str(tmp / "gaps.md"),
                                     "--fail-on-gaps"])
        self.assertEqual(code, 1)
        text = (tmp / "gaps.md").read_text(encoding="utf-8")
        self.assertIn("# Gap report: LegacyATS", text)
        self.assertIn("Entities the compMod delta lists", text)


if __name__ == "__main__":
    unittest.main()
