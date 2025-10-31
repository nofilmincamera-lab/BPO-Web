#!/usr/bin/env python3
"""
Run full extraction using Prefect deployment
"""
import os
import asyncio
from prefect.client.orchestration import get_client
from prefect.client.schemas.filters import DeploymentFilter, DeploymentFilterName

async def run_full_extraction():
    """Run the full document extraction pipeline"""
    
    # Set API URL
    os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"
    
    print("Starting Full Document Extraction Pipeline")
    print("=" * 50)
    
    try:
        async with get_client() as client:
            # Get the document-extraction deployment
            deployments = await client.read_deployments(
                deployment_filter=DeploymentFilter(
                    name=DeploymentFilterName(any_=["document-extraction"])
                )
            )
            
            if not deployments:
                print("ERROR: No 'document-extraction' deployment found!")
                return
            
            deployment = deployments[0]
            print(f"SUCCESS: Found deployment: {deployment.name}")
            print(f"   ID: {deployment.id}")
            print(f"   Flow: {deployment.flow_id}")
            
            # Create flow run
            print("\nCreating flow run...")
            flow_run = await client.create_flow_run_from_deployment(
                deployment_id=deployment.id,
                name="Full Document Extraction - 45K Documents"
            )
            
            print(f"SUCCESS: Flow run created!")
            print(f"   ID: {flow_run.id}")
            print(f"   Name: {flow_run.name}")
            print(f"   Status: {flow_run.state.type}")
            
            # Monitor the run
            print(f"\nMonitoring flow run...")
            print(f"   View in UI: http://localhost:4200/flow-runs/{flow_run.id}")
            print(f"   Or check status with: python check_flow_run.py {flow_run.id}")
            
            # Wait a bit to see initial status
            await asyncio.sleep(5)
            
            # Get updated status
            updated_run = await client.read_flow_run(flow_run.id)
            print(f"   Current Status: {updated_run.state.type}")
            
            if updated_run.state.type == "RUNNING":
                print("   GREEN: Flow is running successfully!")
            elif updated_run.state.type == "COMPLETED":
                print("   SUCCESS: Flow completed successfully!")
            elif updated_run.state.type == "FAILED":
                print("   ERROR: Flow failed!")
                if hasattr(updated_run.state, 'message'):
                    print(f"   Error: {updated_run.state.message}")
            else:
                print(f"   WARNING: Flow status: {updated_run.state.type}")
            
            print(f"\nFlow Run Details:")
            print(f"   - Run ID: {flow_run.id}")
            print(f"   - Deployment: {deployment.name}")
            print(f"   - Flow: {deployment.flow_id}")
            print(f"   - Created: {flow_run.created}")
            
            return flow_run.id
            
    except Exception as e:
        print(f"ERROR: Error running extraction: {e}")
        return None

if __name__ == "__main__":
    print("BPO Document Extraction Pipeline")
    print("================================")
    print("This will process the full 45,403 document dataset")
    print("Expected time: ~17 hours based on test performance")
    print("Expected entities: 900K-1.8M entities")
    print("Expected relationships: 2.7M-5.4M relationships")
    print()
    
    # Run the extraction
    flow_run_id = asyncio.run(run_full_extraction())
    
    if flow_run_id:
        print(f"\nSUCCESS: Extraction started successfully!")
        print(f"   Flow Run ID: {flow_run_id}")
        print(f"   Monitor at: http://localhost:4200/flow-runs/{flow_run_id}")
    else:
        print("\nERROR: Failed to start extraction")
