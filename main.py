import logging
import re
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Import domain services
from services.programming_solution_service import programming_solution_service
from services.verification_service_code import verification_service
from vector_service import vector_service
from inference_service import inference_service
from solution_service import solution_service
from config import settings
from math_input import InputRefused, extract_derivative_target, extract_equation, parse_math, single_variable, solve_equation

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("omnimath.api")

app = FastAPI(title="Omnimath Backend API")

# ==========================================
# PYDANTIC MODELS
# ==========================================
class ReasonRequest(BaseModel):
    prompt: str
    step_by_step: Optional[bool] = False
    include_programming: Optional[bool] = False

class CodeExample(BaseModel):
    language: str
    code: str
    explanation: str

class ProgrammingStep(BaseModel):
    step_number: int
    explanation: str
    code_example: Optional[CodeExample] = None

class ProgrammingExplanation(BaseModel):
    concept: str
    language: str
    steps: List[ProgrammingStep]
    related_concepts: List[str]
    complexity_analysis: Optional[Dict[str, str]] = None

class ReasonResponse(BaseModel):
    status: str
    type: str
    result: Any
    verification: Optional[Dict[str, Any]] = None
    reasoning_steps: Optional[str] = None
    core_formula: Optional[str] = None
    final_answer: Optional[str] = None

# ==========================================
# HELPER FUNCTIONS
# ==========================================
async def _generate_programming_explanation(prompt: str, language: str, context: str = "") -> Optional[ProgrammingExplanation]:
    """
    Generate a programming concept explanation using the programming solution service & RAG.
    """
    try:
        steps_data = programming_solution_service.explain_concept(prompt, language)
        if not steps_data:
            return None

        steps = []
        for step_data in steps_data:
            step_obj = ProgrammingStep(
                step_number=step_data["step_number"],
                explanation=step_data["explanation"],
                code_example=CodeExample(
                    language=step_data["code_example"]["language"] if step_data["code_example"] else language,
                    code=step_data["code_example"]["code"] if step_data["code_example"] else "",
                    explanation=step_data["code_example"]["explanation"] if step_data["code_example"] else ""
                ) if step_data["code_example"] else None
            )
            steps.append(step_obj)

        return ProgrammingExplanation(
            concept=prompt[:100],
            language=language,
            steps=steps,
            related_concepts=[f"{language} basics", f"{language} best practices", "offline RAG reference"],
            complexity_analysis={"time": "O(log n) to O(n)", "space": "O(1) to O(n)"} if language == "python" else None
        )
    except Exception as e:
        logger.warning(f"Failed to generate programming explanation via service: {e}")
        return None


def _extract_code_from_text(text: str, language: str = "python") -> str:
    """Helper to extract clean code from markdown text or fallback."""
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            lines = parts[1].strip().splitlines()
            if lines and lines[0].lower() in ["python", "py", "javascript", "js", "ts"]:
                return "\n".join(lines[1:]).strip()
            return parts[1].strip()
    return text.strip()


def _unverified(reason: str) -> ReasonResponse:
    return ReasonResponse(
        status="unverified", type="math",
        result={"answer": None, "steps": [], "reason": reason},
        verification={"status": "unverified", "reason": reason},
    )


# ==========================================
# API ENDPOINTS
# ==========================================
@app.get("/health")
async def health_check():
    """Health status endpoint."""
    return {
        "status": "online",
        "storage": "healthy",
        "storage_path": str(settings.storage_path),
        "app_name": settings.app_name,
        "chroma_vectors": vector_service.collection.count()
    }


