from __future__ import annotations
"""
BPO Intelligence Pipeline - Cleanup Activity

Clean up temporary files and update documentation.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from temporalio import activity


@activity.defn
async def cleanup_test_files_activity(
    test_files: List[str],
    keep_last_n_reports: int = 5
) -> Dict[str, Any]:
    """
    Clean up temporary test files and old validation reports.
    
    Args:
        test_files: List of test file paths to remove
        keep_last_n_reports: Number of recent reports to keep
    
    Returns:
        Cleanup statistics
    """
    
    cleanup_stats = {
        "files_removed": 0,
        "files_kept": 0,
        "reports_removed": 0,
        "reports_kept": 0,
    }
    
    # Remove test files
    for file_path in test_files:
        path = Path(file_path)
        if path.exists():
            try:
                path.unlink()
                cleanup_stats["files_removed"] += 1
                activity.logger.info(f"Removed test file: {file_path}")
            except Exception as e:
                activity.logger.warning(f"Failed to remove {file_path}: {e}")
        else:
            cleanup_stats["files_kept"] += 1
    
    # Clean up old validation reports
    docs_dir = Path("docs")
    if docs_dir.exists():
        # Find all validation reports
        validation_reports = sorted(
            docs_dir.glob("VALIDATION_REPORT_*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # Keep only the most recent N reports
        reports_to_keep = validation_reports[:keep_last_n_reports]
        reports_to_remove = validation_reports[keep_last_n_reports:]
        
        for report in reports_to_remove:
            try:
                report.unlink()
                cleanup_stats["reports_removed"] += 1
                activity.logger.info(f"Removed old report: {report.name}")
            except Exception as e:
                activity.logger.warning(f"Failed to remove {report}: {e}")
        
        cleanup_stats["reports_kept"] = len(reports_to_keep)
    
    activity.logger.info(
        f"Cleanup complete: {cleanup_stats['files_removed']} files removed, "
        f"{cleanup_stats['reports_removed']} old reports removed"
    )
    
    return cleanup_stats


@activity.defn
async def update_memory_md_activity(
    validation_timestamp: str,
    summary_stats: Dict[str, Any]
) -> None:
    """
    Update MEMORY.md with validation results.
    
    Args:
        validation_timestamp: Timestamp of validation run
        summary_stats: Summary statistics from validation
    """
    
    memory_path = Path("MEMORY.md")
    
    if not memory_path.exists():
        activity.logger.warning("MEMORY.md not found, skipping update")
        return
    
    # Read current content
    with open(memory_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add validation section if not present
    if "## Validation History" not in content:
        validation_section = f"""

## Validation History

**Last Validation**: {validation_timestamp}
- Status: {'✅ PASS' if summary_stats.get('all_checks_passed') else '⚠️ ISSUES'}
- Documents Tested: {summary_stats.get('documents_tested', 0)}
- Heuristics Hit Rate: {summary_stats.get('heuristics_hit_rate', 0):.2%}
"""
        content += validation_section
    else:
        # Update existing validation section
        import re
        pattern = r"(\*\*Last Validation\*\*: )\d{8}T\d{6}"
        replacement = f"\\g<1>{validation_timestamp}"
        content = re.sub(pattern, replacement, content)
    
    # Write updated content
    with open(memory_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    activity.logger.info(f"Updated MEMORY.md with validation timestamp: {validation_timestamp}")

