"""One passing and at least one failing case for every check (spec 0001, acceptance criterion 4)."""

import unittest

from support import Repo, array_of_ref, attr, enum_attr

FOUNDATION = "src/01_foundation/Foundation.hck.json"
COMMON = "src/01_foundation/common/CommonValueTypes.hck.json"
TA = "src/02_domain/HR/TalentAcquisition/TalentAcquisition.hck.json"
CORE_HR = "src/02_domain/HR/CoreHR/CoreHR.hck.json"
PROCESS = "src/03_process/_core/CoreProcess.hck.json"
APP = "src/04_application/CandidateJourney/CandidateJourney-PostgreSQL.hck.json"


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()

    def tearDown(self):
        self.repo.cleanup()

    def rules_found(self, check, rule_fragment):
        return [v for v in self.repo.check(check) if rule_fragment in v.rule or rule_fragment in v.message]


class TestLayers(CheckTest):
    def test_domain_may_reference_foundation(self):
        self.repo.model(FOUNDATION, "Foundation").save()
        ta = self.repo.model(TA, "Domain")
        ta.reference("Person", "../../../01_foundation/Foundation.hck.json")
        ta.save()
        self.assertEqual(self.repo.check("layers"), [])

    def test_foundation_may_not_reference_domain(self):
        self.repo.model(TA, "Domain").save()
        f = self.repo.model(FOUNDATION, "Foundation")
        f.reference("Candidate", "../02_domain/HR/TalentAcquisition/TalentAcquisition.hck.json")
        f.save()
        v = self.repo.check("layers")
        self.assertEqual(len(v), 1)
        self.assertIn("same or a lower layer", v[0].message)

    def test_broken_link(self):
        ta = self.repo.model(TA, "Domain")
        ta.reference("Person", "../../../01_foundation/Missing.hck.json")
        ta.save()
        self.assertIn("does not exist", self.repo.check("layers")[0].message)

    def test_model_outside_layer_folders(self):
        self.repo.model("src/misc/Stray.hck.json").save()
        self.assertIn("not inside any layer", self.repo.check("layers")[0].message)


class TestCycles(CheckTest):
    def test_no_cycle(self):
        self.repo.model(CORE_HR, "Domain").save()
        ta = self.repo.model(TA, "Domain")
        ta.reference("EmployeeRole", "../CoreHR/CoreHR.hck.json")
        ta.save()
        self.assertEqual(self.repo.check("cycles"), [])

    def test_two_model_cycle(self):
        ta = self.repo.model(TA, "Domain")
        ta.reference("EmployeeRole", "../CoreHR/CoreHR.hck.json")
        ta.save()
        core = self.repo.model(CORE_HR, "Domain")
        core.reference("Candidate", "../TalentAcquisition/TalentAcquisition.hck.json")
        core.save()
        v = self.repo.check("cycles")
        self.assertEqual(len(v), 1)
        self.assertIn("dependency cycle", v[0].message)


class TestNaming(CheckTest):
    def test_good_names(self):
        m = self.repo.model(TA, "Domain")
        m.entity("Job Requisition", [attr("requisition_id", code="requisition_id")], foundation_kind="Document",
                 code="job_requisition")
        m.save()
        self.assertEqual(self.repo.check("naming"), [])

    def test_bad_entity_attribute_reserved_and_technical_names(self):
        m = self.repo.model(TA, "Domain")
        m.entity("job requisition", [attr("GivenName"), attr("order"), attr("status", code="Status")],
                 foundation_kind="Document")
        m.save()
        rules = {v.rule for v in self.repo.check("naming")}
        self.assertEqual(rules, {"naming.entity_business_name", "naming.attribute_business_name",
                                 "naming.reserved_words", "naming.technical_name"})


