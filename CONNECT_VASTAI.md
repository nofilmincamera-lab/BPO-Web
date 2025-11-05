# Connect to Your Vast.AI Instance (RTX 6000 Pro 96GB)

## Your Instance Details

```
Instance ID:      27586411
Public IP:        198.53.64.194
SSH Port:         40731
Machine Port:     40749
Port Range:       40510-40731
```

## Quick Connect

### Step 1: Connect via SSH with Port Forwarding

```bash
# Copy and paste this exact command:
ssh -p 40731 root@198.53.64.194 \
  -L 4200:localhost:4200 \
  -L 8000:localhost:8000 \
  -L 5432:localhost:5432 \
  -L 9090:localhost:9090 \
  -L 3000:localhost:3000
```

**What this does:**
- Connects to your Vast.AI GPU instance
- Forwards ports so you can access services on your local machine:
  - `4200` → Prefect UI
  - `8000` → API
  - `5432` → PostgreSQL
  - `9090` → Prometheus (optional)
  - `3000` → Grafana (optional)

**Keep this terminal open while working!**

---

## Step 2: Setup SSH Config (Optional but Recommended)

Add this to `~/.ssh/config` on your local machine:

```
Host vastai-rtx6000
    HostName 198.53.64.194
    Port 40731
    User root
    LocalForward 4200 localhost:4200
    LocalForward 8000 localhost:8000
    LocalForward 5432 localhost:5432
    LocalForward 9090 localhost:9090
    LocalForward 3000 localhost:3000
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

Then connect easily with:
```bash
ssh vastai-rtx6000
```

---

## Step 3: Initial Setup on Instance

Once connected via SSH:

```bash
# 1. Check GPU (should show RTX 6000 Ada with 96GB)
nvidia-smi

# 2. Navigate to workspace
cd /workspace

# 3. Clone repository
git clone https://github.com/nofilmincamera-lab/BPO-Web.git
cd BPO-Web

# 4. Checkout branch with new deployment config
git checkout claude/repo-audit-setup-011CUprP7imMTf57g4GGoLVQ
```

---

## Step 4: Configure for RTX 6000 Pro (96GB)

```bash
# 1. Create environment file
cp .env.example .env

# 2. Edit configuration
nano .env
```

**Essential settings for your RTX 6000 Pro:**

```bash
# GPU Mode
GPU_DEPLOYMENT_MODE=vastai-gpu

# RTX 6000 Pro Optimization (96GB VRAM!)
EMBEDDING_BATCH_SIZE=512           # Start here (16x RTX 3060)
GPU_MEMORY_FRACTION=0.95           # Use 91.2GB of 96GB
NVIDIA_VISIBLE_DEVICES=all

# Database (set a secure password!)
DB_PASSWORD=your_secure_password_change_this

# Model (default is good, but you can upgrade)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# For higher quality (your GPU can handle it):
# EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
# EMBEDDING_BATCH_SIZE=256
```

Save with `Ctrl+X`, `Y`, `Enter`

---

## Step 5: Create Required Directories and Secrets

```bash
# Create secrets directory
mkdir -p ops/secrets

# Set database password (use the same password from .env)
echo "your_secure_password_change_this" > ops/secrets/postgres_password.txt
chmod 600 ops/secrets/postgres_password.txt

# Create Docker networks
docker network create bpo-main-network || true
docker network create bpo-gpu-network || true
docker network create bpo-db-network || true
docker network create bpo-monitoring-network || true
docker network create bpo-external-network || true
```

---

## Step 6: Deploy!

```bash
# Deploy with Vast.AI configuration
docker-compose -f docker-compose.yml -f docker-compose.vastai-gpu.yml --profile base up -d

# Watch the logs
docker-compose logs -f
```

Wait about 30-60 seconds for services to start up.

---

## Step 7: Verify Everything Works

```bash
# 1. Check GPU is visible in Docker
docker exec bpo-prefect-agent nvidia-smi

# Should show: NVIDIA RTX 6000 Ada Generation, 96GB

