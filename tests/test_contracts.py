"""Tests for data contracts — serialization, validation, required fields."""

import pytest
from pydantic import ValidationError

from contracts.models import (
    CrawlStatus,
    Document,
    EvidenceItem,
    EvidenceRefs,
    ExtractedFields,
    FetchMode,
    FetchPlan,
    ProgramInput,
    ProgramRecord,
    RunLogEntry,
    generate_evidence_id,
    generate_program_id,
)


class TestProgramInput:
    def test_required_url(self):
        with pytest.raises(ValidationError):
            ProgramInput()  # missing program_url

    def test_auto_id_generation(self):
        inp = ProgramInput(program_url="https://example.com/program")
        assert inp.program_id is not None
        assert len(inp.program_id) == 12

    def test_stable_id(self):
        url = "https://example.com/program"
        id1 = generate_program_id(url)
        id2 = generate_program_id(url)
        assert id1 == id2

    def test_optional_fields(self):
        inp = ProgramInput(program_url="https://example.com")
        assert inp.school_name is None
        assert inp.program_name is None
        assert inp.degree_level is None

    def test_full_input(self):
        inp = ProgramInput(
            program_url="https://example.com",
            school_name="MIT",
            program_name="CS",
            degree_level="Master",
        )
        assert inp.school_name == "MIT"


class TestFetchPlan:
    def test_defaults(self):
        plan = FetchPlan(url="https://example.com")
        assert plan.mode == FetchMode.BROWSER
        assert plan.wait_until == "networkidle"
        assert plan.timeout_ms == 30000
        assert plan.extra_actions == []


class TestDocument:
    def test_minimal(self):
        doc = Document(
            program_id="abc123",
            source_url="https://example.com",
            final_url="https://example.com",
            fetch_mode=FetchMode.HTTP,
        )
        assert doc.html is None
        assert doc.text is None
        assert doc.fetched_at is not None


class TestEvidenceItem:
    def test_auto_evidence_id(self):
        ev = EvidenceItem(
            program_id="abc123",
            field="language_requirement",
            source_url="https://example.com",
        )
        assert ev.evidence_id.startswith("EVID-")
        assert len(ev.evidence_id) == 13  # EVID- + 8 hex

    def test_multiple_screenshots(self):
        ev = EvidenceItem(
            program_id="abc123",
            field="gpa_requirement",
            source_url="https://example.com",
            screenshot_files=["shot1.png", "shot2.png", "shot3.png"],
        )
        assert len(ev.screenshot_files) == 3

    def test_unique_ids(self):
        id1 = generate_evidence_id()
        id2 = generate_evidence_id()
        assert id1 != id2


class TestExtractedFields:
    def test_all_optional(self):
        f = ExtractedFields()
        assert f.gpa_requirement is None
        assert f.curriculum_links == []

    def test_serialization_roundtrip(self):
        f = ExtractedFields(
            gpa_requirement="3.5",
            language_requirement="IELTS 7.0",
            curriculum_links=["https://example.com/curriculum"],
        )
        data = f.model_dump()
        f2 = ExtractedFields(**data)
        assert f2.gpa_requirement == "3.5"
        assert len(f2.curriculum_links) == 1


class TestProgramRecord:
    def test_default_status(self):
        r = ProgramRecord(program_id="abc", program_url="https://example.com")
        assert r.status == CrawlStatus.SUCCESS
        assert r.warnings == []

    def test_json_roundtrip(self):
        r = ProgramRecord(
            program_id="abc",
            program_url="https://example.com",
            school_name="MIT",
            status=CrawlStatus.PARTIAL,
            warnings=["missing deadlines"],
            fields=ExtractedFields(gpa_requirement="3.0"),
            evidence=EvidenceRefs(gpa_evidence_ids=["EVID-aaa"]),
        )
        json_str = r.model_dump_json()
        r2 = ProgramRecord.model_validate_json(json_str)
        assert r2.status == CrawlStatus.PARTIAL
        assert r2.fields.gpa_requirement == "3.0"
        assert r2.evidence.gpa_evidence_ids == ["EVID-aaa"]


class TestEvidenceRefs:
    def test_all_empty_by_default(self):
        refs = EvidenceRefs()
        assert refs.gpa_evidence_ids == []
        assert refs.language_evidence_ids == []


class TestRunLogEntry:
    def test_required_fields(self):
        from datetime import UTC, datetime
        entry = RunLogEntry(
            program_id="abc",
            program_url="https://example.com",
            status=CrawlStatus.SUCCESS,
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
            duration_s=1.5,
        )
        assert entry.error is None
        assert entry.warnings == []
