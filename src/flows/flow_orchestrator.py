"""Prefect flow orchestration for document extraction."""
from __future__ import annotations

from typing import Any, Dict
import os

from prefect import flow, get_run_logger
from prefect.context import get_run_context
from prefect.task_runners import ConcurrentTaskRunner

from .checkpoint_manager import load_checkpoint, save_checkpoint
from .database_ops import insert_documents, store_entities
from .document_resolver import batched_documents
from .entity_extractors.batch import extract_entities_batch
from .gpu_embedding_manager import generate_and_store_embeddings


@flow(
    name="document-extraction-pipeline",
    task_runner=ConcurrentTaskRunner(),
    retries=1,
    retry_delay_seconds=30,
    log_prints=True,
    timeout_seconds=7200,
)
async def extract_documents_flow(
    source_path: str,
    heuristics_version: str = "2.0.0",
    batch_size: int = 100,
    start_offset: int = 0,
) -> Dict[str, Any]:
    """Main extraction flow for processing documents with spaCy EntityRuler."""
    logger = get_run_logger()
    run_context = get_run_context()
    flow_run = getattr(run_context, "flow_run", None)
    flow_run_id = flow_run.id if flow_run else "local-run"
    workflow_id = f"extraction-{os.path.basename(source_path)}"

    logger.info(f"Starting extraction flow: {workflow_id}")
    logger.info(f"Source: {source_path}, Batch size: {batch_size}, Offset: {start_offset}")

    checkpoint = await load_checkpoint(workflow_id)
    current_offset = checkpoint.get("offset", start_offset)
    logger.info(f"Resuming from offset {current_offset}")

    total_entities = 0
    total_relationships = 0
    all_failed_docs = []
    total_docs_seen = current_offset

    for batch_start, batch_end, batch in batched_documents(
        source_path, current_offset, batch_size
    ):
        batch_id = f"{workflow_id}-batch-{batch_start}"
        logger.info(f"Processing batch {batch_start}-{batch_end}")

        normalized_batch = await insert_documents(batch)
        result = await extract_entities_batch(normalized_batch, batch_id, heuristics_version)
        stored_counts = await store_entities(result)
        embedding_counts = await generate_and_store_embeddings(result)
        if embedding_counts.get("error"):
            logger.warning(f"Embedding generation skipped: {embedding_counts['error']}")

        total_entities += stored_counts["entities"]
        total_relationships += stored_counts["relationships"]
        all_failed_docs.extend(result["failed_docs"])
        total_docs_seen = max(total_docs_seen, batch_end)

        docs_since_start = batch_end - start_offset
        if docs_since_start > 0 and docs_since_start % 1000 == 0:
            await save_checkpoint(
                workflow_id,
                flow_run_id,
                {
                    "offset": batch_end,
                    "total_entities": total_entities,
                    "total_relationships": total_relationships,
                },
            )

    processed_docs = max(total_docs_seen - start_offset, 0)
    summary = {
        "workflow_id": workflow_id,
        "flow_run_id": flow_run_id,
        "total_processed": processed_docs,
        "total_entities": total_entities,
        "total_relationships": total_relationships,
        "failed_documents": all_failed_docs,
        "success_rate": (
            (processed_docs - len(all_failed_docs)) / processed_docs if processed_docs else 0
        ),
    }

    logger.info(f"Extraction complete: {summary}")
    return summary
