"""Action Picker — LLM decides the agent's next step."""

from __future__ import annotations

import logging

from app.llm.base import BaseLLM
from app.tools.registry import ToolRegistry
from contracts.models import ActionType, AgentAction, AgentMemory

logger = logging.getLogger("crawler.agent.action_picker")

ACTION_PICKER_SYSTEM_PROMPT = """\
You are an action decision-maker for a research agent.
Based on the agent's current memory (pages visited, findings so far, \
fields still needed, and available URLs from search results), \
decide the next action.

Return ONLY valid JSON with these fields:
- action_type: one of "search", "visit", "done", "give_up"
- url: string or null — the URL to visit (only for "visit" actions)
- search_query: string or null (only for "search" actions)
- reasoning: string — brief explanation of why

CRITICAL RULES:
- NEVER visit a URL that appears in the "Pages visited" list — it will \
  be skipped automatically. Choose a DIFFERENT URL or search with \
  a NEW query.
- If there are pending URLs from search results, you MUST "visit" \
  one of them. Do NOT search again when you already have URLs to visit.
- If we still need fields and haven't searched yet, use "search"
- If all requested fields have been found, use "done"
- If no progress after visiting many pages, try "search" with a \
  different query. If still no progress, use "done" (partial is OK).
- Prefer official .edu domains and admissions pages
- If a field genuinely does not exist (e.g. no minimum GPA published), \
  use "done" — partial results are acceptable.

Available tools for fetching pages:
{tools_description}
"""


async def pick_action(
    memory: AgentMemory,
    llm: BaseLLM,
    tool_registry: ToolRegistry | None = None,
    pending_urls: list[str] | None = None,
) -> AgentAction:
    """
    Call LLM to decide next agent action.
    Never raises — returns give_up on failure.
    """
    tools_desc = ""
    if tool_registry:
        tools_desc = tool_registry.describe_all_text()

    system = ACTION_PICKER_SYSTEM_PROMPT.replace(
        "{tools_description}", tools_desc
    )
    summary = _summarize_memory(memory, pending_urls or [])

    try:
        data = await llm.chat_json(
            system_prompt=system,
            user_message=summary,
        )

        if isinstance(data, list):
            data = data[0] if data else {}

        action = AgentAction(
            action_type=ActionType(
                data.get("action_type", "give_up")
            ),
            url=data.get("url"),
            search_query=data.get("search_query"),
            reasoning=data.get("reasoning", ""),
        )
        logger.info(
            "Action: %s — %s",
            action.action_type,
            action.reasoning[:80],
        )
        return action

    except Exception as e:
        logger.warning("Action picker failed: %s", e)
        return AgentAction(
            action_type=ActionType.GIVE_UP,
            reasoning=f"Action picker failed: {e}",
        )


def _summarize_memory(
    memory: AgentMemory,
    pending_urls: list[str],
) -> str:
    """Format agent memory as text for the LLM."""
    parts = [
        f"Research query: {memory.query}",
        f"Step: {memory.step_count}/{memory.max_steps}",
    ]

    if memory.goals:
        parts.append(
            "Target entities: "
            + ", ".join(memory.goals.target_entities)
        )
        parts.append(
            "Fields requested: "
            + ", ".join(memory.goals.fields_requested)
        )

    fields_needed = memory.fields_still_needed()
    if fields_needed:
        parts.append(
            "Fields still needed: "
            + ", ".join(fields_needed)
        )
    else:
        parts.append("All fields have been found!")

    if memory.findings:
        parts.append("\nFindings so far:")
        for f in memory.findings:
            parts.append(
                f"  - {f.entity} / {f.field_name}: "
                f"{f.value} (conf: {f.confidence})"
            )

    if pending_urls:
        parts.append(
            f"\nPending URLs from search ({len(pending_urls)}):"
        )
        for url in pending_urls[:10]:
            parts.append(f"  - {url}")
        parts.append(
            ">>> You MUST visit one of these URLs. "
            "Do NOT search again."
        )

    if memory.pages_visited:
        parts.append(
            f"\nPages visited ({len(memory.pages_visited)}):"
        )
        for p in memory.pages_visited[-5:]:
            tag = (
                "relevant" if p.had_relevant_info
                else "not relevant"
            )
            parts.append(f"  - {p.url} ({tag})")
            if p.links_extracted:
                unvisited = [
                    lnk
                    for lnk in p.links_extracted
                    if lnk not in memory.visited_urls()
                ]
                if unvisited:
                    parts.append(
                        "    Unvisited links: "
                        + ", ".join(unvisited[:5])
                    )

    return "\n".join(parts)
