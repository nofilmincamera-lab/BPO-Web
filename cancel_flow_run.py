#!/usr/bin/env python3
"""
Cancel a Prefect flow run
"""
import requests
import json

def cancel_flow_run(flow_run_id):
    """Cancel a flow run via Prefect API"""
    
    # Prefect API endpoint
    api_url = f"http://localhost:4200/api/flow_runs/{flow_run_id}/set_state"
    
    print(f"Cancelling flow run: {flow_run_id}")
    print("=" * 50)
    
    # Cancel the flow run
    cancel_data = {
        "state": {
            "type": "CANCELLED",
            "name": "Cancelled by user"
        }
    }
    
    try:
        # Make API call to cancel flow run
        response = requests.post(api_url, json=cancel_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Flow run cancelled!")
            print(f"Status: {result.get('state', {}).get('type', 'N/A')}")
            return True
        else:
            print(f"ERROR: API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to connect to Prefect API: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python cancel_flow_run.py <flow_run_id>")
        print("Example: python cancel_flow_run.py 57aeac19-bcfd-48a6-80d1-af0f1be4ef0a")
        sys.exit(1)
    
    flow_run_id = sys.argv[1]
    success = cancel_flow_run(flow_run_id)
    
    if success:
        print("\nSUCCESS: Flow run cancelled successfully!")
    else:
        print("\nERROR: Failed to cancel flow run")

