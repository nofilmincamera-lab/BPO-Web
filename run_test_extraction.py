#!/usr/bin/env python3
"""Run a test extraction using the deployed flow."""
import asyncio
import os
from prefect.client.orchestration import get_client

async def main():
    """Run test extraction."""
    os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"
    
    async with get_client() as client:
        # Get the deployment
        deployments = await client.read_deployments()
        if not deployments:
            print("No deployments found!")
            return 1
        
        deployment = deployments[0]
        print(f"Using deployment: {deployment.name}")
        
        # Create a flow run
        print("Creating flow run...")
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
        
        # Wait for completion
        print("Waiting for completion...")
        while True:
            run = await client.read_flow_run(flow_run.id)
            print(f"Status: {run.state.type}")
            if run.state.type in ["COMPLETED", "FAILED", "CANCELLED"]:
                break
            await asyncio.sleep(5)
        
        print(f"Final status: {run.state.type}")
        if run.state.type == "COMPLETED":
            print("✅ Extraction completed successfully!")
        else:
            print(f"❌ Extraction failed: {run.state.message}")

if __name__ == "__main__":
    asyncio.run(main())

