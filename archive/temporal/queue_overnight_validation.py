#!/usr/bin/env python3
"""
Queue overnight validation workflow.

Usage:
    python scripts/queue_overnight_validation.py
"""

import asyncio
import os

from temporalio.client import Client


async def queue_validation():
    """Queue overnight validation workflow."""
    
    # Connect to orchestration namespace
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost")
    temporal_port = os.getenv("TEMPORAL_PORT", "7233")
    orchestration_namespace = os.getenv("TEMPORAL_ORCHESTRATION_NAMESPACE", "bpo-orchestration")
    
    client = await Client.connect(
        f"{temporal_host}:{temporal_port}",
        namespace=orchestration_namespace
    )
    
    # Start workflow
    from datetime import datetime
    workflow_id = f"validation-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    handle = await client.start_workflow(
        "OvernightValidationWorkflow",
        id=workflow_id,
        task_queue="orchestration-queue",
    )
    
    print(f"Overnight validation queued: {handle.id}")
    print(f"View progress at: http://localhost:8233")
    print(f"Namespace: {orchestration_namespace}")
    print(f"Task Queue: orchestration-queue")
    
    # Optionally wait for result
    # result = await handle.result()
    # print(f"Validation complete: {result.summary}")


if __name__ == "__main__":
    asyncio.run(queue_validation())

