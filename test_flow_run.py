#!/usr/bin/env python3
"""Test flow run by queuing a simple extraction."""
import asyncio
import os
from prefect.client.orchestration import get_client

async def main():
    """Queue a test flow run."""
    os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"
    
    async with get_client() as client:
        # Get deployments
        deployments = await client.read_deployments()
        print("Available deployments:")
        for dep in deployments:
            print(f"  - {dep.name} (ID: {dep.id})")
        
        if deployments:
            # Queue a flow run
            deployment = deployments[0]
            print(f"\nQueuing flow run for deployment: {deployment.name}")
            
            flow_run = await client.create_flow_run_from_deployment(
                deployment_id=deployment.id,
                parameters={
                    "source_path": "data/test_10.jsonl",
                    "heuristics_version": "2.0.0",
                    "batch_size": 5,
                    "start_offset": 0
                }
            )
            
            print(f"Flow run created: {flow_run.id}")
            print(f"Monitor at: http://localhost:4200/flow-runs/{flow_run.id}")
        else:
            print("No deployments found. Make sure the flow is being served.")

if __name__ == "__main__":
    asyncio.run(main())

