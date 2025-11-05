# Docker Deployment Guide - Vast.AI RTX 6000 Pro

## Complete Step-by-Step Deployment

Follow these exact steps to deploy on your Vast.AI instance.

---

## Step 1: Connect to Vast.AI Instance

### From Your Local Machine

```bash
# Connect with port forwarding (keeps terminal open)
ssh -p 40731 root@198.53.64.194 \
  -L 4200:localhost:4200 \
  -L 8000:localhost:8000 \
  -L 5432:localhost:5432
```

**Keep this terminal open!** This creates tunnels to access services.

---

## Step 2: Initial Setup (First Time Only)

### Check GPU

```bash
# Should show: NVIDIA RTX 6000 Ada Generation, 96GB
nvidia-smi
```

### Navigate to Workspace

```bash
# Vast.AI persistent storage
cd /workspace

# If repo doesn't exist, clone it
git clone https://github.com/nofilmincamera-lab/BPO-Web.git
cd BPO-Web

# Checkout the deployment branch
git checkout claude/repo-audit-setup-011CUprP7imMTf57g4GGoLVQ

# Pull latest changes
git pull
```

---

## Step 3: Configure Environment

### Create .env File

```bash
# Copy example configuration
cp .env.example .env

# Edit with nano (or vim)
nano .env
```

### Set These Values in .env

```bash
# === GPU Configuration ===
GPU_DEPLOYMENT_MODE=vastai-gpu
NVIDIA_VISIBLE_DEVICES=all
EMBEDDING_BATCH_SIZE=1024          # DOUBLED for your 96GB GPU!
GPU_MEMORY_FRACTION=0.95

# === Database Configuration ===
DB_HOST=postgres
DB_PORT=5432
DB_NAME=bpo_intel
DB_USER=postgres
DB_PASSWORD=your_secure_password_here    # CHANGE THIS!

# === Model Configuration ===
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# === Prefect Configuration ===
PREFECT_API_URL=http://prefect-server:4200/api
PREFECT_WORK_QUEUE=default

# === Other Settings ===
TZ=UTC
LOG_LEVEL=INFO
```

**Press `Ctrl+X`, then `Y`, then `Enter` to save**

---

## Step 4: Create Secrets

```bash
# Create secrets directory
mkdir -p ops/secrets

# Set database password (use same password from .env)
echo "your_secure_password_here" > ops/secrets/postgres_password.txt

# Secure the file
chmod 600 ops/secrets/postgres_password.txt
```

---

## Step 5: Create Docker Networks

```bash
# Create all required networks
docker network create bpo-main-network 2>/dev/null || echo "bpo-main-network exists"
docker network create bpo-gpu-network 2>/dev/null || echo "bpo-gpu-network exists"
docker network create bpo-db-network 2>/dev/null || echo "bpo-db-network exists"
docker network create bpo-monitoring-network 2>/dev/null || echo "bpo-monitoring-network exists"
docker network create bpo-external-network 2>/dev/null || echo "bpo-external-network exists"

echo "✓ All networks created"
```

---

## Step 6: Deploy with Docker Compose

### Option A: Single Worker Deployment (Recommended for Testing)

```bash
# Deploy with Vast.AI optimized configuration
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.vastai-gpu.yml \
  --profile base \
  up -d

echo "✓ Services starting... (wait 60 seconds)"
```

### Option B: Multi-Container Deployment (For Production)

```bash
# Deploy with 2 workers + API (maximum performance)
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.vastai-gpu-scaled.yml \
  --profile scaled \
  up -d

echo "✓ Multi-container services starting... (wait 90 seconds)"
```

---

## Step 7: Wait for Services to Start

```bash
# Wait 60 seconds
echo "Waiting for services to start..."
sleep 60

# Check service status
docker-compose ps
```

**Expected output:**
```
NAME                   STATUS              PORTS
bpo-postgres           Up (healthy)        0.0.0.0:5432->5432/tcp
bpo-prefect-db         Up (healthy)        5432/tcp
bpo-prefect-redis      Up                  6379/tcp
bpo-prefect-server     Up (healthy)        0.0.0.0:4200->4200/tcp
bpo-prefect-agent      Up
bpo-api                Up (healthy)        0.0.0.0:8000->8000/tcp
```

All services should show "Up" status.

---

## Step 8: Verify GPU Access

### Check GPU in Containers

