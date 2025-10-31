#!/usr/bin/env python3
"""Test Prefect flow deployment and execution."""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_prefect_flow():
    """Test if we can create and run a simple Prefect flow."""
    try:
        from prefect import flow, task
        from prefect.deployments import run_deployment
        
        @task
        def simple_task():
            return "Hello from Prefect!"
        
        @flow(name="test-flow")
        def test_flow():
            result = simple_task()
            print(f"Flow result: {result}")
            return result
        
        print("SUCCESS: Prefect imports successful")
        print("SUCCESS: Flow and task decorators working")
        
        # Test running the flow directly
        result = test_flow()
        print(f"SUCCESS: Flow execution successful: {result}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Prefect test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_prefect_flow())
    if success:
        print("\nSUCCESS: Prefect is working! We can proceed with flow development.")
    else:
        print("\nERROR: Prefect setup has issues. Need to troubleshoot.")
