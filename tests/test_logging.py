"""Tests for setup_logging and RunTracker."""

import json
import logging
import tempfile
from pathlib import Path

import pytest

from app.log.config import setup_logging
from app.log.run_tracker import RunTracker


# ------------------------------------------------------------------
# setup_logging
# ------------------------------------------------------------------

class TestSetupLogging:
    def setup_method(self):
        """Remove all handlers from 'crawler' logger before each test."""
        logger = logging.getLogger("crawler")
        logger.handlers.clear()

    def test_returns_logger(self):
        logger = setup_logging()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "crawler"

    def test_console_handler_added(self):
        logger = setup_logging()
        stream_handlers = [
            h for h in logger.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]
        assert len(stream_handlers) == 1

    def test_console_handler_not_duplicated(self):
        setup_logging()
        setup_logging()
        logger = logging.getLogger("crawler")
        stream_handlers = [
            h for h in logger.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]
        assert len(stream_handlers) == 1

    def test_file_handler_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logging(log_dir=tmpdir)
            file_handlers = [
                h for h in logger.handlers
                if isinstance(h, logging.FileHandler)
            ]
            assert len(file_handlers) == 1
            assert hasattr(logger, "run_dir")
            assert Path(logger.run_dir).exists()  # type: ignore[attr-defined]

    def test_run_log_file_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logging(log_dir=tmpdir)
            run_dir = Path(logger.run_dir)  # type: ignore[attr-defined]
            logger.info("test message")
            # Flush handlers
            for h in logger.handlers:
                h.flush()
            assert (run_dir / "run.log").exists()

    def test_debug_level_set_on_logger(self):
        logger = setup_logging()
        assert logger.level == logging.DEBUG


# ------------------------------------------------------------------
# RunTracker
# ------------------------------------------------------------------

class TestRunTracker:
    def test_record_llm_call(self):
        tracker = RunTracker()
        tracker.record_llm_call(
            caller="planner",
            model="test-model",
            duration_s=1.5,
            prompt_preview="hello",
            response_preview="world",
        )
        assert len(tracker.llm_calls) == 1
        assert tracker.llm_calls[0].caller == "planner"
        assert tracker.llm_calls[0].duration_s == 1.5

    def test_record_step(self):
        tracker = RunTracker()
        tracker.record_step(
            step=1,
            action="SEARCH",
            url_or_query="test query",
            duration_s=2.0,
            findings_added=3,
        )
        assert len(tracker.steps) == 1
        assert tracker.steps[0].findings_added == 3

    def test_record_error(self):
        tracker = RunTracker()
        tracker.record_error(step=2, error=ValueError("oops"))
        assert len(tracker.errors) == 1
        assert tracker.errors[0].error_type == "ValueError"
        assert "oops" in tracker.errors[0].message

    def test_finalize_writes_files(self):
        tracker = RunTracker()
        tracker.query = "test query"
        tracker.model = "test-model"
        tracker.max_steps = 10

        tracker.record_llm_call("planner", "test-model", 1.0)
        tracker.record_step(1, "SEARCH", "q", 2.0, findings_added=1)
        tracker.record_error(2, error=RuntimeError("fail"))

        with tempfile.TemporaryDirectory() as tmpdir:
            tracker.finalize(tmpdir)

            # Check JSON
            json_path = Path(tmpdir) / "run_record.json"
            assert json_path.exists()
            data = json.loads(json_path.read_text())
            assert data["query"] == "test query"
            assert data["llm_calls_count"] == 1
            assert data["steps_count"] == 1
            assert data["errors_count"] == 1
            assert len(data["llm_calls"]) == 1
            assert len(data["steps"]) == 1
            assert len(data["errors"]) == 1

            # Check summary
            summary_path = Path(tmpdir) / "run_summary.txt"
            assert summary_path.exists()
            text = summary_path.read_text()
            assert "test query" in text
            assert "planner" in text
            assert "SEARCH" in text
            assert "RuntimeError" in text

    def test_prompt_preview_truncated(self):
        tracker = RunTracker()
        long_prompt = "x" * 500
        tracker.record_llm_call("test", "m", 0.1, prompt_preview=long_prompt)
        assert len(tracker.llm_calls[0].prompt_preview) == 200
