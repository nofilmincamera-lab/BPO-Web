#!/usr/bin/env python3
"""
Simple Prefect deployment using the correct approach.
"""
import asyncio
import os
from prefect import serve
from src.flows.extraction_flow import extract_documents_flow

async def main():
    """Deploy and serve the extraction flow."""
    print("Deploying extraction flow...")
    
    # Set Prefect API URL to connect to Docker server
    os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"
    
    try:
        # Create deployment
        deployment = extract_documents_flow.to_deployment(
            name="document-extraction",
            work_pool_name="default-pool",
            description="Extract entities from documents using spaCy EntityRuler",
            tags=["extraction", "ner", "production"],
            version="1.0.0"
        )
        
        print("Deployment created successfully!")
        print("Starting flow server...")
        print("Monitor at: http://localhost:4200")
        print("Press Ctrl+C to stop")
        
        # Serve the deployment
        await serve(deployment)
        
    except KeyboardInterrupt:
        print("\nStopping flow server...")
    except Exception as e:
        print(f"Failed to deploy/serve flow: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

