"""Tests for input loading."""

from pathlib import Path

from app.runner import load_inputs

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_csv():
    inputs = load_inputs(str(FIXTURES / "inputs.csv"))
    assert len(inputs) == 3
    assert inputs[0].program_url == "https://www.mit.edu/education/"
    assert inputs[0].school_name == "MIT"
    assert inputs[0].program_id is not None


def test_load_jsonl():
    inputs = load_inputs(str(FIXTURES / "inputs.jsonl"))
    assert len(inputs) == 2
    assert inputs[1].school_name == "Stanford University"
    assert inputs[1].degree_level == "Master"
