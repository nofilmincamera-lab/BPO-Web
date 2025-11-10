# Data Cleaning & Enrichment Pipeline

A comprehensive data cleaning and enrichment pipeline for BPO collections extraction data.

## Overview

This pipeline processes raw collections data and produces:
- **Cleaned & enriched dataset** with standardized text, normalized providers, and business insights
- **Provider aggregations** showing trends and distributions
- **Category aggregations** with canonical service taxonomy
- **Tag dictionary** mapping synonyms to canonical categories
- **Data quality report** identifying issues and suggested fixes
- **Executive report** with comprehensive analysis and insights

## Quick Start

### Prerequisites

```bash
pip install pandas numpy
```

### Run the Pipeline

```bash
python3 data_cleaning_pipeline.py
```

The pipeline will:
1. Load `data/collections_extraction.csv` (3,673 rows)
2. Process in memory-efficient chunks (50,000 rows per chunk)
3. Generate all output files in the current directory

### Expected Runtime

- **Small datasets** (<10K rows): 1-2 minutes
- **Medium datasets** (10K-100K rows): 5-15 minutes
- **Large datasets** (>100K rows): 15-60 minutes

## Output Files

| File | Size | Description |
|------|------|-------------|
| `cleaned_enriched.csv` | ~160 MB | **Main output** - Fully enriched dataset (not committed due to size) |
| `aggregates_provider.csv` | ~1 KB | Provider-level statistics and trends |
| `aggregates_category.csv` | ~3 KB | Category prevalence and top providers |
| `tag_dictionary.csv` | ~13 KB | Canonical tag mappings (292 entries) |
| `data_quality_issues.csv` | ~377 KB | Quality issues log (5,743 issues) |
| `REPORT.md` | ~44 KB | Executive summary and analysis |
| `pipeline_execution.log` | ~3 KB | Execution log with statistics |

**Note:** `cleaned_enriched.csv` is excluded from git due to GitHub's 100MB file size limit. Run the pipeline locally to generate it.

## Pipeline Features

### 1. Text Normalization
- Unicode normalization (NFC form)
- Whitespace collapse and trimming
- Preserves original text in `_original_text` column

### 2. Provider Normalization
- Cleans and standardizes company names
- Removes common suffixes (Inc, LLC, Ltd, Corp)
- Maps aliases using `Heuristics/company_aliases.json`
- Handles JSON array formats

### 3. Category Ontology
- 50 canonical service categories from `taxonomy_services.json`
- Hierarchical taxonomy (Level 1 & 2 categories)
- 242+ term-to-category mappings
- Max 10 categories per entry

### 4. Business Lens Analysis

For each entry, generates four analytical fields:

- **Problem:** Core issue or need (≤40 words)
- **Evidence:** Key facts, metrics, or quotes (≤40 words)
- **Analysis:** Why it matters (≤40 words)
- **Solution:** Actionable next step (≤40 words)

### 5. Data Quality Checks

Automatically detects:
- Missing providers (3,362 entries)
- Empty/short text content
- Missing category assignments
- Duplicate entries (2,380 found via content hashing)
- Encoding issues

### 6. Additional Features

- **Tagging:** Extracts novel tags beyond canonical categories
- **Deduplication:** MD5 hash-based duplicate detection
- **Aggregations:** Provider and category trend analysis
- **Reproducibility:** Deterministic, idempotent transformations

## Results Summary

### Processing Statistics
- **Total rows:** 3,673
- **Rows with provider:** 311 (8.5%)
- **Rows with categories:** 3,672 (100.0%)
- **Unique providers:** 3
- **Canonical categories:** 49
- **Quality issues:** 5,743
- **Duplicates detected:** 2,380

### Top Providers
1. **Ar Solutions** - 293 records (94.2%)
2. **Alorica** - 14 records (4.5%)
3. **Encore Capital Group** - 4 records (1.3%)

### Top Categories
1. **Agent Assist & Copilot** - 3,122 entries (85.0%)
2. **Autonomous Service Agents** - 2,939 entries (80.0%)
3. **Procure-to-Pay (P2P)** - 2,286 entries (62.2%)

## Configuration

Edit these constants in `data_cleaning_pipeline.py`:

```python
INPUT_FILE = "data/collections_extraction.csv"
TEXT_COLUMN = "text"
PROVIDER_COLUMN = "matched_companies"
DATE_COLUMN = "fetched_at"
LABEL_COLUMNS = ["matched_terms", "matched_keywords"]
CHUNK_SIZE = 50000
```

