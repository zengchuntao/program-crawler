"""Utility: ID generation, path helpers, logging."""

import logging
from pathlib import Path

from contracts.models import RunLogEntry


def setup_logging(level: str = "INFO", **kwargs) -> logging.Logger:
    """Delegate to app.log.config.setup_logging (backward-compatible)."""
    from app.log.config import setup_logging as _setup
    return _setup(level=level, **kwargs)


def out_dir(base: str | Path = "out") -> Path:
    """Return the resolved output directory, creating it if needed."""
    p = Path(base).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def evidence_dir(base: str | Path, program_id: str) -> Path:
    p = Path(base) / "evidence" / program_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def raw_dir(base: str | Path, program_id: str) -> Path:
    p = Path(base) / "raw" / program_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def append_run_log(base: str | Path, entry: RunLogEntry) -> None:
    """Append a single RunLogEntry to run_log.jsonl."""
    log_path = Path(base) / "run_log.jsonl"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry.model_dump_json() + "\n")
