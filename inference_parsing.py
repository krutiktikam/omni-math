"""Pure parsing of an Ollama /api/generate response. No network, so it is testable offline."""
import json

from inference_errors import InvalidModelOutput, TruncatedOutput

REQUIRED = ("reasoning_steps", "core_formula", "final_answer")


def parse_math_response(resp: dict) -> dict:
    if resp.get("done_reason") == "length":
        raise TruncatedOutput("answer cut off by the token limit")
    try:
        data = json.loads(resp.get("response", ""))
    except (TypeError, json.JSONDecodeError) as exc:
        raise InvalidModelOutput(f"response is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise InvalidModelOutput("JSON root is not an object")
    out = {}
    for key in REQUIRED:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise InvalidModelOutput(f"missing or empty field: {key}")
        out[key] = value.strip()
    return out