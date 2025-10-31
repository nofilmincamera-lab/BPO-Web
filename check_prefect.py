#!/usr/bin/env python3
"""Check and fix Prefect work pool configuration."""
import asyncio
import os
from prefect.client.orchestration import get_client

async def main():
    """Check work pools and fix if needed."""
    os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"
    
    async with get_client() as client:
        # Check existing work pools
        work_pools = await client.read_work_pools()
        print("Existing work pools:")
        for wp in work_pools:
            print(f"  - {wp.name} (type: {wp.type})")
        
        # Delete default-pool if it exists
        existing_pools = [wp.name for wp in work_pools]
        if "default-pool" in existing_pools:
            print("Deleting existing default-pool...")
            await client.delete_work_pool("default-pool")
            print("Deleted default-pool")
        
        # Create new work pool
        print("Creating new default-pool...")
        from prefect.client.schemas.actions import WorkPoolCreate
        work_pool = WorkPoolCreate(
            name="default-pool",
            type="process",
            description="Default work pool for BPO extraction tasks"
        )
        await client.create_work_pool(work_pool)
        print("Created default-pool")

if __name__ == "__main__":
    asyncio.run(main())
