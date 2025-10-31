#!/usr/bin/env python3
"""
Update work pool to support Docker images with GPU
"""
import asyncio
import os
from prefect.client.orchestration import get_client
from prefect.client.schemas.actions import WorkPoolUpdate

async def update_work_pool():
    """Update work pool to support Docker images"""
    
    # Set API URL
    os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"
    
    print("Updating work pool for Docker with GPU support...")
    print("=" * 50)
    
    try:
        async with get_client() as client:
            # Get existing work pool
            work_pools = await client.read_work_pools()
            default_pool = None
            for wp in work_pools:
                if wp.name == "default-pool":
                    default_pool = wp
                    break
            
            if not default_pool:
                print("ERROR: Work pool 'default-pool' not found!")
                return False
            
            print(f"Found work pool: {default_pool.name} (type: {default_pool.type})")
            
            # Update work pool to support Docker images
            update_data = WorkPoolUpdate(
                base_job_template={
                    "job_configuration": {
                        "image": "bpo-worker:latest",
                        "env": {
                            "NVIDIA_VISIBLE_DEVICES": "all",
                            "NVIDIA_DRIVER_CAPABILITIES": "all"
                        }
                    },
                    "variables": {
                        "properties": {
                            "image": {
                                "title": "Image",
                                "description": "Docker image to use for the job",
                                "type": "string",
                                "default": "bpo-worker:latest"
                            }
                        },
                        "required": []
                    }
                }
            )
            
            # Update the work pool
            updated_pool = await client.update_work_pool(
                work_pool_name="default-pool",
                work_pool=update_data
            )
            
            print("SUCCESS: Work pool updated for Docker with GPU support!")
            print(f"   Name: {updated_pool.name}")
            print(f"   Type: {updated_pool.type}")
            print(f"   Image: bpo-worker:latest")
            print(f"   GPU Support: Enabled")
            
            return True
            
    except Exception as e:
        print(f"ERROR: Failed to update work pool: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(update_work_pool())
    
    if success:
        print("\nSUCCESS: Work pool updated successfully!")
        print("Now you can deploy flows with GPU support.")
    else:
        print("\nERROR: Failed to update work pool")

