# Heuristics Data Directory

This directory contains the consolidated heuristics data used by the NER pipeline for entity extraction and classification.

## Files Overview

### Core Data Files

- **`ner_relationships.json`** - Main heuristics data containing:
  - Entity lists (ORG, PRODUCT, CATEGORY)
  - Provider-product relationships
  - Relationship strings for pattern matching
  - Metadata and statistics

- **`company_aliases.json`** - Company name normalization mapping:
  - Case-insensitive alias mappings
  - Canonical company names
  - Product name variations

### Supporting Files

- **`company_aliases.json`** - Company name aliases and variations
- **`ner_relationships_backup_preupdate.json`** - Backup of original relationships data
- **`countries/`** - Country name data for geographic entity extraction

## Data Sources

The heuristics data is consolidated from multiple sources:

1. **Product Partnerships Mapping** (`product_partnerships_mapping_2025-10-16 (1).json`)
   - 753 products across 61 providers
   - Structured provider-product relationships
   - Category and description information

2. **Relationships Mapping** (`relationships_mapping (1).json`)
   - 1,924 provider-partner relationships
   - Product and service categorizations
   - Source attribution

3. **Taxonomy Schema** (`taxonomy.json`)
   - 10 industry categories with hierarchical structure
   - 11 service categories with subcategories
   - Channel mappings and enablement layers

## Data Structure

### ner_relationships.json

```json
{
  "entities": {
    "ORG": ["Provider1", "Provider2", ...],
    "PRODUCT": ["Product1", "Product2", ...],
    "CATEGORY": ["Service Category1", "Service Category2", ...]
  },
  "relationships": {
    "Provider1": {
      "type": "BPO",
      "partners": ["Partner1", "Partner2"],
      "products": ["Product1", "Product2"],
      "categories": ["Category1", "Category2"]
    }
  },
  "relationship_strings": [
    "Product1 belongs to Provider1",
    "Product2 belongs to Provider1"
  ],
  "metadata": {
    "total_providers": 129,
    "total_products": 940,
    "total_categories": 101,
    "category_mappings": {...}
  }
}
```

### company_aliases.json

```json
{
  "provider name": "Provider Name",
  "PROVIDER NAME": "Provider Name",
  "product name": "Product Name",
  "PRODUCT NAME": "Product Name"
}
```

## Usage in NER Pipeline

The heuristics data is used by the `HeuristicExtractor` class in `src/models/heuristics.py`:

```python
from src.models.heuristics import HeuristicExtractor

# Initialize extractor
extractor = HeuristicExtractor("Heuristics/")

# Extract entities from text
entities = extractor.extract_entities(text)

# Get specific entity types
companies = extractor.extract_companies(text)
categories = extractor.extract_categories(text)
industries = extractor.extract_industries(text)
```

## Taxonomy Integration

The system now supports taxonomy-based entity extraction:

- **Industries**: Extracted from the 10 main industry categories
- **Service Categories**: Extracted from the 11 service categories
- **Hierarchical Support**: Supports up to 6 levels of hierarchy
- **Case-Insensitive Matching**: Robust extraction regardless of case

### Example Taxonomy Extraction

```python
text = "IBM provides Customer Experience (CX) Operations for Financial Services & Insurance clients"

# Results:
companies = ["IBM"]  # From heuristics
categories = ["Customer Experience (CX) Operations"]  # From taxonomy
industries = ["Financial Services & Insurance"]  # From taxonomy
```

## Data Maintenance

### Automated Sync

Use the sync script to update heuristics from source files:

```bash
# Check if sync is needed
python scripts/sync_heuristics.py --dry-run

# Perform sync
python scripts/sync_heuristics.py

# Force sync even if not needed
python scripts/sync_heuristics.py --force
```

### Validation

Validate data integrity:

```bash
python scripts/validate_heuristics.py
```

### Consolidation

Manually run consolidation:

```bash
python -m src.data.consolidate_heuristics
```

## Statistics

Current data statistics (as of last consolidation):

- **Total Providers**: 129
- **Total Products**: 940
- **Total Categories**: 101
- **Total Relationships**: 960
- **Company Aliases**: 3,925
- **Taxonomy Industries**: 10
- **Taxonomy Services**: 11

## Backup and Recovery

- Automatic backups are created before each sync operation
- Backups are stored in `Heuristics/backups/`
- Only the last 5 backups are retained
- Sync reports are generated for each operation

## Troubleshooting

### Common Issues

1. **Missing Files**: Ensure all source files are present in the project root
2. **JSON Errors**: Validate JSON syntax in source files
3. **Import Errors**: Install required dependencies (`rapidfuzz`, `jsonschema`)
4. **Permission Issues**: Ensure write access to the Heuristics directory

### Validation Warnings

- **Case-insensitive duplicates**: Normal for company aliases
- **Missing aliases**: Some entities may not have alias mappings
- **Empty entries**: Check source data quality

## Contributing

When adding new heuristics data:

1. Update source files in the project root
2. Run validation to check data quality
3. Use the sync script to update heuristics
4. Test entity extraction with new data
5. Update documentation if needed

## Related Files

- `src/models/heuristics.py` - Main extraction logic
- `src/data/consolidate_heuristics.py` - Data consolidation
- `scripts/sync_heuristics.py` - Automated sync
- `scripts/validate_heuristics.py` - Data validation
- `tests/test_heuristics_integration.py` - Test suite
- `taxonomy.json` - Taxonomy schema

