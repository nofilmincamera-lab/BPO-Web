#!/usr/bin/env python3
"""
Proper Prefect deployment using the correct approach.
"""
import asyncio
import os
from prefect import serve
from prefect.client.orchestration import get_client
from src.flows.extraction_flow import extract_documents_flow

async def main():
    """Deploy the extraction flow properly."""
    print("Deploying extraction flow...")
    
    # Set Prefect API URL to connect to Docker server
    os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"
    
    try:
        # First, let's check if we can connect to the server
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
            
            # Create deployment
            deployment = await extract_documents_flow.to_deployment(
                name="document-extraction",
                work_pool_name="default-pool",
                description="Extract entities from documents using spaCy EntityRuler",
                tags=["extraction", "ner", "production"],
                version="1.0.0"
            )
            
            # Apply the deployment
            await deployment.apply()
            print("Deployment applied successfully!")
            
            # Verify deployment
            deployments = await client.read_deployments()
            print(f"Deployments after creation: {len(deployments)}")
            for dep in deployments:
                print(f"  - {dep.name} (ID: {dep.id})")
        
    except Exception as e:
        print(f"Failed to deploy flow: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
