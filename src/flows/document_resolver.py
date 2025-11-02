"""Utilities for document identity resolution and batching."""
from __future__ import annotations

from typing import Any, Dict, Iterator, List, Tuple
import json
import uuid


def resolve_document_uuid(doc: Dict[str, Any]) -> uuid.UUID:
    """Resolve (or deterministically derive) a UUID for a document."""
    candidates = [
        doc.get("id"),
        doc.get("doc_id"),
        doc.get("metadata", {}).get("id"),
        doc.get("metadata", {}).get("doc_id"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return uuid.UUID(str(candidate))
        except (ValueError, TypeError):
            return uuid.uuid5(uuid.NAMESPACE_URL, str(candidate))

    url = doc.get("url") or doc.get("metadata", {}).get("url")
    if url:
        return uuid.uuid5(uuid.NAMESPACE_URL, url)

    text = doc.get("text") or doc.get("metadata", {}).get("text") or ""
    if text:
        return uuid.uuid5(uuid.NAMESPACE_OID, text[:1024])

    return uuid.uuid4()


def get_doc_id(doc: Dict[str, Any]) -> str:
    """Best-effort retrieval of document ID, mutating the doc with a derived value if needed."""
    doc_id = (
        doc.get("id")
        or doc.get("doc_id")
        or doc.get("metadata", {}).get("doc_id")
        or doc.get("metadata", {}).get("id")
    )
    if doc_id:
        return str(doc_id)

    derived = resolve_document_uuid(doc)
    doc["id"] = str(derived)
    return doc["id"]


def batched_documents(
    source_path: str, start_offset: int, batch_size: int
) -> Iterator[Tuple[int, int, List[Dict[str, Any]]]]:
    """Stream documents from file, yielding ``(batch_start, batch_end, docs)`` tuples."""
    batch: List[Dict[str, Any]] = []
    batch_start: int | None = None
    last_idx = -1
    with open(source_path, "r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle):
            if idx < start_offset:
                continue
            doc = json.loads(line)
            if batch_start is None:
                batch_start = idx
            batch.append(doc)
            if len(batch) == batch_size:
                yield batch_start, idx + 1, batch
                batch = []
                batch_start = None
            last_idx = idx

    if batch:
        end_idx = last_idx + 1 if last_idx >= 0 else start_offset + len(batch)
        start_idx = batch_start if batch_start is not None else max(end_idx - len(batch), start_offset)
        yield start_idx, end_idx, batch
