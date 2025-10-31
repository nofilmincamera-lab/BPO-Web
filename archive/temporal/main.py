"""Temporal worker for BPO Intelligence Pipeline with dual namespace support."""
import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker

async def run_extraction_worker(client: Client, namespace: str, task_queue: str):
    """Run extraction worker for NER/taxonomy processing."""
    from src.workflows.process_documents_workflow import ProcessDocumentsWorkflow
    from src.activities.extraction_activities import (
        load_checkpoint_activity,
        save_checkpoint_activity,
        extract_entities_batch_activity,
        store_entities_activity,
    )
    
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[ProcessDocumentsWorkflow],
        activities=[
            load_checkpoint_activity,
            save_checkpoint_activity,
            extract_entities_batch_activity,
            store_entities_activity,
        ],
    )
    
    print(f"Extraction worker started: namespace={namespace}, queue={task_queue}")
    await worker.run()


async def run_orchestration_worker(client: Client, namespace: str, task_queue: str):
    """Run orchestration worker for Cursor agent tasks and validation."""
    from src.workflows.overnight_work_workflow import OvernightWorkWorkflow
    from src.workflows.overnight_validation_workflow import OvernightValidationWorkflow
    from src.activities.cursor_agent_activity import (
        invoke_cursor_agent_activity,
        batch_cursor_agent_tasks_activity,
    )
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
    
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[OvernightWorkWorkflow, OvernightValidationWorkflow],
        activities=[
            invoke_cursor_agent_activity,
            batch_cursor_agent_tasks_activity,
            verify_docker_containers_activity,
            verify_python_packages_activity,
            verify_heuristics_files_activity,
            verify_database_schema_activity,
            wait_until_time_activity,
            full_code_review_activity,
            preprocess_sample_activity,
            run_batch_extraction_activity,
            analyze_heuristics_performance_activity,
            generate_markdown_report_activity,
            cleanup_test_files_activity,
            update_memory_md_activity,
        ],
    )
    
    print(f"Orchestration worker started: namespace={namespace}, queue={task_queue}")
    await worker.run()


async def main():
    """Run dual Temporal workers for extraction and orchestration."""
    # Get configuration
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost")
    temporal_port = os.getenv("TEMPORAL_PORT", "7233")
    disable_extraction = os.getenv("DISABLE_EXTRACTION_WORKER", "0") in {"1", "true", "True"}
    
    # Extraction namespace config
    extraction_namespace = os.getenv("TEMPORAL_EXTRACTION_NAMESPACE", "bpo-extraction")
    extraction_queue = os.getenv("TEMPORAL_EXTRACTION_QUEUE", "extraction-queue")
    
    # Orchestration namespace config
    orchestration_namespace = os.getenv("TEMPORAL_ORCHESTRATION_NAMESPACE", "bpo-orchestration")
    orchestration_queue = os.getenv("TEMPORAL_ORCHESTRATION_QUEUE", "orchestration-queue")
    
    # Connect to both namespaces
    extraction_client = await Client.connect(
        f"{temporal_host}:{temporal_port}",
        namespace=extraction_namespace
    )
    
    orchestration_client = await Client.connect(
        f"{temporal_host}:{temporal_port}",
        namespace=orchestration_namespace
    )
    
    print("Starting dual worker processes...")
    print(f"Extraction: {extraction_namespace}/{extraction_queue}")
    print(f"Orchestration: {orchestration_namespace}/{orchestration_queue}")
    
    # Run workers concurrently (allow disabling extraction worker)
    tasks = []
    if not disable_extraction:
        tasks.append(run_extraction_worker(extraction_client, extraction_namespace, extraction_queue))
    else:
        print("Extraction worker disabled via DISABLE_EXTRACTION_WORKER=1")
    tasks.append(run_orchestration_worker(orchestration_client, orchestration_namespace, orchestration_queue))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())

