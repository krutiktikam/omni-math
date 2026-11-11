"""Guarded math input parsing.

Why: main.py fed whole English prompts to parse_latex, which reads each letter
as a variable. Every input is checked against a whitelist BEFORE a parser sees it.
Refusing a valid input is cheap; verifying a misparsed one is not.
"""
import re

import sympy as sp
from sympy.core.function import AppliedUndef
from sympy.parsing.sympy_parser import (convert_xor, implicit_multiplication_application,
                                        parse_expr, standard_transformations)

MAX_LEN = 200
ALLOWED_WORDS = {"sin", "cos", "tan", "exp", "sqrt", "ln", "abs", "pi", "e"}  # "log" refused: base is ambiguous
LOCALS = {"ln": sp.log, "abs": sp.Abs, "e": sp.E, "pi": sp.pi}
TRANSFORMS = standard_transformations + (implicit_multiplication_application, convert_xor)


class InputRefused(ValueError):
    """The text is not a clean math expression; do not guess."""


def guard_text(text: str) -> str:
    s = text.strip()
    if not s or len(s) > MAX_LEN:
        raise InputRefused("empty or too long")
    if not re.fullmatch(r"[0-9A-Za-z+\-*/^().\s\\{}]*", s):
        raise InputRefused("unexpected characters")
    for run in re.findall(r"[A-Za-z]+", re.sub(r"\\[A-Za-z]+", " ", s)):
        if run != run.lower():
            raise InputRefused(f"uppercase letters are reserved: {run!r}")
        if len(run) > 1 and run not in ALLOWED_WORDS:
            raise InputRefused(f"word in expression: {run!r}")
    return s


def parse_math(text: str) -> sp.Expr:
    s = guard_text(text)
    try:
        if "\\" in s or "{" in s:
            from sympy.parsing.latex import parse_latex
            expr = parse_latex(s)
        else:
            expr = parse_expr(s, local_dict=LOCALS, transformations=TRANSFORMS)
    except Exception as exc:
        raise InputRefused(f"parse failed: {exc}") from exc
    if expr.atoms(AppliedUndef):
        raise InputRefused("undefined function in expression (a missing '='?)")
    return expr


def single_variable(expr: sp.Expr) -> str:
    syms = sorted(str(s) for s in expr.free_symbols)
    if len(syms) > 1:
        raise InputRefused(f"more than one variable {syms}; refusing to guess which to differentiate")
    return syms[0] if syms else "x"


def extract_derivative_target(prompt: str) -> str:
    p = prompt.strip().rstrip("?.! ")
    if "=" in p:
        return p.split("=", 1)[1].strip()
    m = re.search(r"(?:derivative of|differentiate)\s+(.+)$", p, re.IGNORECASE)
    if not m:
        raise InputRefused("no expression after 'derivative of' / 'differentiate'")
    return m.group(1).strip()


LEAD_VERBS = re.compile(r"^\s*(?:please\s+)?(?:solve|find|calculate|compute)\s+(?:the\s+equation\s+)?", re.IGNORECASE)


def extract_equation(prompt: str) -> tuple[str, str]:
    left, sep, right = prompt.strip().rstrip("?.! ").partition("=")
    if not sep or "=" in right:
        raise InputRefused("need exactly one '='")
    return LEAD_VERBS.sub("", left).strip(), right.strip()


def solve_equation(lhs_text: str, rhs_text: str) -> dict:
    """Polynomial equations in one unknown only: complete root sets, checked by substitution."""
    lhs, rhs = parse_math(lhs_text), parse_math(rhs_text)
    diff_expr = sp.expand(lhs - rhs)
    syms = diff_expr.free_symbols
    if len(syms) != 1:
        raise InputRefused("need exactly one unknown after simplification")
    v = next(iter(syms))
    if not diff_expr.is_polynomial(v):
        raise InputRefused("only polynomial equations are supported (other solution sets can be infinite)")
    solutions = sp.solve(diff_expr, v)
    checked = bool(solutions) and all(sp.simplify(diff_expr.subs(v, s)) == 0 for s in solutions)
    return {"variable": str(v), "solutions": [str(s) for s in solutions], "substitution_check": checked}


def check_derivative(expr_text: str, answer_text: str, var: str = "x") -> dict:
    """Tri-state: verified / refuted / unverified. Used on LLM answers from Day 4."""
    v = sp.Symbol(var)
    try:
        diff_expr = sp.diff(parse_math(expr_text), v) - parse_math(answer_text)
    except InputRefused as exc:
        return {"status": "unverified", "reason": str(exc)}
    if sp.simplify(diff_expr) == 0:
        return {"status": "verified", "method": "symbolic"}
    for val in (0.7, 1.3, 2.9):
        try:
            d = complex(diff_expr.subs(v, val).evalf())
        except (TypeError, ValueError):
            continue
        if abs(d) > 1e-6:
            return {"status": "refuted", "method": "numeric", "at": val}
    return {"status": "unverified", "reason": "could not decide"}
