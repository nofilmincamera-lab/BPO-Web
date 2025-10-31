#!/usr/bin/env python3
"""
Queue overnight work for Cursor background agents.

Usage:
    python scripts/queue_overnight_work.py --task-type review --code-path src/worker/
"""

import argparse
import asyncio
import os
from typing import List

from temporalio.client import Client
from src.activities.cursor_agent_activity import CursorAgentTask
from src.workflows.overnight_work_workflow import OvernightWorkInput


async def queue_overnight_work():
    """Queue tasks for overnight execution."""
    
    # Connect to Temporal
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost")
    temporal_port = os.getenv("TEMPORAL_PORT", "7233")
    temporal_namespace = os.getenv("TEMPORAL_ORCHESTRATION_NAMESPACE", "bpo-orchestration")
    
    client = await Client.connect(f"{temporal_host}:{temporal_port}", namespace=temporal_namespace)
    
    # Define overnight tasks
    tasks = [
        CursorAgentTask(
            task_type="review",
            code_path="src/worker/",
            context={"focus": "error_handling", "priority": "high"},
            priority=1,
        ),
        CursorAgentTask(
            task_type="document",
            code_path="scripts/",
            context={"format": "markdown", "include_examples": True},
            priority=3,
        ),
        CursorAgentTask(
            task_type="test",
            code_path="src/activities/",
            context={"coverage_threshold": 0.8},
            priority=2,
        ),
    ]
    
    # Start workflow with unique ID
    from datetime import datetime
    workflow_id = f"overnight-work-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    handle = await client.start_workflow(
        "OvernightWorkWorkflow",
        args=[OvernightWorkInput(tasks=tasks)],
        id=workflow_id,
        task_queue="orchestration-queue",
    )
    
    print(f"Overnight work queued: {handle.id}")
    print(f"View progress at: http://localhost:8233")
    print(f"Tasks queued: {len(tasks)}")
    
    # Wait for completion
    result = await handle.result()
    
    print("\n" + "="*60)
    print("OVERNIGHT WORK COMPLETE")
    print("="*60)
    print(f"Completed: {result.completed_tasks}/{result.total_tasks}")
    print(f"Failed: {result.failed_tasks}")
    print(f"Action Items: {result.total_action_items}")
    print(f"Skipped Items: {result.total_skipped_items}")
    print("\nAction Items Summary:")
    for item in result.action_items[:10]:  # Show first 10
        print(f"  - {item['task']}: {item['item']} ({item['location']})")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(queue_overnight_work())

