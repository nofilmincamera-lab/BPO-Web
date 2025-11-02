"""Database-oriented Prefect tasks and helpers for the extraction flow."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import asyncio
import asyncpg
import hashlib
import json
import os

from prefect import task, get_run_logger

from src.heuristics import get_heuristics_loader

from .content_classifier import classify_content_type
from .document_resolver import resolve_document_uuid

_DB_POOL: Optional[asyncpg.Pool] = None
_DB_POOL_LOCK = asyncio.Lock()


async def get_db_pool() -> asyncpg.Pool:
    """Return a shared asyncpg pool for task operations."""
    global _DB_POOL
    if _DB_POOL is None:
        async with _DB_POOL_LOCK:
            if _DB_POOL is None:
                _DB_POOL = await asyncpg.create_pool(
                    host=os.getenv("DB_HOST", "localhost"),
                    port=int(os.getenv("DB_PORT", 5432)),
                    database=os.getenv("DB_NAME", "bpo_intel"),
                    user=os.getenv("DB_USER", "postgres"),
                    password=os.getenv("DB_PASSWORD", "postgres"),
                    min_size=int(os.getenv("DB_POOL_MIN_SIZE", 1)),
                    max_size=int(os.getenv("DB_POOL_MAX_SIZE", 10)),
                )
    return _DB_POOL


async def _lookup_entity_id(conn: asyncpg.Connection, doc_id: str, span: Dict[str, Any]):
    return await conn.fetchval(
        """
        SELECT id
        FROM entities
        WHERE doc_id = $1
          AND (span->>'start')::int = $2
          AND (span->>'end')::int = $3
          AND span->>'text' = $4
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        doc_id,
        int(span["start"]),
        int(span["end"]),
        span["text"],
    )


