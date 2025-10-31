#!/usr/bin/env python3
"""
Trigger extraction using the API directly
"""
import requests
import json

def trigger_extraction():
    """Trigger extraction via API"""
    
    # API endpoint for processing documents
    api_url = "http://localhost:8000/api/extraction/process-documents"
    
    print("Triggering Full Document Extraction via API")
    print("=" * 50)
    
    # Parameters for the extraction
    params = {
        "source_path": "data/preprocessed/dataset_45000_converted.jsonl",
        "heuristics_version": "2.0.0",
        "batch_size": 100
    }
    
    try:
        # Make API call to process documents
        response = requests.post(api_url, params=params, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Extraction queued successfully!")
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"ERROR: API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to connect to API: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("BPO Document Extraction Pipeline - API Trigger")
    print("==============================================")
    print("This will process the full 45,403 document dataset")
    print("Expected time: ~17 hours based on test performance")
    print("Expected entities: 900K-1.8M entities")
    print("Expected relationships: 2.7M-5.4M relationships")
    print()
    
    success = trigger_extraction()
    
    if success:
        print("\nSUCCESS: Extraction started via API!")
        print("Monitor progress in Prefect UI: http://localhost:4200")
    else:
        print("\nERROR: Failed to start extraction via API")
