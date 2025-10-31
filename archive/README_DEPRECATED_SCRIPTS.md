# Deprecated Scripts

This directory contains scripts that have been deprecated and archived for reference only.

**DO NOT USE THESE SCRIPTS FOR PRODUCTION EXTRACTION**

---

## Deprecated Scripts

### `run_gpu_extraction_deprecated.py`
**Deprecated:** October 31, 2025  
**Reason:** Bypasses established heuristics-first extraction pipeline

**Issues:**
- Loads entire corpus into memory (causes OOM on large datasets)
- Uses vanilla spaCy extraction only (ignores curated heuristics data)
- Applies fixed confidence score (0.8) instead of proper tier-based scoring
- Stores shallow entity records without proper source attribution
- Contradicts the established multi-tier pipeline in `src/flows/extraction_flow.py`

**Use Instead:**
- `queue_extraction_prefect.py` - Production extraction with Prefect orchestration
- `run_direct_extraction.py` - Direct execution using proper extraction pipeline

---

### `convert_raw_dataset_deprecated.py`
**Deprecated:** October 31, 2025  
**Reason:** Insufficient preprocessing, replaced by superior streaming processor

**Issues:**
- Loads entire raw JSON file into memory (854MB+)
- No deduplication logic
- No URL canonicalization
- Creates output incompatible with established pipeline
- Produces `dataset_45000_converted.jsonl` which is a **FORBIDDEN** dataset

**Use Instead:**
- `scripts/preprocess.py` - Proper streaming preprocessor with:
  - Streaming JSON parser (handles 850MB+ files without memory issues)
  - Bloom filter deduplication
  - URL canonicalization
  - Proper text extraction and cleaning

**Correct Preprocessing Command:**
```bash
python scripts/preprocess.py \
  --input "data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310 (1).json" \
  --output "data/processed/preprocessed.jsonl"
```

---

## Context7 Reference

### `context7_temporal_article.txt`
**Deprecated:** October 25, 2025  
**Reason:** Project migrated from Temporal to Prefect orchestration

This was a reference article about Temporal workflows. The project migrated to Prefect 3.1.9 for simpler, faster, and more reliable orchestration.

**Migration Details:**
- Removed: 5-service Temporal stack with health check issues
- Added: Prefect server + agent with PostgreSQL + Redis backend
- Converted: Workflows → @flow decorators, Activities → @task decorators
- Benefits: Simpler deployment, faster startup, more reliable execution

---

## Canonical Production Paths

For current production paths and recommended scripts, see:
- **Root:** `CANONICAL_PATHS.md`
- **Extraction Summary:** `EXTRACTION_FIXES_SUMMARY.md`
- **Memory Bank:** `memory-bank/activeContext.md`

---

**Last Updated:** October 31, 2025

