#!/usr/bin/env python3
"""
Create a simple flow to test Prefect UI.
"""
import asyncio
import os
from prefect import flow, task
from prefect.client.orchestration import get_client

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
    """Create and register a simple flow."""
    print("Creating simple flow...")
    
    # Set Prefect API URL to connect to Docker server
    os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"
    
    try:
        async with get_client() as client:
            # Create deployment
            deployment = await hello_flow.to_deployment(
                name="hello-flow",
                work_pool_name="default-pool",
                description="A simple hello world flow",
                tags=["test", "hello"],
                version="1.0.0"
            )
            
            # Apply the deployment
            await deployment.apply()
            print("Simple flow deployed successfully!")
            
            # Check flows
            flows = await client.read_flows()
            print(f"Total flows: {len(flows)}")
            for flow in flows:
                print(f"  - {flow.name} (ID: {flow.id})")
            
            # Check deployments
            deployments = await client.read_deployments()
            print(f"Total deployments: {len(deployments)}")
            for dep in deployments:
                print(f"  - {dep.name} (ID: {dep.id})")
        
    except Exception as e:
        print(f"Failed to create flow: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

