"""Record current API behaviour (characterization fixtures, captured BEFORE fixes)."""
import argparse
import datetime
import json
import pathlib
import time

import httpx

OUT = pathlib.Path("tests/fixtures/app")
CASES = {
    "example_binary_search": {"prompt": "Write a python code example for: binary search",
                              "step_by_step": False, "include_programming": True},
    "explain_binary_search": {"prompt": "Explain the concept of binary search in python",
                              "step_by_step": True, "include_programming": True},
    # payload below is a guess; match what chat.py sends for free-form math
    "math_derivative": {"prompt": "Differentiate f(x) = 3x^2 + 2x",
                        "step_by_step": True, "include_programming": False},
    "math_equation": {"prompt": "Solve 2x + 3 = 7",
                      "step_by_step": True, "include_programming": False},
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="exact URL chat.py posts to")
    ap.add_argument("--timeout", type=float, default=180)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for name, payload in CASES.items():
        t0 = time.perf_counter()
        try:
            resp = httpx.post(args.url, json=payload, timeout=args.timeout)
            status, body = resp.status_code, resp.json()
        except Exception as exc:
            status, body = -1, {"client_error": repr(exc)}
        elapsed = round(time.perf_counter() - t0, 2)
        record = {"captured": datetime.datetime.now().isoformat(timespec="seconds"),
                  "elapsed_s": elapsed, "status": status, "request": payload, "response": body}
        (OUT / f"{name}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{name:<24} status={status} elapsed_s={elapsed}")


if __name__ == "__main__":
    main()