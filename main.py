import logging
import os
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import sys

from config import settings
from schemas import HealthResponse, MatrixDataset, InferenceRequest, InferenceResponse
from storage_service import storage_service
from inference_service import inference_service
from verification_service import verification_service
from vector_service import vector_service
from typing import List

# Logging configuration
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("omnimath")

app = FastAPI(title=settings.app_name)

# Error-handling middleware
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.post("/storage/upload", status_code=201)
async def upload_dataset(dataset: MatrixDataset, format: str = "parquet"):
    if format == "parquet":
        filename = await storage_service.save_dataset_parquet(dataset)
    elif format == "json":
        filename = await storage_service.save_dataset_json(dataset)
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'json' or 'parquet'.")
    
    return {"message": f"Dataset saved as {format} successfully", "filename": filename}

@app.get("/storage/list", response_model=List[str])
async def list_datasets():
    return await storage_service.list_datasets()

@app.get("/storage/fetch/{filename}", response_model=MatrixDataset)
async def fetch_dataset(filename: str):
    dataset = await storage_service.get_dataset(filename)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset

@app.post("/inference/reason", response_model=InferenceResponse)
async def reason_mathematically(request: InferenceRequest):
    """
    Triggers the LLM reasoning engine with RAG context and double-checks the math with SymPy.
    """
    try:
        # 1. Retrieve relevant context from Vector DB (RAG)
        context_results = vector_service.query(request.prompt, n_results=2)
        context_str = ""
        if context_results and context_results.get("documents"):
            docs = context_results["documents"][0]
            context_str = "\n".join(docs)
            logger.info(f"Retrieved {len(docs)} RAG context chunks.")

        # 2. Get reasoning from the LLM, passing in the context
        response = await inference_service.generate_math_reasoning(request, context=context_str)
        
        # 3. Verify the core formula using SymPy (The Truth Layer)
        if response.core_formula and response.core_formula.upper() != "N/A":
            # Basic heuristic: only verify if it contains an equals sign or operators
                response.verification_details = verification_service.verify_algebraic_expression(
                    formula_latex=response.core_formula,
                    final_answer_latex=response.final_answer
                )
        
        return response
    except Exception as e:
        logger.error(f"Inference error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=HealthResponse)
async def health_check():
    storage_path = settings.storage_path
    storage_status = "unknown"
    
    try:
        if storage_path.exists() and storage_path.is_dir():
            test_file = storage_path / ".health_check_tmp"
            test_file.touch()
            test_file.unlink()
            storage_status = "healthy"
        else:
            storage_status = "unavailable"
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        storage_status = f"unhealthy: {str(e)}"

    return {
        "status": "online",
        "storage": storage_status,
        "storage_path": str(storage_path),
        "app_name": settings.app_name
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
