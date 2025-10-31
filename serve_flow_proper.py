#!/usr/bin/env python3
"""
Serve the flow properly to register it with Prefect.
"""
import asyncio
import os
from prefect import serve
from src.flows.extraction_flow import extract_documents_flow

async def main():
    """Serve the flow to register it."""
    print("Serving flow to register with Prefect...")
    
    # Set Prefect API URL to connect to Docker server
    os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"
    
    try:
        # Create deployment
        deployment = await extract_documents_flow.to_deployment(
            name="document-extraction-serve",
            work_pool_name="default-pool",
            description="Extract entities from documents using spaCy EntityRuler",
            tags=["extraction", "ner", "production"],
            version="1.0.0"
        )
        
        print("Starting flow server...")
        print("This will register the flow with Prefect server")
        print("Monitor at: http://localhost:4200")
        print("Press Ctrl+C to stop")
        
        # Serve the deployment (this registers the flow)
        await serve(deployment)
        
    except KeyboardInterrupt:
        print("\nStopping flow server...")
    except Exception as e:
        print(f"Failed to serve flow: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