class TestMetadata(CheckTest):
    def test_complete_metadata(self):
        m = self.repo.model(TA, "Domain")
        m.entity("Candidate", foundation_kind="Role")
        m.save()
        self.assertEqual(self.repo.check("metadata"), [])

    def test_missing_and_wrong_values(self):
        m = self.repo.model(TA)  # no edmLayer
        m.entity("Candidate", foundation_kind="Role", steward=None, entity_type="Main", description="")
        m.entity("Offer", foundation_kind="Agreement", layer="Foundation")
        m.save()
        rules = sorted(v.rule for v in self.repo.check("metadata"))
        # Candidate: no layer (model has none), no steward, bad entityType, no description.
        # Offer: layer says Foundation but the file is in the Domain folder.
        self.assertEqual(rules, ["metadata.description", "metadata.edmLayer", "metadata.entityType",
                                 "metadata.layer", "metadata.layer", "metadata.steward"])


class TestFoundationKind(CheckTest):
    def test_valid_kinds_per_layer(self):
        d = self.repo.model(TA, "Domain")
        d.entity("Candidate", foundation_kind="Role")
        d.save()
        f = self.repo.model(FOUNDATION, "Foundation")
        f.entity("Person", foundation_kind="Person")
        f.save()
        c = self.repo.model(COMMON, "Common")
        c.entity("Taxonomy", foundation_kind="none")
        c.save()
        self.assertEqual(self.repo.check("foundation_kind"), [])

    def test_invalid_kinds(self):
        d = self.repo.model(TA, "Domain")
        d.entity("Candidate", foundation_kind="Role;Agreement")
        d.save()
        f = self.repo.model(FOUNDATION, "Foundation")
        f.entity("Person", foundation_kind="Role")
        f.save()
        c = self.repo.model(COMMON, "Common")
        c.entity("Taxonomy", foundation_kind="Document")
        c.save()
        self.assertEqual(len(self.repo.check("foundation_kind")), 3)


def contract_attributes(repo, contract):
    """Attributes exactly as a base-type contract in the rules file describes them."""
    from edm.rules import Rules
    spec = Rules.load(repo.root).section("base_types")[contract]["attributes"]
    kinds = {"uuid": ("string", "uuid"), "string": ("string", "varchar"), "datetime": ("string", "timestamp"),
             "enum": ("string", "enum"), "array": ("array", None)}
    out = []
    for name, s in spec.items():
        type_word = s["type"].split("|")[0]
        if type_word.startswith("array<ref:"):
            a = array_of_ref(name, type_word[10:-1], s.get("description", ""))
        else:
            t, c = kinds[type_word]
            a = attr(name, t, c, s.get("required", False), s.get("primary_key", False), s.get("description", ""))
            if c == "enum":
                a["enum"] = ["ACTIVE"]
        out.append(a)
    return out


class TestBaseTypes(CheckTest):
    def test_entity_matching_contracts(self):
        m = self.repo.model(FOUNDATION, "Foundation")
        attrs = (contract_attributes(self.repo, "Entity") + contract_attributes(self.repo, "Identifiable")
                 + contract_attributes(self.repo, "Lifecycleable"))
        m.entity("Person", attrs, foundation_kind="Person", edmComposes="Entity;Identifiable;Lifecycleable;RoleHolder")
        m.save()
        self.assertEqual(self.repo.check("base_types"), [])

    def test_multiple_select_value_is_accepted(self):
        m = self.repo.model(FOUNDATION, "Foundation")
        m.entity("Period", contract_attributes(self.repo, "Entity"), foundation_kind="Period",
                 edmComposes=["Entity"])  # Hackolade stores a multiple-select property as a list
        m.save()
        self.assertEqual(self.repo.check("base_types"), [])

    def test_contract_violations(self):
        attrs = contract_attributes(self.repo, "Temporal")
        attrs = [a for a in attrs if a["name"] != "recorded_to"]          # missing attribute
        attrs[0]["childType"] = "date"                                     # wrong type (valid_from)
        attrs[1]["description"] = "Something else."                       # wrong description (valid_to)
        attrs[2]["required"] = True                                       # wrong required flag
        m = self.repo.model(FOUNDATION, "Foundation")
        m.entity("Role", attrs, foundation_kind="Role", edmComposes="Temporal;Auditable")
        m.save()
        msgs = [v.message for v in self.repo.check("base_types")]
        self.assertEqual(len(msgs), 5, msgs)
        self.assertTrue(any("unknown base type 'Auditable'" in x for x in msgs))


