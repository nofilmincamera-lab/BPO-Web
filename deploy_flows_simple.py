#!/usr/bin/env python3
"""
Deploy Prefect flows using the Prefect client API directly.
"""
import asyncio
import os
from prefect.client.orchestration import get_client
from src.flows.extraction_flow import extract_documents_flow

async def main():
    """Deploy the extraction flow to Prefect."""
    print("Deploying extraction flow to Prefect...")
    
    # Set the API URL
    os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"
    
    try:
        async with get_client() as client:
            # Create work pool first
            try:
                await client.create_work_pool(
                    name="default-pool",
                    type="process",  # Using process instead of docker due to Windows limitations
                    description="Default process work pool for extraction"
                )
                print("Work pool 'default-pool' created")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("Work pool 'default-pool' already exists")
                else:
                    print(f"Work pool creation failed: {e}")
            
            # Deploy the flow
            deployment = await extract_documents_flow.deploy(
                name="default",
                work_pool_name="default-pool",
                description="Extract entities from documents using spaCy EntityRuler",
                tags=["extraction", "ner", "production"],
                version="1.0.0"
            )
            
            print(f"Flow deployed successfully!")
            print(f"   Deployment ID: {deployment.id}")
            print(f"   Name: {deployment.name}")
            print(f"   Work Pool: {deployment.work_pool_name}")
            print(f"   Monitor at: http://localhost:4200")
            
    except Exception as e:
        print(f"Failed to deploy flow: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
