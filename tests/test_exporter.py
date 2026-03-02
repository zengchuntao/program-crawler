"""Tests for the Excel exporter."""

from pathlib import Path

from contracts.models import (
    CrawlStatus,
    EvidenceItem,
    EvidenceRefs,
    ExtractedFields,
    ProgramRecord,
    ScreenshotType,
)
from app.export.xlsx_exporter import XlsxExporter


def test_exporter_creates_file(tmp_path: Path):
    exporter = XlsxExporter()

    record = ProgramRecord(
        program_id="test123",
        program_url="https://example.com",
        school_name="Test University",
        status=CrawlStatus.SUCCESS,
        fields=ExtractedFields(gpa_requirement="3.5", language_requirement="IELTS 7.0"),
        evidence=EvidenceRefs(
            gpa_evidence_ids=["EVID-001"],
            language_evidence_ids=["EVID-001"],
        ),
    )
    evidence = [
        EvidenceItem(
            evidence_id="EVID-001",
            program_id="test123",
            field="gpa_requirement",
            source_url="https://example.com",
            screenshot_files=["evidence/test123/full_page.png"],
            screenshot_type=ScreenshotType.FULL_PAGE,
        )
    ]

    exporter.add_program(record)
    exporter.add_evidence(evidence)

    out_path = tmp_path / "results.xlsx"
    result = exporter.save(out_path)
    assert result.exists()
    assert result.stat().st_size > 0


def test_exporter_multiple_screenshots(tmp_path: Path):
    exporter = XlsxExporter()

    evidence = [
        EvidenceItem(
            evidence_id="EVID-002",
            program_id="test456",
            field="language_requirement",
            source_url="https://example.com",
            screenshot_files=["shot1.png", "shot2.png", "shot3.png"],
            screenshot_type=ScreenshotType.CROPPED,
        )
    ]
    exporter.add_evidence(evidence)

    out_path = tmp_path / "multi.xlsx"
    result = exporter.save(out_path)
    assert result.exists()
