"""Compatibility layer for the document extraction flow."""
from __future__ import annotations

from .content_classifier import classify_content_type, score_structure_signals as _score_structure_signals
from .database_ops import get_db_pool, insert_documents, store_entities
from .document_resolver import (
    batched_documents as _batched_documents,
    get_doc_id as _get_doc_id,
    resolve_document_uuid as _resolve_document_uuid,
)
from .entity_extractors.batch import extract_entities_batch
from .flow_orchestrator import extract_documents_flow
from .gpu_embedding_manager import generate_and_store_embeddings

__all__ = [
    "extract_documents_flow",
    "classify_content_type",
    "_score_structure_signals",
    "_batched_documents",
    "_resolve_document_uuid",
    "_get_doc_id",
    "get_db_pool",
    "insert_documents",
    "extract_entities_batch",
    "store_entities",
    "generate_and_store_embeddings",
]
