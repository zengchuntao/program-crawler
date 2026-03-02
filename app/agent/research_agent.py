"""Research Agent — core loop using LLM abstraction + Tool registry."""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path

from app.agent.action_picker import pick_action
from app.agent.evaluator import evaluate_page
from app.agent.memory import (
    add_findings,
    create_memory,
    prune_memory,
    record_visit,
)
from app.agent.planner import plan_research
from app.llm.base import BaseLLM
from app.tools.registry import ToolRegistry
from contracts.models import (
    ActionType,
    AgentLogStep,
    EvidenceItem,
    ResearchQuery,
    ResearchResult,
    ResearchStatus,
    generate_evidence_id,
)

logger = logging.getLogger("crawler.agent")


async def run_research(
    query: ResearchQuery,
    llm: BaseLLM,
    tools: ToolRegistry,
    out_base: str = "out",
) -> ResearchResult:
    """
    Main research agent loop.

    1. Planner LLM → structured goals
    2. Loop (max_steps):
       a. Action Picker LLM → next action
       b. Execute action via ToolRegistry
       c. Evaluator LLM → extract findings
       d. Capture evidence screenshots
    3. Return ResearchResult
    """
    start_time = time.time()
    memory = create_memory(query.raw_query, query.max_steps)
    agent_log: list[AgentLogStep] = []
    evidence_items: list[EvidenceItem] = []

    base_path = Path(out_base).resolve()
    base_path.mkdir(parents=True, exist_ok=True)
    ev_dir = base_path / "evidence" / "agent"
    ev_dir.mkdir(parents=True, exist_ok=True)

    # --- Step 0: Plan ---
    logger.info("=== Agent start: %s ===", query.raw_query)
    goals = await plan_research(query, llm)
    memory.goals = goals
    logger.info(
        "Goals: entities=%s, fields=%s, hints=%s",
        goals.target_entities,
        goals.fields_requested,
        goals.search_hints,
    )

    pending_urls: list[str] = []
    failed_searches: int = 0

    # --- Agent Loop ---
    while memory.has_budget():
        memory.step_count += 1
        step_num = memory.step_count

        # Clean pending_urls: remove already-visited URLs
        visited = memory.visited_urls()
        pending_urls = [u for u in pending_urls if u not in visited]

        action = await pick_action(
            memory, llm, tools, pending_urls=pending_urls,
        )

        log_step = AgentLogStep(
            step=step_num,
            action_type=action.action_type.value,
            url_or_query=action.url or action.search_query,
            reasoning=action.reasoning,
        )

        logger.info(
            "[Step %d/%d] %s: %s",
            step_num, memory.max_steps,
            action.action_type.value,
            action.url or action.search_query or "",
        )

        # --- SEARCH ---
        if action.action_type == ActionType.SEARCH:
            search_query = action.search_query or (
                query.raw_query
            )
            log_step.url_or_query = search_query

            search_tool = tools.get("google_search")
            if search_tool:
                result = await search_tool.execute(
                    query=search_query
                )
                if result.success:
                    new_urls = [
                        r["url"]
                        for r in result.data.get("results", [])
                        if r["url"] not in memory.visited_urls()
                    ]
                    if new_urls:
                        pending_urls.extend(new_urls)
                        failed_searches = 0
                        logger.info(
                            "Search: %d results, %d new",
                            result.data.get("count", 0),
                            len(new_urls),
                        )
                    else:
                        failed_searches += 1
                        logger.info(
                            "Search: 0 usable results "
                            "(%d consecutive fails)",
                            failed_searches,
                        )
                        record_visit(
                            memory,
                            f"search:{search_query}",
                            text_snippet=(
                                "Search returned 0 results. "
                                "Try a shorter/different query "
                                "or visit URLs directly."
                            ),
                            had_relevant_info=False,
                        )
                else:
                    failed_searches += 1
                    logger.warning(
                        "Search failed: %s", result.error
                    )

            # After 3 consecutive search failures,
            # force agent to try visiting known URLs
            if failed_searches >= 3 and not pending_urls:
                logger.info(
                    "3+ search failures, injecting "
                    "direct URLs from goals"
                )
                _inject_fallback_urls(
                    goals, pending_urls, memory,
                )

        # --- VISIT ---
        elif action.action_type == ActionType.VISIT:
            url = action.url
            if not url and pending_urls:
                url = pending_urls.pop(0)
            if not url or url in memory.visited_urls():
                record_visit(
                    memory, url or "skipped",
                    had_relevant_info=False,
                )
                agent_log.append(log_step)
                continue

            log_step.url_or_query = url

            # Remove from pending since we're visiting it now
            if url in pending_urls:
                pending_urls.remove(url)

            # Pick which tool to use for fetching
            tool_name = _extract_tool_name(action.reasoning)

            # Fallback chain: try tools in order until one works
            fetch_chain = _build_fetch_chain(tool_name, tools)

            try:
                fetch_result = None
                best_result = None  # Keep best thin result
                for ft_name, ft_tool in fetch_chain:
                    fetch_result = await ft_tool.execute(url=url)
                    if fetch_result.success:
                        text = fetch_result.data.get("text", "")
                        if len(text.strip()) < 100:
                            # Thin content — save as fallback
                            if not best_result:
                                best_result = fetch_result
                            logger.info(
                                "%s returned thin content "
                                "(%d chars), trying next",
                                ft_name, len(text.strip()),
                            )
                            continue
                        break
                    logger.info(
                        "%s failed for %s, trying next",
                        ft_name, url,
                    )

                # Use thin result if all richer tools failed
                if fetch_result and not fetch_result.success:
                    if best_result:
                        fetch_result = best_result
                    else:
                        record_visit(
                            memory, url, had_relevant_info=False
                        )
                        agent_log.append(log_step)
                        continue

                if not fetch_result or not fetch_result.success:
                    record_visit(
                        memory, url, had_relevant_info=False
                    )
                    agent_log.append(log_step)
                    continue

                page_text = fetch_result.data.get("text", "")
                page_title = fetch_result.data.get("title", "")

                # Check if we still need fields
                fields_needed = memory.fields_still_needed()
                if not fields_needed:
                    record_visit(
                        memory, url, title=page_title,
                        had_relevant_info=False,
                    )
                    log_step.found_info = False
                    agent_log.append(log_step)
                    break

                # Evaluate page
                findings, useful_links, relevant = (
                    await evaluate_page(
                        page_text=page_text,
                        page_url=url,
                        fields_needed=fields_needed,
                        target_entities=goals.target_entities,
                        llm=llm,
                    )
                )

                record_visit(
                    memory, url,
                    title=page_title,
                    text_snippet=page_text[:300],
                    had_relevant_info=relevant,
                    links_extracted=useful_links,
                )

                # Process findings + screenshot evidence
                if findings:
                    log_step.found_info = True
                    screenshot_tool = tools.get("screenshot")

                    for finding in findings:
                        finding.source_url = url
                        shot_file = str(
                            ev_dir
                            / f"{finding.finding_id}_full.png"
                        )

                        if screenshot_tool:
                            shot_result = (
                                await screenshot_tool.execute(
                                    url=url,
                                    save_path=shot_file,
                                )
                            )
                            if shot_result.success:
                                finding.screenshot_file = (
                                    shot_file
                                )
                                ev = EvidenceItem(
                                    evidence_id=(
                                        generate_evidence_id()
                                    ),
                                    program_id="agent",
                                    field=finding.field_name,
                                    source_url=url,
                                    screenshot_files=[shot_file],
                                )
                                finding.evidence_id = (
                                    ev.evidence_id
                                )
                                evidence_items.append(ev)

                    add_findings(memory, findings)

                # Queue useful links
                for link in useful_links:
                    if (
                        link not in memory.visited_urls()
                        and link not in pending_urls
                    ):
                        pending_urls.append(link)

            except Exception as e:
                logger.warning("Visit failed %s: %s", url, e)
                record_visit(
                    memory, url, had_relevant_info=False
                )

        # --- DONE ---
        elif action.action_type == ActionType.DONE:
            log_step.found_info = len(memory.findings) > 0
            agent_log.append(log_step)
            logger.info("Agent: DONE")
            break

        # --- GIVE UP ---
        elif action.action_type == ActionType.GIVE_UP:
            agent_log.append(log_step)
            logger.info("Agent: GIVE UP — %s", action.reasoning)
            break

        agent_log.append(log_step)
        prune_memory(memory)

    # --- Build result ---
    duration = time.time() - start_time
    missing = memory.fields_still_needed()

    if not memory.findings:
        status = ResearchStatus.FAILED
    elif missing:
        status = ResearchStatus.PARTIAL
    else:
        status = ResearchStatus.COMPLETE

    result = ResearchResult(
        query=query.raw_query,
        goals=goals,
        findings=memory.findings,
        missing_fields=missing,
        evidence_items=evidence_items,
        agent_log=agent_log,
        status=status,
        duration_s=round(duration, 2),
        total_steps=memory.step_count,
        pages_visited=len(memory.pages_visited),
    )

    logger.info(
        "=== Done: %s | %d findings | %d missing | %.1fs ===",
        status.value, len(result.findings),
        len(missing), duration,
    )
    return result


