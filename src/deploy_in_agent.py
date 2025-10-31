#!/usr/bin/env python3
"""
Run this script INSIDE the agent container to deploy the flow.
Usage: docker exec bpo-prefect-agent python /app/deploy_in_agent.py
"""
import asyncio
import os

# Set API URL to talk to prefect-server container
os.environ["PREFECT_API_URL"] = "http://prefect-server:4200/api"

from src.flows.extraction_flow import extract_documents_flow

async def main():
    print("Deploying flow from agent container...")
    print(f"API URL: {os.environ['PREFECT_API_URL']}")
    
    try:
        # Create deployment - for process worker, no image needed
        deployment_id = await extract_documents_flow.to_deployment(
            name="default",
            work_pool_name="default-pool",
            description="Extract entities from documents",
            tags=["extraction", "ner"],
            version="1.0.0",
        )
        
        print(f"Deployment created successfully!")
        print(f"Deployment ID: {deployment_id}")
        return 0
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))

