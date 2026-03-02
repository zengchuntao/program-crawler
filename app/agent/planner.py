"""Planner — LLM understands the user's query and produces structured goals."""

from __future__ import annotations

import logging

from app.llm.base import BaseLLM
from contracts.models import ResearchGoal, ResearchQuery

logger = logging.getLogger("crawler.agent.planner")

PLANNER_SYSTEM_PROMPT = """\
You are a research planning assistant. Given a user's natural language query \
about academic programs, produce a structured research plan as JSON.

Return ONLY valid JSON with these fields:
- target_entities: list of strings — each entity to research \
  (e.g. "MIT Computer Science Master's")
- fields_requested: list of field name strings to look for. Valid field names:
  gpa_requirement, language_requirement, gre_gmat_requirement, prerequisites,
  deadlines, tuition_fees, materials, curriculum_summary, curriculum_links
- search_hints: list of suggested Google search queries to start the research

If the user's query is vague, infer the most likely intent.
If multiple entities are mentioned, list them all.
If no specific fields are mentioned, include the most relevant ones.
"""


async def plan_research(
    query: ResearchQuery,
    llm: BaseLLM,
) -> ResearchGoal:
    """
    Call LLM to parse a natural language query into structured ResearchGoal.
    Never raises — returns a best-effort goal on failure.
    """
    try:
        data = await llm.chat_json(
            system_prompt=PLANNER_SYSTEM_PROMPT,
            user_message=query.raw_query,
        )
        # Handle Gemini returning list instead of dict
        if isinstance(data, list):
            data = data[0] if data else {}
        goal = ResearchGoal(**data)
        logger.info(
            "Planner: %d entities, %d fields, %d hints",
            len(goal.target_entities),
            len(goal.fields_requested),
            len(goal.search_hints),
        )
        return goal
    except Exception as e:
        logger.warning("Planner failed: %s — using fallback", e)
        return ResearchGoal(
            target_entities=["unknown"],
            fields_requested=[
                "gpa_requirement",
                "language_requirement",
                "deadlines",
            ],
            search_hints=[query.raw_query],
        )