```bash
# Check primary worker
docker exec bpo-prefect-agent nvidia-smi

# Should show:
# +-----------------------------------------------------------------------------------------+
# | NVIDIA-SMI 535.xx.xx            Driver Version: 535.xx.xx      CUDA Version: 12.1      |
# |-------------------------------+------------------------+--------------------------------+
# | GPU  Name                     Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
# |                                           |                        |               MIG M. |
# |===============================+========================+================================|
# |   0  NVIDIA RTX 6000 Ada...     On      | 00000000:00:05.0  Off |                    Off |
# | 30%   45C    P0             75W /  300W |       0MiB /  98304MiB |      0%      Default |
# |                                           |                        |                  N/A |
# +-------------------------------+------------------------+--------------------------------+
```

### Check PyTorch GPU Detection

```bash
docker exec bpo-prefect-agent python -c "
import torch
print(f'✓ GPU Available: {torch.cuda.is_available()}')
print(f'✓ GPU Name: {torch.cuda.get_device_name(0)}')
print(f'✓ GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
"
```

**Expected output:**
```
✓ GPU Available: True
✓ GPU Name: NVIDIA RTX 6000 Ada Generation
✓ GPU Memory: 96.0 GB
```

### Check Embeddings Module

```bash
docker exec bpo-prefect-agent python -c "
from src.extraction.gpu_embeddings import get_embedding_info
info = get_embedding_info()
print(f'✓ Device: {info[\"device\"]}')
print(f'✓ GPU: {info.get(\"gpu_name\", \"N/A\")}')
print(f'✓ Model: {info[\"model_name\"]}')
print(f'✓ Batch Size: {info.get(\"batch_size\", \"N/A\")}')
"
```

---

## Step 9: Access Services

### From Your Local Machine (via SSH tunnel)

Open these URLs in your browser:

1. **Prefect UI**: http://localhost:4200
   - Workflow orchestration dashboard
   - View running flows and tasks
   - Monitor worker status

2. **API**: http://localhost:8000
   - FastAPI endpoints
   - Health check: http://localhost:8000/healthz

3. **API Documentation**: http://localhost:8000/docs
   - Interactive Swagger UI
   - Test API endpoints

4. **PostgreSQL**: localhost:5432
   - Connect with any PostgreSQL client
   - Username: postgres
   - Password: (your password from .env)
   - Database: bpo_intel

---

## Step 10: Quick Performance Test

### Test Embeddings Throughput

```bash
docker exec bpo-prefect-agent python -c "
import time
import torch
from src.extraction.gpu_embeddings import generate_embeddings

print('Running performance test...')

# Test data
texts = ['Test sentence for embeddings'] * 2000

# Warm-up GPU
print('Warming up GPU...')
_ = generate_embeddings(texts[:10])

# Benchmark
print('Running benchmark...')
torch.cuda.synchronize()
start = time.time()
embeddings = generate_embeddings(texts, batch_size=1024)
torch.cuda.synchronize()
elapsed = time.time() - start

print('')
print('=== Performance Results ===')
print(f'✓ Processed: {len(texts)} texts')
print(f'✓ Time: {elapsed:.2f} seconds')
print(f'✓ Throughput: {len(texts) / elapsed:.1f} embeddings/sec')
print(f'✓ GPU Memory: {torch.cuda.memory_allocated() / 1024**3:.2f} GB')
print(f'✓ Expected: 700-900 embeddings/sec')
print('')
if len(texts) / elapsed >= 700:
    print('✅ Performance EXCELLENT!')
elif len(texts) / elapsed >= 500:
    print('✅ Performance GOOD')
else:
    print('⚠️  Performance lower than expected')
"
```

**Expected output:**
```
Running performance test...
Warming up GPU...
Running benchmark...

=== Performance Results ===
✓ Processed: 2000 texts
✓ Time: 2.50 seconds
✓ Throughput: 800.0 embeddings/sec
✓ GPU Memory: 43.20 GB
✓ Expected: 700-900 embeddings/sec

✅ Performance EXCELLENT!
```

---

## Step 11: Monitor Services

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f prefect-agent

# Last 100 lines
docker-compose logs --tail=100

# Follow errors only
docker-compose logs -f | grep ERROR
```

### Monitor GPU Usage

```bash
# Real-time GPU monitoring
watch -n 1 nvidia-smi

# Or continuously
nvidia-smi -l 1

# Detailed memory
nvidia-smi --query-gpu=timestamp,name,memory.used,memory.free,utilization.gpu --format=csv -l 1
```

### Monitor Docker Containers

```bash
# Resource usage
docker stats

# Specific containers
docker stats bpo-prefect-agent bpo-api bpo-postgres
```

---

## Common Commands

### Start Services

```bash
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.vastai-gpu.yml \
  --profile base \
  up -d
