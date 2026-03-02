"""Tests for the validator."""

from app.validate.validator import validate_fields
from contracts.models import ExtractedFields


def test_valid_fields_no_warnings():
    fields = ExtractedFields(
        language_requirement="IELTS 7.0",
        deadlines="January 15, 2025",
    )
    warnings = validate_fields(fields)
    assert len(warnings) == 0


def test_empty_critical_fields():
    fields = ExtractedFields()  # all None
    warnings = validate_fields(fields)
    assert any("language_requirement" in w for w in warnings)
    assert any("deadlines" in w for w in warnings)


def test_unusual_gpa():
    fields = ExtractedFields(
        gpa_requirement="7.5",
        language_requirement="TOEFL 100",
        deadlines="2025-03-01",
    )
    warnings = validate_fields(fields)
    assert any("GPA" in w for w in warnings)


def test_ielts_out_of_range():
    fields = ExtractedFields(
        language_requirement="IELTS 12.0",
        deadlines="2025-03-01",
    )
    warnings = validate_fields(fields)
    assert any("IELTS" in w for w in warnings)
