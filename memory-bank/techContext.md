# Technical Context

## Stack

**Python**: 3.11+ (runtime tested: 3.13)
**Database**: PostgreSQL 16 with pgvector
**Orchestration**: Prefect 3.1.9 (Docker work pool) or direct GPU runner
**API**: FastAPI with asyncpg
**NLP**: spaCy (GPU-enabled via torch), sentence-transformers
**LLM**: Ollama (optional, GPU-enabled)
**Container**: Docker with NVIDIA runtime

## Dependencies

**Core**: FastAPI, Prefect, prefect-docker, asyncpg, Alembic
**NLP**: spaCy[cuda121], sentence-transformers, transformers
**GPU**: torch (CUDA-enabled), torchvision, torchaudio (GPU verified)
**Extraction**: trafilatura, readability-lxml, beautifulsoup4
**Utilities**: ijson, pybloom-live, tldextract, docker, pillow, pytesseract

## Hardware

**GPU**: NVIDIA GeForce RTX 3060 (6GB VRAM, CUDA 13.0)
**Docker**: NVIDIA runtime enabled
**OS**: Windows 10 with WSL2/Docker Desktop

## Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start services (Postgres + Prefect stack + API + agent)
docker-compose --profile base up -d

# Deploy Prefect flows
python deploy_flows.py

# Queue extraction via Prefect deployment
python queue_extraction_prefect.py

# Prefect UI
Start-Process "http://localhost:4200"
```

## MCP Tooling

- Label Studio MCP
  - Command: `python -m label_studio_mcp`
  - Env: `LABEL_STUDIO_API_KEY`, `LABEL_STUDIO_URL`
  - Config client in `.cursor/mcp.json`

- Prefect MCP
  - Command: `uvx --from prefect-mcp prefect-mcp-server`
  - Env (Cloud): `PREFECT_API_URL`, `PREFECT_API_KEY`
  - Env (Self-hosted): `PREFECT_API_URL` (e.g., http://localhost:4200/api)

- Docker MCP (planned), Sequential Thinking MCP (planned), Context7 MCP (planned)
  - Register entries in `.cursor/mcp.json` when endpoints/packages are finalized

