"""
BPO Intelligence Pipeline - Temporal Workflow for Document Processing

This workflow orchestrates the complete NER extraction pipeline with:
- Checkpointing every 1000 documents
- Heartbeats every 100 documents
- Continue-as-new at 5000 documents
- Three-tier error handling
- Async database access with asyncpg
"""

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import List, Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities (with sandbox pass-through)
with workflow.unsafe.imports_passed_through():
    from src.activities.extraction_activities import (
        load_checkpoint_activity,
        save_checkpoint_activity,
        extract_entities_batch_activity,
        store_entities_activity,
        ExtractBatchInput,
        ExtractBatchOutput,
    )


@dataclass
class ProcessDocumentsInput:
    """Input for the document processing workflow."""
    source_path: str
    heuristics_version: str
    embedding_model: str
    start_offset: int = 0
    batch_size: int = 1000
    continue_as_new_threshold: int = 5000


@dataclass
class ProcessDocumentsOutput:
    """Output from the document processing workflow."""
    total_processed: int
    total_entities: int
    total_relationships: int
    failed_documents: List[str]


@workflow.defn
class ProcessDocumentsWorkflow:
    """
    Main workflow for processing documents through the NER pipeline.
    
    Features:
    - Processes documents in batches
    - Checkpoints progress every 1000 documents
    - Heartbeats every 100 documents
    - Continue-as-new when reaching threshold
    - Resilient error handling
    """
    
    def __init__(self) -> None:
        self.processed_count = 0
        self.entity_count = 0
        self.relationship_count = 0
        self.failed_docs: List[str] = []
    
    @workflow.run
    async def run(self, input: ProcessDocumentsInput) -> ProcessDocumentsOutput:
        """Execute the document processing workflow."""
        
        workflow.logger.info(
            f"Starting ProcessDocumentsWorkflow",
            extra={
                "source_path": input.source_path,
                "start_offset": input.start_offset,
                "batch_size": input.batch_size,
            }
        )
        
        # Load checkpoint if resuming
        checkpoint = await workflow.execute_activity(
            load_checkpoint_activity,
            args=[workflow.info().workflow_id, workflow.info().run_id, "extraction"],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                backoff_coefficient=2.0,
                maximum_attempts=3,
            ),
        )
        
        current_offset = checkpoint.get("doc_offset", input.start_offset)
        workflow.logger.info(f"Resuming from offset: {current_offset}")
        
        # Process documents in batches
        while True:
            # Check if we should continue-as-new
            if self.processed_count >= input.continue_as_new_threshold:
                workflow.logger.info(
                    f"Reached continue-as-new threshold: {input.continue_as_new_threshold}"
                )
                # Create new input with updated offset
                new_input = ProcessDocumentsInput(
                    source_path=input.source_path,
                    heuristics_version=input.heuristics_version,
                    embedding_model=input.embedding_model,
                    start_offset=current_offset,
                    batch_size=input.batch_size,
                    continue_as_new_threshold=input.continue_as_new_threshold,
                )
                # Continue as new workflow
                await workflow.continue_as_new(args=[new_input])
            
            # Extract entities for current batch
            batch_input = ExtractBatchInput(
                source_path=input.source_path,
                offset=current_offset,
                batch_size=input.batch_size,
                heuristics_version=input.heuristics_version,
                embedding_model=input.embedding_model,
            )
            
            try:
                # Execute extraction activity with retry and timeout
                batch_result = await workflow.execute_activity(
                    extract_entities_batch_activity,
                    args=[batch_input],
                    start_to_close_timeout=timedelta(minutes=30),
                    heartbeat_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(
                        initial_interval=timedelta(seconds=1),
                        backoff_coefficient=2.0,
                        maximum_interval=timedelta(minutes=1),
                        maximum_attempts=3,
                        non_retryable_error_types=[
                            "ValueError",
                            "DataIntegrityError",
                        ],
                    ),
                )
                
                # Check if we've reached end of data
                if batch_result.doc_count == 0:
                    workflow.logger.info("No more documents to process")
                    break
                
                # Store extracted entities in database
                await workflow.execute_activity(
                    store_entities_activity,
                    args=[batch_result],
                    start_to_close_timeout=timedelta(minutes=10),
                    heartbeat_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(
                        initial_interval=timedelta(seconds=1),
                        backoff_coefficient=2.0,
                        maximum_attempts=5,
                    ),
                )
                
                # Update counters
                self.processed_count += batch_result.doc_count
                self.entity_count += batch_result.entity_count
                self.relationship_count += batch_result.relationship_count
                self.failed_docs.extend(batch_result.failed_docs)
                
                # Update offset for next batch
                current_offset += batch_result.doc_count
                
                # Save checkpoint every 1000 documents
                if self.processed_count % 1000 == 0:
                    await workflow.execute_activity(
                        save_checkpoint_activity,
                        args=[
                            workflow.info().workflow_id,
                            workflow.info().run_id,
                            "extraction",
                            current_offset,
                            {
                                "processed": self.processed_count,
                                "entities": self.entity_count,
                                "relationships": self.relationship_count,
                            }
                        ],
                        start_to_close_timeout=timedelta(seconds=30),
                        retry_policy=RetryPolicy(
                            initial_interval=timedelta(seconds=1),
                            maximum_attempts=3,
                        ),
                    )
                    workflow.logger.info(f"Checkpoint saved at offset: {current_offset}")
                
                workflow.logger.info(
                    f"Batch processed: {batch_result.doc_count} docs, "
                    f"{batch_result.entity_count} entities, "
                    f"{batch_result.relationship_count} relationships"
                )
                
            except Exception as e:
                workflow.logger.error(
                    f"Error processing batch at offset {current_offset}: {str(e)}"
                )
                # Depending on error type, we may want to skip this batch or fail
                # For now, we'll continue to next batch
                current_offset += input.batch_size
                continue
        
        # Final checkpoint
        await workflow.execute_activity(
            save_checkpoint_activity,
            args=[
                workflow.info().workflow_id,
                workflow.info().run_id,
                "extraction",
                current_offset,
                {
                    "processed": self.processed_count,
                    "entities": self.entity_count,
                    "relationships": self.relationship_count,
                    "status": "completed",
                }
            ],
            start_to_close_timeout=timedelta(seconds=30),
        )
        
        workflow.logger.info(
            f"Workflow completed: {self.processed_count} documents processed, "
            f"{self.entity_count} entities, {self.relationship_count} relationships, "
            f"{len(self.failed_docs)} failures"
        )
        
        return ProcessDocumentsOutput(
            total_processed=self.processed_count,
            total_entities=self.entity_count,
            total_relationships=self.relationship_count,
            failed_documents=self.failed_docs,
        )

