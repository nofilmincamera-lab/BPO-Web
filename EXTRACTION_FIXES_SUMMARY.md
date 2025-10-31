# Extraction Scripts - Fixes Applied

## Overview
Fixed all extraction scripts to use the **canonical production dataset** and clarified which scripts use the proper **heuristics-first multi-tier extraction pipeline**.

---

## ✅ Fixed Dataset Paths

All scripts now point to the correct canonical dataset path.

### Canonical Production Dataset
- **Raw**: `data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310 (1).json`
- **Preprocessed (JSONL)**: `data/processed/preprocessed.jsonl`

Generated via: `python scripts/preprocess.py --input <raw> --output <preprocessed>`

### ❌ FORBIDDEN Datasets (No Longer Used)
- `data/preprocessed/dataset_45000_converted.jsonl` - **FAILED CONVERSION**
- `data/preprocessed/preprocessed_full.jsonl` - **LEGACY/TEST ONLY**
- `data/preprocessed/test_5000_rich.jsonl` - **TEST FIXTURE**
- `data/preprocessed/test_*.jsonl` - **TEST FIXTURES**

---

## Files Modified

### 1. `run_gpu_extraction.py`
**Status**: ⚠️ **DEPRECATED** (with warnings)

**Changes**:
- ✅ Updated dataset path: `dataset_45000_converted.jsonl` → `data/processed/preprocessed.jsonl`
- ⚠️ Added deprecation warning at script start
- ⚠️ Added interactive prompt to prevent accidental use

**Issues**:
- Loads entire corpus into memory (OOM risk on 45K docs)
- Uses vanilla spaCy extraction only (ignores heuristics)
- Applies synthetic confidence scores (0.8) instead of tier-based
- Stores shallow entity records without proper source attribution
- **Contradicts the established pipeline design**

**Recommendation**: Use `run_direct_extraction.py` or `queue_extraction_prefect.py` instead

---

### 2. `trigger_extraction_api.py`
**Status**: ✅ **FIXED**

**Changes**:
- ✅ Updated dataset path: `dataset_45000_converted.jsonl` → `data/processed/preprocessed.jsonl`

**Notes**: Triggers extraction via API endpoint

---

### 3. `convert_raw_dataset.py`
**Status**: ⚠️ **DEPRECATED** (with instructions)

**Changes**:
- ⚠️ Added deprecation notice
- ✅ Points users to proper preprocessing: `scripts/preprocess.py`
- ✅ Updated output path: `dataset_45000_converted.jsonl` → `data/processed/preprocessed.jsonl`

**Issues**:
- Old conversion logic (loads entire file into memory)
- No deduplication
- No URL canonicalization

**Recommendation**: Use `scripts/preprocess.py` which includes:
- Streaming JSON parser (handles 850MB+ files)
- Bloom filter deduplication
- URL canonicalization
- Proper text extraction

---

### 4. `queue_extraction_prefect.py`
**Status**: ✅ **FIXED** - ⭐ **RECOMMENDED FOR PRODUCTION**

**Changes**:
- ✅ Updated dataset path: `preprocessed_full.jsonl` → `data/processed/preprocessed.jsonl`

**Pipeline**: Uses proper `src/flows/extraction_flow.py` (heuristics-first multi-tier)

**Features**:
- ✅ Heuristics → Regex → spaCy extraction tiers
- ✅ Proper confidence scoring by tier
- ✅ Source attribution (heuristics vs spacy)
- ✅ Prefect orchestration (retry, caching, monitoring)

---

### 5. `run_simple_extraction.py`
**Status**: ⚠️ **CLARIFIED** (simplified pipeline)

**Changes**:
- ✅ Updated default dataset: `test_5000_rich.jsonl` → `/data/processed/preprocessed.jsonl`
- ⚠️ Added documentation header explaining limitations

**Pipeline**: Simplified regex-based extraction (NOT full heuristics pipeline)

**Good For**:
- Testing
- Development
- Minimal dependency environments

**Not For**:
- Production extraction requiring full heuristics accuracy

**Recommendation**: For production, use `queue_extraction_prefect.py` or `run_direct_extraction.py`

---

### 6. `run_direct_extraction.py`
**Status**: ✅ **FIXED** - ⭐ **RECOMMENDED (Non-Prefect)**

**Changes**:
- ✅ Updated dataset path: `test_5000_rich.jsonl` → `/data/processed/preprocessed.jsonl`

**Pipeline**: Uses proper `src/flows/extraction_flow.py` functions directly

**Features**:
- ✅ Heuristics-first multi-tier extraction
- ✅ Proper confidence scoring
- ✅ Source attribution
- ✅ No Prefect overhead (direct execution)

