# Canonical Paths & Datasets

**Single Source of Truth for BPO Intelligence Pipeline**  
**Last Updated:** October 31, 2025

---

## ⚠️ CRITICAL: Canonical Dataset

### Production Dataset (USE THIS)

```
data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310 (1).json
```

**Status:** ✅ CANONICAL - 45,000 documents  
**Format:** Raw JSON from web scraper  
**Preprocessing:** Must run through `scripts/preprocess.py` first

### Preprocessed Dataset (After Preprocessing)

```
data/processed/preprocessed.jsonl
```

**Status:** ✅ CANONICAL - Output of `scripts/preprocess.py`  
**Format:** JSONL (one JSON object per line)  
**Ready for:** All extraction scripts

---

## ❌ DEPRECATED - DO NOT USE

### Invalid/Test Datasets

```
❌ data/preprocessed/dataset_45000_converted.jsonl     # FAILED CONVERSION
❌ data/preprocessed/test_5000_rich.jsonl              # Test fixture only
❌ data/preprocessed/bpo_preprocessed_full.jsonl       # Legacy test data
❌ data/preprocessed/test_*.jsonl                      # All test files
```

**Why Deprecated:**
- `dataset_45000_converted.jsonl` - Failed conversion with data corruption
- Test fixtures - Not the full 45K corpus, only for unit tests
- Legacy files - Superseded by canonical pipeline

---

## Extraction Scripts

### Active Scripts (Use These)

#### 1. Prefect-Orchestrated Extraction (RECOMMENDED)

```bash
# Deploy flows
python deploy_flows.py

# Queue extraction job
python queue_extraction_prefect.py

# Monitor at http://localhost:4200
```

**Script:** `queue_extraction_prefect.py`  
**Dataset:** `data/processed/preprocessed.jsonl`  
**Features:**
- ✅ Full heuristics-first pipeline
- ✅ Retry logic
- ✅ Progress monitoring
- ✅ Error handling
- ✅ Caching

#### 2. Direct Flow Extraction

```bash
python run_extraction.py
```

**Script:** `run_extraction.py`  
**Dataset:** `data/processed/preprocessed.jsonl`  
**Features:**
- ✅ Full heuristics-first pipeline
- ✅ Runs Prefect flow directly (no deployment)
- ✅ Good for testing

#### 3. Standalone Extraction (No Prefect)

```bash
python run_standalone_extraction.py
```

**Script:** `run_standalone_extraction.py`  
**Dataset:** `data/processed/preprocessed.jsonl`  
**Features:**
- ✅ Full heuristics-first pipeline
- ✅ No Prefect overhead
- ✅ Direct asyncpg connection

#### 4. Simple Extraction (Minimal)

```bash
python run_simple_extraction.py
```

**Script:** `run_simple_extraction.py`  
**Dataset:** `data/processed/preprocessed.jsonl` (configurable)  
**Features:**
- ⚠️ Simplified pipeline (minimal heuristics)
- ⚠️ No Prefect orchestration
- ⚠️ Good for quick testing, not production

#### 5. API-Triggered Extraction

```bash
python trigger_extraction_api.py
```

**Script:** `trigger_extraction_api.py`  
**Dataset:** `data/processed/preprocessed.jsonl`  
**Features:**
- ✅ Triggers extraction via FastAPI endpoint
- ✅ Full heuristics-first pipeline

### Deprecated Scripts (Do Not Use)

```
❌ run_gpu_extraction.py        # DELETED - Bypassed heuristics, used deprecated dataset
❌ convert_raw_dataset.py       # DELETED - Use scripts/preprocess.py instead
```

---

## Data Processing Pipeline

### Step 1: Raw Data → Preprocessed

```bash
python scripts/preprocess.py \
  --input data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310\ \(1\).json \
  --output data/processed/preprocessed.jsonl
```

**Input:** Raw JSON (45K documents)  
**Output:** JSONL (one line per document)  
**Why:** Streaming processing, memory efficient

### Step 2: Preprocessed → Extracted Entities

