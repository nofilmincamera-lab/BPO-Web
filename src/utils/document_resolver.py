"""
Unified document UUID resolution utilities.

This module provides a single source of truth for resolving document UUIDs
across all extraction scripts, eliminating 7x duplication.
"""
import uuid
from typing import Dict, Any


def resolve_document_uuid(doc: Dict[str, Any]) -> uuid.UUID:
    """
    Resolve (or deterministically derive) a UUID for a document.
    
    Prefers explicit UUID values, then falls back to deterministic uuid5 variants.
    """
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
    """Best-effort retrieval of document ID as string."""
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
