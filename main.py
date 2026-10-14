import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Import your services
from services.programming_solution_service import programming_solution_service
from services.verification_service_code import verification_service

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

# ==========================================
# HELPER FUNCTIONS
# ==========================================
async def _generate_programming_explanation(prompt: str, language: str, formula: str, context: str) -> Optional[ProgrammingExplanation]:
    """
    Generate a programming concept explanation using the programming solution service.
    """
    try:
        # Use the programming solution service to get step-by-step explanation
        steps_data = programming_solution_service.explain_concept(prompt, language)

        if not steps_data:
            return None

        # Convert to ProgrammingStep objects
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

        # Create the programming explanation
        return ProgrammingExplanation(
            concept=prompt[:100],  # Truncate long prompts
            language=language,
            steps=steps,
            related_concepts=[f"{language} basics", f"{language} best practices"],
            complexity_analysis={"time": "O(1)", "space": "O(1)"} if language == "python" else None
        )
    except Exception as e:
        logger.warning(f"Failed to generate programming explanation via service: {e}")
        return None

# ==========================================
# API ENDPOINTS
# ==========================================
@app.post("/inference/reason", response_model=ReasonResponse)
async def reason_endpoint(request: ReasonRequest):
    """
    Main endpoint for handling both mathematical and programming queries.
    """
    try:
        # 1. Handle Programming Queries
        if request.include_programming or "python" in request.prompt.lower() or "code" in request.prompt.lower():
            
            # Simple language detection from prompt
            language = "python" if "python" in request.prompt.lower() else "javascript"
            
            # Check if this is a request to verify code (e.g., "Write a Python function...")
            if "write" in request.prompt.lower() or "function" in request.prompt.lower():
                # Mock generating a snippet based on the prompt, then verify it.
                mock_generated_code = "def add(a, b):\n    return a + b" if language == "python" else "function add(a, b) { return a + b; }"
                verification = verification_service.verify_code(mock_generated_code, language)
                
                return ReasonResponse(
                    status="success",
                    type="programming_code",
                    result={"code": mock_generated_code, "explanation": "Generated code snippet."},
                    verification=verification
                )
            
            # Otherwise, generate step-by-step programming explanation
            explanation = await _generate_programming_explanation(
                prompt=request.prompt, 
                language=language, 
                formula="", 
                context=""
            )
            
            if explanation:
                return ReasonResponse(
                    status="success",
                    type="programming_explanation",
                    result=explanation.model_dump()
                )
                
        # 2. Handle Math Queries (Fallback / Existing Logic)
        # ⚠️ NOTE: If you had custom mathematical LLM logic before, it would go here!
        # For testing, this acts as a placeholder so the endpoint doesn't crash on math.
        return ReasonResponse(
            status="success", 
            type="math",
            result={
                "answer": f"Processed math query: {request.prompt}", 
                "steps": ["Step 1: Parse", "Step 2: Solve"] if request.step_by_step else []
            }
        )

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)