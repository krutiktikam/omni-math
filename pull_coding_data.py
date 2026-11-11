"""
OmniMath-Local: Online Coding Data Ingestion Script
Fetches high-quality coding algorithms, design patterns, and programming tasks
directly from GitHub & open sources, saves them offline on local SSD, and indexes
them into ChromaDB for 100% offline retrieval.
"""

import os
import json
import asyncio
from pathlib import Path
import httpx
from config import settings
from parsing_service import parsing_service
from vector_service import vector_service

DOCS_DIR = Path(settings.storage_path) / "programming_docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Curated Algorithms & Data Structures (from TheAlgorithms/Python)
ALGO_SOURCES = [
    {
        "filename": "binary_search.py",
        "url": "https://raw.githubusercontent.com/TheAlgorithms/Python/master/searches/binary_search.py",
        "topic": "algorithms_search"
    },
    {
        "filename": "quick_sort.py",
        "url": "https://raw.githubusercontent.com/TheAlgorithms/Python/master/sorts/quick_sort.py",
        "topic": "algorithms_sorting"
    },
    {
        "filename": "merge_sort.py",
        "url": "https://raw.githubusercontent.com/TheAlgorithms/Python/master/sorts/merge_sort.py",
        "topic": "algorithms_sorting"
    },
    {
        "filename": "lru_cache.py",
        "url": "https://raw.githubusercontent.com/TheAlgorithms/Python/master/data_structures/caches/lru_cache.py",
        "topic": "data_structures"
    },
    {
        "filename": "singly_linked_list.py",
        "url": "https://raw.githubusercontent.com/TheAlgorithms/Python/master/data_structures/linked_list/singly_linked_list.py",
        "topic": "data_structures"
    },
    {
        "filename": "binary_search_tree.py",
        "url": "https://raw.githubusercontent.com/TheAlgorithms/Python/master/data_structures/binary_tree/binary_search_tree.py",
        "topic": "data_structures"
    },
    {
        "filename": "dijkstra.py",
        "url": "https://raw.githubusercontent.com/TheAlgorithms/Python/master/graphs/dijkstra.py",
        "topic": "algorithms_graphs"
    },
    {
        "filename": "fibonacci_dp.py",
        "url": "https://raw.githubusercontent.com/TheAlgorithms/Python/master/dynamic_programming/fibonacci.py",
        "topic": "algorithms"
    }
]

# 2. Curated Python Design Patterns (from faif/python-patterns)
PATTERN_SOURCES = [
    {
        "filename": "singleton_pattern.py",
        "url": "https://raw.githubusercontent.com/faif/python-patterns/master/patterns/creational/singleton.py",
        "topic": "design_patterns"
    },
    {
        "filename": "factory_pattern.py",
        "url": "https://raw.githubusercontent.com/faif/python-patterns/master/patterns/creational/factory.py",
        "topic": "design_patterns"
    },
    {
        "filename": "observer_pattern.py",
        "url": "https://raw.githubusercontent.com/faif/python-patterns/master/patterns/behavioral/observer.py",
        "topic": "design_patterns"
    },
    {
        "filename": "strategy_pattern.py",
        "url": "https://raw.githubusercontent.com/faif/python-patterns/master/patterns/behavioral/strategy.py",
        "topic": "design_patterns"
    },
    {
        "filename": "decorator_pattern.py",
        "url": "https://raw.githubusercontent.com/faif/python-patterns/master/patterns/structural/decorator.py",
        "topic": "design_patterns"
    }
]

# 3. CodeAlpaca instruction dataset (Raw GitHub)
CODE_ALPACA_URL = "https://raw.githubusercontent.com/sahil280114/codealpaca/master/data/code_alpaca_20k.json"


async def fetch_file(client: httpx.AsyncClient, item: dict, subfolder: Path):
    dest_path = subfolder / item["filename"]
    try:
        resp = await client.get(item["url"])
        if resp.status_code == 200:
            dest_path.write_text(resp.text, encoding="utf-8")
            print(f"  [OK] Saved offline: {dest_path.name}")
            return dest_path, item["topic"]
        else:
            print(f"  [FAIL] HTTP {resp.status_code} for {item['filename']}")
            return None, None
    except Exception as e:
        print(f"  [ERROR] {item['filename']}: {e}")
        return None, None


