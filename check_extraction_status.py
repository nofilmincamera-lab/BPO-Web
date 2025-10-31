#!/usr/bin/env python3
"""
Check extraction status via Prefect UI API
"""
import requests
import json

def check_extraction_status(flow_run_id):
    """Check extraction status via Prefect API"""
    
    # Prefect API endpoint
    api_url = f"http://localhost:4200/api/flow_runs/{flow_run_id}"
    
    print(f"Checking extraction status for flow run: {flow_run_id}")
    print("=" * 60)
    
    try:
        # Make API call to get flow run status
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Flow run details retrieved!")
            print(f"Name: {result.get('name', 'N/A')}")
            print(f"Status: {result.get('state', {}).get('type', 'N/A')}")
            print(f"Created: {result.get('created', 'N/A')}")
            print(f"Updated: {result.get('updated', 'N/A')}")
            
            # Check if there are any task runs
            if 'task_runs' in result:
                task_runs = result['task_runs']
                print(f"\nTask Runs ({len(task_runs)}):")
                for task_run in task_runs:
                    print(f"  - {task_run.get('name', 'N/A')}: {task_run.get('state', {}).get('type', 'N/A')}")
            
            return result.get('state', {}).get('type', 'UNKNOWN')
        else:
            print(f"ERROR: API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to connect to Prefect API: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python check_extraction_status.py <flow_run_id>")
        print("Example: python check_extraction_status.py 57aeac19-bcfd-48a6-80d1-af0f1be4ef0a")
        sys.exit(1)
    
    flow_run_id = sys.argv[1]
    status = check_extraction_status(flow_run_id)
    
    if status:
        print(f"\nFinal Status: {status}")
        if status == "COMPLETED":
            print("SUCCESS: Extraction completed successfully!")
        elif status == "FAILED":
            print("ERROR: Extraction failed!")
        elif status == "RUNNING":
            print("GREEN: Extraction is still running...")
        else:
            print(f"WARNING: Extraction status: {status}")
    else:
        print("\nERROR: Could not determine extraction status")

