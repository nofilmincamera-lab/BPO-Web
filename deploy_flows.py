#!/usr/bin/env python3
"""
Deploy Prefect flows to the Prefect server.
Run this after starting the Prefect server.
"""
import asyncio
import os
from prefect import flow
from prefect.client.orchestration import get_client
from src.flows.extraction_flow import extract_documents_flow

async def main():
    """Deploy the extraction flow to Prefect."""
    print("Deploying extraction flow to Prefect...")
    
    try:
        # Set Prefect API URL to connect to Docker server
        os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"
        
        # Create work pool first (one-time setup)
        async with get_client() as client:
            try:
                # Check if work pool exists
                work_pools = await client.read_work_pools()
                existing_pools = [wp.name for wp in work_pools]
                
                if "default-pool" not in existing_pools:
                    # Create work pool
                    from prefect.client.schemas.actions import WorkPoolCreate
                    work_pool = WorkPoolCreate(
                        name="default-pool",
                        type="docker",
                        description="Default work pool for BPO extraction tasks with GPU support"
                    )
                    await client.create_work_pool(work_pool)
                    print("Work pool 'default-pool' created")
                else:
                    print("Work pool 'default-pool' already exists")
                
                # Deploy the flow
                deployment = await extract_documents_flow.deploy(
                    name="default",
                    work_pool_name="default-pool",
                    description="Extract entities from documents using spaCy EntityRuler",
                    tags=["extraction", "ner", "production"],
                    version="1.0.0",
                    image="bpo-worker:latest"
                )
                
                print(f"Flow deployed successfully!")
                print(f"   Deployment ID: {deployment.id}")
                print(f"   Name: {deployment.name}")
                print(f"   Work Pool: {deployment.work_pool_name}")
                print(f"   Monitor at: http://localhost:4200")
                
            except Exception as e:
                print(f"Failed to create work pool or deploy flow: {e}")
                return 1
        
    except Exception as e:
        print(f"Failed to connect to Prefect server: {e}")
        print("Make sure the Prefect server is running: docker-compose --profile base up -d")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
