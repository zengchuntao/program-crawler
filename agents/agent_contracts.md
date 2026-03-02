# Agent-Contracts: Data Contracts + Excel Column Specification

You are Agent-Contracts, responsible for defining the project's single source of truth data contracts.

## Goal

Freeze `ProgramInput / FetchPlan / Document / EvidenceItem / ProgramRecord` and define Excel column names and ordering.

## Deliverables

1. **`contracts/models.py`** (Pydantic v2): All data models with validation
2. **`contracts/columns.yaml`**: Programs sheet and Evidence sheet column definitions (including evidence columns with EvidenceID lists)
3. **`tests/test_contracts.py`**: Serialization/deserialization + required field validation tests

## Requirements

- `EvidenceItem` MUST support `screenshot_files: list[str]` (multiple screenshots per evidence)
- `ProgramRecord` MUST have `*_evidence_ids: list[str]` for each extracted field
- `program_id` generation: `sha256(url)[:12]` — stable and deterministic
- All datetime fields use timezone-aware `datetime.now(UTC)`

## Acceptance Criteria

- Other modules only need `from contracts.models import ...` to align on data structures and column names
- All tests pass: `pytest tests/test_contracts.py -v`
- JSON serialization roundtrip works for all models

## Status: COMPLETE (frozen)

The contracts have been implemented and tested (33 tests passing). Do not modify existing fields.
