"""Memory management — summarization, token budgeting, context pruning."""

from __future__ import annotations

import logging

from contracts.models import AgentMemory, Finding, PageVisit

logger = logging.getLogger("crawler.agent.memory")


def create_memory(query: str, max_steps: int = 20) -> AgentMemory:
    """Initialize a fresh agent memory."""
    return AgentMemory(
        query=query,
        max_steps=max_steps,
    )


def record_visit(
    memory: AgentMemory,
    url: str,
    title: str | None = None,
    text_snippet: str | None = None,
    had_relevant_info: bool = False,
    links_extracted: list[str] | None = None,
) -> None:
    """Record a page visit in memory."""
    memory.pages_visited.append(PageVisit(
        url=url,
        title=title,
        text_snippet=text_snippet[:500] if text_snippet else None,
        had_relevant_info=had_relevant_info,
        links_extracted=links_extracted or [],
    ))


def add_findings(memory: AgentMemory, findings: list[Finding]) -> None:
    """Add new findings to memory, deduplicating by field_name."""
    existing_fields = {(f.entity, f.field_name) for f in memory.findings}
    for finding in findings:
        key = (finding.entity, finding.field_name)
        if key not in existing_fields:
            memory.findings.append(finding)
            existing_fields.add(key)
            logger.info(
                "New finding: %s / %s = %s",
                finding.entity, finding.field_name, finding.value,
            )
        else:
            # Update if new finding has higher confidence
            for i, existing in enumerate(memory.findings):
                if (existing.entity, existing.field_name) == key:
                    if finding.confidence > existing.confidence:
                        memory.findings[i] = finding
                        logger.info(
                            "Updated finding: %s / %s = %s (confidence %.2f → %.2f)",
                            finding.entity, finding.field_name, finding.value,
                            existing.confidence, finding.confidence,
                        )
                    break


def prune_memory(memory: AgentMemory, max_visits: int = 15) -> None:
    """
    Prune old page visits to keep memory within token budget.
    Keeps the most recent visits and all visits with relevant info.
    """
    if len(memory.pages_visited) <= max_visits:
        return

    # Keep visits with relevant info + most recent ones
    relevant = [p for p in memory.pages_visited if p.had_relevant_info]
    non_relevant = [p for p in memory.pages_visited if not p.had_relevant_info]

    # Keep all relevant + as many recent non-relevant as budget allows
    budget = max_visits - len(relevant)
    if budget > 0:
        memory.pages_visited = relevant + non_relevant[-budget:]
    else:
        memory.pages_visited = relevant[-max_visits:]

    logger.debug("Pruned memory to %d visits", len(memory.pages_visited))