def _extract_tool_name(reasoning: str) -> str:
    """Extract tool name from action reasoning if present."""
    match = re.search(r'\[tool=(\w+)\]', reasoning)
    if match:
        return match.group(1)
    return "http_fetch"


def _build_fetch_chain(
    preferred: str, tools: ToolRegistry
) -> list[tuple[str, "BaseTool"]]:
    """Build an ordered list of (name, tool) to try for fetching.

    Order: preferred tool first, then http_fetch, playwright, stealth.
    Deduplicates and skips tools not in the registry.
    """
    order = [preferred, "http_fetch", "playwright", "stealth_browser"]
    seen: set[str] = set()
    chain = []
    for name in order:
        if name in seen:
            continue
        seen.add(name)
        tool = tools.get(name)
        if tool:
            chain.append((name, tool))
    return chain


def _inject_fallback_urls(
    goals, pending_urls: list[str], memory,
) -> None:
    """When searches fail, inject plausible URLs based on goals.

    Uses entity names to construct common university URL patterns.
    """
    visited = memory.visited_urls()
    injected = 0

    for hint in goals.search_hints:
        # Try to extract domain-style keywords from hints
        words = hint.lower().split()
        # Look for university-like patterns
        for word in words:
            if len(word) > 3:
                # Common university postgrad URL patterns
                patterns = [
                    f"https://www.{word}.edu.hk/pg/",
                    f"https://www.{word}.edu/admissions/",
                ]
                for url in patterns:
                    if url not in visited and url not in pending_urls:
                        pending_urls.append(url)
                        injected += 1

    # For known Hong Kong universities, inject specific URLs
    entity_text = " ".join(
        goals.target_entities
    ).lower()
    hk_urls = []
    if "city university" in entity_text or "cityu" in entity_text:
        hk_urls = [
            "https://www.cityu.edu.hk/pg/taught-postgraduate-programmes/list",
            "https://www.cityu.edu.hk/pg/taught-postgraduate-programmes/apply-now",
            "https://www.cb.cityu.edu.hk/postgrad/",
        ]
    elif "hong kong university" in entity_text or "hku" in entity_text:
        hk_urls = [
            "https://www.hku.hk/prospective-students/taught-postgraduate.html",
            "https://admissions.hku.hk/tpg/",
        ]
    elif "chinese university" in entity_text or "cuhk" in entity_text:
        hk_urls = [
            "https://www.gs.cuhk.edu.hk/admissions/",
        ]
    elif "polyu" in entity_text or "polytechnic" in entity_text:
        hk_urls = [
            "https://www.polyu.edu.hk/study/pg/",
        ]

    for url in hk_urls:
        if url not in visited and url not in pending_urls:
            pending_urls.append(url)
            injected += 1

    if injected:
        logger.info("Injected %d fallback URLs", injected)
