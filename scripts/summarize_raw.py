"""Summarise recorded Ollama captures: truncation, thinking share, generation speed."""
import json
import pathlib

for path in sorted(pathlib.Path("tests/fixtures/raw").glob("*.json")):
    rec = json.loads(path.read_text(encoding="utf-8"))
    r = rec["response"]
    msg = r.get("message", {})
    n = r.get("eval_count", 0)
    secs = r.get("eval_duration", 0) / 1e9
    tps = n / secs if secs else float("nan")
    print(
        f"{path.name:<34} done={str(r.get('done_reason')):<7} tokens={n:<5} "
        f"think_chars={len(msg.get('thinking', '')):<6} "
        f"content_chars={len(msg.get('content', '')):<6} tok/s={tps:5.1f} wall_s={rec['wall_s']}"
    )