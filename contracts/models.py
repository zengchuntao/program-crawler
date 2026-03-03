"""
Frozen Data Contracts for Program Crawler / Research Agent
==========================================================
These models are the single source of truth for all modules.
DO NOT modify field names or remove fields — only append new optional fields.
All agents import from here to stay aligned.

Legacy models (ProgramInput, FetchPlan, Document, etc.) are preserved.
New agent-oriented models are appended below.
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


# ===========================================================================
# New Agent-Oriented Models (Research Agent architecture)
# ===========================================================================

# ---------------------------------------------------------------------------
# ID generation for new models
# ---------------------------------------------------------------------------

def generate_finding_id() -> str:
    """Globally unique finding ID."""
    return f"FIND-{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# Enums for Agent
# ---------------------------------------------------------------------------

class ActionType(str, Enum):
    SEARCH = "search"
    VISIT = "visit"
    DONE = "done"
    GIVE_UP = "give_up"


class ResearchStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Research Query (user input)
# ---------------------------------------------------------------------------

class ResearchQuery(BaseModel):
    """Natural language research request from user."""
    raw_query: str
    max_steps: int = 20


# ---------------------------------------------------------------------------
# Research Goal (LLM-parsed from query)
# ---------------------------------------------------------------------------

class ResearchGoal(BaseModel):
    """Structured goals parsed from the user's query by the Planner LLM."""
    target_entities: list[str] = Field(
        default_factory=list,
        description="Entities to research, e.g. ['MIT CS Master\\'s', 'Stanford CS Master\\'s']",
    )
    fields_requested: list[str] = Field(
        default_factory=list,
        description="Field names to look for, e.g. ['gpa_requirement', 'language_requirement']",
    )
    search_hints: list[str] = Field(
        default_factory=list,
        description="Suggested search queries to start with",
    )


# ---------------------------------------------------------------------------
# Agent Action (what the agent decides to do next)
# ---------------------------------------------------------------------------

class AgentAction(BaseModel):
    """A single action decided by the Action Picker LLM."""
    action_type: ActionType
    url: Optional[str] = None
    search_query: Optional[str] = None
    reasoning: str = ""


# ---------------------------------------------------------------------------
# Finding (one confirmed piece of information)
# ---------------------------------------------------------------------------

class Finding(BaseModel):
    """One confirmed data finding with evidence."""
    finding_id: str = Field(default_factory=generate_finding_id)
    entity: str
    field_name: str
    value: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_url: str
    evidence_id: Optional[str] = None
    screenshot_file: Optional[str] = None


# ---------------------------------------------------------------------------
# Page Visit (record of visiting a page)
# ---------------------------------------------------------------------------

class PageVisit(BaseModel):
    """Record of a single page visit during research."""
    url: str
    title: Optional[str] = None
    text_snippet: Optional[str] = None
    had_relevant_info: bool = False
    links_extracted: list[str] = Field(default_factory=list)
    visited_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# Agent Memory (working memory across the loop)
# ---------------------------------------------------------------------------

class AgentMemory(BaseModel):
    """Working memory for the research agent loop."""
    query: str
    goals: Optional[ResearchGoal] = None
    pages_visited: list[PageVisit] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    step_count: int = 0
    max_steps: int = 20

    def fields_still_needed(self) -> list[str]:
        """Return field names not yet found across ALL entities.

        A field is considered "done" only if it has been found for
        at least half of the target entities (or at least 1 if
        there is only 1 entity). This prevents the agent from
        stopping after filling fields for just one entity.
        """
        if not self.goals:
            return []
        num_entities = max(len(self.goals.target_entities), 1)
        threshold = max(num_entities // 2, 1)
        needed = []
        for field in self.goals.fields_requested:
            count = sum(
                1 for f in self.findings
                if f.field_name == field
            )
            if count < threshold:
                needed.append(field)
        return needed

    def visited_urls(self) -> set[str]:
        """Return set of all visited URLs."""
        return {p.url for p in self.pages_visited}

    def has_budget(self) -> bool:
        """Check if the agent has steps remaining."""
        return self.step_count < self.max_steps


# ---------------------------------------------------------------------------
# Agent Log Step (for debugging sheet)
# ---------------------------------------------------------------------------

class AgentLogStep(BaseModel):
    """One step in the agent's execution log (for Excel Agent Log sheet)."""
    step: int
    action_type: str
    url_or_query: Optional[str] = None
    reasoning: str = ""
    found_info: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# Research Result (final output)
# ---------------------------------------------------------------------------

class ResearchResult(BaseModel):
    """Complete output of a research agent run."""
    query: str
    goals: Optional[ResearchGoal] = None
    findings: list[Finding] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    evidence_items: list[EvidenceItem] = Field(default_factory=list)
    agent_log: list[AgentLogStep] = Field(default_factory=list)
    status: ResearchStatus = ResearchStatus.COMPLETE
    duration_s: float = 0.0
    total_steps: int = 0
    pages_visited: int = 0