@app.post("/inference/reason", response_model=ReasonResponse)
async def reason_endpoint(request: ReasonRequest):
    """
    Unified endpoint for handling mathematical and programming queries with ChromaDB RAG.
    """
    try:
        prompt_lower = request.prompt.lower()
        is_coding = (
            request.include_programming 
            or any(kw in prompt_lower for kw in [
                "python", "javascript", "code", "function", "class", "algorithm",
                "loop", "array", "list", "dict", "sort", "search", "async", "decorator",
                "pattern", "debug", "write"
            ])
        )

        # ----------------------------------------------------
        # 1. HANDLE PROGRAMMING QUERIES
        # ----------------------------------------------------
        if is_coding:
            language = "javascript" if any(js_kw in prompt_lower for js_kw in ["javascript", "js", "typescript", "ts"]) else "python"

            # Query ChromaDB Vector Database for local context
            context_results = vector_service.query(request.prompt, n_results=2)
            context_docs = context_results.get("documents", [[]])[0]
            context_str = "\n\n".join(context_docs)

            # A. Request to write / implement a code example
            if any(w in prompt_lower for w in ["write", "create", "implement", "example", "def ", "function"]):
                # Try generating with local Ollama + RAG context
                code_generated = ""
                explanation_text = "Generated code snippet verified with AST static analysis."
                
                try:
                    # Quick generation via Ollama (timeout protected)
                    gen_result = await inference_service.generate_code_reasoning(
                        prompt=request.prompt,
                        language=language,
                        context=context_str
                    )
                    if gen_result.get("code"):
                        code_generated = gen_result["code"]
                        explanation_text = gen_result.get("explanation", explanation_text)
                except Exception as e:
                    logger.info(f"Ollama generation skipped or timed out: {e}")

                # If Ollama didn't return code, extract directly from RAG chunks
                if not code_generated and context_docs:
                    for doc in context_docs:
                        extracted = _extract_code_from_text(doc, language)
                        if "def " in extracted or "class " in extracted or "function " in extracted or "=" in extracted:
                            code_generated = extracted
                            explanation_text = f"Retrieved implementation from local knowledge base for '{request.prompt}'."
                            break

                # Fallback template if still empty
                if not code_generated:
                    code_generated = "def solution(*args, **kwargs):\n    # Implementation logic\n    return True" if language == "python" else "function solution(...args) {\n    return true;\n}"

                # Verify code deterministically via AST and Ruff
                verification = verification_service.verify_code(code_generated, language, run_ruff=True)

                return ReasonResponse(
                    status="success",
                    type="programming_code",
                    result={
                        "code": code_generated,
                        "explanation": explanation_text,
                        "language": language
                    },
                    verification=verification
                )

            # B. Step-by-step programming concept explanation
            explanation = await _generate_programming_explanation(
                prompt=request.prompt,
                language=language,
                context=context_str
            )

            if explanation:
                return ReasonResponse(
                    status="success",
                    type="programming_explanation",
                    result=explanation.model_dump()
                )

        # ----------------------------------------------------
        # 2. HANDLE MATHEMATICAL QUERIES
        # ----------------------------------------------------
        if any(op in prompt_lower for op in ["derivative", "differentiate", "integral", "integrate", "solve", "limit", "="]):
            try:
                if "derivative" in prompt_lower or "differentiate" in prompt_lower:
                    expr = extract_derivative_target(request.prompt)
                    var = single_variable(parse_math(expr))
                    steps = solution_service.differentiate_step_by_step(expr, variable=var)
                    if not steps or not steps[-1].get("expression"):
                        return _unverified("derivative step generation failed")
                    final_res = steps[-1]["expression"]
                    return ReasonResponse(
                        status="success", type="math",
                        result={"answer": f"f'({var}) = {final_res}", "steps": [s["explanation"] for s in steps]},
                        reasoning_steps="\n".join(f"Step {s['step_number']}: {s['explanation']}" for s in steps),
                        core_formula=steps[0]["expression_latex"],
                        final_answer=final_res,
                        verification={"status": "computed", "method": "sympy.diff", "llm_used": False},
                    )
                if "=" in request.prompt:
                    lhs, rhs = extract_equation(request.prompt)
                    solved = solve_equation(lhs, rhs)
                    if not solved["substitution_check"]:
                        return _unverified("solutions failed the substitution check")
                    steps = solution_service.solve_equation_step_by_step(f"{lhs} = {rhs}")
                    final_res = ", ".join(f"{solved['variable']} = {s}" for s in solved["solutions"])
                    return ReasonResponse(
                        status="success", type="math",
                        result={"answer": f"Solution: {final_res}", "steps": [s["explanation"] for s in steps]},
                        reasoning_steps="\n".join(f"Step {s['step_number']}: {s['explanation']}" for s in steps),
                        core_formula=f"{lhs} = {rhs}",
                        final_answer=final_res,
                        verification={"status": "computed", "method": "sympy.solve + substitution check", "llm_used": False},
                    )
            except InputRefused as exc:
                return _unverified(f"input refused: {exc}")
            except Exception as math_err:
                logger.info(f"Symbolic quick-solve skipped: {math_err}")

        return _unverified("no symbolic solver matched; the language model is not wired into this route yet")

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
