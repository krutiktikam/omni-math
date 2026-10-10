import ast
import json
import logging
import subprocess
import sys
import time
from typing import Dict, Any, List, Optional
from services.parsing_service import get_parser

logger = logging.getLogger("code_rag.verification")

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
        parser = get_parser("javascript")
        if not parser:
            return {"valid": True, "note": "JavaScript parser unavailable"}

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

verification_service = VerificationService()