```bash
# Option A: Prefect (recommended)
python deploy_flows.py
python queue_extraction_prefect.py

# Option B: Direct
python run_extraction.py

# Option C: Standalone
python run_standalone_extraction.py
```

**Input:** `data/processed/preprocessed.jsonl`  
**Output:** PostgreSQL database (`bpo_intel`)  
**Pipeline:**
1. Heuristics-first extraction (primary)
2. Regex patterns (secondary)
3. spaCy NER (fallback)

---

## Heuristics Files

### Active Heuristics (Heuristics/)

```
✅ Heuristics/company_aliases_clean.json    # 3,925 company name aliases
✅ Heuristics/products.json                 # Product taxonomy
✅ Heuristics/tech_terms.json               # Technology terms
✅ Heuristics/countries.json                # Geographic entities
✅ Heuristics/taxonomy_*.json               # Hierarchical taxonomy
✅ Heuristics/partnerships.json             # Provider-partner relationships
✅ Heuristics/ner_relationships.json        # Main heuristics (129 providers, 940 products)
✅ Heuristics/content_types.json            # Content categorization
✅ Heuristics/version.json                  # Version tracking
```

**Loaded by:** `src/heuristics/loader.py`  
**Used by:** All extraction scripts

### Heuristics Validation

```bash
# Validate taxonomy
python scripts/validate_taxonomy.py

# Consolidate taxonomy
python scripts/consolidate_taxonomy.py
```

---

## Database Schema

### Primary Schema File

```
ops/schema.sql
```

**Status:** ✅ CANONICAL - Full schema reference  
**Tables:**
- `documents` - Source documents
- `chunks` - Document chunks
- `entities` - Extracted entities
- `relationships` - Entity relationships
- `entity_mentions` - Entity mention spans

### Migration Files

```
ops/init-scripts/01_init.sql              # Bootstrap SQL
alembic/versions/001_initial_schema.py    # Initial migration
```

**Note:** Alembic migrations are tracked but not actively used (schema applied via init-scripts)

---

## Docker Volumes

### Volume Mounts (docker-compose.yml)

```yaml
volumes:
  - "./data:/data"                        # Data directory
  - "./Heuristics:/heuristics"            # Heuristics files
  - "./src:/app/src"                      # Source code
  - "./ops/init-scripts:/docker-entrypoint-initdb.d"  # DB init scripts
  - "./ops/secrets/postgres_password.txt:/run/secrets/postgres_password"  # DB password
```

**Status:** ✅ All relative paths (platform-neutral)

---

## Environment Variables

### Required Variables

```bash
# Database
DB_HOST=postgres                          # Docker service name
DB_PORT=5432                              # PostgreSQL port
DB_NAME=bpo_intel                         # Database name
DB_USER=postgres                          # Database user
DB_PASSWORD_FILE=/run/secrets/postgres_password  # Password file

# Prefect
PREFECT_API_URL=http://prefect-server:4200/api  # Prefect API

# Heuristics
HEURISTICS_DIR=/heuristics                # Heuristics directory
HEURISTICS_VERSION=2.0.0                  # Version

# Data
DATA_DIR=/data                            # Data directory

# GPU
NVIDIA_VISIBLE_DEVICES=all                # GPU visibility
```

---

## Directory Structure

