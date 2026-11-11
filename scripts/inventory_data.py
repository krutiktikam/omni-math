"""
Data Inventory Script (Day 1 Safety & Governance Audit)
Stdlib only - walks data/ and computes SHA-256, file sizes, and metadata columns.
"""

import os
import csv
import hashlib
from pathlib import Path

def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 hash in 64KB blocks."""
    sha = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(65536), b""):
                sha.update(block)
        return sha.hexdigest()
    except Exception as e:
        return f"ERROR: {e}"

def generate_inventory(data_dir: str = "data", output_csv: str = "data_inventory.csv"):
    root_path = Path(data_dir)
    if not root_path.exists():
        print(f"Error: {data_dir} directory not found.")
        return

    fieldnames = [
        "path",
        "size_bytes",
        "sha256",
        "extension",
        "origin",
        "licence",
        "redistributable",
        "evidence"
    ]

    records = []
    print(f"Scanning directory: {data_dir}...")
    
    for current_root, _, files in os.walk(root_path):
        for f in files:
            file_path = Path(current_root) / f
            rel_path = file_path.as_posix()
            size = file_path.stat().st_size
            ext = file_path.suffix.lower()
            sha256_hash = compute_sha256(file_path)

            records.append({
                "path": rel_path,
                "size_bytes": size,
                "sha256": sha256_hash,
                "extension": ext,
                "origin": "",
                "licence": "",
                "redistributable": "",
                "evidence": ""
            })

    output_path = Path(output_csv)
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Successfully inventoried {len(records)} files -> {output_path.resolve()}")

if __name__ == "__main__":
    generate_inventory()
