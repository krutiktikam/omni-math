import sympy
from sympy.parsing.latex import parse_latex
from sympy import *
import logging

logger = logging.getLogger("omnimath.verification")

class VerificationService:
    def __init__(self):
        pass

    def verify_algebraic_expression(self, formula_latex: str, final_answer_latex: str = None) -> dict:
        """
        Parses a LaTeX formula and performs symbolic verification.
        Handles equations, expressions, and optional final answer validation.
        """
        try:
            clean_latex = formula_latex.replace('$', '').strip()

            # If LaTeX contains '=', handle LHS and RHS separately
            if '=' in clean_latex and not clean_latex.startswith('Eq('):
                parts = clean_latex.split('=', 1)
                lhs_str, rhs_str = parts[0].strip(), parts[1].strip()

                # If LHS is function notation like f(x) or y, evaluate RHS
                if lhs_str in ['f(x)', 'g(x)', 'y', 'z', 'f', 'g']:
                    expr = parse_latex(rhs_str)
                else:
                    expr_lhs = parse_latex(lhs_str)
                    expr_rhs = parse_latex(rhs_str)
                    expr = expr_lhs - expr_rhs
            else:
                expr = parse_latex(clean_latex)

            simplified = sympy.simplify(expr)
            expanded = sympy.expand(expr)

            x = sympy.Symbol('x')
            derivative_wrt_x = sympy.diff(expr, x) if expr.has(x) else None

            # Extended verification for calculus operations
            integral_wrt_x = None
            if expr.has(x):
                try:
                    integral_wrt_x = sympy.integrate(expr, x)
                except Exception:
                    integral_wrt_x = None

            answer_verified = None
            if final_answer_latex:
                try:
                    ans_clean = final_answer_latex.replace('$', '').strip()
                    ans_expr = parse_latex(ans_clean)
                    # Check if final answer matches expression or its derivative
                    is_exact_match = sympy.simplify(expr - ans_expr) == 0
                    is_deriv_match = derivative_wrt_x is not None and sympy.simplify(derivative_wrt_x - ans_expr) == 0
                    answer_verified = is_exact_match or is_deriv_match
                except Exception:
                    answer_verified = False

            result = {
                "verified": True,
                "simplified": str(simplified),
                "expanded": str(expanded),
                "derivative_wrt_x": str(derivative_wrt_x) if derivative_wrt_x is not None else "N/A",
                "answer_verified": answer_verified
            }

            # Add integral information if available
            if integral_wrt_x is not None:
                result["integral_wrt_x"] = str(integral_wrt_x)

            return result
        except Exception as e:
            logger.warning(f"SymPy verification failed for formula '{formula_latex}': {e}")
            return {
                "verified": False,
                "error": str(e)
            }

    def check_equality(self, formula_left_latex: str, formula_right_latex: str) -> bool:
        """
        Checks if two LaTeX expressions are mathematically equivalent.
        """
        try:
            expr1 = parse_latex(formula_left_latex.replace('$', '').strip())
            expr2 = parse_latex(formula_right_latex.replace('$', '').strip())
            return sympy.simplify(expr1 - expr2) == 0
        except Exception as e:
            logger.error(f"Equality check failed: {e}")
            return False

    def verify_calculus_operation(self, operation_type: str, expression_latex: str,
                                result_latex: str, variable: str = "x") -> dict:
        """
        Verify calculus operations like differentiation and integration.
        """
        try:
            clean_latex = expression_latex.replace('$', '').strip()
            clean_result = result_latex.replace('$', '').strip()
            expr = parse_latex(clean_latex)
            result_expr = parse_latex(clean_result)
            var_symbol = symbols(variable)

            if operation_type.lower() == "derivative":
                # Verify that result_expr is the derivative of expr
                expected_derivative = sympy.diff(expr, var_symbol)
                is_correct = sympy.simplify(expected_derivative - result_expr) == 0
                return {
                    "verified": is_correct,
                    "expected": str(expected_derivative),
                    "got": str(result_expr),
                    "operation": "derivative"
                }
            elif operation_type.lower() == "integral":
                # Verify that result_expr is an integral of expr (up to constant)
                expected_integral = sympy.integrate(expr, var_symbol)
                # Check if they differ by at most a constant
                diff = sympy.simplify(expected_integral - result_expr)
                is_constant = diff.free_symbols == set()  # No variables means it's constant
                is_correct = is_constant
                return {
                    "verified": is_correct,
                    "expected": str(expected_integral) + " + C",
                    "got": str(result_expr),
                    "operation": "integral"
                }
            else:
                return {
                    "verified": False,
                    "error": f"Unsupported operation type: {operation_type}"
                }
        except Exception as e:
            logger.warning(f"Calculus verification failed: {e}")
            return {
                "verified": False,
                "error": str(e)
            }

verification_service = VerificationService()
