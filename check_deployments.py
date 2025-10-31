#!/usr/bin/env python3
"""Check available deployments."""
import asyncio
import os
from prefect.client.orchestration import get_client

async def main():
    """Check deployments."""
    os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"
    
    async with get_client() as client:
        deployments = await client.read_deployments()
        print("Available deployments:")
        for dep in deployments:
            print(f"  - {dep.name} (ID: {dep.id})")
        
        if not deployments:
            print("No deployments found.")

if __name__ == "__main__":
    asyncio.run(main())

