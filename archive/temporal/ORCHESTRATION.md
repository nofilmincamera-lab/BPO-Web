# BPO Intelligence Pipeline - Orchestration Guide

## Overview

The orchestration namespace (`bpo-orchestration`) handles automated tasks and validation workflows, separate from the extraction namespace (`bpo-extraction`) which handles NER/taxonomy processing.

## Workflows

### 1. Overnight Work Workflow

Orchestrates Cursor background agents for autonomous tasks.

**Queue**:
```bash
curl -X POST http://localhost:8000/api/orchestration/queue-work \
  -H "Content-Type: application/json" \
  -d '[{"task_type":"review","code_path":"src/worker/","context":{},"priority":1}]'
```

**Features**:
- Batch task execution
- Automatic action item generation
- User-needed item skipping
- Comprehensive reporting

### 2. Overnight Validation Workflow

Comprehensive system validation with 6 phases:

**Queue**:
```bash
curl -X POST http://localhost:8000/api/orchestration/queue-validation
```

**Phases**:
1. **Verification** (0-15 min): Containers, packages, heuristics, database
2. **Wait** (variable): Sleep until 4:30 AM with heartbeat
3. **Code Review** (15-30 min): Operational readiness check
4. **Batch Test** (30-45 min): Preprocess and extract 1000 records
5. **Analytics** (5-10 min): Heuristics performance analysis
6. **Reporting** (5-10 min): Generate markdown report, cleanup, update MEMORY.md

**Outputs**:
- `docs/VALIDATION_REPORT_[timestamp].md` - Human-readable report
- Updated `MEMORY.md` with validation timestamp
- Analytics on heuristics performance

## Activities

### Validation Activities

- `verify_docker_containers_activity` - Check all containers running
- `verify_python_packages_activity` - Verify requirements.txt installed
- `verify_heuristics_files_activity` - Validate taxonomy files
- `verify_database_schema_activity` - Check Alembic migrations
- `wait_until_time_activity` - Sleep until target time with heartbeat

### Code Review Activity

- `full_code_review_activity` - Operational readiness review
  - Checks for missing dependencies
  - Identifies TODO items
  - Flags configuration issues
  - Generates action items

### Testing Activities

- `preprocess_sample_activity` - Stream N records from raw JSON
- `run_batch_extraction_activity` - Extract entities from batch
- `analyze_heuristics_performance_activity` - Generate analytics

### Reporting Activities

- `generate_markdown_report_activity` - Create validation report
- `cleanup_test_files_activity` - Remove temp files
- `update_memory_md_activity` - Update MEMORY.md

## Monitoring

**Temporal UI**: http://localhost:8233

Navigate to `bpo-orchestration` namespace to view:
- Workflow execution history
- Activity logs
- Retry attempts
- Heartbeat status

## Configuration

Environment variables in `docker-compose.yml`:

```yaml
TEMPORAL_ORCHESTRATION_NAMESPACE=bpo-orchestration
TEMPORAL_ORCHESTRATION_QUEUE=orchestration-queue
CURSOR_AGENT_URL=http://localhost:8080
```

## Background Agent Instructions

When executing autonomous tasks, agents:

1. **Skip**: User-needed items (passwords, API keys, approvals)
2. **Execute**: All autonomous tasks (code analysis, refactoring, testing)
3. **Document**: Action items with type, location, reason, impact
4. **Report**: Completion status and skipped items

## Troubleshooting

**Workflow not starting**:
- Check Temporal server: `docker ps | grep temporal`
- Check worker logs: `docker logs bpo-worker`
- Verify namespace exists in Temporal UI

**Activities failing**:
- Check activity logs in Temporal UI
- Verify container access (Docker socket mounted)
- Check Python packages installed in containers

**Validation report not generated**:
- Check `docs/` directory permissions
- Verify worker has write access
- Check Temporal UI for errors

