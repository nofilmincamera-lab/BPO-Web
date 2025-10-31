#!/usr/bin/env python3
"""
Recreate work pool with Docker and GPU support
"""
import asyncio
import os
from prefect.client.orchestration import get_client
from prefect.client.schemas.actions import WorkPoolCreate

async def recreate_work_pool():
    """Recreate work pool with Docker and GPU support"""
    
    # Set API URL
    os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"
    
    print("Recreating work pool with Docker and GPU support...")
    print("=" * 50)
    
    try:
        async with get_client() as client:
            # Delete existing work pool if it exists
            try:
                await client.delete_work_pool("default-pool")
                print("Deleted existing work pool")
            except Exception as e:
                print(f"Note: Could not delete existing work pool: {e}")
            
            # Create new work pool with Docker support
            work_pool = WorkPoolCreate(
                name="default-pool",
                type="docker",
                description="Docker work pool for BPO extraction tasks with GPU support",
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
            
            # Create the work pool
            created_pool = await client.create_work_pool(work_pool)
            
            print("SUCCESS: Work pool created with Docker and GPU support!")
            print(f"   Name: {created_pool.name}")
            print(f"   Type: {created_pool.type}")
            print(f"   Image: bpo-worker:latest")
            print(f"   GPU Support: Enabled")
            
            return True
            
    except Exception as e:
        print(f"ERROR: Failed to recreate work pool: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(recreate_work_pool())
    
    if success:
        print("\nSUCCESS: Work pool recreated successfully!")
        print("Now you can deploy flows with GPU support.")
    else:
        print("\nERROR: Failed to recreate work pool")

