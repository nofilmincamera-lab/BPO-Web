#!/usr/bin/env python3
"""Test entity storage"""
import asyncio
import sys
import os
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from run_simple_extraction import insert_documents_simple, extract_entities_simple, store_entities_simple

async def test():
    # Test with one document
    default_path = REPO_ROOT / "data" / "preprocessed" / "preprocessed_full.jsonl"
    sample_path = Path(os.getenv("TEST_DOCUMENT_PATH", default_path))

    if not sample_path.exists():
        raise FileNotFoundError(
            f"Sample document file not found at {sample_path}. "
            "Set TEST_DOCUMENT_PATH to point to a JSONL file with documents."
        )

    with sample_path.open("r", encoding="utf-8") as f:
        line = f.readline()
        doc = json.loads(line)
    
    title = doc.get("title", "No title")
    print(f"Testing with document: {title[:50]}...")
    
    # Insert document
    batch = [doc]
    normalized = await insert_documents_simple(batch)
    print(f"Document inserted: {len(normalized)}")
    
    # Extract entities
    result = await extract_entities_simple(normalized, "2.0.0")
    entities_count = len(result["entities"])
    relationships_count = len(result["relationships"])
    print(f"Entities extracted: {entities_count}")
    print(f"Relationships extracted: {relationships_count}")
    
    if entities_count > 0:
        print("Sample entity:", result["entities"][0])
    
    # Store entities
    stored = await store_entities_simple(result)
    print(f"Stored: {stored}")

if __name__ == "__main__":
    asyncio.run(test())




