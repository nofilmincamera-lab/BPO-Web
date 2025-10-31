#!/usr/bin/env python3
"""
Check the status of a Prefect flow run
"""
import os
import sys
import asyncio
from prefect.client.orchestration import get_client

async def check_flow_run(flow_run_id: str):
    """Check the status of a flow run"""
    
    # Set API URL
    os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"
    
    try:
        async with get_client() as client:
            # Get flow run details
            flow_run = await client.read_flow_run(flow_run_id)
            
            print(f"Flow Run Status: {flow_run_id}")
            print("=" * 50)
            print(f"Name: {flow_run.name}")
            print(f"Status: {flow_run.state.type}")
            print(f"Created: {flow_run.created}")
            print(f"Updated: {flow_run.updated}")
            
            if hasattr(flow_run.state, 'message') and flow_run.state.message:
                print(f"Message: {flow_run.state.message}")
            
            # Get task runs if available
            task_runs = await client.read_task_runs(
                flow_run_filter={"id": {"any_": [flow_run_id]}}
            )
            
            if task_runs:
                print(f"\nTask Runs ({len(task_runs)}):")
                for task_run in task_runs:
                    print(f"  - {task_run.name}: {task_run.state.type}")
                    if hasattr(task_run.state, 'message') and task_run.state.message:
                        print(f"    Message: {task_run.state.message}")
            
            # Get logs if available
            try:
                logs = await client.read_logs(flow_run_id=flow_run_id)
                if logs:
                    print(f"\nRecent Logs ({len(logs)} entries):")
                    for log in logs[-5:]:  # Show last 5 logs
                        print(f"  [{log.timestamp}] {log.level}: {log.message}")
            except Exception as e:
                print(f"\nWARNING: Could not fetch logs: {e}")
            
            return flow_run.state.type
            
    except Exception as e:
        print(f"ERROR: Error checking flow run: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_flow_run.py <flow_run_id>")
        sys.exit(1)
    
    flow_run_id = sys.argv[1]
    status = asyncio.run(check_flow_run(flow_run_id))
    
    if status:
        print(f"\nFinal Status: {status}")
        if status == "COMPLETED":
            print("SUCCESS: Flow completed successfully!")
        elif status == "FAILED":
            print("ERROR: Flow failed!")
        elif status == "RUNNING":
            print("GREEN: Flow is still running...")
        else:
            print(f"WARNING: Flow status: {status}")