async def ingest_online_coding_data(num_code_alpaca_tasks: int = 400):
    print("=" * 60)
    print("  OMNIMATH-LOCAL: PULLING ONLINE CODING DATA TO LOCAL SSD")
    print("=" * 60)

    algo_dir = DOCS_DIR / "algorithms"
    patterns_dir = DOCS_DIR / "patterns"
    tasks_dir = DOCS_DIR / "tasks"
    algo_dir.mkdir(parents=True, exist_ok=True)
    patterns_dir.mkdir(parents=True, exist_ok=True)
    tasks_dir.mkdir(parents=True, exist_ok=True)

    all_chunks = []

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        # Step A: Pull Algorithms & Data Structures
        print("\n1. Fetching Algorithms & Data Structures from TheAlgorithms/Python...")
        for item in ALGO_SOURCES:
            fpath, topic = await fetch_file(client, item, algo_dir)
            if fpath:
                chunks = parsing_service.parse_file(fpath)
                for c in chunks:
                    c["metadata"]["topic"] = topic
                    c["metadata"]["source"] = fpath.name
                all_chunks.extend(chunks)

        # Step B: Pull Design Patterns
        print("\n2. Fetching Python Design Patterns...")
        for item in PATTERN_SOURCES:
            fpath, topic = await fetch_file(client, item, patterns_dir)
            if fpath:
                chunks = parsing_service.parse_file(fpath)
                for c in chunks:
                    c["metadata"]["topic"] = topic
                    c["metadata"]["source"] = fpath.name
                all_chunks.extend(chunks)

        # Step C: Pull Curated Code Tasks from CodeAlpaca
        print(f"\n3. Fetching {num_code_alpaca_tasks} Programming Tasks from CodeAlpaca...")
        try:
            resp = await client.get(CODE_ALPACA_URL)
            if resp.status_code == 200:
                data = resp.json()[:num_code_alpaca_tasks]
                
                # Save full raw subset as JSON offline
                raw_json_path = tasks_dir / "code_alpaca_curated.json"
                raw_json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                print(f"  [OK] Saved {len(data)} tasks to {raw_json_path.name}")

                # Convert into clean Markdown files for sliding-window chunking
                markdown_doc_lines = ["# Curated Python Programming Tasks & Solutions\n\n"]
                for i, row in enumerate(data):
                    instruction = row.get("instruction", "").strip()
                    code_output = row.get("output", "").strip()
                    if not instruction or not code_output:
                        continue
                    markdown_doc_lines.append(f"## Task {i+1}: {instruction}\n\n```python\n{code_output}\n```\n\n")

                md_path = tasks_dir / "code_alpaca_tasks.md"
                md_path.write_text("".join(markdown_doc_lines), encoding="utf-8")
                print(f"  [OK] Created Markdown task knowledge base: {md_path.name}")

                # Parse into AST & Markdown chunks
                task_chunks = parsing_service.chunk_markdown(md_path.read_text(encoding="utf-8"), md_path.name)
                print(f"  [OK] Generated {len(task_chunks)} chunks from coding tasks")
                all_chunks.extend(task_chunks)
            else:
                print(f"  [FAIL] Failed to fetch CodeAlpaca: HTTP {resp.status_code}")
        except Exception as e:
            print(f"  [ERROR] CodeAlpaca fetch error: {e}")

    # Step D: Index into ChromaDB
    print(f"\n4. Indexing total {len(all_chunks)} new coding chunks into ChromaDB...")
    if all_chunks:
        await vector_service.add_documents(all_chunks, batch_size=250)
        print(f"\n SUCCESS: Successfully indexed {len(all_chunks)} coding chunks into local vector DB!")
        print(f" Total ChromaDB Collection Size: {vector_service.collection.count()} vectors.")
    else:
        print("No new chunks to index.")


if __name__ == "__main__":
    asyncio.run(ingest_online_coding_data())
