# BPO Intelligence Pipeline - Command Reference

Quick reference for all system commands.

---

## Service Management

### Start All Services
```bash
docker-compose --profile base up -d
```

### Stop All Services
```bash
docker-compose --profile base down
```

### Restart Specific Service
```bash
docker-compose --profile base restart worker
docker-compose --profile base restart api
docker-compose --profile base restart postgres
```

### Check Service Status
```bash
docker ps --filter "name=bpo-"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### View Logs
```bash
# Worker logs
docker logs bpo-worker --tail 50
docker logs bpo-worker -f  # Follow mode

# Prefect server logs
docker logs bpo-prefect-server --tail 50
docker logs bpo-prefect-agent --tail 50

# API logs
docker logs bpo-api --tail 50

# PostgreSQL logs
docker logs bpo-postgres --tail 50
```

---

## Database Operations

### Connect to Database
```bash
docker exec -it bpo-postgres psql -U postgres -d bpo_intel
```

### Common SQL Commands
```sql
-- List tables
\dt

-- List extensions
\dx

-- Describe table
\d entities

-- Count rows
SELECT COUNT(*) FROM documents;

-- Check schema version
SELECT * FROM schema_version;
```

### Manual Schema Creation
```bash
Get-Content ops/schema.sql | docker exec -i bpo-postgres psql -U postgres -d bpo_intel
```

### Backup Database
```bash
docker exec bpo-postgres pg_dump -U postgres bpo_intel > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql
```

---

## Heuristics

### Validate Taxonomy
```bash
python scripts/validate_taxonomy.py
```

### Check Version
```powershell
Get-Content Heuristics/version.json | ConvertFrom-Json | Select-Object version
```

### Count Entries
```powershell
# Company aliases
(Get-Content Heuristics/company_aliases_clean.json | ConvertFrom-Json).PSObject.Properties.Count

# Countries
(Get-Content Heuristics/countries.json | ConvertFrom-Json).Length

# Tech terms
((Get-Content Heuristics/tech_terms.json | ConvertFrom-Json).tech_terms).Count
```

---

## Preprocessing

### Preprocess Sample (1000 records)
```bash
docker exec bpo-worker python scripts/preprocess.py \
  --input "/data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310 (1).json" \
  --output /data/processed/test_1000.jsonl \
  --limit 1000
```

### Check Output
```bash
docker exec bpo-worker wc -l /data/processed/test_1000.jsonl
docker exec bpo-worker head -n 5 /data/processed/test_1000.jsonl
```

---

## Prefect Orchestration

### Queue Validation Workflow (API)
```powershell
Invoke-RestMethod -Uri http://localhost:8000/api/orchestration/queue-validation -Method Post
```

### Queue Overnight Work (API)
```powershell
$body = @(
    @{
        task_type = "review"
        code_path = "src/worker/"
        context = @{}
        priority = 1
    }
) | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/api/orchestration/queue-work `
  -Method Post `
  -ContentType "application/json" `
  -Body "[$body]"
```

### Queue Extraction Flow (CLI)
```bash
prefect deployment run document-extraction-pipeline/default \
  --param source_path=data/preprocessed/test_10.jsonl \
  --param heuristics_version=2.0.0 \
  --param batch_size=5
```

### Queue Extraction Flow (Script)
```bash
python queue_extraction_prefect.py
```

### List Deployments
```bash
prefect deployment ls
```

### Inspect Flow Runs
```bash
prefect flow-run ls --limit 10
```

---

## Testing

### Test API Health
```bash
curl http://localhost:8000/healthz
```

### Test API Root
```bash
curl http://localhost:8000/
```

### Test API Endpoints
```powershell
# Get namespace configuration
Invoke-RestMethod -Uri http://localhost:8000/ | ConvertTo-Json

# Queue validation
Invoke-RestMethod -Uri http://localhost:8000/api/orchestration/queue-validation -Method Post

# Check workflow status
Invoke-RestMethod -Uri http://localhost:8000/api/orchestration/status/validation-20251025-161443
```

### Verify Worker
```powershell
# Check worker started
docker logs bpo-worker | Select-String "Orchestration worker started"

# Check for errors
docker logs bpo-worker 2>&1 | Select-String -Pattern "error|exception" -CaseSensitive
```

---

## Monitoring

### Prefect UI
```
http://localhost:4200
→ Navigate to Deployments / Flow Runs
→ default-pool (Docker) work pool should be healthy
```

### Check Container Health
```bash
docker inspect bpo-postgres --format='{{.State.Health.Status}}'
docker inspect bpo-prefect-server --format='{{.State.Health.Status}}'
docker inspect bpo-api --format='{{.State.Health.Status}}'
```

### Check Resource Usage
```bash
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

---

## Troubleshooting

### Worker Won't Start
```bash
# Check logs for errors
docker logs bpo-worker

# Check if main.py exists
docker exec bpo-worker ls -lh src/worker/main.py

# Rebuild worker
docker-compose --profile base build --no-cache worker
docker-compose --profile base up -d worker
```

### Prefect Not Connecting
```bash
# Check Prefect server logs
docker logs bpo-prefect-server --tail 100

# Validate API responds
curl http://localhost:4200/api/health

# Restart Prefect stack
docker-compose --profile base restart prefect-server prefect-agent
```

### Database Issues
```bash
# Check PostgreSQL is ready
docker exec bpo-postgres pg_isready -U postgres

# Verify extensions
docker exec bpo-postgres psql -U postgres -d bpo_intel -c "\dx"

# Recreate schema
Get-Content ops/schema.sql | docker exec -i bpo-postgres psql -U postgres -d bpo_intel
```

### Workflows Not Appearing
```bash
# Check worker is running
docker ps | grep bpo-worker

# Verify worker logs show registration
docker logs bpo-worker | Select-String "worker started"

# List Prefect deployments and runs
prefect deployment ls
prefect flow-run ls --limit 10
```

---

## Development

### Rebuild Worker After Code Changes
```bash
docker-compose --profile base build worker
docker-compose --profile base restart worker
```

### Run Python in Worker Container
```bash
docker exec -it bpo-worker python
```

### Test Heuristics Loader
```bash
docker exec bpo-worker python -c "from src.heuristics import get_heuristics_loader; h=get_heuristics_loader(); print(f'Loaded {len(h.data.company_aliases)} companies')"
```

---

## GPU

### Check GPU Availability
```bash
nvidia-smi
docker exec bpo-worker nvidia-smi  # If GPU enabled
```

### Enable GPU for Worker
Already enabled in docker-compose.yml:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

---

## Cleanup

### Remove Old Containers
```bash
docker-compose --profile base down
docker system prune -f
```

### Clean Build Cache
```bash
docker builder prune -f
```

### Archive Old Reports
```bash
# Move to archive
Move-Item -Path "docs/OLD_REPORT.md" -Destination "archive/"

# Update archive/README.md
# Add entry with date and reason
```

---

## Quick Reference URLs

| Service | URL |
|---------|-----|
| Prefect UI | http://localhost:4200 |
| Prefect API Health | http://localhost:4200/api/health |
| API | http://localhost:8000 |
| API Health | http://localhost:8000/healthz |
| Label Studio | http://localhost:8082 (--profile qc) |
| PostgreSQL | localhost:5432 |

---

**For detailed information, see**: MEMORY.md, IMPLEMENTATION_COMPLETE.md, docs/DEPLOYMENT_COMPLETE.md

