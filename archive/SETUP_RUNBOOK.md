# BPO Intelligence Pipeline - Setup Runbook

**Version**: 1.0.0  
**Last Updated**: October 24, 2025  
**Target Platform**: Windows Server 2022 / Windows 11 with Docker Desktop

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: GPO-Based Automated Deployment](#phase-1-gpo-based-automated-deployment)
4. [Phase 2: Database Schema & Migrations](#phase-2-database-schema--migrations)
5. [Phase 3: Preprocessing Pipeline](#phase-3-preprocessing-pipeline)
6. [Phase 3.5: Content Extraction & Chunking](#phase-35-content-extraction--chunking)
7. [Phase 4: Temporal Workflow Orchestration](#phase-4-temporal-workflow-orchestration)
8. [Phase 5: Entity Extraction (Fast Path)](#phase-5-entity-extraction-fast-path)
9. [Phase 6: Storage & Idempotency](#phase-6-storage--idempotency)
10. [Phase 7: LLM Fallback (Optional)](#phase-7-llm-fallback-optional)
11. [Phase 8: Human QC (Optional)](#phase-8-human-qc-optional)
12. [Phase 9: Monitoring & Operations](#phase-9-monitoring--operations)
13. [Phase 10: Model Training (Optional)](#phase-10-model-training-optional)
14. [Troubleshooting](#troubleshooting)
15. [Redis vs Temporal: Memory & State Management](#redis-vs-temporal-memory--state-management)

---

## Architecture Overview

### Stack Components

```
┌─────────────────────────────────────────────────────────────┐
│                  BPO Intelligence Pipeline                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   API    │  │  Worker  │  │ Temporal │  │   UI     │  │
│  │ (FastAPI)│  │ (Python) │  │  Server  │  │ (Web UI) │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │             │              │              │         │
│       └─────────────┴──────────────┴──────────────┘         │
│                          │                                   │
│       ┌──────────────────┴──────────────────┐              │
│       │                                      │              │
│  ┌────▼─────┐  ┌──────────┐  ┌──────────┐  │              │
│  │ Postgres │  │PgBouncer │  │ pgvector │  │              │
│  │   +      │  │ (Pooling)│  │(Embeddings)│              │
│  │  Alembic │  └──────────┘  └──────────┘  │              │
│  └──────────┘                                │              │
│                                              │              │
│  Optional Services:                          │              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │              │
│  │  Ollama  │  │  Label   │  │ Prometheus│  │              │
│  │  (LLM)   │  │  Studio  │  │ + Grafana │  │              │
│  └──────────┘  └──────────┘  └──────────┘  │              │
│                                              │              │
└──────────────────────────────────────────────┘              
```

### Data Flow

```
Raw Data → Preprocessing → Chunking → Extraction → Storage
    │          │              │           │          │
    │          │              │           │          ▼
    │          │              │           │      PostgreSQL
    │          │              │           │      + pgvector
    │          │              │           │
    │          │              │           └─→ Heuristics
    │          │              │               + spaCy
    │          │              │               + Embeddings
    │          │              │               └→ (Optional) LLM
    │          │              │
    │          │              └─→ document_chunks table
    │          │
    │          └─→ preprocessed.jsonl (deduplicated, canonical)
    │
    └─→ D:\BPO-Project\data\raw\*.json
```

---

## Prerequisites

### Hardware Requirements

- **CPU**: 8+ cores recommended (4 minimum)
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 500GB SSD minimum (for data + Docker volumes)
- **GPU**: Optional (NVIDIA with CUDA support for Ollama LLM fallback)

### Software Requirements

- **OS**: Windows Server 2022 or Windows 11 Pro/Enterprise
- **Docker Desktop**: 4.25+ with WSL2 backend
- **PowerShell**: 7.0+
- **Domain**: Active Directory with GPO support
- **Network**: Access to Docker Hub, PyPI

---

## Phase 1: GPO-Based Automated Deployment

### 1.1 Prerequisites Installation via GPO

**Objective**: Automate installation of all prerequisites using Group Policy.

#### Step 1.1.1: Create GPO

1. Open **Group Policy Management Console** (gpmc.msc)
2. Create new GPO: **"BPO Intel Pipeline - Prerequisites"**
3. Scope: Target computers (Security Filtering or WMI filter)

#### Step 1.1.2: Configure Computer Startup Script

1. **Computer Configuration** → **Policies** → **Windows Settings** → **Scripts (Startup/Shutdown)**
2. **Startup** → **PowerShell Scripts** → **Add**
3. **Script**: `\\DOMAIN\SYSVOL\YourDomain\BPO\prereqs-install.ps1`
4. **Parameters**: (none)

**Script Location**: Copy `ops\gpo\prereqs-install.ps1` to SYSVOL

**What it does**:
- Enables WSL2, Hyper-V, Containers features
- Creates directory structure at `D:\BPO-Project`
- Installs Docker Desktop, Git, Node.js (for Context7 MCP)
- Configures firewall rules
- May trigger reboot if Windows features are enabled

#### Step 1.1.3: Deploy Project Files via GPP

1. **Computer Configuration** → **Preferences** → **Windows Settings** → **Files**
2. Add file copy operations:
   - Source: `\\DOMAIN\SYSVOL\YourDomain\BPO\*`
   - Destination: `D:\BPO-Project\`
   - Files to copy:
     - `docker-compose.yml`
     - `env.example` → `.env`
     - `requirements.txt`
     - `alembic.ini`
     - `alembic\**` (migrations)
     - `ops\**` (scripts, configs)
     - `Heuristics\**` (seed data)

#### Step 1.1.4: Deploy Secrets

1. **Computer Configuration** → **Preferences** → **Windows Settings** → **Files**
2. Add file copy:
   - Source: `\\DOMAIN\SYSVOL\YourDomain\BPO\secrets\postgres_password.txt` (protected share)
   - Destination: `D:\BPO-Project\ops\secrets\postgres_password.txt`
   - **Security**: Grant read access to LOCAL SYSTEM and BPO admins only

**Generate postgres_password.txt**:
```powershell
# Generate secure password
Add-Type -AssemblyName System.Web
$Password = [System.Web.Security.Membership]::GeneratePassword(32, 10)
$Password | Out-File -FilePath "postgres_password.txt" -NoNewline -Encoding ASCII
```

#### Step 1.1.5: Create Scheduled Task for Compose Startup

1. **Computer Configuration** → **Preferences** → **Control Panel Settings** → **Scheduled Tasks**
2. **Action**: Create
3. **Name**: BPO-Compose-Up
4. **Run as**: SYSTEM
5. **Run whether user is logged on or not**: Yes
6. **Trigger**: At startup, delay 2 minutes
7. **Action**: Run a program
   - **Program**: `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`
   - **Arguments**: `-ExecutionPolicy Bypass -File "D:\BPO-Project\ops\gpo\compose-up.ps1"`

**Script Location**: `D:\BPO-Project\ops\gpo\compose-up.ps1` (deployed via GPP)

**What it does**:
- Ensures Docker Desktop is running
- Verifies .env and secrets exist
- Pulls Docker images
- Starts services with `--profile base --profile dbpool`
- Logs to `D:\BPO-Project\ops\logs\compose-startup.log`

#### Step 1.1.6: Apply GPO

```powershell
# Link GPO to target OU
New-GPLink -Name "BPO Intel Pipeline - Prerequisites" -Target "OU=BPO-Servers,DC=domain,DC=com"

# Force update on target machine
gpupdate /force

# Verify GPO applied
gpresult /H gpresult.html
```

#### Step 1.1.7: Verify Deployment

After reboot, verify:

```powershell
# Check Docker
docker --version
docker compose version

# Check services
Set-Location D:\BPO-Project
docker compose ps

# Expected services:
# - bpo-postgres (healthy)
# - bpo-pgbouncer (healthy)
# - bpo-temporal (healthy)
# - bpo-temporal-ui (healthy)
# - bpo-api (healthy)
# - bpo-worker (running)
```

**Acceptance Criteria**:
- ✅ All 6 base services running
- ✅ Temporal UI accessible at http://localhost:8233
- ✅ API healthcheck returns 200: `curl http://localhost:8000/healthz`

---

## Phase 2: Database Schema & Migrations

**Objective**: Initialize the database with all Phase 2 schema improvements.

### 2.1 Run Initial Migration

```powershell
cd D:\BPO-Project

# Method 1: Via docker compose run (recommended)
docker compose run --rm api alembic upgrade head

# Method 2: Local (if Python installed)
# python -m alembic upgrade head
```

### 2.2 Verify Schema

```powershell
# Connect to database
docker compose exec postgres psql -U postgres -d bpo_intel

# Verify extensions
\dx

# Expected:
# vector | 0.7.4
# uuid-ossp
# pgcrypto

# Verify tables
\dt

# Expected tables:
# documents
# document_chunks
# entities
# relationships
# taxonomy_labels
# entity_embeddings
# pipeline_checkpoints
# schema_version
# alembic_version

# Check span_hash column on entities
\d entities

# Verify generated column:
# span_hash | bytea | generated always as (digest(span::text, 'sha256'::text)) stored

# Check unique constraint
\d+ entities

# Expected:
# uq_entities_doc_type_span UNIQUE (doc_id, type, span_hash)

# Check vector index on entity_embeddings
\d entity_embeddings

# Expected index:
# idx_entity_embeddings_vector hnsw (embedding::vector(384)) vector_cosine_ops

# Exit psql
\q
```

### 2.3 Seed Heuristics

```powershell
# Verify heuristics directory
Get-ChildItem D:\BPO-Project\Heuristics

# Expected files:
# - company_aliases.json (or company_aliases_clean.json)
# - countries.json
# - ner_relationships.json
# - tech_terms.json
# - version.json (create if missing)
```

**Create `Heuristics\version.json`**:
```json
{
  "version": "1.0.0",
  "updated_at": "2025-10-24T00:00:00Z",
  "description": "Initial heuristics set for BPO Intel Pipeline"
}
```

**Acceptance Criteria**:
- ✅ All tables created
- ✅ `span_hash` generated column exists
- ✅ Vector extension and HNSW index created
- ✅ Provenance fields (source, source_version, heuristics_version, confidence_method) present
- ✅ `document_chunks` table with (doc_id, seq) unique constraint
- ✅ ON DELETE CASCADE foreign keys verified

---

## Phase 3: Preprocessing Pipeline

**Objective**: Clean, deduplicate, and prepare raw data for chunking and extraction.

### 3.1 Input Schema

Raw data format (from `data\raw\*.json`):

```json
{
  "url": "https://example.com/page",
  "status": 200,
  "content_type": "text/html",
  "fetched_at": "2025-10-23T18:17:00Z",
  "title": "Example Page",
  "html": "<html>...</html>",
  "headers": {...}
}
```

### 3.2 Preprocessing Steps

The preprocessing script performs:

1. **URL Canonicalization**:
   - Remove tracking parameters
   - Normalize scheme/host
   - Use `tldextract` for robust parsing

2. **Deduplication**:
   - Bloom filter for fast URL membership test
   - Content hash (`_text_sha256`) for exact duplicate detection
   - LMDB/SQLite for persistent hash storage (if needed)

3. **404 & Soft-404 Detection**:
   - Drop HTTP 404/410/503
   - Detect "Page Not Found" patterns in content

4. **Boilerplate Removal**:
   - Detect list pages, navigation pages, thin content
   - Tag with `_is_list_page`, `_is_thin_content` for optional filtering

5. **Language Detection**:
   - Use `langcodes` library
   - Store in `_lang` field

6. **Alias Hits** (optional):
   - Precompute company/tech term hits from heuristics
   - Store in `_alias_hits` for priority ranking

### 3.3 Output Schema

```json
{
  "url": "https://example.com/page",
  "status": 200,
  "content_type": "text/html",
  "fetched_at": "2025-10-23T18:17:00Z",
  "title": "Example Page",
  "raw": {
    "html": "...",
    "headers": {...}
  },
  "_canonical_url": "https://example.com/page",
  "_text_sha256": "abcdef123456...",
  "_alias_hits": {
    "companies": ["Acme Corp", "Globex"],
    "technologies": ["AWS", "Docker"]
  },
  "_lang": "en",
  "_notes": ""
}
```

### 3.4 Run Preprocessing

```powershell
cd D:\BPO-Project

# Create preprocessing script (simplified example)
# In production, this would be a full Python module

docker compose run --rm worker python scripts/preprocess.py `
  --input /data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310.json `
  --output /data/processed/preprocessed.jsonl `
  --batch-size 1000
```

**Script pseudo-code**:

```python
import ijson  # Streaming JSON parser
import hashlib
from pybloom_live import BloomFilter

bloom = BloomFilter(capacity=100000, error_rate=0.001)
seen_hashes = set()

with open(input_file, 'rb') as infile:
    with open(output_file, 'w') as outfile:
        for item in ijson.items(infile, 'item'):
            # Canonicalize URL
            canonical = canonicalize_url(item['url'])
            
            # Check Bloom filter (fast)
            if canonical in bloom:
                continue  # Duplicate URL
            bloom.add(canonical)
            
            # Extract text and hash
            text = extract_text_from_html(item.get('html', ''))
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            
            # Check content hash
            if text_hash in seen_hashes:
                continue  # Duplicate content
            seen_hashes.add(text_hash)
            
            # Filter 404s, thin content, etc.
            if item['status'] != 200:
                continue
            if is_thin_content(text):
                continue
            
            # Build output record
            output_record = {
                'url': item['url'],
                'status': item['status'],
                'content_type': item.get('content_type'),
                'fetched_at': item.get('fetched_at'),
                'title': item.get('title'),
                'raw': {'html': item.get('html'), 'headers': item.get('headers')},
                '_canonical_url': canonical,
                '_text_sha256': text_hash,
                '_lang': detect_language(text),
                '_alias_hits': find_alias_hits(text, heuristics),
                '_notes': ''
            }
            
            outfile.write(json.dumps(output_record) + '\n')
```

**Acceptance Criteria**:
- ✅ `preprocessed.jsonl` created
- ✅ Duplicate URLs removed
- ✅ Duplicate content removed (by `_text_sha256`)
- ✅ 404/soft-404 filtered
- ✅ `_canonical_url` and `_text_sha256` present on all records
- ✅ Counts logged: total input, dropped (404, dupe_url, dupe_hash), output

---

## Phase 3.5: Content Extraction & Chunking

**Objective**: Deterministic text extraction and chunking before NER.

### 3.5.1 Extraction

**Tools**:
- **HTML**: trafilatura, readability-lxml
- **PDF**: pdfminer.six
- **DOCX**: unstructured (optional, heavy)

**Normalization**:
- Unicode NFKC
- Whitespace normalization
- Preserve original offsets mapping

### 3.5.2 Chunking Strategy

**Parameters** (from `.env`):
- `CHUNK_SIZE=1500` (chars)
- `CHUNK_OVERLAP=175` (chars)

**Algorithm**:
1. Split on sentence boundaries (use `langcodes` + spaCy sentencizer)
2. Accumulate sentences until ~1500 chars
3. Create chunk with 175-char overlap from previous chunk

**Schema**: Store in `document_chunks` table

### 3.5.3 Run Chunking

```powershell
docker compose run --rm worker python scripts/chunk_documents.py `
  --input /data/processed/preprocessed.jsonl `
  --chunk-size 1500 `
  --overlap 175
```

**Pseudo-code**:

```python
import asyncpg

async def chunk_documents():
    pool = await asyncpg.create_pool(...)
    
    with open('preprocessed.jsonl') as f:
        for line in f:
            doc = json.loads(line)
            
            # Insert document
            doc_id = await insert_document(pool, doc)
            
            # Extract text
            text = extract_text_from_html(doc['raw']['html'])
            
            # Normalize
            text = normalize_text(text)
            
            # Chunk
            chunks = chunk_text(text, chunk_size=1500, overlap=175)
            
            # Insert chunks
            for seq, chunk_text in enumerate(chunks):
                chunk_hash = hashlib.sha256(chunk_text.encode()).hexdigest()
                await pool.execute(
                    """
                    INSERT INTO document_chunks (doc_id, seq, text, text_sha256)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (doc_id, seq) DO NOTHING
                    """,
                    doc_id, seq, chunk_text, chunk_hash
                )
```

**Acceptance Criteria**:
- ✅ All documents in `preprocessed.jsonl` inserted into `documents` table
- ✅ `document_chunks` populated with chunked text
- ✅ Each chunk has `text_sha256`
- ✅ Unique constraint (doc_id, seq) enforced
- ✅ Span offsets verified on sample (100 docs)

---

## Phase 4: Temporal Workflow Orchestration

**Objective**: Orchestrate extraction pipeline with Temporal for resilience.

### 4.1 Start Temporal Workflow

```powershell
# Verify Temporal is running
docker compose ps temporal temporal-ui

# Check Temporal UI
Start-Process "http://localhost:8233"

# Trigger workflow via API
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/run" `
  -ContentType "application/json" `
  -Body '{"source_path": "/data/processed/preprocessed.jsonl"}'

# Response:
# {
#   "workflow_id": "process-documents-abc123",
#   "run_id": "xyz789",
#   "status": "running"
# }
```

### 4.2 Monitor Workflow in Temporal UI

1. Open http://localhost:8233
2. Navigate to **Workflows**
3. Find `ProcessDocumentsWorkflow`
4. View:
   - Execution history
   - Activity status
   - Heartbeats
   - Checkpoints
   - Retry attempts

### 4.3 Checkpointing

**Checkpoint Frequency**: Every 1000 documents

**Checkpoint Storage**: `pipeline_checkpoints` table

**Resume on Failure**:

```powershell
# If workflow fails, simply restart - it will resume from last checkpoint
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/run" `
  -Body '{"source_path": "/data/processed/preprocessed.jsonl"}'
```

### 4.4 Continue-as-New

**Threshold**: 5000 documents per workflow run

**Behavior**: Automatically continues as new workflow with updated offset

**Monitor**:
- Check Temporal UI for workflow chain
- Each run processes up to 5000 docs
- State passed via `continue_as_new(args=[new_input])`

**Acceptance Criteria**:
- ✅ Workflow starts successfully
- ✅ Activities heartbeat visible in Temporal UI
- ✅ Checkpoints saved every 1000 docs
- ✅ Workflow resumes from checkpoint on failure
- ✅ Continue-as-new triggers at 5000 docs
- ✅ `/run` API returns workflow_id and run_id

---

## Phase 5: Entity Extraction (Fast Path)

**Objective**: Extract entities using heuristics → spaCy → embeddings → (optional) LLM cascade.

### 5.1 Extraction Tiers

**Tier 1: Heuristics** (Fastest, highest confidence)
- Load from `D:\BPO-Project\Heuristics\*.json`
- Regex patterns for MONEY, PERCENT, DATE
- Alias maps for COMPANY, TECHNOLOGY
- Confidence: 0.85+

**Tier 2: spaCy NER** (Fast, good confidence)
- Model: `en_core_web_sm`
- Entity types: PERSON, ORG, LOC, GPE
- Confidence: 0.70+

**Tier 3: Embeddings** (Moderate speed, lower confidence)
- Model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- KNN search in `entity_embeddings` table
- Threshold: cosine similarity ≥ 0.62
- Confidence: 0.62+

**Tier 4: LLM Fallback** (Slowest, variable confidence)
- Model: Ollama `llama3.2:3b`
- Only for ambiguous cases near thresholds
- Strict JSON schema validation
- Temperature=0, top_p=0
- Confidence: 0.50+

### 5.2 Confidence Fusion

When multiple tiers match the same span:

```python
final_conf = max(heuristic_conf, spacy_conf, embedding_conf, llm_conf)
confidence_method = f"{tier1},{tier2},..."  # e.g. "heuristics+spacy"
```

### 5.3 Normalized Values

**MONEY**:
```json
{
  "amount": 1234.56,
  "currency": "USD",
  "surface": "$1,234.56"
}
```

**DATE**:
```json
{
  "date": "2025-10-24",
  "granularity": "day",
  "surface": "Oct 24, 2025"
}
```

**PERCENT**:
```json
{
  "value": 0.17,
  "surface": "17%"
}
```

**LOC**:
```json
{
  "surface": "São Paulo",
  "iso2": "BR-SP"
}
```

### 5.4 Span Storage

**Format**:
```json
{
  "chunk_seq": 2,
  "start": 145,
  "end": 160,
  "surface": "Acme Corp"
}
```

**Hash**: `span_hash` generated column ensures uniqueness

**Acceptance Criteria**:
- ✅ ≥90% of entities labeled at chunk level
- ✅ LLM usage <15% of total entities
- ✅ Per-type precision on 200-doc gold set ≥ baseline
- ✅ Confidence method recorded (e.g. "heuristics_only", "heuristics+spacy")
- ✅ Provenance fields populated (source, source_version, heuristics_version)

---

## Phase 6: Storage & Idempotency

**Objective**: Store entities and relationships idempotently.

### 6.1 UPSERT Keys

**documents**:
- Unique on `text_sha256`
- ON CONFLICT UPDATE: title, metadata (keep newer)

**entities**:
- Unique on `(doc_id, type, span_hash)`
- ON CONFLICT UPDATE: `conf = GREATEST(EXCLUDED.conf, conf)`

**relationships**:
- Unique on `(doc_id, head_entity, tail_entity, type, evidence->>'pattern' NULLS FIRST)`
- ON CONFLICT DO UPDATE SET conf = ...

**taxonomy_labels**:
- Unique on `(doc_id, industry, service, technology, category, source)`
- ON CONFLICT: keep higher confidence

**entity_embeddings**:
- Primary key on `entity_id`
- ON CONFLICT UPDATE: embedding, model_name (if newer)

### 6.2 Idempotency Test

**Test**: Run workflow twice with identical input

```powershell
# Run 1
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/run" `
  -Body '{"source_path": "/data/processed/test_sample.jsonl"}'

# Wait for completion (check Temporal UI)

# Run 2 (identical input)
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/run" `
  -Body '{"source_path": "/data/processed/test_sample.jsonl"}'
```

**Verify**:

```sql
-- Check counts are identical after both runs
SELECT 'documents' AS tbl, COUNT(*) FROM documents
UNION ALL
SELECT 'entities', COUNT(*) FROM entities
UNION ALL
SELECT 'relationships', COUNT(*) FROM relationships;

-- Check text_sha256 checksums
SELECT text_sha256, COUNT(*) FROM documents GROUP BY text_sha256 HAVING COUNT(*) > 1;
-- Should return 0 rows
```

**Acceptance Criteria**:
- ✅ Reruns with identical input produce identical counts
- ✅ Checksums match between runs
- ✅ No duplicate entities/relationships (verified by unique constraints)
- ✅ Confidence values updated correctly (GREATEST logic)

---

## Phase 7: LLM Fallback (Optional)

**Objective**: Use Ollama for ambiguous entity extraction when heuristics/spaCy/embeddings are inconclusive.

### 7.1 Enable Ollama Profile

```powershell
cd D:\BPO-Project

# Start Ollama service
docker compose --profile llm up -d ollama

# Pull model
docker compose exec ollama ollama pull llama3.2:3b

# Verify model
docker compose exec ollama ollama list
```

### 7.2 Budget Guard

**Configuration** (`.env`):
- `OLLAMA_MAX_FALLBACKS_PER_MINUTE=50`

**Implementation**: Track fallback rate, reject requests exceeding limit

### 7.3 Prompt Template

```python
system_prompt = """
You are an NER assistant. Extract entities from the provided text.
Output ONLY valid JSON, no markdown, no explanations.

Schema:
{
  "entities": [
    {"type": "PERSON|ORG|LOC|MONEY|DATE|PERCENT", "surface": "...", "norm_value": {...}}
  ]
}
"""

user_prompt = f"Extract entities from: \"{text_chunk}\""
```

### 7.4 Validation

```python
import fastjsonschema

schema = {
    "type": "object",
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["PERSON", "ORG", "LOC", "MONEY", "DATE", "PERCENT"]},
                    "surface": {"type": "string"},
                    "norm_value": {"type": "object"}
                },
                "required": ["type", "surface"]
            }
        }
    },
    "required": ["entities"]
}

validate = fastjsonschema.compile(schema)

try:
    validate(llm_response)
except fastjsonschema.JsonSchemaException as e:
    # Retry once with "your JSON was invalid" system reminder
    pass
```

**Acceptance Criteria**:
- ✅ Ollama running and model loaded
- ✅ Budget guard enforces max fallbacks/min
- ✅ Temperature=0, top_p=0 for determinism
- ✅ JSON schema validation rejects invalid responses
- ✅ Provenance: `source='llm'`, `source_version='llama3.2:3b'`

---

## Phase 8: Human QC (Optional)

**Objective**: Enable Label Studio for human review and adjudication.

### 8.1 Enable Label Studio

```powershell
cd D:\BPO-Project

# Start Label Studio
docker compose --profile qc up -d label-studio

# Open UI
Start-Process "http://localhost:8082"

# Default credentials (change after first login):
# Username: admin@bpo-intel.local
# Password: (from postgres_password.txt)
```

### 8.2 Configure Project

1. Create project: "BPO Entity Review"
2. Import labeling config from `label_config.xml`
3. Configure export format: JSON

### 8.3 Sampling Strategy

**Sample by confidence buckets**:
- High confidence (0.85+): 5% sample
- Medium confidence (0.65-0.85): 20% sample
- Low confidence (<0.65): 100% sample

```sql
-- Export sample for review
COPY (
    SELECT 
        e.id,
        e.surface,
        e.type,
        e.conf,
        c.text AS chunk_text,
        e.span
    FROM entities e
    JOIN document_chunks c ON e.chunk_id = c.id
    WHERE e.conf < 0.85
    AND random() < CASE 
        WHEN e.conf >= 0.65 THEN 0.20
        ELSE 1.0
    END
    LIMIT 1000
) TO '/data/qc/sample_for_review.json' WITH (FORMAT json);
```

### 8.4 Adjudication Workflow

1. Import sample into Label Studio
2. Human reviewers correct/confirm entities
3. Export adjudicated data
4. Update entities table:

```sql
-- Update from adjudications
UPDATE entities
SET 
    surface = adj.corrected_surface,
    conf = 0.95,  -- High confidence after human review
    source = 'human_qc',
    updated_at = NOW()
FROM adjudications adj
WHERE entities.id = adj.entity_id;
```

5. Update alias maps:

```sql
-- Augment alias maps (staged, not hot-merged)
INSERT INTO alias_augmentations (term, type, source)
SELECT DISTINCT surface, type, 'human_qc'
FROM entities
WHERE source = 'human_qc'
AND conf >= 0.95;
```

**Acceptance Criteria**:
- ✅ Label Studio accessible
- ✅ Sample exported and imported
- ✅ Adjudications update entities table
- ✅ Alias maps updated behind `reviewed` flag
- ✅ QC guidelines documented in `Heuristics\docs\qc_guide.md`

---

## Phase 9: Monitoring & Operations

**Objective**: Observability and operational metrics.

### 9.1 Enable Metrics Profile

```powershell
cd D:\BPO-Project

# Start Prometheus + Grafana
docker compose --profile metrics up -d prometheus grafana

# Open Grafana
Start-Process "http://localhost:3000"

# Default credentials:
# Username: admin
# Password: (from postgres_password.txt)
```

### 9.2 Prometheus Configuration

**File**: `ops\prometheus.yml`

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'bpo-api'
    static_configs:
      - targets: ['api:8000']
  
  - job_name: 'temporal'
    static_configs:
      - targets: ['temporal:7233']
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:9187']  # postgres_exporter
```

### 9.3 Grafana Dashboards

**Provisioned Dashboards** (place in `ops\grafana-dashboards\`):

1. **Pipeline Overview**:
   - Documents processed/hour
   - Entities extracted/hour
   - Workflow success rate
   - Activity duration (P50, P95, P99)

2. **Database Metrics**:
   - Connection pool usage
   - Query latency
   - Autovacuum status
   - Table sizes

3. **Temporal Metrics**:
   - Workflow backlog
   - Activity task queue depth
   - Retry counts
   - Continue-as-new frequency

4. **Extraction Quality**:
   - Confidence distribution
   - LLM fallback rate
   - Failed documents
   - Per-type extraction counts

### 9.4 Structured Logging

**Log Format** (JSON):

```json
{
  "timestamp": "2025-10-24T23:00:00Z",
  "level": "INFO",
  "service": "worker",
  "activity_name": "extract_entities_batch_activity",
  "doc_id": "abc123",
  "chunk_seq": 2,
  "entity_count": 15,
  "relationship_count": 7,
  "lat_ms": 345,
  "conf_avg": 0.78,
  "drop_reason": null
}
```

**View Logs**:

```powershell
# Worker logs
docker compose logs -f --tail=100 worker

# API logs
docker compose logs -f --tail=100 api

# Temporal logs
docker compose logs -f --tail=100 temporal
```

### 9.5 Alerts (Optional)

**Alertmanager Configuration** (if using Prometheus Alertmanager):

```yaml
groups:
  - name: bpo_pipeline
    interval: 1m
    rules:
      - alert: HighFailureRate
        expr: rate(pipeline_failed_documents_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High document failure rate"
      
      - alert: LLMFallbackExceeded
        expr: rate(llm_fallback_total[1m]) > 50
        for: 1m
        annotations:
          summary: "LLM fallback budget exceeded"
      
      - alert: DBConnectionPoolExhausted
        expr: pgbouncer_active_connections / pgbouncer_max_connections > 0.9
        for: 2m
        annotations:
          summary: "Database connection pool near capacity"
```

**Acceptance Criteria**:
- ✅ Prometheus collecting metrics from API, Temporal, Postgres
- ✅ Grafana dashboards show real-time metrics
- ✅ Structured logs in JSON format
- ✅ Alerts configured for critical thresholds

---

## Phase 10: Model Training (Optional)

**Objective**: Fine-tune a transformer model on gold-labeled data.

### 10.1 Evaluation Harness

**Script**: `scripts/evaluate_ner.py`

**Metrics**:
- Per-type precision, recall, F1 (macro/micro)
- Confusion matrix
- PR curves

**Baseline**: Frozen evaluation set (200 docs with gold labels)

**Run**:

```powershell
docker compose run --rm worker python scripts/evaluate_ner.py `
  --gold-data /data/qc/gold_labels.json `
  --predictions /data/eval/predictions.json `
  --output /data/eval/metrics.json
```

### 10.2 Model Training

**Model**: DistilBERT fine-tuned for NER

**Data**: Human-adjudicated entities from Label Studio

**Framework**: Transformers + Hugging Face Trainer

**Script**: `scripts/train_ner_model.py`

```powershell
docker compose run --rm --gpus all worker python scripts/train_ner_model.py `
  --train-data /data/qc/train.json `
  --val-data /data/qc/val.json `
  --model-name distilbert-base-uncased `
  --output /data/models/ner_distilbert_v1 `
  --epochs 3 `
  --batch-size 16
```

### 10.3 Model Promotion

**Regression Check**:

```powershell
# Evaluate new model
docker compose run --rm worker python scripts/evaluate_ner.py `
  --gold-data /data/qc/gold_labels.json `
  --model /data/models/ner_distilbert_v1 `
  --output /data/eval/distilbert_v1_metrics.json

# Compare to baseline
python scripts/compare_metrics.py `
  --baseline /data/eval/baseline_metrics.json `
  --candidate /data/eval/distilbert_v1_metrics.json
```

**Promote if**:
- F1 improvement on priority entity types (e.g. COMPANY, MONEY)
- No regression on high-confidence types
- Inference latency acceptable (<500ms/doc)

**Update Configuration**:

```powershell
# Update .env
Set-Content -Path .env -Value (Get-Content .env | ForEach-Object {
    $_ -replace 'EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2', 
                 'EMBEDDING_MODEL=/data/models/ner_distilbert_v1'
})

# Restart worker
docker compose restart worker
```

**Acceptance Criteria**:
- ✅ Evaluation harness calculates per-type precision/recall/F1
- ✅ Baseline metrics stored for comparison
- ✅ New models pass regression check before promotion
- ✅ Model version tracked in entity provenance

---

## Troubleshooting

### Common Issues

#### 1. Docker Desktop Not Starting

**Symptoms**:
- `compose-up.ps1` times out waiting for Docker
- `docker info` returns error

**Solution**:
```powershell
# Check WSL2 status
wsl --list --verbose

# Ensure default WSL2 distro is set
wsl --set-default Ubuntu

# Restart Docker Desktop
Stop-Process -Name "Docker Desktop" -Force
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# Wait 30 seconds
Start-Sleep -Seconds 30

# Verify
docker info
```

#### 2. Postgres Connection Refused

**Symptoms**:
- API healthcheck fails
- Worker logs show connection errors

**Solution**:
```powershell
# Check Postgres health
docker compose ps postgres

# If unhealthy, check logs
docker compose logs postgres

# Common issue: secrets file not found
Test-Path "D:\BPO-Project\ops\secrets\postgres_password.txt"

# If missing, create and restart
"YourPasswordHere" | Out-File -FilePath "D:\BPO-Project\ops\secrets\postgres_password.txt" -NoNewline
docker compose restart postgres
```

#### 3. Temporal UI Shows "Connection Refused"

**Symptoms**:
- UI loads but can't connect to Temporal server

**Solution**:
```powershell
# Check Temporal server health
docker compose exec temporal tctl cluster health

# If unhealthy, check Postgres connection
docker compose logs temporal | Select-String -Pattern "error|failed"

# Restart Temporal
docker compose restart temporal

# Wait for healthy status
docker compose ps temporal
```

#### 4. Alembic Migration Fails

**Symptoms**:
- `alembic upgrade head` returns error
- Tables not created

**Solution**:
```powershell
# Check current revision
docker compose exec postgres psql -U postgres -d bpo_intel -c "SELECT version_num FROM alembic_version;"

# If mismatch, stamp with current version
docker compose run --rm api alembic stamp head

# Force re-run migration
docker compose run --rm api alembic upgrade head --sql > migration.sql
# Review migration.sql, then apply manually if needed
```

#### 5. Workflow Stuck in "Running" State

**Symptoms**:
- Workflow shows running in Temporal UI but no activity progress
- No heartbeats visible

**Solution**:
```powershell
# Check worker logs
docker compose logs worker | Select-String -Pattern "error|exception"

# Verify worker is connected to Temporal
docker compose logs worker | Select-String -Pattern "Worker started"

# If worker not running activities, restart
docker compose restart worker

# If workflow is truly stuck, cancel and restart
# (Use Temporal UI: Workflow → Actions → Terminate)
```

#### 6. High Memory Usage

**Symptoms**:
- Worker container using >8GB RAM
- System slow/unresponsive

**Solution**:
```powershell
# Check container stats
docker stats bpo-worker

# If using >8GB, likely not using streaming
# Verify preprocessing/chunking scripts use server-side cursors

# Temporary fix: Reduce batch size
# Edit .env:
# PREPROCESS_BATCH_SIZE=500  # down from 1000

# Restart worker
docker compose restart worker
```

---

## Redis vs Temporal: Memory & State Management

### Do You Need Redis?

**TL;DR**: **No, Redis is NOT required.** Temporal + Postgres provide sufficient state management for this pipeline.

### Comparison

| Feature | Temporal + Postgres | Redis |
|---------|-------------------|-------|
| Workflow State | ✅ Durable (Postgres) | ❌ Ephemeral (unless persistence enabled) |
| Retry Logic | ✅ Built-in with RetryPolicy | ⚠️ Manual implementation |
| Checkpointing | ✅ Native (workflow history) | ⚠️ Manual implementation |
| Idempotency | ✅ Workflow ID deduplication | ⚠️ Manual keys |
| Observability | ✅ Temporal UI (full history) | ⚠️ Redis CLI only |
| Scalability | ✅ Horizontal (continue-as-new) | ✅ Horizontal (but requires clustering) |
| Failure Recovery | ✅ Automatic (workflow replay) | ❌ Manual (detect failure, reload state) |

### When to Add Redis (Optional)

**Use Case 1: Fast In-Memory Cache**
- **Purpose**: Cache alias maps, KNN results for repeated lookups
- **TTL**: 1 hour (automatically expires)
- **Example**: Cache top 1000 company names for fast matching

```python
import redis

redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Cache company aliases
redis_client.setex('alias:acme', 3600, json.dumps({'canonical': 'Acme Corp', 'variants': ['ACME', 'Acme Inc']}))

# Lookup
cached = redis_client.get('alias:acme')
if cached:
    alias = json.loads(cached)
```

**Use Case 2: Rate Limiting (LLM Fallback)**
- **Purpose**: Enforce `OLLAMA_MAX_FALLBACKS_PER_MINUTE=50`
- **Implementation**: Sliding window counter in Redis

```python
from redis import Redis

redis_client = Redis(host='redis', port=6379)

def check_llm_rate_limit() -> bool:
    key = "llm:fallback:count"
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, 60)  # 1 minute window
    return current <= 50
```

**Use Case 3: Short-Lived Deduplication**
- **Purpose**: Fast dedupe across multiple workers (avoid DB lookups)
- **Example**: Bloom filter for URL canonicalization

**Enable Redis**:

```powershell
cd D:\BPO-Project

# Start Redis
docker compose --profile cache up -d redis

# Verify
docker compose exec redis redis-cli ping
# Expected: PONG

# Configure workers to use Redis
# Update .env:
REDIS_ENABLED=true
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_TTL=3600

# Restart workers
docker compose restart worker
```

### Summary

- **Temporal + Postgres**: Handles workflow state, retries, checkpoints, idempotency ✅
- **Redis (Optional)**: Use for fast caching, rate limiting, short-lived dedupe ⚠️
- **Recommendation**: Start without Redis. Add later if specific caching needs arise.

---

## Next Steps

1. **Verify Phase 1-2**: Ensure all services running and schema applied
2. **Run Preprocessing**: Process raw data → `preprocessed.jsonl`
3. **Run Chunking**: Chunk documents → `document_chunks` table
4. **Start Extraction Workflow**: Trigger Temporal workflow via API
5. **Monitor**: Watch Temporal UI and logs for progress
6. **Evaluate**: Check extraction quality on sample
7. **Iterate**: Adjust thresholds, heuristics, or enable optional services (LLM, QC, metrics)

---

## Support & Documentation

- **Temporal UI**: http://localhost:8233
- **API Docs**: http://localhost:8000/docs (FastAPI auto-docs)
- **Grafana**: http://localhost:3000 (if metrics profile enabled)
- **Label Studio**: http://localhost:8082 (if qc profile enabled)

**Logs**:
- Compose startup: `D:\BPO-Project\ops\logs\compose-startup.log`
- API: `docker compose logs api`
- Worker: `docker compose logs worker`
- Temporal: `docker compose logs temporal`

**Configuration Files**:
- Environment: `D:\BPO-Project\.env`
- Compose: `D:\BPO-Project\docker-compose.yml`
- Alembic: `D:\BPO-Project\alembic.ini`
- Heuristics: `D:\BPO-Project\Heuristics\*`

---

**End of Runbook** 🚀

