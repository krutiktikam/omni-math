import sympy
from sympy.parsing.latex import parse_latex
import logging

logger = logging.getLogger("omnimath.verification")

class VerificationService:
    def __init__(self):
        pass

    def verify_algebraic_expression(self, formula_latex: str) -> dict:
        """
        Parses a LaTeX formula and performs symbolic verification.
        Returns a dictionary with the results.
        """
        try:
            # Clean up LaTeX string for parsing (basic cleanup)
            clean_latex = formula_latex.replace('$', '').strip()
            
            # Parse LaTeX to SymPy expression
            expr = parse_latex(clean_latex)
            
            # Perform basic operations (simplification, expansion)
            simplified = sympy.simplify(expr)
            expanded = sympy.expand(expr)
            
            return {
                "verified": True,
                "simplified": str(simplified),
                "expanded": str(expanded),
                "is_identity": simplified == 0 or simplified == 1 # Just a basic check
            }
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

verification_service = VerificationService()
