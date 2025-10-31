# Active Context

## Current Focus (2025-10-31)

1) Production extraction pipeline stabilized
- Prefect 3.1.9 running; UI accessible at http://localhost:4200
- Canonical dataset path established: `data/processed/preprocessed.jsonl`
- Production extraction via `queue_extraction_prefect.py` (Prefect-orchestrated, RECOMMENDED)
- Alternative paths: `run_extraction.py`, `run_standalone_extraction.py`, `run_simple_extraction.py`
- All use proper heuristics-first multi-tier extraction pipeline

2) Codebase cleanup completed (Oct 31, 2025)
- Removed deprecated scripts: `run_gpu_extraction.py`, `convert_raw_dataset.py`
- All extraction scripts now use canonical dataset: `data/processed/preprocessed.jsonl`
- Removed 79% of bloated dependencies (58 → 12 packages)
- Platform-neutralized Docker configuration (relative paths, LF line endings)
- Created `CANONICAL_PATHS.md` as single source of truth

## Recent Changes (Oct 29-31, 2025)

### Codebase Cleanup (Oct 31, 2025) ✅
- Removed deprecated scripts that bypassed heuristics pipeline
- Established canonical dataset paths across all scripts: `data/processed/preprocessed.jsonl`
- Ultra-minimal dependencies: 58 → 12 packages (79% reduction)
- Platform-neutralized Docker: relative paths, LF line endings, `.gitattributes`
- Created `CANONICAL_PATHS.md` for single source of truth
- Created `PLATFORM_NEUTRALIZATION.md` for cross-platform compatibility
- Created `DEPENDENCIES_AUDIT.md` documenting all package decisions

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
- Prefect MCP: monitoring/inspection of flows and deployments
  - URL: http://localhost:4200/api
  - Tools: flows, flow runs, deployments, work pools, task runs, events
- Sequential Thinking MCP: structured chain-of-thought reasoning
- Cursor configuration in `.cursor/mcp.json`

## Next Steps

1. Label Studio validation pipeline ✅
   - Label Studio running at http://localhost:8082 (Docker)
   - MCP integration configured with API key 131a97106e49f9f2ed0db70d24f85092570753f3
   - BPO Project (ID: 2) configured with full entity schema
   - Ready to import tasks from `data/processed/preprocessed.jsonl` (canonical dataset)
   - Entity schema: COMPANY, PERSON, DATE, TECHNOLOGY, MONEY, PERCENT, PRODUCT/COMPUTING_PRODUCT, BUSINESS_TITLE, LOCATION, TIME_RANGE, ORL, TEMPORAL, SKILL
   - Pre-annotated tasks available in `data/label-studio/tasks_with_predictions_5k.json`

2. Run production extraction
   - Preprocess canonical dataset: `python scripts/preprocess.py`
     - Input: `data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310 (1).json`
     - Output: `data/processed/preprocessed.jsonl`
   - Execute extraction (RECOMMENDED): `python queue_extraction_prefect.py`
   - Alternative extraction paths:
     - `python run_extraction.py` (direct flow)
     - `python run_standalone_extraction.py` (no Prefect)
     - `python run_simple_extraction.py` (minimal)
   - Monitor at http://localhost:4200 for Prefect-orchestrated runs

3. Production deployment considerations
   - Validate extraction results in Label Studio
   - Set up automated validation workflows
   - Configure monitoring and alerting

## Active Decisions

- **Prefect orchestration** (replaced Temporal Oct 25, 2025)
- **Canonical dataset**: `data/processed/preprocessed.jsonl` (from `scripts/preprocess.py`)
- **Raw dataset**: `data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310 (1).json`
- **Production extraction**: `queue_extraction_prefect.py` (RECOMMENDED)
- **Heuristics-first multi-tier pipeline**: heuristics (0.90) → regex (0.92) → spaCy (0.70)
- **PostgreSQL + Redis** for Prefect backend
- **Single agent** with GPU support for extraction tasks (RTX 3060, CUDA 13.0)
- **Python-first flows** with @flow/@task decorators
- **Docker-based deployment** with prefect-docker blocks
- **Ultra-minimal dependencies**: 12 packages (down from 58)
- **Platform-neutral**: Relative paths, LF line endings, cross-platform Docker
- Streaming JSON parsing for large files (ijson via `scripts/preprocess.py`)

