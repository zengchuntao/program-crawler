"""Logging configuration: console (INFO, concise) + file (DEBUG, full)."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path


def setup_logging(
    level: str = "INFO",
    log_dir: str | Path | None = None,
) -> logging.Logger:
    """Configure the 'crawler' logger with console + optional file handler.

    Args:
        level: Console log level (default INFO).
        log_dir: If provided, creates a timestamped subfolder with a
                 DEBUG-level ``run.log`` file. Returns the run folder path
                 via ``logger.run_dir`` attribute.

    Returns:
        The configured ``crawler`` logger.
    """
    logger = logging.getLogger("crawler")
    logger.setLevel(logging.DEBUG)

    # Console handler (INFO, concise) — add only once
    if not any(
        isinstance(h, logging.StreamHandler)
        and not isinstance(h, logging.FileHandler)
        for h in logger.handlers
    ):
        console = logging.StreamHandler()
        console.setLevel(getattr(logging, level.upper(), logging.INFO))
        console.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        ))
        logger.addHandler(console)

    # File handler (DEBUG, full) — one per run
    if log_dir is not None:
        run_dir = Path(log_dir) / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_dir.mkdir(parents=True, exist_ok=True)

        log_file = run_dir / "run.log"
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(fh)

        # Attach run_dir so callers can find it
        logger.run_dir = run_dir  # type: ignore[attr-defined]

    return logger
