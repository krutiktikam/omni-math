from pydantic import BaseModel, Field
from typing import List, Optional
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

class InferenceRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    stream: bool = False

class InferenceResponse(BaseModel):
    reasoning_steps: str = Field(..., description="Step-by-step mathematical reasoning.")
    core_formula: str = Field(..., description="The primary LaTeX formula identified.")
    final_answer: str = Field(..., description="The final calculated result.")
    model_used: str
    generation_time: float
    verification_details: Optional[dict] = Field(None, description="Symbolic verification results from SymPy.")