# 2. Check PyTorch detects GPU
docker exec bpo-prefect-agent python -c "
import torch
print(f'GPU Available: {torch.cuda.is_available()}')
print(f'GPU Name: {torch.cuda.get_device_name(0)}')
print(f'GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
"

# Should show: GPU Available: True, GPU Name: NVIDIA RTX 6000 Ada Generation, GPU Memory: 96.0 GB

# 3. Check embedding module
docker exec bpo-prefect-agent python -c "
from src.extraction.gpu_embeddings import get_embedding_info
info = get_embedding_info()
print(f'Loaded: {info[\"loaded\"]}')
print(f'Device: {info[\"device\"]}')
print(f'GPU: {info.get(\"gpu_name\", \"N/A\")}')
"

# 4. Check all containers running
docker-compose ps
```

All services should show "Up" status.

---

## Step 8: Access Services (From Your Local Machine)

Open in your web browser:

- **Prefect UI**: http://localhost:4200
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

These work because of the SSH port forwarding!

---

## Quick Performance Test

```bash
# Run a quick embeddings benchmark
docker exec bpo-prefect-agent python -c "
import time
import torch
from src.extraction.gpu_embeddings import generate_embeddings

# Test data
texts = ['Test sentence'] * 1000

# Warm-up
_ = generate_embeddings(texts[:10])

# Benchmark
start = time.time()
embeddings = generate_embeddings(texts, batch_size=512)
elapsed = time.time() - start

print(f'Processed {len(texts)} texts in {elapsed:.2f}s')
print(f'Throughput: {len(texts) / elapsed:.1f} embeddings/sec')
print(f'GPU Memory: {torch.cuda.memory_allocated() / 1024**3:.2f} GB')
"
```

**Expected results:**
```
Processed 1000 texts in 1.5-2.0s
Throughput: 500-700 embeddings/sec
GPU Memory: 5-8 GB
```

**This is 5x faster than RTX 3060!**

---

## Monitor GPU Usage

```bash
# Watch GPU in real-time
watch -n 1 nvidia-smi

# Detailed monitoring
nvidia-smi --query-gpu=timestamp,name,temperature.gpu,utilization.gpu,memory.used,memory.free --format=csv -l 1

# Just memory
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader -l 1
```

---

## Troubleshooting

### Can't connect via SSH?

```bash
# Try with verbose logging
ssh -v -p 40731 root@198.53.64.194

# Check if port is open
nc -zv 198.53.64.194 40731

# Verify in Vast.AI dashboard that instance is "running"
```

### GPU not detected?

```bash
# Check nvidia-smi works on host
nvidia-smi

# Check Docker has GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Restart Docker daemon
sudo systemctl restart docker
```

### Services not starting?

```bash
# Check logs for errors
docker-compose logs

# Check specific service
docker-compose logs prefect-agent

# Restart services
docker-compose down
docker-compose -f docker-compose.yml -f docker-compose.vastai-gpu.yml --profile base up -d
```

### Port forwarding not working?

```bash
# Reconnect SSH with verbose
ssh -v -p 40731 root@198.53.64.194 -L 4200:localhost:4200

# Check service is listening
docker-compose ps
netstat -tlnp | grep -E '4200|8000'

# Try accessing with curl
curl http://localhost:4200/api/health
```

---

## Important Notes

### 🔴 Data Persistence
- **Persistent**: `/workspace` directory survives instance restarts
- **Ephemeral**: Everything else is lost when instance destroyed
- **Always deploy in**: `/workspace/BPO-Web`

### 💰 Cost Management
- Check Vast.AI dashboard for hourly rate
- **Stop instance** when not in use (billing stops)
- **Destroy instance** if you're done (releases GPU)
- Typical RTX 6000 Pro cost: $0.80-1.50/hr

### 💾 Backup Before Destroying
```bash
# Backup database
docker exec bpo-postgres pg_dump -U postgres bpo_intel | gzip > /workspace/backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Download to local machine (from local terminal)
scp -P 40731 root@198.53.64.194:/workspace/backup_*.sql.gz ./
```

---

## Performance Expectations

With your **RTX 6000 Pro (96GB)**:

| Metric | Value |
|--------|-------|
| **Embeddings/sec** | 600-700 (5x faster than RTX 3060) |
| **Batch Size** | 512-1024 (vs 32 for RTX 3060) |
| **45,000 docs** | 4-5 hours (vs 17 hours on RTX 3060) |
| **GPU Memory** | 5-10GB used (plenty of headroom) |

---

## Next Steps

1. ✅ Connect via SSH: `ssh -p 40731 root@198.53.64.194 -L 4200:localhost:4200 -L 8000:localhost:8000`
2. ✅ Clone repo: `cd /workspace && git clone <repo> && cd BPO-Web`
3. ✅ Configure: `cp .env.example .env && nano .env`
4. ✅ Deploy: `docker-compose -f docker-compose.yml -f docker-compose.vastai-gpu.yml --profile base up -d`
5. ✅ Verify: Check http://localhost:4200
6. ✅ Run extraction pipeline!

---

**Ready to process at 5x speed with your 96GB beast! 🚀**
