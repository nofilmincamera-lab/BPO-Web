# System Patterns

## Architecture

**Prefect Work Pool Pattern (optional)**:
- Single work pool (`default-pool`) with Docker worker (GPU-enabled)
- Prefect server + agent architecture
- PostgreSQL backend for Prefect state management

**Heuristics-First Extraction**:
1. Heuristics (aliases, tech terms, taxonomy) - 0.85+ confidence
2. spaCy NER with EntityRuler - 0.70+ confidence
3. Embeddings similarity - 0.62+ confidence
4. LLM fallback - 0.50+ confidence

**Entity set**: COMPANY, PERSON, DATE, TECHNOLOGY, MONEY, PERCENT, PRODUCT/COMPUTING_PRODUCT, BUSINESS_TITLE, LOCATION, TIME_RANGE, ORL, TEMPORAL, SKILL.

**Flow Orchestration**:
- Prefect for durable execution and monitoring
- or Direct GPU runner `run_gpu_extraction.py` for simplicity/speed
- Chunking and progress reporting regardless of orchestration
- Retry policies per task with caching

## Key Components

**Tasks**: Stateless, retryable, idempotent with caching
**Flows**: Orchestrate tasks, manage state and parameters
**Work Pools**: Route tasks to appropriate workers
**Deployments**: Versioned flow definitions with schedules

## Design Principles

- GPU acceleration when available (spaCy, embeddings, Ollama)
- Streaming for large files (ijson for 854MB+ JSON)
- Bloom filters for URL deduplication
- UPSERT semantics for idempotency
- Provenance tracking (source, source_version, heuristics_version, confidence_method)
- Task progress monitoring (every 100 docs/items)
- Retry policies per task (typically 2-3 attempts with exponential backoff)
- Flow chunking for large document processing
- Scheduled execution via Prefect deployments when enabled
- Automated cleanup (keep last 5 reports)
- Self-updating documentation (MEMORY.md)

## MCP Servers Pattern

- Label Studio MCP
  - Purpose: human-in-the-loop annotation management (projects, tasks, annotations, imports)
  - Access: local stdio via `python -m label_studio_mcp`
  - Usage: Drive validation workflows and dataset curation

- Prefect MCP
  - Purpose: monitoring/inspection of deployments, flow runs, task runs; docs proxy for write guidance
  - Access: `uvx --from prefect-mcp prefect-mcp-server`
  - Credentials: inherit Prefect profile or env (`PREFECT_API_URL`, `PREFECT_API_KEY`)

- Docker MCP (planned)
  - Purpose: container visibility/health checks from MCP client
  - Access: package/entrypoint to be confirmed; prefer local stdio when available

- Sequential Thinking MCP (planned)
  - Purpose: structured multi-step reasoning tools
  - Access: package/entrypoint to be confirmed or hosted endpoint

- Context7 MCP (planned)
  - Purpose: enterprise knowledge/context retrieval as a tool
  - Access: hosted `httpUrl` endpoint when provisioned

