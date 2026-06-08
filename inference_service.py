import httpx
import json
import time
from typing import Optional, Dict, Any
from config import settings
from schemas import InferenceRequest, InferenceResponse
import logging

logger = logging.getLogger("omnimath.inference")

class InferenceService:
    def __init__(self, base_url: str = settings.ollama_base_url):
        self.base_url = base_url

    async def generate_math_reasoning(self, request: InferenceRequest, context: str = "") -> InferenceResponse:
        """
        Communicates with local Ollama instance to generate structured mathematical reasoning.
        Enforces JSON output schema and utilizes RAG context if provided.
        """
        model = request.model or settings.default_model
        start_time = time.time()

        # Few-Shot System Prompt to guide the small 1.5B model
        system_prompt = (
            "You are a mathematical reasoning engine. You MUST output ONLY valid JSON.\n"
            "Example JSON Output:\n"
            "{\n"
            "  \"reasoning_steps\": \"Step 1: Identify the variables. Step 2: Use the formula.\",\n"
            "  \"core_formula\": \"a^2 + b^2 = c^2\",\n"
            "  \"final_answer\": \"5\"\n"
            "}\n"
            "Strictly follow this structure. Do not add explanations outside the JSON."
        )

        full_prompt = request.prompt
        if context:
            full_prompt = f"Context:\n{context}\n\nQuestion: {request.prompt}\n\nProvide the answer in the JSON format specified."

        payload = {
            "model": model,
            "prompt": full_prompt,
            "system": system_prompt,
            "stream": False,
            "format": "json" 
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                
                result = response.json()
                response_content = result.get("response", "{}").strip()
                
                # Basic JSON repair for small models
                if not response_content.startswith("{"):
                    start = response_content.find("{")
                    end = response_content.rfind("}")
                    if start != -1 and end != -1:
                        response_content = response_content[start:end+1]
                
                # Parse the inner JSON
                parsed_content = json.loads(response_content)
                
                generation_time = time.time() - start_time
                
                return InferenceResponse(
                    reasoning_steps=parsed_content.get("reasoning_steps", "No reasoning provided."),
                    core_formula=parsed_content.get("core_formula", "N/A"),
                    final_answer=parsed_content.get("final_answer", "N/A"),
                    model_used=model,
                    generation_time=generation_time
                )

        except httpx.HTTPError as e:
            logger.error(f"Ollama connection error: {e}")
            raise Exception(f"Failed to connect to Ollama: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON output: {e}. Raw content: {response_content}")
            raise Exception("Model failed to return valid JSON reasoning.")
        except Exception as e:
            logger.error(f"Inference unexpected error: {e}")
            raise

inference_service = InferenceService()
