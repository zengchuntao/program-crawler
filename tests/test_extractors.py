"""Tests for rule-based extractors."""

from app.extractor.rule_extractors import (
    extract_credits,
    extract_deadline_dates,
    extract_ielts_toefl,
)


class TestIeltsToefl:
    def test_ielts_score(self):
        text = "Applicants must have IELTS overall 7.0 or TOEFL iBT 100"
        result = extract_ielts_toefl(text)
        assert result is not None
        assert "IELTS" in result
        assert "TOEFL" in result

    def test_duolingo(self):
        text = "DET 120 or Duolingo English Test 115"
        result = extract_ielts_toefl(text)
        assert result is not None
        assert "120" in result or "115" in result

    def test_no_match(self):
        result = extract_ielts_toefl("No language requirements mentioned here.")
        assert result is None


class TestDeadlines:
    def test_date_format_1(self):
        text = "Application deadline: January 15, 2025"
        result = extract_deadline_dates(text)
        assert result is not None
        assert "January 15" in result

    def test_iso_format(self):
        text = "Deadline: 2025-03-01"
        result = extract_deadline_dates(text)
        assert "2025-03-01" in result

    def test_no_match(self):
        result = extract_deadline_dates("Rolling admissions are available.")
        assert result is None


class TestCredits:
    def test_credit_hours(self):
        result = extract_credits("The program requires 36 credit hours")
        assert result is not None
        assert "36" in result

    def test_units(self):
        result = extract_credits("Students must complete 48 units")
        assert result is not None
        assert "48" in result

    def test_no_match(self):
        result = extract_credits("No information about workload.")
        assert result is None
