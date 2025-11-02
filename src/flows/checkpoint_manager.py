"""Checkpoint persistence tasks for the extraction pipeline."""
from __future__ import annotations

from typing import Any, Dict
import json

from prefect import task, get_run_logger

from .database_ops import get_db_pool


@task(
    retries=3,
    retry_delay_seconds=10,
    cache_key_fn=lambda ctx, params: f"load_checkpoint_{params['workflow_id']}",
    persist_result=True,
    tags=["checkpoint"],
)
async def load_checkpoint(workflow_id: str) -> Dict[str, Any]:
    """Load checkpoint from database."""
    query = """
        SELECT doc_offset, state
        FROM pipeline_checkpoints
        WHERE workflow_id = $1 AND phase = 'extraction'
        ORDER BY updated_at DESC
        LIMIT 1
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchrow(query, workflow_id)
            if not result:
                return {}
            state = result["state"] or {}
            state["offset"] = result["doc_offset"]
            return state
    except Exception as exc:
        get_run_logger().warning(f"Failed to load checkpoint: {exc}")
        return {}


@task(
    retries=3,
    retry_delay_seconds=5,
    tags=["checkpoint"],
)
async def save_checkpoint(workflow_id: str, run_id: str, checkpoint_data: Dict[str, Any]) -> None:
    """Save checkpoint to database."""
    logger = get_run_logger()

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO pipeline_checkpoints (workflow_id, run_id, phase, doc_offset, state, created_at, updated_at)
            VALUES ($1, $2, 'extraction', $3, $4, NOW(), NOW())
            ON CONFLICT (workflow_id, run_id, phase) DO UPDATE
            SET doc_offset = EXCLUDED.doc_offset,
                state = EXCLUDED.state,
                updated_at = NOW()
            """,
            workflow_id,
            run_id,
            checkpoint_data.get("offset", 0),
            json.dumps(checkpoint_data),
        )

    logger.info(f"Checkpoint saved at offset {checkpoint_data.get('offset', 0)}")
