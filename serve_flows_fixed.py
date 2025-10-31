#!/usr/bin/env python3
"""
Serve Prefect flows for process work pools.
This is the correct approach for local process work pools.
"""
import asyncio
import os
from prefect import serve
from src.flows.extraction_flow import extract_documents_flow

async def main():
    """Serve the extraction flow."""
    print("Serving extraction flow...")
    
    # Set Prefect API URL to connect to Docker server
    os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"
    
    try:
        # Create deployment configuration
        deployment = extract_documents_flow.to_deployment(
            name="default",
            work_pool_name="default-pool",
            description="Extract entities from documents using spaCy EntityRuler",
            tags=["extraction", "ner", "production"],
            version="1.0.0"
        )
        
        # Serve the flow
        print("Starting flow server...")
        print("Monitor at: http://localhost:4200")
        print("Press Ctrl+C to stop")
        
        await serve(deployment)
        
    except KeyboardInterrupt:
        print("\nStopping flow server...")
    except Exception as e:
        print(f"Failed to serve flow: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

