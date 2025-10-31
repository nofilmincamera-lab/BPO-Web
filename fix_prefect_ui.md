# Prefect UI Access Fix

## Issue
The Prefect server is advertising itself as `http://0.0.0.0:4200/api` but browsers cannot connect to `0.0.0.0`.

## Solution

### Option 1: Access UI Directly (Recommended)
Simply access the UI at: **http://localhost:4200**

The error message "Can't connect to Server API at http://0.0.0.0:4200/api" can often be ignored - the UI should still work when accessed via localhost.

### Option 2: Use the API Directly
Since the UI might have issues, you can use the Python API to interact with Prefect:

```python
import os
os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"

# Now you can use the Prefect client
from prefect.client.orchestration import get_client
# ... your code here
```

### Option 3: Deploy and Run Flows via Script
Use the deployment scripts we created:

```bash
# Deploy the flow (if not already deployed)
python deploy_simple.py

# Queue a flow run via the API endpoint
curl -X POST http://localhost:8000/api/orchestration/queue-work
```

### Verification
Test that the API is accessible:
```bash
curl http://localhost:4200/api/health
# Should return: true
```

### Note
The `0.0.0.0` error is cosmetic - it's how Docker advertises the binding address. The actual API is accessible at `localhost:4200`.


