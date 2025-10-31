# Archive Directory

This directory contains obsolete or superseded files that are kept for reference.

## Contents

### Test Scripts (Archived on 2025-10-25)

- `test_heuristics.py` - Original heuristics test script (superseded by `scripts/validate_taxonomy.py`)
- `test_heuristics_simple.py` - Simplified heuristics test script (superseded by `scripts/validate_taxonomy.py`)

**Reason**: Consolidated into comprehensive `scripts/validate_taxonomy.py` with full validation coverage.

### Docker Compose Configs (Archived on 2025-10-25)

- `docker-compose.temporal.yml` - Old Temporal-only compose file (integrated into main `docker-compose.yml`)

**Reason**: Dual namespace architecture requires unified docker-compose configuration.

### Label Studio Configs (Archived on 2025-10-25)

- `label_config_validation.xml` - Old Label Studio config for validation
- `label_config.xml` - Previous Label Studio config
- `label_studio_config.json` - JSON config for Label Studio

**Reason**: Label Studio configured via profiles in main docker-compose, no separate configs needed.

### Data Mappings (Archived on 2025-10-25)

- `product_partnerships_mapping_2025-10-16 (1).json` - Old product/partnership mappings
- `relationships_mapping (1).json` - Old relationship mappings

**Reason**: Consolidated into main Heuristics directory with versioned files.

### Deployment and Test Reports (Archived on 2025-10-25)

- `DEPLOYMENT_SUMMARY.md` - Early deployment summary (superseded by DEPLOYMENT_COMPLETE.md)
- `SETUP_RUNBOOK.md` - Setup guide (superseded by install.ps1 and MEMORY.md)
- `TEST_RESULTS_20251025_144500.md` - Initial test results (superseded by FINAL_TEST_REPORT.md)
- `TEST_IMPLEMENTATION_COMPLETE.md` - Intermediate test report
- `SERVICE_STATUS_FINAL.md` - Intermediate status (superseded by SYSTEM_READY.md)
- `WORK_IN_PROGRESS.md` - Work tracker (superseded by IMPLEMENTATION_COMPLETE.md)
- `DEPLOYMENT_STATUS.md` - Intermediate status (superseded by DEPLOYMENT_COMPLETE.md)

**Reason**: Superseded by comprehensive final documentation in root and docs/.

### Research Files (Archived on 2025-10-25)

- `context7_temporal_article.txt` - Temporal research notes
- `product_partnerships_mapping_2025-10-21.json` - Old data mapping

**Reason**: Research complete, data consolidated into Heuristics/.

### Duplicate Files (Archived on 2025-10-25)

- `company_aliases.json` - Duplicate of company_aliases_clean.json

**Reason**: Using company_aliases_clean.json as canonical source.

## Notes

- These files are archived for reference only and should not be used in active development
- Current active scripts are in `scripts/` directory
- Current documentation in root: IMPLEMENTATION_COMPLETE.md, ORCHESTRATION_COMPLETE.md, MEMORY.md
- Current documentation in docs/: FINAL_TEST_REPORT.md, DEPLOYMENT_COMPLETE.md, SYSTEM_READY.md
- When archiving new files, add entries here with date and reason

