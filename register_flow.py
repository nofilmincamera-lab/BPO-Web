#!/usr/bin/env python3
"""
Register the flow directly with Prefect server.
"""
import asyncio
import os
from prefect.client.orchestration import get_client
from src.flows.extraction_flow import extract_documents_flow

async def main():
    """Register the flow directly."""
    print("Registering flow...")
    
    # Set Prefect API URL to connect to Docker server
    os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"
    
    try:
        async with get_client() as client:
            # Register the flow
            flow_id = await extract_documents_flow.register()
            print(f"Flow registered with ID: {flow_id}")
            
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
        print(f"Failed to register flow: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

