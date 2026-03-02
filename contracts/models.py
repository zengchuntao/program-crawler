"""
Frozen Data Contracts for Program Crawler
==========================================
These models are the single source of truth for all modules.
DO NOT modify field names or remove fields — only append new optional fields.
All agents import from here to stay aligned.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class FetchMode(str, Enum):
    HTTP = "http"
    BROWSER = "browser"
    PDF = "pdf"


class CrawlStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class ScreenshotType(str, Enum):
    FULL_PAGE = "full_page"
    CROPPED = "cropped"
    PDF_PAGE = "pdf_page"


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------

def generate_program_id(url: str) -> str:
    """Stable program ID derived from URL hash (first 12 hex chars)."""
    return hashlib.sha256(url.encode()).hexdigest()[:12]


def generate_evidence_id() -> str:
    """Globally unique evidence ID."""
    return f"EVID-{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

class ProgramInput(BaseModel):
    """One row of the input CSV/JSONL."""
    program_id: Optional[str] = None
    school_name: Optional[str] = None
    program_name: Optional[str] = None
    program_url: str
    degree_level: Optional[str] = None

    def model_post_init(self, __context) -> None:
        if not self.program_id:
            self.program_id = generate_program_id(self.program_url)


# ---------------------------------------------------------------------------
# Fetch Plan
# ---------------------------------------------------------------------------

class FetchPlan(BaseModel):
    """How to fetch a given URL."""
    url: str
    mode: FetchMode = FetchMode.BROWSER
    wait_until: str = "networkidle"  # domcontentloaded | networkidle | load
    timeout_ms: int = 30000
    extra_actions: list[dict] = Field(default_factory=list)  # click/scroll steps


# ---------------------------------------------------------------------------
# Document (post-fetch)
# ---------------------------------------------------------------------------

class Document(BaseModel):
    """Unified representation of a fetched page."""
    program_id: str
    source_url: str
    final_url: str
    fetch_mode: FetchMode
    html: Optional[str] = None
    text: Optional[str] = None
    raw_path: Optional[str] = None          # path to saved raw HTML
    screenshot_path: Optional[str] = None   # path to full-page screenshot
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Evidence Item
# ---------------------------------------------------------------------------

class EvidenceItem(BaseModel):
    """One piece of evidence (may contain multiple screenshots)."""
    evidence_id: str = Field(default_factory=generate_evidence_id)
    program_id: str
    field: str                             # e.g. "language_requirement"
    source_url: str
    captured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    screenshot_files: list[str] = Field(default_factory=list)   # relative paths
    screenshot_type: ScreenshotType = ScreenshotType.FULL_PAGE
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Extracted Fields (the actual data we care about)
# ---------------------------------------------------------------------------

class ExtractedFields(BaseModel):
    """MVP field values extracted from a program page."""
    gpa_requirement: Optional[str] = None
    language_requirement: Optional[str] = None
    gre_gmat_requirement: Optional[str] = None
    prerequisites: Optional[str] = None
    deadlines: Optional[str] = None
    tuition_fees: Optional[str] = None
    materials: Optional[str] = None
    curriculum_summary: Optional[str] = None
    curriculum_links: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Evidence References (parallel to ExtractedFields)
# ---------------------------------------------------------------------------

class EvidenceRefs(BaseModel):
    """Maps each field to its supporting evidence IDs."""
    gpa_evidence_ids: list[str] = Field(default_factory=list)
    language_evidence_ids: list[str] = Field(default_factory=list)
    gre_gmat_evidence_ids: list[str] = Field(default_factory=list)
    prerequisites_evidence_ids: list[str] = Field(default_factory=list)
    deadlines_evidence_ids: list[str] = Field(default_factory=list)
    tuition_evidence_ids: list[str] = Field(default_factory=list)
    materials_evidence_ids: list[str] = Field(default_factory=list)
    curriculum_evidence_ids: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Program Record (one row in output)
# ---------------------------------------------------------------------------

class ProgramRecord(BaseModel):
    """Final structured result for one program — goes into Programs sheet."""
    program_id: str
    school_name: Optional[str] = None
    program_name: Optional[str] = None
    degree_level: Optional[str] = None
    program_url: str
    final_url: Optional[str] = None
    captured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: CrawlStatus = CrawlStatus.SUCCESS
    warnings: list[str] = Field(default_factory=list)

    # Extracted field values
    fields: ExtractedFields = Field(default_factory=ExtractedFields)

    # Evidence references
    evidence: EvidenceRefs = Field(default_factory=EvidenceRefs)


# ---------------------------------------------------------------------------
# Run Log Entry
# ---------------------------------------------------------------------------

class RunLogEntry(BaseModel):
    """One line in run_log.jsonl."""
    program_id: str
    program_url: str
    status: CrawlStatus
    started_at: datetime
    finished_at: datetime
    duration_s: float
    warnings: list[str] = Field(default_factory=list)
    error: Optional[str] = None
