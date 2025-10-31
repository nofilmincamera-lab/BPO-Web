"""BPO Intelligence Pipeline API with Prefect orchestration."""
import os
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from prefect.client.orchestration import get_client
from prefect.deployments import run_deployment

app = FastAPI(title="BPO Intelligence API")


@app.get("/healthz")
async def healthz():
    """Health check endpoint."""
    return {"status": "healthy", "service": "bpo-api"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "BPO Intelligence Pipeline API",
        "version": "1.0.0",
        "orchestration": "Prefect",
        "api_url": os.getenv("PREFECT_API_URL", "http://localhost:4200/api"),
        "work_queue": os.getenv("PREFECT_WORK_QUEUE", "default"),
    }




@app.post("/api/extraction/process-documents")
async def queue_extraction_workflow(
    source_path: str,
    heuristics_version: str = "2.0.0",
    batch_size: int = 100
) -> Dict[str, Any]:
    """Queue extraction workflow for document processing."""
    try:
        # Run Prefect deployment
        flow_run = await run_deployment(
            name="document-extraction-pipeline/default",
            parameters={
                "source_path": source_path,
                "heuristics_version": heuristics_version,
                "batch_size": batch_size,
                "start_offset": 0
            },
            timeout=0  # Don't wait
        )
        
        return {
            "flow_run_id": str(flow_run.id),
            "flow_run_name": flow_run.name,
            "monitor_url": f"http://localhost:4200/flow-runs/flow-run/{flow_run.id}",
            "status": "queued"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

