"""GPU embedding orchestration task."""
from __future__ import annotations

from typing import Any, Dict
import asyncpg
import os

from prefect import task, get_run_logger


@task(
    retries=2,
    retry_delay_seconds=3,
    tags=["embeddings", "gpu"],
)
async def generate_and_store_embeddings(extraction_result: Dict[str, Any]) -> Dict[str, int]:
    """Generate GPU-accelerated embeddings for entities and store them."""
    logger = get_run_logger()

    try:
        from src.extraction.gpu_embeddings import generate_entity_embeddings, get_embedding_info
    except ImportError as exc:
        logger.warning(
            f"GPU embeddings module not available: {exc}. Skipping embeddings generation."
        )
        return {"embeddings": 0, "error": "module_not_available"}

    info = get_embedding_info()
    logger.info(
        f"Generating embeddings with model: {info.get('model_name', 'unknown')} on {info.get('device', 'unknown')}"
    )

    try:
        entities = extraction_result.get("entities", [])
        if not entities:
            logger.info("No entities to generate embeddings for")
            return {"embeddings": 0}

        logger.info(f"Generating embeddings for {len(entities)} entities...")
        entities_with_embeddings = generate_entity_embeddings(entities)

        embeddings_stored = 0
        async with asyncpg.create_pool(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME", "bpo_intel"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
        ) as pool:
            async with pool.acquire() as conn:
                for entity in entities_with_embeddings:
                    if "embedding" not in entity:
                        continue

                    try:
                        entity_id = await conn.fetchval(
                            """
                            SELECT id FROM entities
                            WHERE doc_id = $1
                              AND type = $2
                              AND surface = $3
                            ORDER BY created_at DESC
                            LIMIT 1
                            """,
                            entity["doc_id"],
                            entity["type"],
                            entity["surface"],
                        )

                        if entity_id:
                            await conn.execute(
                                """
                                INSERT INTO entity_embeddings (entity_id, embedding, model_name)
                                VALUES ($1, $2, $3)
                                ON CONFLICT (entity_id) DO UPDATE
                                SET embedding = EXCLUDED.embedding,
                                    model_name = EXCLUDED.model_name,
                                    created_at = NOW()
                                """,
                                entity_id,
                                entity["embedding"],
                                entity.get(
                                    "embedding_model",
                                    "sentence-transformers/all-MiniLM-L6-v2",
                                ),
                            )
                            embeddings_stored += 1
                    except Exception as exc:
                        logger.warning(f"Failed to store embedding for entity: {exc}")
                        continue

        logger.info(f"Stored {embeddings_stored} entity embeddings in database")
        return {"embeddings": embeddings_stored}

    except Exception as exc:
        logger.error(f"Failed to generate/store embeddings: {exc}")
        return {"embeddings": 0, "error": str(exc)}