class TestEnums(CheckTest):
    def test_same_values_and_per_entity_lifecycles(self):
        m = self.repo.model(TA, "Domain")
        m.entity("Interview", [enum_attr("format", ["ONSITE", "VIDEO"]), enum_attr("lifecycle_state", ["A"])],
                 foundation_kind="Activity")
        m.entity("Assessment", [enum_attr("format", ["VIDEO", "ONSITE"]), enum_attr("lifecycle_state", ["B"])],
                 foundation_kind="Activity")
        m.save()
        self.assertEqual(self.repo.check("enums"), [])

    def test_drifting_values(self):
        m = self.repo.model(TA, "Domain")
        m.entity("Interview", [enum_attr("format", ["ONSITE", "VIDEO"])], foundation_kind="Activity")
        m.entity("Assessment", [enum_attr("format", ["ONSITE", "PHONE"])], foundation_kind="Activity")
        m.save()
        v = self.repo.check("enums")
        self.assertEqual(len(v), 1)
        self.assertIn("PHONE", v[0].message)


class TestJunctions(CheckTest):
    def build(self, links, key=True, connects="Interview;Interviewer"):
        m = self.repo.model(TA, "Domain")
        a = m.entity("Interview", foundation_kind="Activity")
        b = m.entity("Interviewer", foundation_kind="Role")
        c = m.entity("Person", foundation_kind="Role")
        j = m.entity("InterviewPanelAssignment", [attr("assignment_id", pk=key)], foundation_kind="Role",
                     entity_type="Bridge/Junction", edmConnects=connects)
        for parent in [a, b][:links]:
            m.relate("links", parent, j)
        m.relate("held by", c, j)   # a further relationship (inherited from Role) is allowed
        m.save()

    def test_valid_junction(self):
        self.build(2)
        self.assertEqual(self.repo.check("junctions"), [])

    def test_one_relationship(self):
        self.build(1)
        self.assertIn("no relationship to 'Interviewer'", self.repo.check("junctions")[0].message)

    def test_connects_must_name_two(self):
        self.build(2, connects="Interview")
        self.assertIn("must name the 2 entities", self.repo.check("junctions")[0].message)

    def test_no_key(self):
        self.build(2, key=False)
        self.assertIn("primary key", self.repo.check("junctions")[0].message)


class TestReferences(CheckTest):
    def build(self, values, with_id=True, with_target=True, extra=()):
        if with_target:
            d = self.repo.model(TA, "Domain")
            d.entity("Job Application", foundation_kind="Document")
            d.save()
        p = self.repo.model(PROCESS, "Process")
        attrs = [enum_attr("subject_entity_type", values)] + list(extra)
        if with_id:
            attrs.append(attr("subject_entity_id"))
        p.entity("ProcessInstance", attrs, foundation_kind="Activity")
        p.save()

    def test_allowed_pair(self):
        self.build(["JobApplication"])
        self.assertEqual(self.repo.check("references"), [])

    def test_type_not_allowed(self):
        self.build(["JobApplication", "Invoice"])
        self.assertIn("Invoice", self.repo.check("references")[0].message)

    def test_missing_id_attribute(self):
        self.build(["JobApplication"], with_id=False)
        self.assertIn("no matching id attribute", self.repo.check("references")[0].message)

    def test_allowed_type_not_in_edm(self):
        self.build(["JobApplication"], with_target=False)
        self.assertIn("not an entity in the EDM", self.repo.check("references")[0].message)

    def test_unconfigured_pair(self):
        self.build(["JobApplication"], extra=[attr("owner_entity_type"), attr("owner_entity_id")])
        self.assertIn("not listed", self.repo.check("references")[0].message)