@task(
    retries=3,
    retry_delay_seconds=5,
    tags=["database", "documents"],
)
async def insert_documents(batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure documents exist in the database prior to entity persistence."""
    logger = get_run_logger()
    heuristics_loader = get_heuristics_loader()
    heuristics_data = heuristics_loader.data if heuristics_loader else None
    content_rules = heuristics_data.content_types if heuristics_data else []

    normalized_docs: List[Dict[str, Any]] = []

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        for raw_doc in batch:
            doc_uuid = resolve_document_uuid(raw_doc)
            url = raw_doc.get("url") or raw_doc.get("metadata", {}).get("url") or f"synthetic://{doc_uuid}"
            title = raw_doc.get("title") or raw_doc.get("metadata", {}).get("title")
            text = raw_doc.get("text") or raw_doc.get("metadata", {}).get("text") or ""
            status = int(raw_doc.get("status", 200))
            content_type = raw_doc.get("content_type") or raw_doc.get("metadata", {}).get("content_type")
            fetched_at = raw_doc.get("fetched_at") or raw_doc.get("metadata", {}).get("extracted_at")
            lang = raw_doc.get("lang") or raw_doc.get("metadata", {}).get("lang")

            text_sha256 = (
                hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
                if text
                else hashlib.sha256(url.encode("utf-8")).hexdigest()
            )

            raw_metadata = raw_doc.get("metadata")
            if isinstance(raw_metadata, dict):
                metadata = dict(raw_metadata)
            elif isinstance(raw_metadata, str):
                try:
                    metadata = json.loads(raw_metadata)
                except json.JSONDecodeError:
                    metadata = {"raw": raw_metadata}
            else:
                metadata = {}

            metadata.setdefault("source_url", url)
            metadata.setdefault("raw_id", raw_doc.get("id") or raw_doc.get("doc_id"))
            if fetched_at and "extracted_at" not in metadata:
                metadata["extracted_at"] = fetched_at

            content_type_value = content_type
            if content_rules:
                classification = classify_content_type(url, title, text, content_rules)
                if classification:
                    auto_meta = metadata.setdefault("auto_classification", {})
                    auto_meta["content_type"] = classification["label"]
                    auto_meta["content_type_raw"] = classification["raw_label"]
                    auto_meta["score"] = classification["score"]
                    auto_meta["confidence"] = classification["confidence"]
                    auto_meta["needs_review"] = classification["needs_review"]
                    auto_meta["scores"] = classification["scores"]
                    content_type_value = classification["label"]

            doc_record = {
                "id": str(doc_uuid),
                "url": url,
                "title": title,
                "text": text,
                "status": status,
                "content_type": content_type_value,
                "fetched_at": fetched_at,
                "lang": lang,
                "metadata": metadata,
                "text_sha256": text_sha256,
            }

            try:
                await conn.execute(
                    """
                    INSERT INTO documents (id, url, title, text, status, content_type, fetched_at, lang, metadata, text_sha256)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10)
                    ON CONFLICT (id) DO UPDATE
                    SET url = EXCLUDED.url,
                        title = EXCLUDED.title,
                        text = EXCLUDED.text,
                        status = EXCLUDED.status,
                        content_type = COALESCE(EXCLUDED.content_type, documents.content_type),
                        fetched_at = COALESCE(EXCLUDED.fetched_at, documents.fetched_at),
                        lang = COALESCE(EXCLUDED.lang, documents.lang),
                        metadata = documents.metadata || EXCLUDED.metadata,
                        text_sha256 = EXCLUDED.text_sha256,
                        updated_at = NOW()
                    """,
                    doc_record["id"],
                    doc_record["url"],
                    doc_record["title"],
                    doc_record["text"],
                    doc_record["status"],
                    doc_record["content_type"],
                    doc_record["fetched_at"],
                    doc_record["lang"],
                    json.dumps(doc_record["metadata"]),
                    doc_record["text_sha256"],
                )
            except Exception as exc:
                logger.warning(f"Failed to upsert document {doc_record['id']}: {exc}")
                continue

            normalized_docs.append(doc_record)

    logger.info(f"Prepared {len(normalized_docs)} documents for extraction")
    return normalized_docs


@task(
    retries=5,
    retry_delay_seconds=2,
    tags=["database", "storage"],
)
async def store_entities(extraction_result: Dict[str, Any]) -> Dict[str, int]:
    """Store extracted entities (and derived relationships) in database."""
    logger = get_run_logger()
    result_heuristics_version = extraction_result.get("heuristics_version")

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        entity_count = 0
        for entity in extraction_result["entities"]:
            try:
                await conn.execute(
                    """
                    INSERT INTO entities (doc_id, type, surface, norm_value, span, conf, source, source_version, heuristics_version, confidence_method)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (doc_id, type, span_hash) DO NOTHING
                    """,
                    entity["doc_id"],
                    entity["type"],
                    entity["surface"],
                    entity["norm_value"],
                    entity["span"],
                    entity["conf"],
                    entity["source"],
                    entity["source_version"],
                    entity["heuristics_version"],
                    entity["confidence_method"],
                )
                entity_count += 1
            except Exception as exc:
                logger.warning(f"Failed to insert entity: {exc}")
                continue

        relationship_count = 0
        for rel in extraction_result.get("relationships", []):
            try:
                head_id = await _lookup_entity_id(conn, rel["doc_id"], rel["head_span"])
                tail_id = await _lookup_entity_id(conn, rel["doc_id"], rel["tail_span"])
                if not head_id or not tail_id:
                    continue
                await conn.execute(
                    """
                    INSERT INTO relationships (doc_id, head_entity, tail_entity, type, conf, evidence, heuristics_version)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT DO NOTHING
                    """,
                    rel["doc_id"],
                    head_id,
                    tail_id,
                    rel["type"],
                    rel["conf"],
                    rel["evidence"],
                    rel.get("heuristics_version", result_heuristics_version),
                )
                relationship_count += 1
            except Exception as exc:
                logger.warning(f"Failed to insert relationship: {exc}")
                continue

        logger.info(
            f"Stored {entity_count} entities and {relationship_count} relationships in database"
        )
        return {"entities": entity_count, "relationships": relationship_count}