## Schema

### Input Columns
- `text` - Main content to analyze
- `matched_companies` - Provider information (JSON or string)
- `matched_terms`, `matched_keywords` - Existing labels
- `fetched_at` - Optional timestamp
- Additional metadata columns preserved in output

### Output Columns (cleaned_enriched.csv)

| Column | Type | Description |
|--------|------|-------------|
| `_row_id` | int | Stable row identifier (1-indexed) |
| `_original_text` | string | Unmodified original text |
| `clean_text` | string | Normalized text |
| `provider` | string | Normalized provider name |
| `categories` | string | Pipe-delimited canonical categories |
| `additional_tags` | string | Pipe-delimited novel tags |
| `problem` | string | Business problem statement |
| `evidence` | string | Supporting evidence |
| `analysis` | string | Analytical interpretation |
| `solution` | string | Recommended action |
| `text_hash` | string | MD5 hash for deduplication |
| _(all original columns)_ | various | Preserved from input |

## Taxonomy Reference

### Level 1 Categories (10 top-level domains)

- AI-Enabled CX & Automation
- Collections, Credit & Revenue Recovery
- Customer Experience (CX) Operations
- CX Transformation & Consulting
- Data, Analytics & Insights
- Back-Office & Process Management
- Finance & Accounting (F&A)
- Human Resources (HRO)
- Risk, Compliance & Trust
- Supply Chain & Logistics Management
- Technology Services

### Level 2 Categories (40 specialized services)

See `Heuristics/taxonomy_services.json` for complete hierarchy.

## Data Quality Notes

### Known Issues

1. **Low Provider Coverage (8.5%)**
   - Only 311 of 3,673 entries have identified providers
   - Most entries lack provider metadata
   - Recommendation: Enhance provider extraction from URLs and text

2. **High Duplicate Rate (64.8%)**
   - 2,380 duplicate entries based on content hashing
   - May indicate data collection issues
   - Recommendation: Deduplicate source data

3. **Missing Temporal Data**
   - `fetched_at` column not consistently populated
   - Limits time-series trend analysis
   - Recommendation: Ensure timestamp capture in data collection

### Quality Severity Levels

- **High:** Critical issues requiring immediate attention (empty text)
- **Medium:** Important issues affecting analysis quality (missing provider)
- **Low:** Minor issues or informational flags (no categories)

## Customization

### Add Custom Categories

Edit `Heuristics/taxonomy_services.json`:

```json
{
  "id": "custom_category",
  "name": "Custom Category Name",
  "description": "What this category covers",
  "level": 2,
  "parent_id": "parent_category_id",
  "path": ["parent_category_id", "custom_category"]
}
```

### Modify Business Lens Extraction

Edit the `generate_business_lens()` method in `data_cleaning_pipeline.py` to customize:
- Pattern matching rules
- Field content and length
- Extraction heuristics

### Adjust Quality Checks

Edit the `check_quality()` method to add/modify quality rules:
- Add new issue types
- Change severity thresholds
- Customize suggested fixes

## Troubleshooting

### Memory Issues

If processing large datasets causes memory issues:

```python
CHUNK_SIZE = 10000  # Reduce chunk size
```

### Encoding Errors

The pipeline uses UTF-8 with error handling:

```python
encoding='utf-8', on_bad_lines='skip'
```

### Missing Dependencies

```bash
pip install pandas numpy --upgrade
```

## Next Steps

### Recommended Actions

1. **High Priority**
   - Review high-severity quality issues in `data_quality_issues.csv`
   - Validate provider normalizations for top 50 providers
   - Investigate duplicate entries and deduplicate source data

2. **Medium Priority**
   - Enhance business lens extraction with domain patterns
   - Expand taxonomy for uncovered service domains
   - Improve provider extraction from URLs and text

3. **Low Priority**
   - Temporal trend analysis (requires date quality improvement)
   - Cross-validate additional tags with experts
   - Build provider hierarchy for multi-brand orgs

### Further Analysis

The enriched dataset enables:
- **Market analysis** - Provider positioning and service coverage
- **Trend identification** - Category growth and adoption patterns
- **Competitive intelligence** - Service offering comparison
- **Content analysis** - Topic modeling and semantic clustering
- **Quality improvement** - Data collection optimization

## Support

For issues or questions:
1. Check `REPORT.md` for detailed analysis
2. Review `data_quality_issues.csv` for specific problems
3. Examine `pipeline_execution.log` for processing details

## License

See repository LICENSE file.