class TestDeviations(CheckTest):
    def test_bookkeeping_only_and_reasoned_change(self):
        self.repo.model(FOUNDATION, "Foundation").save()
        self.repo.model(TA, "Domain").save()
        app = self.repo.model(APP, "Application", polyglot=False)
        app.derived("Person", "../../01_foundation/Foundation.hck.json",
                    {"properties": [{"GUID": "x", "childRelationships": ["r1"], "hackoladeMeta": {}}]})
        app.derived("Candidate", "../../02_domain/HR/TalentAcquisition/TalentAcquisition.hck.json",
                    {"properties": [{"GUID": "y", "required": True}]}, deviationReason="Not null in this application.")
        app.save()
        self.assertEqual(self.repo.check("deviations"), [])

    def test_forbidden_and_unexplained_changes(self):
        self.repo.model(FOUNDATION, "Foundation").save()
        self.repo.model(TA, "Domain").save()
        app = self.repo.model(APP, "Application", polyglot=False)
        app.derived("Person", "../../01_foundation/Foundation.hck.json",
                    {"properties": [{"GUID": "x", "description": "Changed locally."}]})
        app.derived("Candidate", "../../02_domain/HR/TalentAcquisition/TalentAcquisition.hck.json",
                    {"properties": [{"GUID": "y", "referenceDiffDeleted": True}]})
        app.save()
        rules = sorted(v.rule for v in self.repo.check("deviations"))
        self.assertEqual(rules, ["deviations.forbidden_from_layers", "deviations.reason_property"])


class TestFormat(CheckTest):
    def test_supported(self):
        self.repo.model(TA, "Domain").save()
        self.assertEqual(self.repo.check("format"), [])

    def test_old_version_bad_schema_and_unreadable(self):
        self.repo.model(TA, "Domain", version="8.11.6").save()
        self.repo.model(CORE_HR, "Domain", persistenceSchemaVersion="7").save()
        bad = self.repo.root / "src/02_domain/HR/Broken.hck.json"
        bad.write_text("{not json", encoding="utf-8")
        rules = sorted(v.rule for v in self.repo.check("format"))
        self.assertEqual(rules, ["format", "format.min_studio_version", "format.persistence_schema_versions"])


class TestOwnership(CheckTest):
    def test_single_owner(self):
        core = self.repo.model(CORE_HR, "Domain")
        core.entity("EmployeeRole", foundation_kind="Role")
        core.save()
        ta = self.repo.model(TA, "Domain")
        ta.derived("EmployeeRole", "../CoreHR/CoreHR.hck.json")
        ta.save()
        self.assertEqual(self.repo.check("ownership"), [])

    def test_defined_twice(self):
        for path in (CORE_HR, TA):
            m = self.repo.model(path, "Domain")
            m.entity("Employee Role", foundation_kind="Role")
            m.save()
        self.assertIn("also defined", self.repo.check("ownership")[0].message)


if __name__ == "__main__":
    unittest.main()


class TestFoundationContract(CheckTest):
    def foundation(self):
        f = self.repo.model(FOUNDATION, "Foundation")
        f.entity("Role", [attr("entity_id", pk=True, required=True),
                          enum_attr("role_type", ["EMPLOYEE", "CANDIDATE"], required=True),
                          attr("held_by_person"),
                          enum_attr("lifecycle_state", ["ACTIVE", "ENDED"], required=True)],
                 foundation_kind="Role")
        f.entity("Organization", [attr("legal_name", required=True)], foundation_kind="Organization")
        f.entity("LegalEntity", [attr("legal_name", required=True), attr("tax_identifier")],
                 foundation_kind="LegalEntity")
        f.entity("Activity", [attr("outcome")], foundation_kind="Activity")
        f.save()

    def test_allowed_changes(self):
        self.foundation()
        d = self.repo.model(TA, "Domain")
        d.entity("Candidate", [attr("entity_id", pk=True, required=True), attr("candidate_id", required=True),
                               enum_attr("role_type", ["CANDIDATE"], required=True),          # narrowed
                               attr("held_by_person", required=True),                          # tightened
                               enum_attr("lifecycle_state", ["NEW", "HIRED"], required=True)],  # replaced
                 foundation_kind="Role")
        d.entity("SelectionDecision", [enum_attr("outcome", ["HIRE", "REJECT"])],              # closed
                 foundation_kind="Activity")
        d.save()
        self.assertEqual(self.repo.check("foundation_contract"), [])

    def test_violations(self):
        self.foundation()
        d = self.repo.model(TA, "Domain")
        d.entity("Candidate", [attr("entity_id", pk=True, required=True),
                               enum_attr("role_type", ["VISITOR"], required=True),   # not a Foundation value
                               attr("held_by_person", "numeric", "integer"),         # type changed
                               enum_attr("lifecycle_state", ["NEW"])],               # loosened
                 foundation_kind="Role")
        d.entity("Interview", [], foundation_kind="Activity")                         # outcome missing
        d.save()
        msgs = sorted(v.obj + ": " + v.message for v in self.repo.check("foundation_contract"))
        self.assertEqual(len(msgs), 4, msgs)
        self.assertTrue(any("Interview.outcome: attribute of Foundation Activity is missing" in x for x in msgs))
        self.assertTrue(any("may not be made optional" in x for x in msgs))

    def test_foundation_subkind_carries_its_kind(self):
        f = self.repo.model(FOUNDATION, "Foundation")
        f.entity("Organization", [attr("legal_name", required=True)], foundation_kind="Organization")
        f.entity("OrganizationalUnit", [attr("cost_center_code")], foundation_kind="OrganizationalUnit")
        f.save()
        v = self.repo.check("foundation_contract")
        self.assertEqual([x.obj for x in v], ["OrganizationalUnit.legal_name"])


