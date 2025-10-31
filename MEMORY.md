# BPO Intelligence Pipeline - Memory

## Project Structure

**Root**: `D:\BPO-Project\`

- `Heuristics/` - NER extraction data (taxonomy, aliases, synonyms)
- `scripts/` - Preprocessing and installation automation
  - `preprocess.py` - Streaming JSON parser (854MB+ support)
  - `install.ps1` - Automated installation with GPU checks
  - `validate_taxonomy.py` - Heuristics validation
- `docker-compose.yml` - Container orchestration (profiles: base, dbpool, llm, metrics, qc)
  - GPU support: worker + ollama (NVIDIA runtime)
- `alembic/` - Database migrations (postgresql with pgvector)
- `src/api/` - FastAPI service (asyncpg for PostgreSQL)
- `src/worker/` - Prefect worker utilities (GPU-enabled container hooks)
- `ops/gpo/` - PowerShell scripts for Windows domain GPO deployment
- `docs/` - Architecture documentation (NER_LABELS_AND_TAXONOMY.md)

## Data Taxonomy

**Heuristics Files**:
- `company_aliases_clean.json` (3,359 aliases) - Dict mapping alias → canonical
- `countries.json` (52 countries) - ISO codes, aliases (USA, U.S., etc.)
- `tech_terms.json` (20 terms) - Context-aware confidence (boosters/detractors arrays)
- `taxonomy_industries.json` (67 industries) - Hierarchical (id, name, level, parent_id, path)
- `taxonomy_services.json` (50 services) - BPO service categories
- `products.json` (1,072 products) - Brand/product names (NER tag: PRODUCT)
- `partnerships.json` (116 relationship types) - Company-to-company relations for Label Studio
- `version.json` - Schema versioning (currently 2.0.0)

**NER Labels**: COMPANY, LOCATION, PERSON, TECHNOLOGY, MONEY, PERCENT, DATE, PRODUCT (new)

**Confidence Tiers**: Heuristics (0.85+) → spaCy (0.70+) → Embeddings (0.62+) → LLM (0.50+)

## Database Schema

**Tables**:
- `documents` - Source URL, status, title, raw HTML, SHA256 hash
- `document_chunks` - Sequenced text chunks (seq, text, text_sha256, meta JSONB)
- `entities` - Type, span (JSONB), span_hash (SHA256 generated), confidence, source fields
- `relationships` - Head/tail entity IDs, type, confidence, evidence JSONB, chunk_id
- `taxonomy_labels` - Industry, service, technology, category, source, confidence
- `entity_embeddings` - Vector(384) for cosine similarity, model_name

**Indexes**:
- HNSW on entity_embeddings (vector_cosine_ops, m=16, ef_construction=64)
- Unique on (doc_id, type, span_hash) for entities
- GIN on documents.tsv for full-text search (optional)

**Provenance**: source, source_version, heuristics_version, confidence_method fields on entities/relationships

## Pipeline Flow

**Phase 3 (Preprocessing)**:
- **Input**: 854MB raw JSON (`data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310 (1).json`)
- **Streaming parser**: ijson library (don't load entire file into memory)
- **Deduplication**: Bloom filter (pybloom-live) for URLs, SHA256 content hashes
- **URL canonicalization**: tldextract + parameter stripping
- **Filtering**: Hard 404s, soft 404s, thin content, non-content pages
- **Text extraction**: trafilatura primary, readability-lxml fallback
- **Output**: `data/processed/preprocessed.jsonl` (JSON Lines, one doc per line)
- **Schema**: `{url, canonical_url, title, text, text_sha256, lang, fetched_at, status, content_type}`
- **Libraries**: ijson, pybloom-live, tldextract, trafilatura, beautifulsoup4, lxml

**Phase 4 (Prefect Orchestration)**:
- **Work Pool**: `default-pool` (Docker) – no manual namespace management
- **Deployment**: `document-extraction-pipeline/default`
  - Flow: `extract_documents_flow` (load_checkpoint → extract_entities_batch → store_entities)
  - Task runner: `ConcurrentTaskRunner` with Prefect-managed retries + caching
- **Trigger Options**: Prefect UI, CLI (`prefect deployment run ...`), or `queue_extraction_prefect.py`
- **Future Workflows**: validation + overnight work to be rewritten as Prefect flows (Temporal versions archived)
- **Worker Model**: Prefect agent container with CUDA runtime executes queued deployments

**Phase 5 (Extraction)**:
- Heuristics-first (company_aliases_clean.json loaded at startup)
- Regex: MONEY, PERCENT, DATE (Babel/dateparser, ISO 8601 normalization)
- spaCy: en_core_web_sm model (multi-lang fallback if _lang != en)
  - **GPU acceleration**: spacy.prefer_gpu() if NVIDIA runtime available
  - **CUDA**: Install spacy[cuda120] for GPU support
- Embeddings: sentence-transformers, cached inference results
  - **GPU acceleration**: device="cuda" when available (RTX 3060, CUDA 13.0)
  - **Model**: all-MiniLM-L6-v2 (384-dim, fast GPU inference)
- LLM: Ollama (strict budget guard, JSON schema validation)
  - **GPU**: Ollama with CUDA support via NVIDIA runtime

**Phase 6 (Storage)**:
- UPSERT keys: text_sha256 (documents), (doc_id, type, span_hash) (entities)
- ON CONFLICT DO UPDATE SET conf = GREATEST(EXCLUDED.conf, conf)
- ON DELETE CASCADE for FKs to documents

## Key Decisions

**Separate taxonomy files vs monolithic**: Separation of concerns (industries/services distinct from aliases), easier maintenance, load only needed taxonomy

**HNSW over IVFFlat**: Better query quality at scale (m=16, ef_construction=64)

**Prefect vs raw async/queue**: Built-in retries, result caching, deployment history, and UI observability without custom state machines.

**Prefect work pool architecture**: `default-pool` (Docker) handles extraction deployments; additional pools can be added for validation/orchestration flows instead of Temporal namespaces.

**Windows path mappings**: Use quotes in docker-compose: `"D:\\BPO-Project\\data:/data"`

**GPU acceleration**: Prefer CUDA when available (RTX 3060), fallback to CPU. Enabled for worker (spaCy, embeddings) and ollama (LLM inference)

**Streaming JSON parsing**: Use ijson library for 854MB files to avoid memory loading. Bloom filter for URL deduplication, SHA256 for content deduplication

**Automated installation**: scripts/install.ps1 with BuildKit optimization, GPU detection, validation, and dependency handling

## Hardware & GPU

**GPU**: NVIDIA GeForce RTX 3060 (6GB VRAM, CUDA 13.0)
- Docker NVIDIA runtime installed
- GPU available for spaCy NER, sentence-transformers embeddings, Ollama LLM
- Prefer GPU when available, fallback to CPU

**Preprocessing**: Handle 854MB raw JSON via streaming (no memory load)

## Assumptions & UNKNOWNs

- **UNKNOWN**: Production data volume → Assume <1M docs initially (HNSW config sufficient)
- **UNKNOWN**: QC staffing model → Assume Label Studio profiles optional (--profile qc to enable)
- **UNKNOWN**: LLM fallback rate → Assume <15% of chunks need LLM (heuristics cover 90%+)
- **ASSUMPTION**: Redis not needed (Prefect + PostgreSQL cover orchestration + persistence)

## Quick Commands

### Deployment
```bash
# Start all services
docker-compose --profile base up -d

