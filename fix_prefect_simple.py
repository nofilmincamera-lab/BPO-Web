#!/usr/bin/env python3
"""
Simple fix for Prefect UI - register flows and create deployments.
"""
import asyncio
import os
from prefect import flow, task
from prefect.client.orchestration import get_client
from src.flows.extraction_flow import extract_documents_flow

@task
def hello_task(name: str = "world"):
    """A simple task."""
    return f"Hello {name}!"

@flow
def hello_flow(name: str = "world"):
    """A simple flow."""
    result = hello_task(name)
    print(result)
    return result

async def main():
    """Fix Prefect UI by ensuring flows are properly registered."""
    print("Fixing Prefect UI...")
    
    # Set Prefect API URL to connect to Docker server
    os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"
    
    try:
        async with get_client() as client:
            # Test connection
            health = await client.api_healthcheck()
            print(f"Connected to Prefect server: {health}")
            
            # Check existing flows
            flows = await client.read_flows()
            print(f"Existing flows: {len(flows)}")
            
            # Check existing deployments
            deployments = await client.read_deployments()
            print(f"Existing deployments: {len(deployments)}")
            
            # Create a simple flow if none exist
            if len(flows) == 0:
                print("Creating simple flow...")
                deployment = await hello_flow.to_deployment(
                    name="hello-flow",
                    work_pool_name="default-pool",
                    description="A simple hello world flow",
                    tags=["test", "hello"],
                    version="1.0.0"
                )
                await deployment.apply()
                print("Simple flow created")
            
            # Create extraction flow deployment
            print("Creating extraction flow deployment...")
            deployment = await extract_documents_flow.to_deployment(
                name="document-extraction",
                work_pool_name="default-pool",
                description="Extract entities from documents using spaCy EntityRuler",
                tags=["extraction", "ner", "production"],
                version="1.0.0"
            )
            await deployment.apply()
            print("Extraction flow deployment created")
            
            # Final verification
            flows = await client.read_flows()
            deployments = await client.read_deployments()
            
            print(f"\nSUCCESS!")
            print(f"Total flows: {len(flows)}")
            print(f"Total deployments: {len(deployments)}")
            print(f"Prefect UI: http://localhost:4200")
            print(f"Available deployments:")
            for dep in deployments:
                print(f"   - {dep.name} (ID: {dep.id})")
            
            print(f"\nPrefect is now fully operational!")
            print(f"You can now:")
            print(f"   1. Open http://localhost:4200 in your browser")
            print(f"   2. Go to 'Deployments' tab")
            print(f"   3. Click 'Run' on any deployment")
            print(f"   4. Monitor execution in 'Flow Runs' tab")
        
    except Exception as e:
        print(f"Failed to fix Prefect: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

