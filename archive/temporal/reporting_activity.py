"""
BPO Intelligence Pipeline - Reporting Activity

Generate markdown validation reports.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from temporalio import activity


@activity.defn
async def generate_markdown_report_activity(
    verification_results: List[Dict[str, Any]],
    code_review_result: Dict[str, Any],
    analytics: Dict[str, Any],
    validation_timestamp: str
) -> str:
    """
    Generate human-readable markdown validation report.
    
    Args:
        verification_results: Results from all verification activities
        code_review_result: Results from code review
        analytics: Heuristics performance analytics
        validation_timestamp: Timestamp of validation run
    
    Returns:
        Path to generated report file
    """
    
    report_dir = Path("docs")
    report_dir.mkdir(exist_ok=True)
    
    report_path = report_dir / f"VALIDATION_REPORT_{validation_timestamp}.md"
    
    # Generate report content
    report_lines = [
        "# BPO Intelligence Pipeline - Validation Report",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Validation Run**: {validation_timestamp}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"- **Status**: {'✅ PASS' if all(r.get('status') != 'fail' for r in verification_results) else '⚠️ ISSUES FOUND'}",
        f"- **Total Checks**: {len(verification_results)}",
        f"- **Passed**: {sum(1 for r in verification_results if r.get('status') == 'pass')}",
        f"- **Failed**: {sum(1 for r in verification_results if r.get('status') == 'fail')}",
        f"- **Warnings**: {sum(1 for r in verification_results if r.get('status') == 'warning')}",
        "",
        "---",
        "",
        "## 1. Container Verification",
        "",
    ]
    
    # Add container results
    for result in verification_results:
        if "container" in result.get("component", "").lower():
            status_icon = "✅" if result.get("status") == "pass" else "❌" if result.get("status") == "fail" else "⚠️"
            report_lines.extend([
                f"### {status_icon} {result.get('component')}",
                f"**Status**: {result.get('status')}",
                f"**Message**: {result.get('message')}",
                "",
            ])
    
    report_lines.extend([
        "---",
        "",
        "## 2. Package Verification",
        "",
    ])
    
    # Add package results
    for result in verification_results:
        if "package" in result.get("component", "").lower():
            status_icon = "✅" if result.get("status") == "pass" else "❌" if result.get("status") == "fail" else "⚠️"
            report_lines.extend([
                f"### {status_icon} {result.get('component')}",
                f"**Status**: {result.get('status')}",
                f"**Message**: {result.get('message')}",
                "",
            ])
    
    report_lines.extend([
        "---",
        "",
        "## 3. Code Review",
        "",
        f"**Critical Issues**: {len(code_review_result.get('critical_issues', []))}",
        f"**Warnings**: {len(code_review_result.get('warnings', []))}",
        "",
    ])
    
    if code_review_result.get('critical_issues'):
        report_lines.extend([
            "### Critical Issues",
            "",
        ])
        for issue in code_review_result['critical_issues']:
            report_lines.append(f"- ❌ {issue}")
        report_lines.append("")
    
    if code_review_result.get('warnings'):
        report_lines.extend([
            "### Warnings",
            "",
        ])
        for warning in code_review_result['warnings']:
            report_lines.append(f"- ⚠️ {warning}")
        report_lines.append("")
    
    report_lines.extend([
        "---",
        "",
        "## 4. Heuristics Performance",
        "",
        "### Extraction Summary",
        "",
        f"- **Total Documents Tested**: {analytics.get('extraction_summary', {}).get('total_documents', 0)}",
        f"- **Total Entities Extracted**: {analytics.get('extraction_summary', {}).get('total_entities', 0)}",
        f"- **Avg Entities per Doc**: {analytics.get('extraction_summary', {}).get('avg_entities_per_doc', 0):.2f}",
        "",
        "### Tier Usage",
        "",
    ])
    
    for tier, count in analytics.get('extraction_tier_breakdown', {}).items():
        report_lines.append(f"- **{tier}**: {count}")
    
    report_lines.extend([
        "",
        "### Entity Type Distribution",
        "",
    ])
    
    for entity_type, count in analytics.get('entity_type_breakdown', {}).items():
        report_lines.append(f"- **{entity_type}**: {count}")
    
    report_lines.extend([
        "",
        "### Performance Metrics",
        "",
        f"- **Heuristics Hit Rate**: {analytics.get('heuristics_hit_rate', 0):.2%}",
        f"- **High Confidence Rate**: {analytics.get('performance_metrics', {}).get('high_confidence_rate', 0):.2%}",
        "",
        "---",
        "",
        "## 5. Recommendations",
        "",
    ])
    
    # Add recommendations based on results
    if any(r.get('status') == 'fail' for r in verification_results):
        report_lines.append("- ❌ **Action Required**: Address failed verification checks")
    
    if analytics.get('heuristics_hit_rate', 0) < 0.5:
        report_lines.append("- ⚠️ **Heuristics Coverage**: Consider expanding heuristics database")
    
    if code_review_result.get('critical_issues'):
        report_lines.append("- ❌ **Code Review**: Fix critical issues identified")
    
    report_lines.extend([
        "",
        "---",
        "",
        "## Appendix",
        "",
        "### Raw Metrics",
        "",
        "```json",
        json.dumps({
            "verification": verification_results,
            "code_review": code_review_result,
            "analytics": analytics
        }, indent=2),
        "```",
        "",
    ])
    
    # Write report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    activity.logger.info(f"Validation report generated: {report_path}")
    
    return str(report_path)

