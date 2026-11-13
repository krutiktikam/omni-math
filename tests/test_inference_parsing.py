import json
import pathlib

import pytest

from inference_errors import InvalidModelOutput, TruncatedOutput
from inference_parsing import parse_math_response

RAW = pathlib.Path("tests/fixtures/raw_generate")


def _response(name: str) -> dict:
    return json.loads((RAW / f"{name}.json").read_text(encoding="utf-8"))["response"]


def test_recorded_good_response_parses():
    out = parse_math_response(_response("A_asis_word_problem"))
    assert out["final_answer"] == "320"
    assert set(out) == {"reasoning_steps", "core_formula", "final_answer"}


def test_truncated_response_is_typed_error():
    r = _response("A_asis_word_problem")
    r["done_reason"] = "length"
    with pytest.raises(TruncatedOutput):
        parse_math_response(r)


def test_missing_key_is_not_defaulted():
    r = {"done_reason": "stop", "response": json.dumps({"reasoning_steps": "x", "core_formula": "y"})}
    with pytest.raises(InvalidModelOutput):
        parse_math_response(r)


def test_non_json_is_invalid():
    with pytest.raises(InvalidModelOutput):
        parse_math_response({"done_reason": "stop", "response": "not json at all"})


def test_empty_answer_is_invalid():
    r = {"done_reason": "stop", "response": json.dumps(
        {"reasoning_steps": "x", "core_formula": "y", "final_answer": "  "})}
    with pytest.raises(InvalidModelOutput):
        parse_math_response(r)