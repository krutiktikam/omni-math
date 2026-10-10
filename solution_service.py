import sympy
from sympy.parsing.latex import parse_latex
from sympy import *
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("omnimath.solution")

class SolutionService:
    def __init__(self):
        pass

    def solve_equation_step_by_step(self, equation_latex: str) -> List[Dict[str, Any]]:
        """
        Solve an equation step-by-step with detailed explanations.
        Returns a list of steps with explanations and mathematical expressions.
        """
        try:
            # Clean LaTeX input
            clean_latex = equation_latex.replace('$', '').strip()

            # Parse the equation
            if '=' not in clean_latex:
                raise ValueError("Equation must contain an equals sign")

            lhs_str, rhs_str = clean_latex.split('=', 1)
            lhs_expr = parse_latex(lhs_str.strip())
            rhs_expr = parse_latex(rhs_str.strip())

            # Create equation: lhs - rhs = 0
            equation = lhs_expr - rhs_expr

            steps = []

            # Step 1: Original equation
            steps.append({
                "step_number": 1,
                "explanation": "Start with the given equation",
                "expression_latex": sympy.latex(equation) + " = 0",
                "expression": str(equation)
            })

            # Step 2: Simplify both sides if possible
            simplified_lhs = sympy.simplify(lhs_expr)
            simplified_rhs = sympy.simplify(rhs_expr)

            if simplified_lhs != lhs_expr or simplified_rhs != rhs_expr:
                steps.append({
                    "step_number": len(steps) + 1,
                    "explanation": "Simplify both sides of the equation",
                    "expression_latex": sympy.latex(simplified_lhs) + " = " + sympy.latex(simplified_rhs),
                    "expression": f"{simplified_lhs} = {simplified_rhs}"
                })
                lhs_expr, rhs_expr = simplified_lhs, simplified_rhs
                equation = lhs_expr - rhs_expr

            # Step 3: Move all terms to one side
            if not equation.equals(0):  # Not already simplified to 0
                steps.append({
                    "step_number": len(steps) + 1,
                    "explanation": "Rearrange equation to set one side to zero",
                    "expression_latex": sympy.latex(lhs_expr) + " - (" + sympy.latex(rhs_expr) + ") = 0",
                    "expression": f"({lhs_expr}) - ({rhs_expr}) = 0"
                })
                equation = lhs_expr - rhs_expr

            # Step 4: Factor if polynomial
            if equation.is_polynomial():
                factored = sympy.factor(equation)
                if not factored.equals(equation):
                    steps.append({
                        "step_number": len(steps) + 1,
                        "explanation": "Factor the polynomial",
                        "expression_latex": sympy.latex(factored) + " = 0",
                        "expression": str(factored)
                    })
                    equation = factored

            # Step 5: Solve for variable
            # Find the variable(s) in the equation
            variables = equation.free_symbols
            if variables:
                # Solve for the first variable (typically x)
                var = list(variables)[0] if len(variables) == 1 else symbols('x')
                solutions = sympy.solve(equation, var)

                if solutions:
                    steps.append({
                        "step_number": len(steps) + 1,
                        "explanation": f"Solve for {sympy.latex(var)}",
                        "expression_latex": sympy.latex(var) + " = " + sympy.latex(solutions[0]) if len(solutions) == 1 else
                                        sympy.latex(var) + " = " + ", ".join([sympy.latex(sol) for sol in solutions]),
                        "expression": str(solutions[0]) if len(solutions) == 1 else str(solutions)
                    })

                    # Step 6: Verify solution
                    steps.append({
                        "step_number": len(steps) + 1,
                        "explanation": "Verify the solution by substitution",
                        "expression_latex": sympy.latex(lhs_expr.subs(var, solutions[0])) + " = " +
                                        sympy.latex(rhs_expr.subs(var, solutions[0])),
                        "expression": f"{lhs_expr.subs(var, solutions[0])} = {rhs_expr.subs(var, solutions[0])}"
                    })

                    # Check if LHS equals RHS after substitution
                    lhs_sub = lhs_expr.subs(var, solutions[0])
                    rhs_sub = rhs_expr.subs(var, solutions[0])
                    if sympy.simplify(lhs_sub - rhs_sub) == 0:
                        steps[-1]["explanation"] = "Verify the solution by substitution - SOLUTION VERIFIED"
                    else:
                        steps[-1]["explanation"] = "Verify the solution by substitution - SOLUTION NEEDS CHECKING"

            return steps

        except Exception as e:
            logger.warning(f"Step-by-step equation solving failed: {e}")
            return [{
                "step_number": 1,
                "explanation": f"Unable to generate step-by-step solution: {str(e)}",
                "expression_latex": "",
                "expression": ""
            }]

    def differentiate_step_by_step(self, expression_latex: str, variable: str = "x") -> List[Dict[str, Any]]:
        """
        Differentiate an expression step-by-step with detailed explanations.
        """
        try:
            clean_latex = expression_latex.replace('$', '').strip()
            expr = parse_latex(clean_latex)
            var_symbol = symbols(variable)

            steps = []

            # Step 1: Original expression
            steps.append({
                "step_number": 1,
                "explanation": "Start with the given function",
                "expression_latex": "f(" + sympy.latex(var_symbol) + ") = " + sympy.latex(expr),
                "expression": str(expr)
            })

            # Step 2: Apply differentiation rules
            # For simplicity, we'll show the derivative directly but explain common rules
            derivative = sympy.diff(expr, var_symbol)

            steps.append({
                "step_number": 2,
                "explanation": "Apply differentiation rules",
                "expression_latex": "f'(" + sympy.latex(var_symbol) + ") = " + sympy.latex(derivative),
                "expression": str(derivative)
            })

            # Step 3: Simplify if possible
            simplified_derivative = sympy.simplify(derivative)
            if not simplified_derivative.equals(derivative):
                steps.append({
                    "step_number": 3,
                    "explanation": "Simplify the derivative",
                    "expression_latex": "f'(" + sympy.latex(var_symbol) + ") = " + sympy.latex(simplified_derivative),
                    "expression": str(simplified_derivative)
                })
                derivative = simplified_derivative

            return steps

        except Exception as e:
            logger.warning(f"Step-by-step differentiation failed: {e}")
            return [{
                "step_number": 1,
                "explanation": f"Unable to generate step-by-step differentiation: {str(e)}",
                "expression_latex": "",
                "expression": ""
            }]

    def integrate_step_by_step(self, expression_latex: str, variable: str = "x") -> List[Dict[str, Any]]:
        """
        Integrate an expression step-by-step with detailed explanations.
        """
        try:
            clean_latex = expression_latex.replace('$', '').strip()
            expr = parse_latex(clean_latex)
            var_symbol = symbols(variable)

            steps = []

            # Step 1: Original expression
            steps.append({
                "step_number": 1,
                "explanation": "Start with the given function to integrate",
                "expression_latex": "∫ " + sympy.latex(expr) + " d" + sympy.latex(var_symbol),
                "expression": str(expr)
            })

            # Step 2: Apply integration
            integral = sympy.integrate(expr, var_symbol)

            steps.append({
                "step_number": 2,
                "explanation": "Apply integration rules",
                "expression_latex": "∫ " + sympy.latex(expr) + " d" + sympy.latex(var_symbol) + " = " +
                                sympy.latex(integral) + " + C",
                "expression": str(integral) + " + C"
            })

            # Step 3: Simplify if possible
            simplified_integral = sympy.simplify(integral)
            if not simplified_integral.equals(integral):
                steps.append({
                    "step_number": 3,
                    "explanation": "Simplify the result",
                    "expression_latex": "∫ " + sympy.latex(expr) + " d" + sympy.latex(var_symbol) + " = " +
                                    sympy.latex(simplified_integral) + " + C",
                    "expression": str(simplified_integral) + " + C"
                })

            return steps

        except Exception as e:
            logger.warning(f"Step-by-step integration failed: {e}")
            return [{
                "step_number": 1,
                "explanation": f"Unable to generate step-by-step integration: {str(e)}",
                "expression_latex": "",
                "expression": ""
            }]

    def evaluate_limit_step_by_step(self, expression_latex: str, variable: str = "x",
                                  approach_to: str = "0", direction: str = None) -> List[Dict[str, Any]]:
        """
        Evaluate a limit step-by-step with detailed explanations.
        """
        try:
            clean_latex = expression_latex.replace('$', '').strip()
            expr = parse_latex(clean_latex)
            var_symbol = symbols(variable)
            approach_value = sympy.sympify(approach_to)

            steps = []

            # Step 1: Original limit expression
            if direction == "+":
                limit_notation = "lim_{" + sympy.latex(var_symbol) + "→" + sympy.latex(approach_value) + "^+} "
            elif direction == "-":
                limit_notation = "lim_{" + sympy.latex(var_symbol) + "→" + sympy.latex(approach_value) + ^-} "
            else:
                limit_notation = "lim_{" + sympy.latex(var_symbol) + "→" + sympy.latex(approach_value) + "} "

            steps.append({
                "step_number": 1,
                "explanation": "Start with the given limit expression",
                "expression_latex": limit_notation + sympy.latex(expr),
                "expression": str(expr)
            })

            # Step 2: Try direct substitution
            try:
                substituted = expr.subs(var_symbol, approach_value)
                if not substituted.has(oo, -oo, nan):  # Not infinite or undefined
                    steps.append({
                        "step_number": 2,
                        "explanation": "Evaluate by direct substitution",
                        "expression_latex": limit_notation + sympy.latex(expr) + " = " +
                                        sympy.latex(substituted),
                        "expression": str(substituted)
                    })
                    return steps
            except Exception:
                pass  # Direct substitution failed, continue to other methods

            # Step 3: Apply limit rules
            limit_value = sympy.limit(expr, var_symbol, approach_value, direction)

            steps.append({
                "step_number": 2,
                "explanation": "Apply limit evaluation rules",
                "expression_latex": limit_notation + sympy.latex(expr) + " = " +
                                sympy.latex(limit_value),
                "expression": str(limit_value)
            })

            return steps

        except Exception as e:
            logger.warning(f"Step-by-step limit evaluation failed: {e}")
            return [{
                "step_number": 1,
                "explanation": f"Unable to generate step-by-step limit evaluation: {str(e)}",
                "expression_latex": "",
                "expression": ""
            }]

solution_service = SolutionService()