# Dependencies Cleanup Summary

**Date:** October 31, 2025  
**Status:** ✅ Completed

---

## Removed Dependencies

### Database Tooling (Unused ORM/Migrations)
```
❌ psycopg[binary]==3.2.3       # ORM connector, never imported
❌ SQLAlchemy==2.0.35            # ORM, never imported
❌ alembic==1.13.3               # Migrations, never imported
❌ pgvector==0.3.5               # Python client, never imported
```

**Reasoning:**
- All database operations use `asyncpg` directly
- No ORM layer in active codebase
- No migration framework (manual schema via `ops/schema.sql`)
- pgvector extension still available in postgres container, just not using Python client

**Kept:**
- ✅ `asyncpg==0.29.0` - Used extensively in `src/flows/extraction_flow.py`

---

### Serialization Helpers (Never Imported)
```
❌ orjson==3.10.7                # Fast JSON, never imported
❌ ujson==5.10.0                 # Ultra JSON, never imported
❌ msgpack==1.1.0                # MessagePack, never imported
```

**Reasoning:**
- No imports found in entire codebase
- Using standard library `json` module
- Using Pydantic for data validation/serialization

---

### Monitoring & Logging (Unused Stack)
```
❌ structlog==24.4.0                              # Structured logging, never imported
❌ loguru==0.7.2                                  # Logging framework, never imported
❌ prometheus-client==0.21.0                      # Metrics client, never imported
❌ opentelemetry-api==1.27.0                      # Telemetry API, never imported
❌ opentelemetry-sdk==1.27.0                      # Telemetry SDK, never imported
❌ opentelemetry-instrumentation-fastapi==0.48b0  # FastAPI instrumentation, never imported
❌ opentelemetry-instrumentation-asyncpg==0.48b0  # asyncpg instrumentation, never imported
```

**Reasoning:**
- No monitoring packages imported in active code
- Using Prefect's built-in logging and observability
- Using Python's standard `logging` module
- Prometheus/Grafana available via `docker-compose --profile metrics` (external to Python)

---

### Docker SDK (Kept - Required)
```
✅ docker==7.1.0                 # KEPT - Required by prefect-docker
```

**Reasoning:**
- `prefect-docker==0.6.0` requires `docker>=6.1.1`
- Used for Docker work pool operations in `deploy_flows.py`
- Used in docker-compose.yml: `command: prefect worker start --pool default-pool --type docker`

---

## Metrics Stack Status

### Available But Optional
The Prometheus/Grafana observability stack is available but **optional** and **unfinished**:

```bash
# Start metrics stack
docker-compose --profile metrics up -d
```

**Services:**
- `prometheus` (port 9090) - Metrics collection
- `grafana` (port 3000) - Dashboards

**Current State:**
- ✅ Services defined in docker-compose.yml
- ✅ Using relative paths (portable)
- ✅ Optional profile (not required for extraction)
- ⚠️ No Python instrumentation (removed unused packages)
- ⚠️ No pre-built dashboards
- ⚠️ No application-level metrics export

**Recommendation:**
- Keep services for future implementation
- Add instrumentation when needed (can re-add packages)
- Current setup allows external monitoring without bloating Python dependencies

---

## Temporal References Status

### Archive (Correct Location)
All Temporal orchestration code properly archived:
- `archive/temporal/*.py` - Old Temporal workflows/activities
- `archive/docker-compose.temporal.yml` - Old orchestration
- `archive/context7_temporal_article.txt` - Reference documentation

### Memory Bank (Historical Notes - Keep)
Historical migration notes in memory-bank provide useful context:
- Why Prefect was chosen over Temporal
- Migration completed October 25, 2025
- Benefits: simpler, faster, more reliable

### Active Code (Entity Type - Not Orchestration)
`TEMPORAL` in active code is an **entity type**, not orchestration reference:
```python
# src/flows/extraction_flow.py
TEMPORAL_REGEX = re.compile(r"\b(?:pre|post|mid)-(?:launch|merger|acquisition|pandemic)\b")
```

**Entity Schema:**
- `TEMPORAL` = Temporal context spans (e.g., "pre-launch", "post-merger")
- Part of extraction schema: `COMPANY, PERSON, DATE, TECHNOLOGY, MONEY, PERCENT, PRODUCT, BUSINESS_TITLE, LOCATION, TIME_RANGE, ORL, TEMPORAL, SKILL`

---

## Before & After

### Before Cleanup
```
Total dependencies: ~50 packages
Unused packages: 13 (26%)
requirements.txt size: ~163 lines
```

### After Cleanup
```
Total dependencies: ~37 packages
All packages actively used
requirements.txt size: ~145 lines (with comments)
Savings: ~13 packages removed
```

---

## Migration Guide

If you previously had these packages installed:

### Clean Installation
```bash
# Remove old environment
pip uninstall -y psycopg SQLAlchemy alembic pgvector orjson ujson msgpack structlog loguru prometheus-client opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-asyncpg

# Install clean requirements
pip install -r requirements.txt
```

### Docker Rebuild
```bash
# Rebuild images with updated requirements
docker-compose build --no-cache
```

---

## Future Considerations

### If You Need These Features Again:

**ORM/Migrations:**
```bash
pip install SQLAlchemy==2.0.35 alembic==1.13.3
```

**Fast JSON Serialization:**
```bash
pip install orjson==3.10.7  # Fastest
# or
pip install ujson==5.10.0   # Fast alternative
```

**Observability Stack:**
```bash
pip install structlog==24.4.0 prometheus-client==0.21.0
pip install opentelemetry-api==1.27.0 opentelemetry-sdk==1.27.0
pip install opentelemetry-instrumentation-fastapi==0.48b0
```

---

## Related Documentation

- `requirements.txt` - Updated with inline comments explaining removals
- `CANONICAL_PATHS.md` - Database and infrastructure references
- `memory-bank/progress.md` - Migration history
- `archive/README_DEPRECATED_SCRIPTS.md` - Deprecated code references

---

**Summary:** Removed 13 unused packages (26% reduction), clarified remaining dependencies, documented metrics stack status. All active code continues to function with leaner dependency footprint.

