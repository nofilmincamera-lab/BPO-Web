"""
BPO Intelligence Pipeline - Code Review Activity

Comprehensive code review for operational readiness.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Any

from temporalio import activity

from src.activities.cursor_agent_activity import (
    CursorAgentTask,
    invoke_cursor_agent_activity,
)


@dataclass
class CodeReviewResult:
    """Result of code review."""
    action_items: List[Dict[str, Any]]
    critical_issues: List[str]
    warnings: List[str]
    completion_message: str


@activity.defn
async def full_code_review_activity() -> CodeReviewResult:
    """
    Perform comprehensive code review for operational readiness.
    
    Focus areas:
    - Missing dependencies
    - Incomplete migrations
    - TODO items
    - Configuration issues
    - Operational gaps
    """
    
    # Create Cursor agent task for code review
    review_task = CursorAgentTask(
        task_type="review",
        code_path=".",
        context={
            "focus": "operational_readiness",
            "check_list": [
                "Missing dependencies in requirements.txt",
                "Incomplete Alembic migrations",
                "TODO/FIXME comments",
                "Configuration missing from .env",
                "Container health issues",
                "Missing error handling",
                "Incomplete documentation",
            ],
            "priority": "critical"
        },
        priority=1,
    )
    
    try:
        # Invoke Cursor agent for review
        result = await invoke_cursor_agent_activity(review_task)
        
        if result.success:
            # Process action items
            critical_issues = []
            warnings = []
            
            for item in result.action_items:
                if "critical" in item.lower() or "error" in item.lower():
                    critical_issues.append(item)
                else:
                    warnings.append(item)
            
            return CodeReviewResult(
                action_items=result.action_items,
                critical_issues=critical_issues,
                warnings=warnings,
                completion_message=f"Code review complete: {len(critical_issues)} critical, {len(warnings)} warnings"
            )
        else:
            activity.logger.error(f"Code review failed: {result.error}")
            return CodeReviewResult(
                action_items=[],
                critical_issues=[f"Code review failed: {result.error}"],
                warnings=[],
                completion_message="Code review could not be completed"
            )
    
    except Exception as e:
        activity.logger.error(f"Error during code review: {e}")
        return CodeReviewResult(
            action_items=[],
            critical_issues=[f"Error: {str(e)}"],
            warnings=[],
            completion_message=f"Code review encountered error: {e}"
        )

