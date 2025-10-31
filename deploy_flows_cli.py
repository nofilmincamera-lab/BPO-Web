#!/usr/bin/env python3
"""
Deploy Prefect flows using CLI approach.
Run this after starting the Prefect server.
"""
import subprocess
import sys
import os

def main():
    """Deploy the extraction flow to Prefect using CLI."""
    print("Deploying extraction flow to Prefect...")
    
    # Set environment variables
    os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"
    
    try:
        # Create work pool first (one-time setup)
        print("Creating work pool...")
        result = subprocess.run([
            "prefect", "work-pool", "create", 
            "--type", "process", 
            "default-pool"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Work pool 'default-pool' created")
        elif "already exists" in result.stderr:
            print("Work pool 'default-pool' already exists")
        else:
            print(f"Work pool creation failed: {result.stderr}")
            return 1
        
        # Deploy the flow using CLI
        print("Deploying flow...")
        result = subprocess.run([
            "prefect", "deployment", "build",
            "src/flows/extraction_flow.py:extract_documents_flow",
            "--name", "default",
            "--pool", "default-pool",
            "--tag", "extraction,ner,production",
            "--version", "1.0.0",
            "--apply"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Flow deployed successfully!")
            print("Monitor at: http://localhost:4200")
        else:
            print(f"Deployment failed: {result.stderr}")
            return 1
        
    except Exception as e:
        print(f"Failed to deploy flow: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

