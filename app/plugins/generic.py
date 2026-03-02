"""Default plugin — given a URL, fetch + extract + produce record."""

from __future__ import annotations

import logging
from typing import Optional

from app.evidence.capture import capture_full_page
from app.extractor.llm_extractor import extract_with_llm
from app.extractor.rule_extractors import extract_deadline_dates, extract_ielts_toefl
from app.fetcher.browser_fetcher import fetch_browser
from app.fetcher.http_fetcher import fetch_http
from app.util.helpers import evidence_dir, raw_dir
from app.validate.validator import validate_fields
from contracts.models import (
    CrawlStatus,
    Document,
    EvidenceItem,
    EvidenceRefs,
    ExtractedFields,
    FetchPlan,
    ProgramInput,
    ProgramRecord,
)

logger = logging.getLogger("crawler.plugin.generic")


async def process_program(
    inp: ProgramInput,
    out_base: str,
    mode: str = "browser_only",
    llm_api_key: Optional[str] = None,
    llm_model: str = "gpt-4o-mini",
    llm_base_url: Optional[str] = None,
) -> tuple[ProgramRecord, list[EvidenceItem]]:
    """
    End-to-end processing of a single program:
      1. Fetch page (browser or http)
      2. Save raw HTML + full-page screenshot
      3. Extract fields (LLM + rules)
      4. Build EvidenceItems and ProgramRecord
    Returns (record, evidence_items).
    Never raises — returns status=failed on error.
    """
    pid = inp.program_id or ""
    warnings: list[str] = []
    evidence_items: list[EvidenceItem] = []

    try:
        # --- Fetch ---
        plan = FetchPlan(url=inp.program_url)
        ev_path = evidence_dir(out_base, pid)
        rw_path = raw_dir(out_base, pid)
        screenshot_path = ev_path / "full_page.png"
        raw_html_path = rw_path / "page.html"

        doc: Document
        if mode == "http_first":
            try:
                doc = await fetch_http(plan, pid)
            except Exception:
                logger.info("HTTP failed for %s, falling back to browser", inp.program_url)
                doc = await fetch_browser(plan, pid, screenshot_path, raw_html_path)
        else:
            doc = await fetch_browser(plan, pid, screenshot_path, raw_html_path)

        # --- Evidence: full-page screenshot ---
        fp_evidence = capture_full_page(doc, field="_full_page")
        if fp_evidence:
            evidence_items.append(fp_evidence)

        # --- Extract fields ---
        fields = await extract_with_llm(
            doc, api_key=llm_api_key, model=llm_model, base_url=llm_base_url
        )

        # Rule-based augmentation
        if doc.text:
            if not fields.language_requirement:
                fields.language_requirement = extract_ielts_toefl(doc.text)
            if not fields.deadlines:
                fields.deadlines = extract_deadline_dates(doc.text)

        # --- Validate ---
        warnings = validate_fields(fields)

        # --- Build evidence refs (MVP: all fields share full_page evidence) ---
        shared_ids = [e.evidence_id for e in evidence_items]
        evidence_refs = EvidenceRefs(
            gpa_evidence_ids=shared_ids if fields.gpa_requirement else [],
            language_evidence_ids=shared_ids if fields.language_requirement else [],
            gre_gmat_evidence_ids=shared_ids if fields.gre_gmat_requirement else [],
            prerequisites_evidence_ids=shared_ids if fields.prerequisites else [],
            deadlines_evidence_ids=shared_ids if fields.deadlines else [],
            tuition_evidence_ids=shared_ids if fields.tuition_fees else [],
            materials_evidence_ids=shared_ids if fields.materials else [],
            curriculum_evidence_ids=shared_ids if fields.curriculum_summary else [],
        )

        # --- Per-field evidence items ---
        field_names = [
            "gpa_requirement", "language_requirement", "gre_gmat_requirement",
            "prerequisites", "deadlines", "tuition_fees", "materials", "curriculum_summary",
        ]
        for fname in field_names:
            if getattr(fields, fname):
                for ev in evidence_items:
                    field_ev = ev.model_copy(update={"field": fname})
                    evidence_items.append(field_ev)

        status = CrawlStatus.SUCCESS if not warnings else CrawlStatus.PARTIAL

        record = ProgramRecord(
            program_id=pid,
            school_name=inp.school_name,
            program_name=inp.program_name,
            degree_level=inp.degree_level,
            program_url=inp.program_url,
            final_url=doc.final_url,
            status=status,
            warnings=warnings,
            fields=fields,
            evidence=evidence_refs,
        )
        return record, evidence_items

    except Exception as e:
        logger.error("Failed to process %s: %s", inp.program_url, e)
        record = ProgramRecord(
            program_id=pid,
            program_url=inp.program_url,
            school_name=inp.school_name,
            program_name=inp.program_name,
            status=CrawlStatus.FAILED,
            warnings=[str(e)],
            fields=ExtractedFields(),
            evidence=EvidenceRefs(),
        )
        return record, []
