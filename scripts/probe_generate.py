"""Probe the /api/generate call inference_service.py makes, under 4 settings."""
import datetime
import json
import pathlib
import time

import httpx

URL = "http://localhost:11434/api/generate"
MODEL = "deepseek-r1:1.5b"
OUT = pathlib.Path("tests/fixtures/raw_generate")

# Keep in sync with inference_service.generate_math_reasoning
SYSTEM = (
    "You are a mathematical reasoning engine. You MUST output ONLY valid JSON.\n"
    "Example JSON Output:\n"
    "{\n"
    '  "reasoning_steps": "Step 1: Identify the variables. Step 2: Use the formula.",\n'
    '  "core_formula": "a^2 + b^2 = c^2",\n'
    '  "final_answer": "5"\n'
    "}\n"
    "Strictly follow this structure. Do not add explanations outside the JSON."
)
KEYS = ["reasoning_steps", "core_formula", "final_answer"]
SCHEMA = {"type": "object", "properties": {k: {"type": "string"} for k in KEYS}, "required": KEYS}
PROMPTS = {
    "derivative": "Differentiate f(x) = 3x^2 + 2x",
    "word_problem": "A train covers 120 km in 1.5 hours. At the same speed, how far does it travel in 4 hours?",
}
VARIANTS = {
    "A_asis": {"format": "json"},
    "B_nothink": {"format": "json", "think": False},
    "C_schema_nothink": {"format": SCHEMA, "think": False},
    "D_schema_think": {"format": SCHEMA, "think": True},
}


def call(extra: dict, prompt: str) -> tuple[int, dict, float]:
    body = {
        "model": MODEL, "prompt": prompt, "system": SYSTEM, "stream": False,
        "options": {"temperature": 0, "seed": 0, "num_predict": 2048}, **extra,
    }
    t0 = time.perf_counter()
    resp = httpx.post(URL, json=body, timeout=300)
    wall = time.perf_counter() - t0
    try:
        data = resp.json()
    except Exception:
        data = {"error": resp.text[:200]}
    return resp.status_code, {"request": body, "response": data}, wall


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    call({}, "hi")  # warm-up so load time is not counted below
    print(f"{'variant':<18}{'prompt':<14}{'status':<7}{'done':<8}{'tok':<6}{'think':<7}{'resp':<6}{'json':<6}{'keys':<6}wall_s")
    for vname, extra in VARIANTS.items():
        for pname, prompt in PROMPTS.items():
            status, rec, wall = call(extra, prompt)
            r = rec["response"]
            text = r.get("response", "")
            try:
                parsed = json.loads(text)
                json_ok, keys_ok = True, all(k in parsed for k in KEYS)
            except Exception:
                json_ok = keys_ok = False
            rec.update(captured=datetime.datetime.now().isoformat(timespec="seconds"), wall_s=round(wall, 2))
            (OUT / f"{vname}_{pname}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"{vname:<18}{pname:<14}{status:<7}{str(r.get('done_reason')):<8}{r.get('eval_count', '?'):<6}"
                  f"{len(r.get('thinking', '')):<7}{len(text):<6}{json_ok!s:<6}{keys_ok!s:<6}{wall:.1f}")


if __name__ == "__main__":
    main()
