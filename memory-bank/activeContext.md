# Active Context

## Current Focus (2025-10-30)

1) Stabilize orchestration and execution paths
- Prefect 3.1.9 running; UI accessible at http://localhost:4200 (cosmetic 0.0.0.0 warning)
- Programmatic client has Pydantic v2 model_rebuild issues for read operations; UI/HTTP used as workaround
- Direct GPU runner added to bypass orchestration complexity when needed

2) High-throughput extraction
- Direct GPU extraction runner processes 45,403 docs at ~5.3 docs/sec (RTX 3060)
- Entities ~3.26M; relationships ~334M (stored only when DB password configured)
- Temporary DB auth issue noted (password for postgres), extraction continues without writes

## Recent Changes (Oct 29-30, 2025)

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
- Context7 MCP: register hosted endpoint for enterprise context retrieval [pending config]
- Cursor configuration consolidated in `.cursor/mcp.json`

## Next Steps

1. Label Studio validation pipeline ✅
   - Label Studio running at http://localhost:8082 (Docker)
   - MCP integration configured with API key 131a97106e49f9f2ed0db70d24f85092570753f3
   - BPO Project (ID: 2) configured with full entity schema
   - Ready to import tasks from `data/preprocessed/dataset_45000_converted.jsonl`
   - Entity schema: COMPANY, PERSON, DATE, TECHNOLOGY, MONEY, PERCENT, PRODUCT/COMPUTING_PRODUCT, BUSINESS_TITLE, LOCATION, TIME_RANGE, ORL, TEMPORAL, SKILL
   - Pre-annotated tasks available in `data/label-studio/tasks_with_predictions_5k.json`

2. Fix DB auth for writes
   - Provide postgres password env var to direct runner or update connection
   - Re-run or write-back results in batches

3. Decide orchestration mode per run
   - Prefect deployment when monitoring/auditing is needed
   - Direct GPU runner for speed/simple ops

## Active Decisions

- **Prefect orchestration** (replaced Temporal for reliability) with optional bypass
- **PostgreSQL + Redis** for Prefect backend
- **Single agent** with GPU support for extraction tasks
- **Python-first flows** with @flow/@task decorators
- **Docker-based deployment** with prefect-docker blocks
- Streaming JSON parsing for 854MB+ files (ijson)
- GPU acceleration when available (RTX 3060, CUDA 13.0)
- Manual schema creation due to Alembic mount issues

