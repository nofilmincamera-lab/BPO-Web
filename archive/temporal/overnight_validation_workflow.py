"""
BPO Intelligence Pipeline - Overnight Validation Workflow

Comprehensive overnight validation and testing workflow.
"""

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, Any, List

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from datetime import datetime
    from src.activities.validation_activities import (
        verify_docker_containers_activity,
        verify_python_packages_activity,
        verify_heuristics_files_activity,
        verify_database_schema_activity,
        wait_until_time_activity,
    )
    from src.activities.code_review_activity import full_code_review_activity
    from src.activities.preprocessing_activity import preprocess_sample_activity
    from src.activities.batch_test_activity import run_batch_extraction_activity
    from src.activities.analytics_activity import analyze_heuristics_performance_activity
    from src.activities.reporting_activity import generate_markdown_report_activity
    from src.activities.cleanup_activity import cleanup_test_files_activity, update_memory_md_activity


@dataclass
class OvernightValidationOutput:
    """Output from overnight validation workflow."""
    validation_timestamp: str
    verification_results: List[Dict[str, Any]]
    code_review_results: Dict[str, Any]
    analytics_results: Dict[str, Any]
    report_path: str
    summary: Dict[str, Any]


@workflow.defn
class OvernightValidationWorkflow:
    """
    Orchestrates comprehensive overnight validation.
    
    Phases:
    1. Verification (containers, packages, heuristics, database)
    2. Wait until 4:30 AM
    3. Code review
    4. Batch test (preprocess + extract 1000 records)
    5. Analytics
    6. Reporting and cleanup
    """
    
    @workflow.run
    async def run(self) -> OvernightValidationOutput:
        """Execute overnight validation workflow."""
        
        # Use workflow.now() for deterministic timestamp
        validation_timestamp = workflow.now().strftime("%Y%m%dT%H%M%S")
        
        workflow.logger.info(f"Starting overnight validation: {validation_timestamp}")
        
        # Phase 1: Verification
        workflow.logger.info("Phase 1: Verification")
        
        verification_results = []
        
        # Verify containers
        container_results = await workflow.execute_activity(
            verify_docker_containers_activity,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )
        verification_results.extend([
            {
                "component": r.component,
                "status": r.status,
                "message": r.message,
                "details": r.details
            }
            for r in container_results
        ])
        
        # Verify packages
        package_results = await workflow.execute_activity(
            verify_python_packages_activity,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )
        verification_results.extend([
            {
                "component": r.component,
                "status": r.status,
                "message": r.message,
                "details": r.details
            }
            for r in package_results
        ])
        
        # Verify heuristics
        heuristics_results = await workflow.execute_activity(
            verify_heuristics_files_activity,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )
        verification_results.extend([
            {
                "component": r.component,
                "status": r.status,
                "message": r.message,
                "details": r.details
            }
            for r in heuristics_results
        ])
        
        # Verify database schema
        schema_results = await workflow.execute_activity(
            verify_database_schema_activity,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )
        verification_results.extend([
            {
                "component": r.component,
                "status": r.status,
                "message": r.message,
                "details": r.details
            }
            for r in schema_results
        ])
        
        # Log verification summary
        passed = sum(1 for r in verification_results if r.get('status') == 'pass')
        failed = sum(1 for r in verification_results if r.get('status') == 'fail')
        workflow.logger.info(f"Verification complete: {passed} passed, {failed} failed")
        
        # Phase 2: Wait until 4:30 AM
        workflow.logger.info("Phase 2: Waiting until 4:30 AM")
        
        await workflow.execute_activity(
            wait_until_time_activity,
            args=[4, 30],
            start_to_close_timeout=timedelta(hours=12),  # Long timeout for overnight wait
            heartbeat_timeout=timedelta(minutes=10),
        )
        
        workflow.logger.info("Target time reached: 4:30 AM")
        
        # Phase 3: Code Review
        workflow.logger.info("Phase 3: Code Review")
        
        code_review_result = await workflow.execute_activity(
            full_code_review_activity,
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )
        
        workflow.logger.info(
            f"Code review complete: {len(code_review_result.critical_issues)} critical issues, "
            f"{len(code_review_result.warnings)} warnings"
        )
        
        # Phase 4: Batch Test
        workflow.logger.info("Phase 4: Batch Test")
        
        # Preprocess sample
        preprocess_result = await workflow.execute_activity(
            preprocess_sample_activity,
            args=[
                "data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310 (1).json",
                "data/processed/test_batch_1000.jsonl",
                1000
            ],
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )
        
        workflow.logger.info(f"Preprocessed {preprocess_result['processed']} records")
        
        # Run batch extraction
        batch_metrics = await workflow.execute_activity(
            run_batch_extraction_activity,
            args=["data/processed/test_batch_1000.jsonl"],
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )
        
        workflow.logger.info(
            f"Batch extraction complete: {batch_metrics['total_documents']} docs, "
            f"{sum(batch_metrics['entity_types'].values())} entities"
        )
        
        # Phase 5: Analytics
        workflow.logger.info("Phase 5: Analytics")
        
        analytics_result = await workflow.execute_activity(
            analyze_heuristics_performance_activity,
            args=[batch_metrics],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )
        
        workflow.logger.info("Analytics generated")
        
        # Phase 6: Reporting and Cleanup
        workflow.logger.info("Phase 6: Reporting and Cleanup")
        
        # Generate report
        report_path = await workflow.execute_activity(
            generate_markdown_report_activity,
            args=[
                verification_results,
                {
                    "action_items": code_review_result.action_items,
                    "critical_issues": code_review_result.critical_issues,
                    "warnings": code_review_result.warnings,
                    "completion_message": code_review_result.completion_message,
                },
                analytics_result,
                validation_timestamp
            ],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )
        
        workflow.logger.info(f"Report generated: {report_path}")
        
        # Cleanup test files
        cleanup_stats = await workflow.execute_activity(
            cleanup_test_files_activity,
            args=[["data/processed/test_batch_1000.jsonl"]],
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )
        
        workflow.logger.info(f"Cleanup complete: {cleanup_stats['files_removed']} files removed")
        
        # Update MEMORY.md
        await workflow.execute_activity(
            update_memory_md_activity,
            args=[
                validation_timestamp,
                {
                    "all_checks_passed": failed == 0,
                    "documents_tested": batch_metrics['total_documents'],
                    "heuristics_hit_rate": analytics_result.get('heuristics_hit_rate', 0),
                }
            ],
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )
        
        workflow.logger.info("MEMORY.md updated")
        
        # Generate summary
        summary = {
            "validation_timestamp": validation_timestamp,
            "verification": {
                "total_checks": len(verification_results),
                "passed": passed,
                "failed": failed,
            },
            "code_review": {
                "critical_issues": len(code_review_result.critical_issues),
                "warnings": len(code_review_result.warnings),
            },
            "batch_test": {
                "documents": batch_metrics['total_documents'],
                "entities": sum(batch_metrics['entity_types'].values()),
            },
            "analytics": {
                "heuristics_hit_rate": analytics_result.get('heuristics_hit_rate', 0),
            },
            "report_path": report_path,
        }
        
        workflow.logger.info(f"Overnight validation complete: {validation_timestamp}")
        
        return OvernightValidationOutput(
            validation_timestamp=validation_timestamp,
            verification_results=verification_results,
            code_review_results={
                "action_items": code_review_result.action_items,
                "critical_issues": code_review_result.critical_issues,
                "warnings": code_review_result.warnings,
            },
            analytics_results=analytics_result,
            report_path=report_path,
            summary=summary,
        )

