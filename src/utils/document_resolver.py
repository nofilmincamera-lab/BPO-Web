"""
Unified document UUID resolution utilities.

This module provides a single source of truth for resolving document UUIDs
across all extraction scripts, eliminating 7x duplication.

Centralized implementation ensures consistent UUID generation across:
- run_simple_extraction.py
- run_standalone_extraction.py
- run_extraction.py
- run_direct_extraction.py
- run_full_extraction.py
- run_test_extraction.py
- src/flows/extraction_flow.py
"""
import uuid
from typing import Dict, Any


def resolve_document_uuid(doc: Dict[str, Any]) -> uuid.UUID:
    """
    Resolve (or deterministically derive) a UUID for a document.
    
    Prefers explicit UUID values, then falls back to deterministic uuid5 variants.
    This ensures consistent UUID generation across runs for the same document.
    
    Args:
        doc: Document dictionary with potential id/doc_id/url/text fields
        
    Returns:
        UUID object representing the document identifier
        
    Strategy:
        1. Check explicit ID fields (id, doc_id, metadata.id, metadata.doc_id)
        2. If found, parse as UUID or generate deterministic UUID5 from string
        3. Fallback to URL-based UUID5 if available
        4. Fallback to text-based UUID5 (first 1024 chars) if available
        5. Final fallback: random UUID4
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
    """
    Best-effort retrieval of document ID as string.
    
    Attempts to find an explicit ID field, then falls back to
    deterministic UUID resolution via resolve_document_uuid().
    
    Modifies the input doc dict in-place by setting doc["id"] if missing.
    
    Args:
        doc: Document dictionary
        
    Returns:
        String representation of document ID
    """
    doc_id = (
        doc.get("id")
        or doc.get("doc_id")
        or doc.get("metadata", {}).get("doc_id")
        or doc.get("metadata", {}).get("id")
    )
    if doc_id:
        return str(doc_id)

    # Fall back to deterministic UUID so downstream tables remain consistent.
    derived = resolve_document_uuid(doc)
    doc["id"] = str(derived)
    return doc["id"]


# Backward compatibility aliases for existing code
_resolve_document_uuid = resolve_document_uuid
_get_doc_id = get_doc_id
