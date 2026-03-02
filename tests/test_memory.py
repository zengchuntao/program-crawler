"""Tests for agent memory management."""

from app.agent.memory import add_findings, create_memory, prune_memory, record_visit
from contracts.models import Finding


class TestCreateMemory:
    def test_basic(self):
        mem = create_memory("test query")
        assert mem.query == "test query"
        assert mem.max_steps == 20
        assert mem.step_count == 0

    def test_custom_steps(self):
        mem = create_memory("test", max_steps=10)
        assert mem.max_steps == 10


class TestRecordVisit:
    def test_basic_visit(self):
        mem = create_memory("test")
        record_visit(mem, "https://example.com")
        assert len(mem.pages_visited) == 1
        assert mem.pages_visited[0].url == "https://example.com"

    def test_visit_with_details(self):
        mem = create_memory("test")
        record_visit(
            mem, "https://example.com",
            title="Test Page",
            text_snippet="Some content...",
            had_relevant_info=True,
            links_extracted=["https://example.com/link1"],
        )
        pv = mem.pages_visited[0]
        assert pv.title == "Test Page"
        assert pv.had_relevant_info is True
        assert len(pv.links_extracted) == 1


class TestAddFindings:
    def test_add_new_finding(self):
        mem = create_memory("test")
        findings = [Finding(
            entity="MIT", field_name="gpa_requirement",
            value="3.5", source_url="https://example.com",
        )]
        add_findings(mem, findings)
        assert len(mem.findings) == 1

    def test_deduplicate_findings(self):
        mem = create_memory("test")
        f1 = Finding(
            entity="MIT", field_name="gpa_requirement",
            value="3.5", source_url="https://a.com", confidence=0.8,
        )
        f2 = Finding(
            entity="MIT", field_name="gpa_requirement",
            value="3.5", source_url="https://b.com", confidence=0.7,
        )
        add_findings(mem, [f1])
        add_findings(mem, [f2])
        assert len(mem.findings) == 1  # deduplicated
        assert mem.findings[0].confidence == 0.8  # kept higher confidence

    def test_update_higher_confidence(self):
        mem = create_memory("test")
        f1 = Finding(
            entity="MIT", field_name="gpa_requirement",
            value="3.5", source_url="https://a.com", confidence=0.5,
        )
        f2 = Finding(
            entity="MIT", field_name="gpa_requirement",
            value="3.5", source_url="https://b.com", confidence=0.9,
        )
        add_findings(mem, [f1])
        add_findings(mem, [f2])
        assert len(mem.findings) == 1
        assert mem.findings[0].confidence == 0.9  # updated to higher

    def test_different_fields_not_deduplicated(self):
        mem = create_memory("test")
        f1 = Finding(entity="MIT", field_name="gpa_requirement", value="3.5", source_url="https://a.com")
        f2 = Finding(entity="MIT", field_name="language_requirement", value="IELTS 7.0", source_url="https://a.com")
        add_findings(mem, [f1, f2])
        assert len(mem.findings) == 2


class TestPruneMemory:
    def test_no_prune_needed(self):
        mem = create_memory("test")
        for i in range(5):
            record_visit(mem, f"https://example.com/{i}")
        prune_memory(mem, max_visits=10)
        assert len(mem.pages_visited) == 5

    def test_prune_keeps_relevant(self):
        mem = create_memory("test")
        # Add 20 visits, 3 relevant
        for i in range(20):
            record_visit(
                mem, f"https://example.com/{i}",
                had_relevant_info=(i in (2, 8, 15)),
            )
        prune_memory(mem, max_visits=10)
        assert len(mem.pages_visited) <= 10
        relevant = [p for p in mem.pages_visited if p.had_relevant_info]
        assert len(relevant) == 3  # all relevant visits kept
