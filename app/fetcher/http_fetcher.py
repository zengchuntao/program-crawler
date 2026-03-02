"""HTTP fetcher — lightweight requests via httpx."""

from __future__ import annotations

import httpx

from contracts.models import Document, FetchMode, FetchPlan


async def fetch_http(plan: FetchPlan, program_id: str) -> Document:
    """
    Fetch a URL via plain HTTP (no JS rendering).
    Returns a Document with html/text populated.
    """
    async with httpx.AsyncClient(follow_redirects=True, timeout=plan.timeout_ms / 1000) as client:
        resp = await client.get(plan.url)
        resp.raise_for_status()
        return Document(
            program_id=program_id,
            source_url=plan.url,
            final_url=str(resp.url),
            fetch_mode=FetchMode.HTTP,
            html=resp.text,
            text=resp.text,  # TODO: strip tags for plain text
        )
