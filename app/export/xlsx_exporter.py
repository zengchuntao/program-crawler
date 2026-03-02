"""Excel exporter — writes results.xlsx with Programs and Evidence sheets."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

from contracts.models import EvidenceItem, ProgramRecord


def _load_columns() -> dict:
    """Load column definitions from contracts/columns.yaml."""
    yaml_path = Path(__file__).resolve().parent.parent.parent / "contracts" / "columns.yaml"
    with open(yaml_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class XlsxExporter:
    """Builds an Excel workbook with Programs and Evidence sheets."""

    def __init__(self):
        self._columns = _load_columns()
        self._programs: list[ProgramRecord] = []
        self._evidence: list[EvidenceItem] = []

    def add_program(self, record: ProgramRecord) -> None:
        self._programs.append(record)

    def add_evidence(self, items: list[EvidenceItem]) -> None:
        self._evidence.extend(items)

    def _get_cell_value(self, record: ProgramRecord, key: str) -> str:
        """Resolve a column key to its string value from a ProgramRecord."""
        # Direct top-level fields
        if hasattr(record, key):
            val = getattr(record, key)
        # Fields inside ExtractedFields
        elif hasattr(record.fields, key):
            val = getattr(record.fields, key)
        # Evidence refs
        elif hasattr(record.evidence, key):
            val = getattr(record.evidence, key)
        else:
            return ""

        if val is None:
            return ""
        if isinstance(val, list):
            return ";".join(str(v) for v in val)
        return str(val)

    def save(self, path: str | Path) -> Path:
        """Write the workbook to disk and return the path."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        wb = Workbook()
        cols = self._columns

        # --- Programs sheet ---
        ps = wb.active
        ps.title = cols["programs_sheet"]["name"]
        prog_cols = cols["programs_sheet"]["columns"]

        # Header row
        for i, col_def in enumerate(prog_cols, start=1):
            cell = ps.cell(row=1, column=i, value=col_def["header"])
            cell.font = Font(bold=True)
            ps.column_dimensions[cell.column_letter].width = col_def.get("width", 15)

        # Data rows
        for row_idx, record in enumerate(self._programs, start=2):
            for col_idx, col_def in enumerate(prog_cols, start=1):
                ps.cell(row=row_idx, column=col_idx, value=self._get_cell_value(record, col_def["key"]))

        # --- Evidence sheet ---
        es = wb.create_sheet(title=cols["evidence_sheet"]["name"])
        ev_cols = cols["evidence_sheet"]["columns"]

        for i, col_def in enumerate(ev_cols, start=1):
            cell = es.cell(row=1, column=i, value=col_def["header"])
            cell.font = Font(bold=True)
            es.column_dimensions[cell.column_letter].width = col_def.get("width", 15)

        for row_idx, item in enumerate(self._evidence, start=2):
            for col_idx, col_def in enumerate(ev_cols, start=1):
                key = col_def["key"]
                val = getattr(item, key, "")
                if val is None:
                    val = ""
                if isinstance(val, list):
                    val = ";".join(str(v) for v in val)
                es.cell(row=row_idx, column=col_idx, value=str(val))

        wb.save(str(path))
        return path
