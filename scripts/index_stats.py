"""Read-only: vectors per collection and per metadata value."""
import collections
import sys

import chromadb

path = sys.argv[1] if len(sys.argv) > 1 else "data/vector_db"
client = chromadb.PersistentClient(path=path)
for item in client.list_collections():
    col = item if hasattr(item, "count") else client.get_collection(item)
    print(f"collection={col.name} count={col.count()}")
    counters: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    offset = 0
    while True:
        batch = col.get(include=["metadatas"], limit=5000, offset=offset)
        if not batch["ids"]:
            break
        for meta in batch["metadatas"] or []:
            for k, v in (meta or {}).items():
                counters[k][str(v)[:80]] += 1
        offset += 5000
    for k, c in counters.items():
        shown = dict(c.most_common(30)) if len(c) <= 30 else f"{len(c)} distinct values"
        print(f"  {k}: {shown}")
