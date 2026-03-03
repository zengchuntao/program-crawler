"""Evaluator — LLM reads page content and extracts findings."""

from __future__ import annotations

import logging

from app.llm.base import BaseLLM
from app.util.text_utils import truncate_text
from contracts.models import Finding, generate_finding_id

logger = logging.getLogger("crawler.agent.evaluator")

EVALUATOR_SYSTEM_PROMPT = """\
You are a page content evaluator for academic program research.
Given a page's text content and a list of fields we're still looking for, \
extract any relevant FACTUAL information found on this page.

Return ONLY valid JSON with these fields:
- findings: list of objects, each with:
  - entity: string (the specific program this info is about, e.g. "CityU MSc Finance")
  - field_name: string (one of the requested field names)
  - value: string (the extracted factual value)
  - confidence: float between 0.0 and 1.0
- useful_links: list of URL strings found on the page that might \
contain more relevant info (especially links to individual program pages)
- page_relevant: boolean — was this page relevant to our research?

CRITICAL RULES:
- Extract ONLY concrete, factual data — specific dates, scores, dollar \
amounts, document lists, course names.
- Do NOT extract marketing slogans, taglines, or vague descriptions as \
"curriculum_summary". A real curriculum_summary must list actual courses \
or describe the program structure (e.g. "42 credits, core courses include \
Financial Accounting, Corporate Finance, Capstone Project").
- For "deadlines", extract specific dates (e.g. "31 March 2026"), NOT \
vague statements like "applications open".
- For "tuition_fees", extract actual numbers with currency.
- If a page only lists program NAMES without details, report useful_links \
to each program's detail page instead of creating low-value findings.
- Do not invent data — only extract what is clearly stated on the page.

If no concrete factual info is found, return:
{"findings": [], "useful_links": [], "page_relevant": false}.
"""


async def evaluate_page(
    page_text: str,
    page_url: str,
    fields_needed: list[str],
    target_entities: list[str],
    llm: BaseLLM,
) -> tuple[list[Finding], list[str], bool]:
    """
    Call LLM to evaluate a page's content.

    Returns:
        (findings, useful_links, page_relevant)
    """
    text = truncate_text(page_text, max_chars=12000)

    user_msg = (
        f"Page URL: {page_url}\n"
        f"Target entities: {', '.join(target_entities)}\n"
        f"Fields we still need: {', '.join(fields_needed)}\n\n"
        f"Page text:\n{text}"
    )

    try:
        data = await llm.chat_json(
            system_prompt=EVALUATOR_SYSTEM_PROMPT,
            user_message=user_msg,
        )

        # Handle Gemini returning list instead of dict
        if isinstance(data, list):
            data = data[0] if data else {}

        findings = []
        for f in data.get("findings", []):
            findings.append(Finding(
                finding_id=generate_finding_id(),
                entity=f.get(
                    "entity",
                    target_entities[0]
                    if target_entities
                    else "unknown",
                ),
                field_name=f.get("field_name", ""),
                value=f.get("value", ""),
                confidence=float(f.get("confidence", 0.5)),
                source_url=page_url,
            ))

        useful_links = data.get("useful_links", [])
        page_relevant = data.get(
            "page_relevant", len(findings) > 0
        )

        logger.info(
            "Evaluator: %d findings, %d links, relevant=%s (%s)",
            len(findings),
            len(useful_links),
            page_relevant,
            page_url,
        )
        return findings, useful_links, page_relevant

    except Exception as e:
        logger.warning("Evaluator failed: %s", e)
        return [], [], False