```
BPO-Web/
├── data/
│   ├── raw/
│   │   └── dataset_webscrape-bpo_2025-10-13_10-15-17-310 (1).json  ← CANONICAL
│   ├── processed/
│   │   └── preprocessed.jsonl           ← CANONICAL (after preprocessing)
│   ├── preprocessed/                    ← DEPRECATED (old test files)
│   └── ollama/                          ← Optional (LLM models)
├── Heuristics/                          ← CANONICAL (entity heuristics)
├── src/
│   ├── api/                             ← FastAPI service
│   ├── flows/                           ← Prefect flows
│   ├── extraction/                      ← Extraction logic
│   └── heuristics/                      ← Heuristics loader/extractor
├── scripts/
│   ├── preprocess.py                    ← CANONICAL preprocessor
│   ├── validate_taxonomy.py             ← Heuristics validation
│   └── consolidate_taxonomy.py          ← Taxonomy consolidation
├── ops/
│   ├── schema.sql                       ← CANONICAL schema
│   ├── init-scripts/                    ← DB initialization
│   └── secrets/                         ← Secrets files
├── docker/
│   ├── Dockerfile.worker                ← GPU worker image
│   ├── Dockerfile.api                   ← API image
│   └── entrypoints/                     ← Container entrypoints
├── run_extraction.py                    ← Direct flow extraction
├── run_standalone_extraction.py         ← Standalone extraction
├── run_simple_extraction.py             ← Simplified extraction
├── queue_extraction_prefect.py          ← Prefect deployment runner
├── deploy_flows.py                      ← Prefect deployment setup
└── trigger_extraction_api.py            ← API-triggered extraction
```

---

## Quick Reference

### What to Use

| Task | Script | Dataset |
|------|--------|---------|
| **Production extraction** | `queue_extraction_prefect.py` | `data/processed/preprocessed.jsonl` |
| **Test extraction** | `run_extraction.py` | `data/processed/preprocessed.jsonl` |
| **No Prefect** | `run_standalone_extraction.py` | `data/processed/preprocessed.jsonl` |
| **Quick test** | `run_simple_extraction.py` | `data/processed/preprocessed.jsonl` |
| **Preprocess raw data** | `scripts/preprocess.py` | `data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310 (1).json` |

### What NOT to Use

| File | Status | Reason |
|------|--------|--------|
| `dataset_45000_converted.jsonl` | ❌ INVALID | Failed conversion |
| `test_*.jsonl` | ❌ TEST ONLY | Not full corpus |
| `run_gpu_extraction.py` | ❌ DELETED | Bypassed heuristics |
| `convert_raw_dataset.py` | ❌ DELETED | Use `scripts/preprocess.py` |

---

## Extraction Flow Architecture

### Multi-Tier Extraction Pipeline

```
Document → Heuristics Extractor → Regex Extractor → spaCy NER → Database
           (Primary)               (Secondary)       (Fallback)
```

**Tier 1: Heuristics** (Highest Confidence)
- Exact matches from `Heuristics/*.json`
- Company aliases, products, tech terms
- Confidence: 0.95-1.0

**Tier 2: Regex** (Medium Confidence)
- Pattern-based extraction
- URLs, emails, phone numbers
- Confidence: 0.7-0.85

**Tier 3: spaCy** (Lower Confidence)
- GPU-accelerated NER
- Catches entities missed by heuristics
- Confidence: 0.5-0.8

**All tiers write to PostgreSQL with pgvector embeddings**

---

## Port Reference

```
5432  - PostgreSQL (main database)
6432  - PgBouncer (connection pooler)
4200  - Prefect UI/API
8000  - FastAPI application
8082  - Label Studio (optional QC)
11434 - Ollama (optional LLM)
6379  - Redis (optional cache)
9090  - Prometheus (optional metrics)
3000  - Grafana (optional dashboards)
```

---

## Secrets Management

```
ops/secrets/postgres_password.txt    # Main DB password
```

**Mounted as:** `/run/secrets/postgres_password` in containers  
**Used by:** postgres, pgbouncer, prefect-agent, api services

---

## Common Commands

```bash
# Preprocess raw data
python scripts/preprocess.py

# Deploy Prefect flows
python deploy_flows.py

# Queue extraction (recommended)
python queue_extraction_prefect.py

# Monitor extraction
http://localhost:4200

# Check database
docker exec -it bpo-postgres psql -U postgres -d bpo_intel -c "SELECT COUNT(*) FROM entities;"

# Validate heuristics
python scripts/validate_taxonomy.py

# Check GPU
docker exec bpo-prefect-agent nvidia-smi
```

---

**This document is the SINGLE SOURCE OF TRUTH for all paths, datasets, and scripts in the BPO Intelligence Pipeline.**

**When in doubt, consult this file.**

---

**Last Updated:** October 31, 2025  
**Version:** 2.0.0