# Check status
docker ps --filter "name=bpo-"

# Restart specific service
docker-compose --profile base restart worker

# View logs
docker logs bpo-worker --tail 50
```

### Database
```bash
# Connect to PostgreSQL
docker exec -it bpo-postgres psql -U postgres -d bpo_intel

# List tables
docker exec bpo-postgres psql -U postgres -d bpo_intel -c "\dt"

# Create schema manually (if Alembic fails)
Get-Content ops/schema.sql | docker exec -i bpo-postgres psql -U postgres -d bpo_intel

# Check extensions
docker exec bpo-postgres psql -U postgres -d bpo_intel -c "\dx"
```

### Heuristics
```bash
# Validate taxonomy
python scripts/validate_taxonomy.py

# Check version
Get-Content Heuristics/version.json | ConvertFrom-Json | Select-Object version

# Count entries
(Get-Content Heuristics/company_aliases_clean.json | ConvertFrom-Json).PSObject.Properties.Count
```

### Preprocessing
```bash
# Preprocess sample (1000 records)
docker exec bpo-worker python scripts/preprocess.py --input "/data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310 (1).json" --output /data/processed/test_1000.jsonl --limit 1000

# Check output
docker exec bpo-worker wc -l /data/processed/test_1000.jsonl
```

### Prefect Workflows
```bash
# Queue validation workflow
Invoke-RestMethod -Uri http://localhost:8000/api/orchestration/queue-validation -Method Post

# Queue overnight work
Invoke-RestMethod -Uri http://localhost:8000/api/orchestration/queue-work -Method Post -ContentType "application/json" -Body '[{"task_type":"review","code_path":"src/worker/","context":{}}]'

# List deployments
prefect deployment ls

# Recent flow runs
prefect flow-run ls --limit 10

# Prefect UI
# Open: http://localhost:4200
# Deployments + Flow Runs tabs show live status
```

### Testing
```bash
# Test API health
curl http://localhost:8000/healthz

# Test API root
curl http://localhost:8000/

# Check worker is running
docker logs bpo-worker | Select-String "Orchestration worker started"
```

### Monitoring
```bash
# Prefect UI
http://localhost:4200

# API Swagger docs (if enabled)
http://localhost:8000/docs

# Label Studio (requires --profile qc)
http://localhost:8082
```

## Orchestration

**Overnight Validation Workflow** (6 phases):
1. Verification: containers, packages, heuristics, database schema
2. Wait until 4:30 AM with heartbeat
3. Code review for operational readiness
4. Batch test: preprocess + extract 1000 records
5. Analytics: heuristics performance metrics
6. Reporting: markdown report, cleanup, update MEMORY.md

**Activities**: validation, code review, preprocessing, batch testing, analytics, reporting, cleanup

**Outputs**: `docs/VALIDATION_REPORT_[timestamp].md`, updated MEMORY.md with validation metrics

