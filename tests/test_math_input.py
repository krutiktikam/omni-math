import json
import pathlib

import pytest
import sympy as sp

from math_input import (InputRefused, check_derivative, extract_derivative_target,
                        extract_equation, parse_math)

FIXTURE = pathlib.Path("tests/fixtures/app/math_derivative.json")
PROMPT = json.loads(FIXTURE.read_text(encoding="utf-8"))["request"]["prompt"]
x = sp.Symbol("x")


def test_recorded_prompt_extracts_clean_expression():
    assert extract_derivative_target(PROMPT) == "3x^2 + 2x"


def test_english_word_is_refused():
    with pytest.raises(InputRefused):
        parse_math("Differentiate f(x) 3x^2 + 2x")


def test_derivative_value():
    assert sp.simplify(sp.diff(parse_math("3x^2 + 2x"), x) - parse_math("6x + 2")) == 0


def test_equation_extraction():
    assert extract_equation("Solve 2x + 3 = 7") == ("2x + 3", "7")


def test_check_derivative_three_states():
    assert check_derivative("3x^2 + 2x", "6x + 2")["status"] == "verified"
    assert check_derivative("3x^2 + 2x", "6x + 1")["status"] == "refuted"
    assert check_derivative("Differentiate f(x) 3x^2", "6x")["status"] == "unverified"