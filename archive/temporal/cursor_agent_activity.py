"""
BPO Intelligence Pipeline - Cursor Agent Integration Activity

This activity allows Temporal workflows to invoke Cursor background agents
for automated tasks like code review, documentation generation, and refactoring.
"""

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime

import httpx
from temporalio import activity
from temporalio.exceptions import ApplicationError


@dataclass
class CursorAgentTask:
    """Task definition for Cursor agent."""
    task_type: str  # "review", "document", "refactor", "test", "analyze"
    code_path: str
    context: Dict[str, Any]
    priority: int = 5  # 1=highest, 10=lowest
    max_timeout_minutes: int = 30


@dataclass
class CursorAgentResponse:
    """Response from Cursor agent."""
    success: bool
    result: Dict[str, Any]
    action_items: List[str]  # Items needing user configuration
    skipped_items: List[str]  # Items skipped (user input needed)
    execution_time_seconds: float
    error: Optional[str] = None


@activity.defn
async def invoke_cursor_agent_activity(task: CursorAgentTask) -> CursorAgentResponse:
    """
    Invoke Cursor background agent to perform automated task.
    
    Background Agent Instructions:
    - Skip any user-needed information (passwords, API keys, approvals)
    - Make a list for any needed user configuration
    - Work autonomously on everything else
    - Report completion status and action items
    """
    start_time = datetime.now()
    
    try:
        # Check if Cursor agent is available
        cursor_agent_url = os.getenv("CURSOR_AGENT_URL", "http://localhost:8080")
        
        # Prepare task payload
        payload = {
            "task_type": task.task_type,
            "code_path": task.code_path,
            "context": task.context,
            "priority": task.priority,
            "instructions": get_background_agent_instructions(),
        }
        
        # Make async HTTP request to Cursor agent
        async with httpx.AsyncClient(timeout=task.max_timeout_minutes * 60) as client:
            response = await client.post(
                f"{cursor_agent_url}/api/tasks",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                activity.logger.info(
                    f"Cursor agent task completed: {task.task_type} on {task.code_path}"
                )
                
                return CursorAgentResponse(
                    success=True,
                    result=result.get("result", {}),
                    action_items=result.get("action_items", []),
                    skipped_items=result.get("skipped_items", []),
                    execution_time_seconds=execution_time,
                )
            else:
                error_msg = f"Cursor agent returned status {response.status_code}: {response.text}"
                activity.logger.error(error_msg)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return CursorAgentResponse(
                    success=False,
                    result={},
                    action_items=[],
                    skipped_items=[],
                    execution_time_seconds=execution_time,
                    error=error_msg,
                )
    
    except httpx.TimeoutException as e:
        activity.logger.error(f"Cursor agent request timed out: {e}")
        raise  # Temporal will retry based on activity retry policy
    
    except httpx.RequestError as e:
        activity.logger.error(f"Cursor agent request failed: {e}")
        raise  # Transient error - Temporal will retry
    
    except Exception as e:
        activity.logger.error(f"Unexpected error invoking Cursor agent: {e}")
        raise ApplicationError(f"Unexpected error: {e}", non_retryable=True)


def get_background_agent_instructions() -> str:
    """
    Get instructions for Cursor background agents.
    
    These instructions ensure agents work autonomously while marking
    items that need user input.
    """
    return """
# Background Agent Instructions for Overnight Work

## Primary Objectives:
1. Complete all autonomous tasks (code analysis, refactoring, testing)
2. Skip any items requiring user input (passwords, approvals, API keys)
3. Generate comprehensive action item lists for user review

## Workflow:
1. **Analyze** the task and context
2. **Identify** user-needed items and skip them
3. **Execute** all autonomous tasks
4. **Document** action items in results
5. **Report** completion status

## Skip These Items (User Needed):
- 🔐 Authentication credentials (passwords, API keys, tokens)
- ✅ Approval workflows (merges, deployments)
- 🔑 Secret management (env vars, vault access)
- 📝 User-specific configuration (personal email, preferences)
- 💰 Cost-sensitive operations (cloud resource creation > $100)

## Action Item Format:
For each skipped item, include:
- **Type**: What kind of user input is needed
- **Location**: Where this needs to be configured
- **Reason**: Why user input is required
- **Estimated Impact**: Low/Medium/High

## Success Criteria:
- ✅ All autonomous tasks completed
- 📋 Action items clearly documented
- ⏭️ User-needed items properly skipped
- 📊 Results formatted for easy review

## Error Handling:
- If unsure whether something needs user input, ASK (add to action items)
- Log all skipped items with reasons
- Complete partial work rather than failing entirely
- Return clear error messages if critical blockers exist
"""


@activity.defn
async def batch_cursor_agent_tasks_activity(
    tasks: List[CursorAgentTask]
) -> List[CursorAgentResponse]:
    """
    Execute multiple Cursor agent tasks in parallel.
    
    Useful for overnight batch processing.
    """
    activity.logger.info(f"Starting batch of {len(tasks)} Cursor agent tasks")
    
    # Execute tasks concurrently (but respect resource limits)
    semaphore = asyncio.Semaphore(3)  # Max 3 concurrent agent tasks
    
    async def execute_with_limit(task: CursorAgentTask) -> CursorAgentResponse:
        async with semaphore:
            # Heartbeat for long-running batches
            activity.heartbeat(f"Processing {task.task_type} on {task.code_path}")
            return await invoke_cursor_agent_activity(task)
    
    # Run all tasks concurrently
    results = await asyncio.gather(
        *[execute_with_limit(task) for task in tasks],
        return_exceptions=True
    )
    
    # Process results
    agent_responses = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            activity.logger.error(f"Task {i} failed: {result}")
            agent_responses.append(CursorAgentResponse(
                success=False,
                result={},
                action_items=[],
                skipped_items=[],
                execution_time_seconds=0,
                error=str(result),
            ))
        else:
            agent_responses.append(result)
    
    # Summarize batch results
    successful = sum(1 for r in agent_responses if r.success)
    total_action_items = sum(len(r.action_items) for r in agent_responses)
    total_skipped = sum(len(r.skipped_items) for r in agent_responses)
    
    activity.logger.info(
        f"Batch complete: {successful}/{len(tasks)} successful, "
        f"{total_action_items} action items, {total_skipped} skipped items"
    )
    
    return agent_responses

