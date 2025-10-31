# BPO Intelligence Pipeline - Command Reference

## Quick Start

### Start Services
```bash
# Create networks first (one-time setup)
python manage_docker_networks.py create

# Start base stack (Postgres + Prefect + API)
docker-compose --profile base up -d

# Start with all optional services
docker-compose --profile base --profile qc --profile llm up -d

# Check service health
docker ps
docker-compose ps
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (DANGER: deletes data)
docker-compose down -v

# Stop specific service
docker-compose stop prefect-agent
```

## Extraction Commands

### Direct GPU Extraction (Fastest)
```bash
# Run direct extraction (bypasses Prefect)
python run_gpu_extraction.py

# Check progress
tail -f extraction.log

# View summary
cat extraction_summary.json | jq
```

### Prefect-Based Extraction (With Monitoring)
```bash
# Deploy flows (one-time or after changes)
python deploy_flows.py

# Queue extraction job
python queue_extraction_prefect.py

# Monitor in UI
Start-Process "http://localhost:4200"  # Windows
open http://localhost:4200              # Mac
xdg-open http://localhost:4200          # Linux
```

### Simple Extraction (No Prefect, Direct DB)
```bash
python run_simple_extraction.py
```

## Database Commands

### Connect to Database
```bash
# Via Docker
docker exec -it bpo-postgres psql -U postgres -d bpo_intel

# Via PgBouncer (connection pooling)
docker exec -it bpo-pgbouncer psql -h localhost -p 6432 -U postgres -d bpo_intel

# From host (if psql installed)
psql -h localhost -p 5432 -U postgres -d bpo_intel
```

### Database Queries
```sql
-- Count entities
SELECT COUNT(*) FROM entities;

-- Count by entity type
SELECT label, COUNT(*) FROM entities GROUP BY label ORDER BY COUNT(*) DESC;

-- Count relationships
SELECT COUNT(*) FROM relationships;

-- Count by relationship type
SELECT relationship_type, COUNT(*) 
FROM relationships 
GROUP BY relationship_type 
ORDER BY COUNT(*) DESC;

-- Recent extractions
SELECT doc_id, COUNT(*) as entity_count, MAX(extracted_at) as last_extraction
FROM entities 
GROUP BY doc_id 
ORDER BY last_extraction DESC 
LIMIT 10;

-- Check extraction coverage by method
SELECT extraction_method, COUNT(*), AVG(confidence)
FROM entities
GROUP BY extraction_method
ORDER BY COUNT(*) DESC;

-- Find high-confidence companies
SELECT text, confidence, extraction_method
FROM entities
WHERE label = 'COMPANY' AND confidence > 0.85
ORDER BY confidence DESC
LIMIT 20;

-- Check for duplicates
SELECT text, label, COUNT(*)
FROM entities
GROUP BY text, label
HAVING COUNT(*) > 1;
```

### Database Backup & Restore
```bash
# Backup
docker exec bpo-postgres pg_dump -U postgres bpo_intel > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
docker exec -i bpo-postgres psql -U postgres -d bpo_intel < backup.sql

# Backup specific table
docker exec bpo-postgres pg_dump -U postgres -d bpo_intel -t entities > entities_backup.sql
```

## GPU Commands

### Check GPU Status
```bash
# From host
nvidia-smi

# Watch GPU usage (updates every 2 seconds)
watch -n 2 nvidia-smi

# Check in Prefect agent
docker exec bpo-prefect-agent nvidia-smi

# Check in API container
docker exec bpo-api nvidia-smi

# Check CUDA version
docker exec bpo-prefect-agent nvcc --version
```

### GPU Troubleshooting
```bash
# Verify NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Check Docker GPU config
docker info | grep -i runtime

# Test GPU in Python
docker exec bpo-prefect-agent python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## Service Health Checks

### Check All Services
```bash
# Quick status
docker-compose ps

# Detailed health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check logs
docker-compose logs --tail=50 -f
```

### Individual Service Health
```bash
# Postgres
docker exec bpo-postgres pg_isready -U postgres

# Prefect Server
curl http://localhost:4200/api/health

# API
curl http://localhost:8000/healthz

# Label Studio
curl http://localhost:8082/health

# Redis
docker exec bpo-redis redis-cli ping
```

### Service Logs
```bash
# Follow logs (live)
docker logs -f bpo-api
docker logs -f bpo-prefect-agent
docker logs -f bpo-postgres

# Last 100 lines
docker logs --tail=100 bpo-api

# With timestamps
docker logs -f --timestamps bpo-prefect-agent

# All services
docker-compose logs -f
```

## Heuristics Management

### Validate Heuristics
```bash
# Run validation
python scripts/validate_taxonomy.py

# Consolidate taxonomy
python scripts/consolidate_taxonomy.py

# Check version
cat Heuristics/version.json
```

### Update Heuristics
```bash
# After modifying Heuristics/*.json files
# Restart services to reload

docker-compose restart prefect-agent
docker-compose restart api
```

## Data Pipeline

### Preprocessing
```bash
# Preprocess raw JSON to JSONL
python scripts/preprocess.py

