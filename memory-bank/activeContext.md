# Active Context

## Current Focus (2025-10-31)

1) Production extraction pipeline stabilized
- Prefect 3.1.9 running; UI accessible at http://localhost:4200
- Canonical dataset path established: `data/processed/preprocessed.jsonl`
- Production extraction via `queue_extraction_prefect.py` (orchestrated) or `run_direct_extraction.py` (direct)
- Both use proper heuristics-first multi-tier extraction pipeline

2) Codebase cleanup completed
- Deprecated scripts archived: `run_gpu_extraction.py`, `convert_raw_dataset.py`
- All extraction scripts now use canonical dataset paths
- Memory-bank updated to reflect Oct 31, 2025 state

## Recent Changes (Oct 29-31, 2025)

### Codebase Cleanup (Oct 31, 2025) ✅
- Archived deprecated scripts that bypassed heuristics pipeline
- Established canonical dataset paths across all scripts
- Updated memory-bank to reflect current state
- Created `CANONICAL_PATHS.md` for single source of truth
- Removed Context7/Temporal references (migrated to Prefect Oct 25)

### Prefect Migration ✅
- Removed Temporal (fragile 5-service stack with health check issues)
- Added Prefect 3.1.9 + prefect-docker to requirements.txt
- Created docker-compose.prefect.yml with server + agent
- Converted ProcessDocumentsWorkflow → extract_documents_flow
- Converted activities → @task functions with retries and caching
- Created deploy_flows.py for deployment
- Created queue_extraction_prefect.py for queueing runs
- Benefits: Simpler, faster, more reliable

### spaCy EntityRuler Integration ✅
- Custom pipeline with 4,505+ taxonomy patterns
- EntityRuler runs BEFORE statistical NER (taxonomy-first)
- Tested successfully: 5 entities extracted from sample text
- Performance: ~1,658 chars/second

### Extraction Implementation ✅
- Heuristics loader with 4,505 entries (3,361 companies + 52 countries + 20 tech + 1,072 products)
- Multi-tiered extraction: heuristics (0.90) → regex (0.92) → spaCy (0.70)
- MONEY and PERCENT regex patterns
- Proximity-based relationships

### Infrastructure
- Database: 8 tables + pgvector 0.8.1
- GPU: CUDA available (RTX 3060)
- Test data: test_10.jsonl with 5 synthetic documents

### MCP Integrations ✅ (2025-10-30)
- Label Studio MCP: installed and configured
  - API Key: 131a97106e49f9f2ed0db70d24f85092570753f3
  - URL: http://localhost:8082
  - BPO Project (ID: 2) with comprehensive entity schema
  - Tools: projects, tasks, annotations, imports
  - Automation script: `bpo_mcp_automation.py`
- Prefect MCP: to enable monitoring/inspection of flows and deployments
  - Local profile by default; env override via `PREFECT_API_URL` (+ `PREFECT_API_KEY` for Cloud)
  - Intended URL (self-hosted): http://localhost:4200/api
- Docker MCP: register to interact with Docker engine (container listing/health) [pending config]
- Sequential Thinking MCP: register for structured chain-of-thought tool use [pending config]
- Cursor configuration consolidated in `.cursor/mcp.json`

## Next Steps

1. Label Studio validation pipeline ✅
   - Label Studio running at http://localhost:8082 (Docker)
   - MCP integration configured with API key 131a97106e49f9f2ed0db70d24f85092570753f3
   - BPO Project (ID: 2) configured with full entity schema
   - Ready to import tasks from `data/processed/preprocessed.jsonl` (canonical dataset)
   - Entity schema: COMPANY, PERSON, DATE, TECHNOLOGY, MONEY, PERCENT, PRODUCT/COMPUTING_PRODUCT, BUSINESS_TITLE, LOCATION, TIME_RANGE, ORL, TEMPORAL, SKILL
   - Pre-annotated tasks available in `data/label-studio/tasks_with_predictions_5k.json`

2. Run production extraction
   - Preprocess canonical dataset: `python scripts/preprocess.py --input <raw> --output data/processed/preprocessed.jsonl`
   - Execute extraction: `python queue_extraction_prefect.py` (with Prefect) or `python run_direct_extraction.py` (direct)
   - Monitor at http://localhost:4200 if using Prefect

3. Production deployment considerations
   - Validate extraction results in Label Studio
   - Set up automated validation workflows
   - Configure monitoring and alerting

## Active Decisions

- **Prefect orchestration** (replaced Temporal Oct 25, 2025)
- **Canonical dataset path**: `data/processed/preprocessed.jsonl` (preprocessed via `scripts/preprocess.py`)
- **Production extraction**: `queue_extraction_prefect.py` or `run_direct_extraction.py`
- **Heuristics-first multi-tier pipeline**: heuristics (0.90) → regex (0.92) → spaCy (0.70)
- **PostgreSQL + Redis** for Prefect backend
- **Single agent** with GPU support for extraction tasks (RTX 3060, CUDA 13.0)
- **Python-first flows** with @flow/@task decorators
- **Docker-based deployment** with prefect-docker blocks
- Streaming JSON parsing for large files (ijson via `scripts/preprocess.py`)
- Manual schema creation due to Alembic mount issues

