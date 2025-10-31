#!/usr/bin/env python3
"""
Serve Prefect flows instead of deploying them.
This approach works better with process work pools.
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
        # Serve the flow
        await serve(
            extract_documents_flow.to_deployment(
                name="default",
                work_pool_name="default-pool",
                description="Extract entities from documents using spaCy EntityRuler",
                tags=["extraction", "ner", "production"],
                version="1.0.0"
            )
        )
        
    except Exception as e:
        print(f"Failed to serve flow: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