---

### 7. `run_standalone_extraction.py`
**Status**: ✅ **FIXED**

**Changes**:
- ✅ Updated dataset path: `test_5000_rich.jsonl` → `/data/processed/preprocessed.jsonl`
- ✅ Added comment for testing override

---

### 8. `run_extraction.py`
**Status**: ✅ **FIXED**

**Changes**:
- ✅ Updated dataset path: `test_5000_rich.jsonl` → `/data/processed/preprocessed.jsonl`
- ✅ Added comment for testing override

---

## Extraction Pipeline Comparison

| Script | Dataset | Heuristics Pipeline | Confidence Tiers | Prefect | Status |
|--------|---------|---------------------|------------------|---------|--------|
| `queue_extraction_prefect.py` | ✅ Canonical | ✅ Yes | ✅ Proper | ✅ Yes | ⭐ **PRODUCTION** |
| `run_direct_extraction.py` | ✅ Canonical | ✅ Yes | ✅ Proper | ❌ No | ⭐ **PRODUCTION** |
| `run_extraction.py` | ✅ Canonical | ✅ Yes | ✅ Proper | ✅ Yes | ✅ **GOOD** |
| `run_standalone_extraction.py` | ✅ Canonical | ⚠️ Partial | ⚠️ Basic | ❌ No | ⚠️ **LIMITED** |
| `run_simple_extraction.py` | ✅ Canonical | ❌ No | ⚠️ Basic | ❌ No | ⚠️ **SIMPLIFIED** |
| `trigger_extraction_api.py` | ✅ Canonical | ✅ Yes (via API) | ✅ Proper | ✅ Yes (via API) | ✅ **GOOD** |
| `run_gpu_extraction.py` | ✅ Canonical | ❌ No | ❌ Synthetic | ❌ No | ❌ **DEPRECATED** |
| `convert_raw_dataset.py` | N/A | N/A | N/A | N/A | ❌ **DEPRECATED** |

---

## Proper Extraction Flow

The established multi-tier extraction pipeline (in `src/flows/extraction_flow.py`):

### Tier 1: Heuristics (Highest Confidence)
- Uses `Heuristics/ner_relationships.json`
- Company names, products, technologies from curated lists
- Confidence: **0.90**
- Source: `heuristics`

### Tier 2: Regex Patterns (High Confidence)
- Money: `$1,000.00` → Confidence: **0.92**
- Percent: `45%` → Confidence: **0.90**
- Source: `regex`

### Tier 3: spaCy NER (Variable Confidence)
- Person, Date: Confidence: **0.75**
- Cardinal, Ordinal: Confidence: **0.85**
- Other: Confidence: **0.70**
- Source: `spacy`

---

## Recommended Usage

### Production Extraction (Full 45K dataset)

**Option 1: With Prefect Orchestration** (Recommended)
```bash
python queue_extraction_prefect.py
# Monitor at http://localhost:4200
```

**Option 2: Direct Execution** (No Prefect)
```bash
python run_direct_extraction.py
```

### Testing/Development

**Small Test**:
```bash
python run_simple_extraction.py --source /data/preprocessed/test_5000_rich.jsonl
```

**API Trigger**:
```bash
python trigger_extraction_api.py
```

---

## Data Preprocessing

Before extraction, preprocess the raw dataset:

```bash
python scripts/preprocess.py \
  --input "data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310 (1).json" \
  --output "data/processed/preprocessed.jsonl"
```

This creates the canonical JSONL file used by all extraction scripts.

---

## Summary of Issues Fixed

### Issue 1: Wrong Dataset Paths ✅ FIXED
- ❌ Before: Scripts used `dataset_45000_converted.jsonl`, `preprocessed_full.jsonl`, `test_*` files
- ✅ After: All scripts point to `data/processed/preprocessed.jsonl` (canonical)

### Issue 2: Bypassed Heuristics Pipeline ✅ FIXED
- ❌ Before: `run_gpu_extraction.py` did vanilla spaCy with synthetic confidence
- ✅ After: Deprecated with warnings, redirects to proper scripts

### Issue 3: Test Fixtures as Defaults ✅ FIXED
- ❌ Before: Many scripts defaulted to `test_5000_rich.jsonl`
- ✅ After: Default to canonical production dataset with comments for testing

---

## Verification Checklist

- [x] All scripts use canonical dataset path
- [x] Deprecated scripts have clear warnings
- [x] Production scripts use proper heuristics pipeline
- [x] Scripts document their extraction approach
- [x] Conversion script points to proper preprocessor
- [x] Test-only scripts are clearly labeled

---

**Date**: 2025-10-31
**Status**: ✅ **All extraction path issues resolved**

