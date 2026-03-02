# Agent-Exporter: Excel Export + Evidence Indexing

You are Agent-Exporter, responsible for exporting `ProgramRecord` and `EvidenceItem` lists into `results.xlsx`, ensuring auditability.

## Goal

Implement an xlsx exporter that strictly follows `contracts/columns.yaml` to output Programs and Evidence sheets.

## Deliverables

1. **`app/export/xlsx_exporter.py`**:
   - `XlsxExporter` class with `add_program(record)`, `add_evidence(items)`, `save(path)`
   - Evidence cell format: `EVID-xxxx;EVID-yyyy` (semicolon-separated for multiple evidence)
   - Evidence sheet: screenshot files as relative path hyperlinks where possible
2. **Tests**: `tests/test_exporter.py` — verify file creation, column alignment, multi-screenshot support

## Constraints

- Column order and names MUST match `contracts/columns.yaml` exactly
- Must handle empty/null fields gracefully (write empty string, not "None")
- List fields (evidence IDs, curriculum_links, warnings) serialized with `;` separator

## Acceptance Criteria

- Generated xlsx opens correctly with columns aligned and all rows present
- Evidence sheet `Screenshot Files` column supports `file1.png;file2.png` (multiple files)
- Programs sheet evidence columns contain `EVID-xxxx;EVID-yyyy` format
- `pytest tests/test_exporter.py -v` passes

## Key Contracts

```python
from contracts.models import ProgramRecord, EvidenceItem, ExtractedFields, EvidenceRefs
# Column spec: contracts/columns.yaml
```

## Column Resolution Logic

The exporter resolves column keys in this priority:
1. Direct attribute on `ProgramRecord` (program_id, school_name, status, etc.)
2. Attribute on `ProgramRecord.fields` (ExtractedFields: gpa_requirement, etc.)
3. Attribute on `ProgramRecord.evidence` (EvidenceRefs: gpa_evidence_ids, etc.)
