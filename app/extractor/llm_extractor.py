"""LLM-based field extractor — calls OpenAI-compatible API."""

from __future__ import annotations

import json
import logging
from typing import Optional

from contracts.models import Document, ExtractedFields

logger = logging.getLogger("crawler.extractor.llm")

SYSTEM_PROMPT = """\
You are a structured data extractor for graduate/undergraduate program pages.
Given the page text, extract the following fields as JSON. Return ONLY valid JSON.
If a field is not found, set it to null. Do not invent data.

Fields:
- gpa_requirement: string or null
- language_requirement: string or null (IELTS, TOEFL, DET scores)
- gre_gmat_requirement: string or null
- prerequisites: string or null
- deadlines: string or null
- tuition_fees: string or null
- materials: string or null (application materials required)
- curriculum_summary: string or null (brief summary of curriculum)
- curriculum_links: list of URLs or empty list
"""


async def extract_with_llm(
    document: Document,
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini",
    base_url: Optional[str] = None,
) -> ExtractedFields:
    """
    Send page text to LLM and parse structured response into ExtractedFields.
    Falls back to empty fields on any error (never raises).
    """
    import openai

    text = document.text or ""
    if len(text) > 15000:
        text = text[:15000]  # Truncate to control token usage

    try:
        client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Page URL: {document.final_url}\n\n{text}"},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        return ExtractedFields(**data)
    except Exception as e:
        logger.warning("LLM extraction failed: %s", e)
        return ExtractedFields()
