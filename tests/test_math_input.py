import json
import pathlib

import pytest
import sympy as sp

from math_input import (InputRefused, check_derivative, extract_derivative_target,
                        extract_equation, parse_math, single_variable, solve_equation)

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


def test_extract_equation_keeps_function_names():
    assert extract_equation("Solve sin x = 0") == ("sin x", "0")


def test_solve_linear():
    r = solve_equation("2x + 3", "7")
    assert r["solutions"] == ["2"] and r["substitution_check"] is True


def test_solve_quadratic():
    r = solve_equation("x^2 - 5x + 6", "0")
    assert sorted(r["solutions"]) == ["2", "3"] and r["substitution_check"] is True


def test_trig_equation_refused():
    with pytest.raises(InputRefused):
        solve_equation("sin x", "0")


def test_two_unknowns_refused():
    with pytest.raises(InputRefused):
        solve_equation("x + y", "3")


def test_missing_equals_is_refused():
    # recorded from the CLI: "Differentiate f(x) 3x^2" was answered 9*f*x**2
    with pytest.raises(InputRefused):
        single_variable(parse_math(extract_derivative_target("Differentiate f(x) 3x^2")))


def test_single_variable_is_detected():
    assert single_variable(parse_math("3x^2 + 2x")) == "x"
    assert single_variable(parse_math("3t^2 + t")) == "t"