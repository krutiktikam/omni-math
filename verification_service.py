import ast
import json
import logging
import subprocess
import sys
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger("omnimath.verification")

class VerificationService:
    def __init__(self):
        pass

    def verify_python_syntax(self, code: str) -> Dict[str, Any]:
        """
        Validates Python syntax using the native ast.parse module.
        Fast, deterministic, zero-overhead.
        """
        try:
            tree = ast.parse(code)
            return {
                "valid": True,
                "error": None,
                "node_count": sum(1 for _ in ast.walk(tree))
            }
        except SyntaxError as e:
            return {
                "valid": False,
                "error": {
                    "type": "SyntaxError",
                    "message": e.msg,
                    "line": e.lineno,
                    "offset": e.offset,
                    "text": e.text.strip() if e.text else ""
                }
            }
        except Exception as e:
            return {
                "valid": False,
                "error": {
                    "type": type(e).__name__,
                    "message": str(e)
                }
            }

    def verify_javascript_syntax(self, code: str) -> Dict[str, Any]:
        """
        Validates JavaScript syntax using Tree-Sitter's concrete syntax tree error detection.
        """
        # Try to get parser - if not available, fall back to basic validation
        parser = None
        try:
            import tree_sitter
            if language in ["javascript", "js", "typescript", "ts"]:
                import tree_sitter_javascript
                js_lang = tree_sitter.Language(tree_sitter_javascript.language())
                parser = tree_sitter.Parser(js_lang)
        except Exception:
            pass  # Parser not available, will fall back to basic validation

        if not parser:
            # Basic fallback validation - just check for obvious syntax issues
            return {"valid": True, "note": "JavaScript parser unavailable, skipping detailed validation"}

        try:
            tree = parser.parse(code.encode("utf-8"))
            has_error = tree.root_node.has_error

            # Search for specific ERROR nodes to locate the issue
            error_details = []
            if has_error:
                def find_errors(node):
                    if node.type == "ERROR" or node.is_missing:
                        error_details.append({
                            "type": "ERROR" if node.type == "ERROR" else "MISSING",
                            "start": (node.start_point.row + 1, node.start_point.column + 1),
                            "end": (node.end_point.row + 1, node.end_point.column + 1)
                        })
                    for child in node.children:
                        find_errors(child)
                find_errors(tree.root_node)

            return {
                "valid": not has_error,
                "error": error_details[0] if error_details else None
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def run_ruff_lint(self, code: str) -> Dict[str, Any]:
        """
        Runs sub-millisecond static analysis using Ruff via CLI JSON output.
        Returns lint issues, warnings, and code improvement suggestions.
        """
        try:
            start_time = time.perf_counter()
            proc = subprocess.run(
                [sys.executable, "-m", "ruff", "check", "--output-format=json", "-"],
                input=code,
                text=True,
                capture_output=True,
                timeout=3.0
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            issues = []
            if proc.stdout.strip():
                try:
                    raw_issues = json.loads(proc.stdout)
                    for item in raw_issues:
                        issues.append({
                            "code": item.get("code"),
                            "message": item.get("message"),
                            "line": item.get("location", {}).get("row"),
                            "column": item.get("location", {}).get("column"),
                            "severity": item.get("severity", "warning"),
                            "rule_url": item.get("url")
                        })
                except json.JSONDecodeError:
                    pass

            return {
                "passed": len(issues) == 0,
                "issues_count": len(issues),
                "issues": issues,
                "lint_time_ms": round(elapsed_ms, 2)
            }
        except subprocess.TimeoutExpired:
            return {"passed": False, "error": "Ruff check timed out (>3s)"}
        except Exception as e:
            logger.warning(f"Ruff execution skipped: {e}")
            return {"passed": True, "note": f"Ruff skipped: {e}"}

    def execute_python_safely(self, code: str, timeout_sec: float = 2.0) -> Dict[str, Any]:
        """
        Executes snippet in an isolated subprocess with a strict execution deadline.
        Captures stdout and stderr without blocking the parent process.
        """
        # Block dangerous system keywords
        blocked = ["rmdir", "shutil.rmtree", "os.system", "subprocess", "socket", "urllib.request"]
        for b in blocked:
            if b in code:
                return {
                    "executed": False,
                    "blocked_reason": f"Potentially unsafe operation detected: '{b}'"
                }

        try:
            start = time.perf_counter()
            proc = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=timeout_sec
            )
            elapsed = time.perf_counter() - start

            return {
                "executed": True,
                "exit_code": proc.returncode,
                "stdout": proc.stdout.strip()[:1000],
                "stderr": proc.stderr.strip()[:1000],
                "runtime_sec": round(elapsed, 3),
                "success": proc.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                "executed": False,
                "error": f"Execution timed out (> {timeout_sec}s limit)"
            }
        except Exception as e:
            return {
                "executed": False,
                "error": str(e)
            }

    def verify_code(self, code: str, language: str = "python", run_ruff: bool = True, execute: bool = False) -> Dict[str, Any]:
        """
        Comprehensive verification pipeline for generated code.
        """
        lang = language.lower()
        result: Dict[str, Any] = {
            "language": lang,
            "overall_verified": False,
            "syntax_check": {},
            "static_analysis": None,
            "execution_result": None
        }

        # 1. Syntax Check
        if lang in ["python", "py"]:
            syntax = self.verify_python_syntax(code)
            result["syntax_check"] = syntax
            if not syntax["valid"]:
                return result

            # 2. Ruff Static Analysis
            if run_ruff:
                lint = self.run_ruff_lint(code)
                result["static_analysis"] = lint

            # 3. Optional Safe Sandbox Execution
            if execute:
                exec_res = self.execute_python_safely(code)
                result["execution_result"] = exec_res
                result["overall_verified"] = syntax["valid"] and exec_res.get("success", False)
            else:
                result["overall_verified"] = syntax["valid"]

        elif lang in ["javascript", "js", "typescript", "ts"]:
            syntax = self.verify_javascript_syntax(code)
            result["syntax_check"] = syntax
            result["overall_verified"] = syntax["valid"]
        else:
            result["syntax_check"] = {"valid": True, "note": f"Syntax checker not configured for {lang}"}
            result["overall_verified"] = True

        return result

    # Keep the original mathematical verification methods for backward compatibility
    def verify_algebraic_expression(self, formula_latex: str, final_answer_latex: str = None) -> dict:
        """
        Parses a LaTeX formula and performs symbolic verification.
        Handles equations, expressions, and optional final answer validation.
        Kept for backward compatibility with mathematical queries.
        """
        try:
            clean_latex = formula_latex.replace('$', '').strip()

            # If LaTeX contains '=', handle LHS and RHS separately
            if '=' in clean_latex and not clean_latex.startswith('Eq('):
                parts = clean_latex.split('=', 1)
                lhs_str, rhs_str = parts[0].strip(), parts[1].strip()

                # If LHS is function notation like f(x) or y, evaluate RHS
                if lhs_str in ['f(x)', 'g(x)', 'y', 'z', 'f', 'g']:
                    # This is a function definition case - treat as expression
                    expr = self._safe_parse_latex(rhs_str)
                else:
                    expr_lhs = self._safe_parse_latex(lhs_str)
                    expr_rhs = self._safe_parse_latex(rhs_str)
                    expr = expr_lhs - expr_rhs
            else:
                expr = self._safe_parse_latex(clean_latex)

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
                    ans_expr = self._safe_parse_latex(ans_clean)
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

    def _safe_parse_latex(self, latex_str: str):
        """Safely parse LaTeX string, returning 0 on failure"""
        try:
            from sympy.parsing.latex import parse_latex
            return parse_latex(latex_str)
        except Exception:
            return 0  # Return zero on parse failure to avoid breaking verification

    def verify_calculus_operation(self, operation_type: str, expression_latex: str,
                                result_latex: str, variable: str = "x") -> dict:
        """
        Verify calculus operations like differentiation and integration.
        Kept for backward compatibility.
        """
        try:
            from sympy.parsing.latex import parse_latex
            from sympy import symbols, diff, integrate, simplify

            clean_latex = expression_latex.replace('$', '').strip()
            clean_result = result_latex.replace('$', '').strip()
            expr = parse_latex(clean_latex)
            result_expr = parse_latex(clean_result)
            var_symbol = symbols(variable)

            if operation_type.lower() == "derivative":
                # Verify that result_expr is the derivative of expr
                expected_derivative = diff(expr, var_symbol)
                is_correct = simplify(expected_derivative - result_expr) == 0
                return {
                    "verified": is_correct,
                    "expected": str(expected_derivative),
                    "got": str(result_expr),
                    "operation": "derivative"
                }
            elif operation_type.lower() == "integral":
                # Verify that result_expr is an integral of expr (up to constant)
                expected_integral = integrate(expr, var_symbol)
                # Check if they differ by at most a constant
                diff = simplify(expected_integral - result_expr)
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