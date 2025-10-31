#!/usr/bin/env python3
"""
Queue extraction workflow via Prefect API.
"""
import asyncio
import os
from prefect.deployments import run_deployment

async def main():
    """Queue extraction workflow."""
    # CANONICAL PRODUCTION DATASET - preprocessed from scripts/preprocess.py
    source_path = "data/processed/preprocessed.jsonl"
    heuristics_version = "2.0.0"
    batch_size = 100
    
    print(f"Queueing extraction workflow...")
    print(f"  Source: {source_path}")
    print(f"  Heuristics: {heuristics_version}")
    print(f"  Batch size: {batch_size}")
    
    try:
        # Run deployment
        flow_run = await run_deployment(
            name="document-extraction-pipeline/default",
            parameters={
                "source_path": source_path,
                "heuristics_version": heuristics_version,
                "batch_size": batch_size,
                "start_offset": 0
            },
            timeout=0  # Don't wait
        )
        
        print(f"✅ Flow run queued successfully!")
        print(f"   Flow Run ID: {flow_run.id}")
        print(f"   Flow Run Name: {flow_run.name}")
        print(f"   Monitor at: http://localhost:4200/flow-runs/flow-run/{flow_run.id}")
        
    except Exception as e:
        print(f"❌ Failed to queue flow run: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)