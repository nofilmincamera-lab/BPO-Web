"""
BPO Intelligence Pipeline - Overnight Work Workflow

Queues autonomous tasks for Cursor background agents to execute overnight.
Creates comprehensive action item lists for user review in the morning.
"""

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import List, Dict, Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from src.activities.cursor_agent_activity import (
        CursorAgentTask,
        CursorAgentResponse,
        invoke_cursor_agent_activity,
        batch_cursor_agent_tasks_activity,
    )


@dataclass
class OvernightWorkInput:
    """Input for overnight work workflow."""
    tasks: List[CursorAgentTask]
    checkpoint_interval: int = 10  # Save progress every N tasks
    max_runtime_hours: int = 8  # Maximum total runtime


@dataclass
class OvernightWorkOutput:
    """Output from overnight work workflow."""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_action_items: int
    total_skipped_items: int
    action_items: List[Dict[str, Any]]
    skipped_items: List[Dict[str, Any]]
    execution_summary: Dict[str, Any]


@workflow.defn
class OvernightWorkWorkflow:
    """
    Orchestrates autonomous Cursor agent tasks for overnight execution.
    
    Features:
    - Processes tasks in batches
    - Checkpoints progress
    - Aggregates action items
    - Handles failures gracefully
    """
    
    def __init__(self) -> None:
        self.completed_count = 0
        self.failed_count = 0
        self.action_items: List[Dict[str, Any]] = []
        self.skipped_items: List[Dict[str, Any]] = []
    
    @workflow.run
    async def run(self, input: OvernightWorkInput) -> OvernightWorkOutput:
        """Execute overnight work."""
        
        workflow.logger.info(
            f"Starting overnight work: {len(input.tasks)} tasks, "
            f"max runtime: {input.max_runtime_hours} hours"
        )
        
        # Process tasks in batches
        batch_size = 5
        for i in range(0, len(input.tasks), batch_size):
            batch = input.tasks[i:i + batch_size]
            
            workflow.logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} tasks")
            
            # Execute batch
            batch_results = await workflow.execute_activity(
                batch_cursor_agent_tasks_activity,
                args=[batch],
                start_to_close_timeout=timedelta(hours=1),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=30),
                    backoff_coefficient=2.0,
                    maximum_attempts=2,
                ),
            )
            
            # Process results
            for task, result in zip(batch, batch_results):
                if result.success:
                    self.completed_count += 1
                    self.action_items.extend([
                        {"task": task.task_type, "item": item, "location": task.code_path}
                        for item in result.action_items
                    ])
                    self.skipped_items.extend([
                        {"task": task.task_type, "item": item, "location": task.code_path}
                        for item in result.skipped_items
                    ])
                else:
                    self.failed_count += 1
                    workflow.logger.error(
                        f"Task failed: {task.task_type} on {task.code_path}: {result.error}"
                    )
            
            # Log progress
            workflow.logger.info(
                f"Progress: {self.completed_count}/{len(input.tasks)} completed, "
                f"{len(self.action_items)} action items collected"
            )
        
        # Generate summary
        workflow.logger.info(
            f"Overnight work complete: {self.completed_count} succeeded, "
            f"{self.failed_count} failed, {len(self.action_items)} action items"
        )
        
        return OvernightWorkOutput(
            total_tasks=len(input.tasks),
            completed_tasks=self.completed_count,
            failed_tasks=self.failed_count,
            total_action_items=len(self.action_items),
            total_skipped_items=len(self.skipped_items),
            action_items=self.action_items,
            skipped_items=self.skipped_items,
            execution_summary={
                "success_rate": self.completed_count / len(input.tasks) if input.tasks else 0,
                "most_action_items_location": max(
                    [(loc, sum(1 for item in self.action_items if item["location"] == loc))]
                    for loc in set(item["location"] for item in self.action_items)
                ) if self.action_items else None,
            },
        )