# OCR preprocessing
python scripts/preprocess_ocr.py

# Analyze dataset
python analyze_raw_dataset.py
```

### Check Data Files
```bash
# Count documents in JSONL
wc -l data/preprocessed/dataset_45000_converted.jsonl

# View first document
head -n 1 data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310\ \(1\).json | jq

# Check file size
ls -lh data/raw/*.json
```

## Prefect Operations

### Prefect CLI
```bash
# List deployments
docker exec bpo-prefect-agent prefect deployment ls

# List flows
docker exec bpo-prefect-agent prefect flow ls

# List work pools
docker exec bpo-prefect-agent prefect work-pool ls

# View flow runs
docker exec bpo-prefect-agent prefect flow-run ls --limit 10

# Cancel flow run
docker exec bpo-prefect-agent prefect flow-run cancel <run-id>
```

### Prefect UI Access
```bash
# Open UI (Windows)
Start-Process "http://localhost:4200"

# Open UI (Mac)
open http://localhost:4200

# Open UI (Linux)
xdg-open http://localhost:4200
```

## Label Studio Operations

### Access Label Studio
```bash
# URL: http://localhost:8082
# Login: admin@bpo-intel.local / admin123

# Import tasks (if MCP not used)
# Go to: Project → Import → Upload JSON
# File: data/label-studio/tasks_with_predictions_5k.json
```

### Label Studio via MCP
```bash
# Already configured in .cursor/mcp.json
# Use Claude to:
# - List projects
# - Import tasks
# - Export annotations
# - Check project status
```

## Network Management

### Docker Networks
```bash
# Create all BPO networks
python manage_docker_networks.py create

# Check network status
python manage_docker_networks.py status

# Remove networks
python manage_docker_networks.py remove

# Inspect specific network
docker network inspect bpo-main-network

# List all networks
docker network ls | grep bpo
```

## Troubleshooting

### Reset Everything (NUCLEAR OPTION)
```bash
# WARNING: This deletes all data!
docker-compose down -v
python manage_docker_networks.py remove
python manage_docker_networks.py create
docker-compose --profile base up -d
```

### Common Issues

**Issue: "Network not found"**
```bash
python manage_docker_networks.py create
docker-compose up -d
```

**Issue: "Port already in use"**
```bash
# Find process using port
netstat -ano | findstr :5432  # Windows
lsof -i :5432                  # Mac/Linux

# Kill process or stop conflicting service
```

**Issue: "GPU not available"**
```bash
# Check NVIDIA drivers
nvidia-smi

# Restart Docker Desktop
# Ensure "Use WSL 2" is enabled (Windows)

# Test GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

**Issue: "Database connection failed"**
```bash
# Check postgres is running
docker ps | grep postgres

# Check password file exists
cat ops/secrets/postgres_password.txt

# Test connection
docker exec -it bpo-postgres psql -U postgres -c "SELECT 1"
```

**Issue: "Prefect agent not picking up work"**
```bash
# Check agent logs
docker logs bpo-prefect-agent

# Verify work pool exists
docker exec bpo-prefect-agent prefect work-pool ls

# Restart agent
docker-compose restart prefect-agent
```

## Performance Monitoring

### Monitor Resource Usage
```bash
# Docker stats
docker stats --no-stream

# Continuous monitoring
docker stats

# Specific service
docker stats bpo-prefect-agent
```

### Extraction Performance
```bash
# Check extraction speed
tail -f extraction_progress.log | grep "Rate:"

# View extraction summary
cat extraction_summary.json | jq '.processing_rate'

# Database query performance
docker exec bpo-postgres psql -U postgres -d bpo_intel -c "EXPLAIN ANALYZE SELECT * FROM entities LIMIT 100;"
```

## Development

### Install Dependencies
```bash
# Install Python packages
pip install -r requirements.txt

# Install spaCy model
python -m spacy download en_core_web_sm
```

### Run Tests
```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_heuristics_integration.py

# With coverage
pytest --cov=src tests/
```

### Code Quality
```bash
# Format code
black src/

# Lint
pylint src/

# Type checking
mypy src/
```

## Quick References

### Important URLs
- Prefect UI: http://localhost:4200
- API Docs: http://localhost:8000/docs
- Label Studio: http://localhost:8082
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

### Important Files
- Production dataset: `data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310 (1).json`
- Main heuristics: `Heuristics/ner_relationships.json`
- Company aliases: `Heuristics/company_aliases_clean.json`
- DB password: `ops/secrets/postgres_password.txt`
- Extraction logs: `extraction.log`, `extraction_progress.log`

### Port Reference
| Service | Port | URL |
|---------|------|-----|
| PostgreSQL | 5432 | localhost:5432 |
| PgBouncer | 6432 | localhost:6432 |
| Prefect | 4200 | http://localhost:4200 |
| API | 8000 | http://localhost:8000 |
| Label Studio | 8082 | http://localhost:8082 |
| Ollama | 11434 | http://localhost:11434 |
| Redis | 6379 | localhost:6379 |
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3000 | http://localhost:3000 |