```

### Stop Services

```bash
docker-compose down
```

### Restart Services

```bash
docker-compose restart
```

### Restart Specific Service

```bash
docker-compose restart prefect-agent
docker-compose restart api
```

### View Service Status

```bash
docker-compose ps
```

### Update Configuration

```bash
# Edit .env
nano .env

# Restart affected services
docker-compose restart prefect-agent api
```

### Rebuild Images

```bash
# Rebuild all images
docker-compose build

# Rebuild specific service
docker-compose build prefect-agent

# Rebuild and restart
docker-compose up -d --build
```

### Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes data!)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

---

## Troubleshooting

### Issue: Containers Won't Start

```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs prefect-agent

# Restart Docker daemon
sudo systemctl restart docker

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Issue: GPU Not Detected

```bash
# Check GPU on host
nvidia-smi

# Check nvidia-docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Check container GPU access
docker exec bpo-prefect-agent nvidia-smi

# Restart container
docker-compose restart prefect-agent
```

### Issue: Services Not Accessible

```bash
# Check services are running
docker-compose ps

# Check ports are listening
netstat -tlnp | grep -E '4200|8000'

# Check SSH tunnel is active (on local machine)
# Reconnect: ssh -p 40731 root@198.53.64.194 -L 4200:localhost:4200 -L 8000:localhost:8000

# Try accessing from host
curl http://localhost:4200/api/health
curl http://localhost:8000/healthz
```

### Issue: Out of Memory

```bash
# Check GPU memory
nvidia-smi

# Reduce batch size
./scripts/update-batch-size.sh 768

# Restart services
docker-compose restart
```

### Issue: Database Connection Failed

```bash
# Check postgres is healthy
docker-compose ps postgres

# Check postgres logs
docker-compose logs postgres

# Verify password file exists
cat ops/secrets/postgres_password.txt

# Restart postgres
docker-compose restart postgres

# Wait for health check
sleep 30
docker-compose ps postgres
```

---

## Production Deployment Checklist

- [ ] SSH connection established with port forwarding
- [ ] Git repository cloned to /workspace
- [ ] .env file configured with secure password
- [ ] Secrets file created (postgres_password.txt)
- [ ] Docker networks created
- [ ] Services deployed with docker-compose
- [ ] All containers show "Up" status
- [ ] GPU detected in containers (nvidia-smi works)
- [ ] PyTorch detects GPU (torch.cuda.is_available() = True)
- [ ] Performance test passes (700+ embeddings/sec)
- [ ] Prefect UI accessible at http://localhost:4200
- [ ] API accessible at http://localhost:8000
- [ ] Services monitored (docker stats, nvidia-smi)

---

## Next Steps

### Run Extraction Pipeline

```bash
# Queue extraction job via API (from local machine)
curl -X POST http://localhost:8000/api/v1/extraction/queue \
  -H "Content-Type: application/json" \
  -d '{
    "source": "crawl_data",
    "batch_size": 100
  }'

# Monitor in Prefect UI
open http://localhost:4200
```

### Scale Up (Add More Workers)

```bash
# Deploy multi-container configuration
docker-compose down
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.vastai-gpu-scaled.yml \
  --profile scaled \
  up -d
```

### Backup Database

```bash
# Create backup
docker exec bpo-postgres pg_dump -U postgres bpo_intel | gzip > /workspace/backup_$(date +%Y%m%d_%H%M%S).sql.gz

# List backups
ls -lh /workspace/backup_*.sql.gz

# Download to local machine (from local terminal)
scp -P 40731 root@198.53.64.194:/workspace/backup_*.sql.gz ./
```

---

## Quick Reference Card

```bash
# === CONNECT ===
ssh -p 40731 root@198.53.64.194 -L 4200:localhost:4200 -L 8000:localhost:8000

# === DEPLOY ===
cd /workspace/BPO-Web
docker-compose -f docker-compose.yml -f docker-compose.vastai-gpu.yml --profile base up -d

# === CHECK STATUS ===
docker-compose ps
nvidia-smi
docker stats

# === VIEW LOGS ===
docker-compose logs -f

# === RESTART ===
docker-compose restart

# === STOP ===
docker-compose down

# === PERFORMANCE TEST ===
docker exec bpo-prefect-agent python -c "from src.extraction.gpu_embeddings import generate_embeddings; import time; texts=['test']*2000; start=time.time(); generate_embeddings(texts, batch_size=1024); print(f'{len(texts)/(time.time()-start):.1f} emb/sec')"

# === ACCESS SERVICES ===
# Prefect UI: http://localhost:4200
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

**You're ready to deploy! Follow the steps above and your pipeline will be running at 700-900 embeddings/sec! 🚀**
