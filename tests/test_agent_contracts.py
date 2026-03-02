"""Tests for new agent-oriented data contracts."""

import pytest
from pydantic import ValidationError

from contracts.models import (
    ActionType,
    AgentAction,
    AgentLogStep,
    AgentMemory,
    Finding,
    PageVisit,
    ResearchGoal,
    ResearchQuery,
    ResearchResult,
    ResearchStatus,
    generate_finding_id,
)


class TestResearchQuery:
    def test_required_query(self):
        with pytest.raises(ValidationError):
            ResearchQuery()

    def test_defaults(self):
        rq = ResearchQuery(raw_query="Find MIT CS GPA requirements")
        assert rq.max_steps == 20

    def test_custom_max_steps(self):
        rq = ResearchQuery(raw_query="test", max_steps=10)
        assert rq.max_steps == 10


class TestResearchGoal:
    def test_empty_defaults(self):
        goal = ResearchGoal()
        assert goal.target_entities == []
        assert goal.fields_requested == []
        assert goal.search_hints == []

    def test_full_goal(self):
        goal = ResearchGoal(
            target_entities=["MIT CS Master's"],
            fields_requested=["gpa_requirement", "language_requirement"],
            search_hints=["MIT EECS graduate admissions"],
        )
        assert len(goal.target_entities) == 1
        assert len(goal.fields_requested) == 2


class TestAgentAction:
    def test_search_action(self):
        action = AgentAction(
            action_type=ActionType.SEARCH,
            search_query="MIT admissions",
            reasoning="Need to find MIT admission page",
        )
        assert action.action_type == ActionType.SEARCH
        assert action.url is None

    def test_visit_action(self):
        action = AgentAction(
            action_type=ActionType.VISIT,
            url="https://example.com",
            reasoning="Visiting admission page",
        )
        assert action.action_type == ActionType.VISIT

    def test_done_action(self):
        action = AgentAction(action_type=ActionType.DONE, reasoning="All fields found")
        assert action.action_type == ActionType.DONE


class TestFinding:
    def test_auto_id(self):
        f = Finding(
            entity="MIT CS Master's",
            field_name="gpa_requirement",
            value="3.5",
            source_url="https://example.com",
        )
        assert f.finding_id.startswith("FIND-")
        assert len(f.finding_id) == 13

    def test_unique_ids(self):
        id1 = generate_finding_id()
        id2 = generate_finding_id()
        assert id1 != id2

    def test_confidence_bounds(self):
        f = Finding(
            entity="MIT", field_name="gpa", value="3.5",
            source_url="https://example.com", confidence=0.95,
        )
        assert f.confidence == 0.95

    def test_confidence_out_of_range(self):
        with pytest.raises(ValidationError):
            Finding(
                entity="MIT", field_name="gpa", value="3.5",
                source_url="https://example.com", confidence=1.5,
            )


class TestPageVisit:
    def test_defaults(self):
        pv = PageVisit(url="https://example.com")
        assert pv.had_relevant_info is False
        assert pv.links_extracted == []
        assert pv.visited_at is not None

    def test_with_data(self):
        pv = PageVisit(
            url="https://example.com",
            title="Test Page",
            text_snippet="Some text...",
            had_relevant_info=True,
            links_extracted=["https://example.com/link1"],
        )
        assert pv.had_relevant_info is True
        assert len(pv.links_extracted) == 1


class TestAgentMemory:
    def test_empty_memory(self):
        mem = AgentMemory(query="test query")
        assert mem.step_count == 0
        assert mem.max_steps == 20
        assert mem.has_budget()

    def test_fields_still_needed_no_goals(self):
        mem = AgentMemory(query="test")
        assert mem.fields_still_needed() == []

    def test_fields_still_needed_with_goals(self):
        mem = AgentMemory(
            query="test",
            goals=ResearchGoal(
                target_entities=["MIT"],
                fields_requested=["gpa_requirement", "language_requirement"],
            ),
            findings=[
                Finding(
                    entity="MIT", field_name="gpa_requirement",
                    value="3.5", source_url="https://example.com",
                ),
            ],
        )
        needed = mem.fields_still_needed()
        assert needed == ["language_requirement"]

    def test_visited_urls(self):
        mem = AgentMemory(
            query="test",
            pages_visited=[
                PageVisit(url="https://a.com"),
                PageVisit(url="https://b.com"),
            ],
        )
        assert mem.visited_urls() == {"https://a.com", "https://b.com"}

    def test_budget_exhausted(self):
        mem = AgentMemory(query="test", max_steps=5, step_count=5)
        assert not mem.has_budget()


class TestAgentLogStep:
    def test_creation(self):
        step = AgentLogStep(
            step=1,
            action_type="search",
            url_or_query="MIT admissions",
            reasoning="Starting research",
        )
        assert step.step == 1
        assert step.found_info is False


class TestResearchResult:
    def test_empty_result(self):
        result = ResearchResult(query="test")
        assert result.status == ResearchStatus.COMPLETE
        assert result.findings == []
        assert result.total_steps == 0

    def test_full_result(self):
        result = ResearchResult(
            query="Find MIT CS info",
            findings=[
                Finding(
                    entity="MIT", field_name="gpa_requirement",
                    value="3.5", source_url="https://example.com",
                ),
            ],
            missing_fields=["language_requirement"],
            status=ResearchStatus.PARTIAL,
            duration_s=15.3,
            total_steps=8,
            pages_visited=5,
        )
        assert result.status == ResearchStatus.PARTIAL
        assert len(result.findings) == 1
        assert result.duration_s == 15.3

    def test_json_roundtrip(self):
        result = ResearchResult(
            query="test",
            status=ResearchStatus.COMPLETE,
            findings=[
                Finding(
                    entity="MIT", field_name="gpa_requirement",
                    value="3.5", source_url="https://example.com",
                    confidence=0.9,
                ),
            ],
        )
        json_str = result.model_dump_json()
        r2 = ResearchResult.model_validate_json(json_str)
        assert r2.findings[0].value == "3.5"
        assert r2.findings[0].confidence == 0.9
