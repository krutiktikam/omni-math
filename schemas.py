from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class MatrixRow(BaseModel):
    values: List[float] = Field(..., description="A list of numerical values representing a row in the matrix.")

class MatrixDataset(BaseModel):
    name: str = Field(..., description="Name of the dataset.")
    rows: List[MatrixRow]
    metadata: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class HealthResponse(BaseModel):
    status: str
    storage: str
    storage_path: str
    app_name: str

class SolutionStep(BaseModel):
    step_number: int = Field(..., description="The step number in the solution process")
    explanation: str = Field(..., description="Plain language explanation of what happens in this step")
    expression_latex: str = Field(..., description="Mathematical expression in LaTeX format")
    expression: str = Field(..., description="Mathematical expression in plain text format")

class StepByStepSolution(BaseModel):
    operation_type: str = Field(..., description="Type of mathematical operation (equation, derivative, integral, limit)")
    steps: List[SolutionStep] = Field(..., description="List of solution steps")
    final_result: str = Field(..., description="Final result of the operation")
    final_result_latex: str = Field(..., description="Final result in LaTeX format")

# Programming-specific models
class CodeExample(BaseModel):
    language: str = Field(..., description="Programming language of the code example")
    code: str = Field(..., description="Code snippet")
    explanation: str = Field(..., description="Explanation of what the code does")

class ProgrammingStep(BaseModel):
    step_number: int = Field(..., description="The step number in the explanation process")
    explanation: str = Field(..., description="Plain language explanation of this step")
    code_example: Optional[CodeExample] = Field(None, description="Code example illustrating this step")

class ProgrammingExplanation(BaseModel):
    concept: str = Field(..., description="The programming concept being explained")
    language: str = Field(..., description="Primary programming language")
    steps: List[ProgrammingStep] = Field(..., description="Step-by-step explanation")
    related_concepts: List[str] = Field(default_factory=list, description="Related programming concepts")
    complexity_analysis: Optional[Dict[str, Any]] = Field(None, description="Time/space complexity analysis")

class InferenceRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    stream: bool = False
    step_by_step: Optional[bool] = Field(False, description="Whether to return step-by-step solution")
    include_programming: Optional[bool] = Field(False, description="Whether to include programming-specific explanations")

class InferenceResponse(BaseModel):
    reasoning_steps: str = Field(..., description="Step-by-step mathematical reasoning.")
    core_formula: str = Field(..., description="The primary LaTeX formula identified.")
    final_answer: str = Field(..., description="The final calculated result.")
    model_used: str
    generation_time: float
    verification_details: Optional[dict] = Field(None, description="Symbolic verification results from SymPy or code validation.")
    step_by_step_solution: Optional[StepByStepSolution] = Field(None, description="Detailed step-by-step solution if requested")
    # Programming-specific fields
    programming_explanation: Optional[ProgrammingExplanation] = Field(None, description="Programming concept explanation")
    language_detected: Optional[str] = Field(None, description="Detected programming language from the query")
    code_examples: Optional[List[CodeExample]] = Field(None, description="Extracted or generated code examples")