class TestRulesForKindsAndTechnicalEntities(CheckTest):
    def test_rule_on_a_kind_applies_to_its_specialisations(self):
        f = self.repo.model(FOUNDATION, "Foundation")
        for name in ("Person", "LegalEntity", "OrganizationalUnit", "Organization", "Team"):
            f.entity(name, foundation_kind=name)
        f.entity("Role", [enum_attr("engaging_party_entity_type", ["Person"]), attr("engaging_party_entity_id")],
                 foundation_kind="Role")
        f.save()
        d = self.repo.model(TA, "Domain")
        d.entity("Candidate", [enum_attr("engaging_party_entity_type", ["Person", "Invoice"]),
                               attr("engaging_party_entity_id")], foundation_kind="Role")
        d.save()
        v = [x for x in self.repo.check("references") if x.obj.startswith("Candidate")]
        self.assertEqual(len(v), 1, [x.message for x in v])
        self.assertIn("Invoice", v[0].message)

    def test_technical_entities_in_application_shared(self):
        m = self.repo.model("src/04_application/_shared/ApplicationShared.hck.json", "Application")
        m.entity("SourceSystemReference", foundation_kind="none", entity_type="Supporting")
        m.save()
        self.assertEqual(self.repo.check("foundation_kind"), [])
        app = self.repo.model("src/04_application/CandidateJourney/Local.hck.json", "Application")
        app.entity("LocalTable", foundation_kind="none")
        app.save()
        self.assertEqual(len(self.repo.check("foundation_kind")), 1)


class TestPhysicalAndBuilderOutput(CheckTest):
    def test_physical_type_change_on_foundation_entity_needs_only_a_reason(self):
        self.repo.model(FOUNDATION, "Foundation").save()
        app = self.repo.model(APP, "Application", polyglot=False)
        app.derived("Person", "../../01_foundation/Foundation.hck.json",
                    {"properties": [{"GUID": "x", "childType": "uuid", "mode": ""}]},
                    deviationReason="uuid columns in PostgreSQL.")
        app.save()
        self.assertEqual(self.repo.check("deviations"), [])

    def test_physical_type_change_without_reason(self):
        self.repo.model(FOUNDATION, "Foundation").save()
        app = self.repo.model(APP, "Application", polyglot=False)
        app.derived("Person", "../../01_foundation/Foundation.hck.json",
                    {"properties": [{"GUID": "x", "childType": "uuid"}]})
        app.save()
        self.assertEqual([v.rule for v in self.repo.check("deviations")], ["deviations.reason_property"])

    def test_builder_output_awaiting_studio_verification(self):
        self.repo.model(TA, "Domain", version="8.11.6", edmBuiltBy="migration/build.py").save()
        self.assertEqual(self.repo.check("format"), [])
