"""Capture raw Ollama responses so output-handling bugs can be reproduced offline."""
import argparse
import datetime
import json
import pathlib
import time

import httpx

URL = "http://localhost:11434/api/chat"
OUT = pathlib.Path("tests/fixtures/raw")

PROMPTS = {
    "derivative_simple": "Differentiate f(x) = 3x^2 + 2x and state the final answer.",
    "word_problem": "A train covers 120 km in 1.5 hours. At the same speed, how far does it travel in 4 hours?",
    "code_example": "Give a short Python example of binary search, with a brief explanation.",
    "complexity_claim": "What are the time and space complexity of binary search?",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="deepseek-r1:1.5b")
    ap.add_argument("--num-predict", type=int, default=1024)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"{'name':<20}{'done_reason':<13}{'tokens':<8}{'think_in_content':<18}{'thinking_field'}")
    for name, prompt in PROMPTS.items():
        body = {
            "model": args.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0, "seed": 0, "num_predict": args.num_predict},
        }
        t0 = time.perf_counter()
        resp = httpx.post(URL, json=body, timeout=300)
        resp.raise_for_status()
        wall = time.perf_counter() - t0
        data = resp.json()
        record = {
            "captured": datetime.datetime.now().isoformat(timespec="seconds"),
            "wall_s": round(wall, 2),
            "request": body,
            "response": data,
        }
        path = OUT / f"{name}_np{args.num_predict}.json"
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        msg = data.get("message", {})
        print(
            f"{name:<20}{data.get('done_reason', '?'):<13}{data.get('eval_count', '?'):<8}"
            f"{'<think>' in msg.get('content', ''):<18}{bool(msg.get('thinking'))}"
        )


if __name__ == "__main__":
    main()
