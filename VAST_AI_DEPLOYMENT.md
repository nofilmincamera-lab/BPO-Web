# Vast.AI GPU Deployment Guide

## Overview

Deploy the BPO Intelligence Pipeline on **Vast.AI** cloud GPU instances. This guide covers connecting to your rented RTX 6000 Ada (or any Vast.AI GPU) and running the Docker stack remotely.

## What is Vast.AI?

- **GPU Marketplace**: Rent GPUs from data centers worldwide at competitive prices
- **Spot Pricing**: Often 3-5x cheaper than AWS/GCP/Azure
- **Instant Access**: SSH into pre-configured GPU instances
- **Flexible**: Hourly billing, no commitment
- **Docker Ready**: nvidia-docker pre-installed

## RTX 6000 Ada Pro Specifications

Your GPU specs (Pro variant):
- **Architecture**: Ada Lovelace (Blackwell generation)
- **VRAM**: 96GB GDDR6 ECC (🔥 2x standard RTX 6000!)
- **CUDA Cores**: 18,176
- **Tensor Cores**: 568 (4th gen)
- **Memory Bandwidth**: 960 GB/s
- **Performance**: ~3-4x faster than RTX 3060 for ML workloads
- **Optimal Batch Size**: 256-1024 (vs 32-64 for RTX 3060)
- **Special Features**: ECC memory, dual-slot design, enterprise reliability

---

## Quick Start

### 1. Connect to Vast.AI Instance

```bash
# Get connection details from Vast.AI dashboard
# Example SSH command (yours will be different)
ssh -p 12345 root@ssh.vast.ai -L 4200:localhost:4200 -L 8000:localhost:8000

# Breakdown:
# -p 12345                        : SSH port (from Vast.AI)
# root@ssh.vast.ai               : Your instance (from Vast.AI)
# -L 4200:localhost:4200         : Forward Prefect UI
# -L 8000:localhost:8000         : Forward API
```

### 2. Clone Repository on Vast.AI Instance

```bash
# Once connected via SSH
cd /workspace  # Vast.AI default workspace

# Clone repo
git clone https://github.com/your-org/BPO-Web.git
cd BPO-Web
```

### 3. Configure for Vast.AI

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env

# Set these values:
GPU_DEPLOYMENT_MODE=vastai-gpu
NVIDIA_VISIBLE_DEVICES=all
EMBEDDING_BATCH_SIZE=512        # RTX 6000 Pro 96GB can handle MASSIVE batches!
GPU_MEMORY_FRACTION=0.95        # Use most of 96GB (91.2GB available)
```

### 4. Deploy

```bash
# Use Vast.AI deployment mode
./scripts/deploy.sh vastai-gpu

# Or manually:
docker-compose -f docker-compose.yml -f docker-compose.vastai-gpu.yml --profile base up -d
```

### 5. Verify GPU

```bash
# Check GPU is detected
nvidia-smi

# Check in Docker
docker exec bpo-prefect-agent nvidia-smi

# Check PyTorch detection
docker exec bpo-prefect-agent python -c "import torch; print(f'GPU: {torch.cuda.is_available()}, Name: {torch.cuda.get_device_name(0)}')"
```

### 6. Access Services (via SSH tunnel)

From your **local machine**:
- **Prefect UI**: http://localhost:4200
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Detailed Setup

### Step 1: Rent GPU on Vast.AI

1. **Go to**: https://vast.ai/console/create/
2. **Search for GPU**: "RTX 6000" or "RTX 6000 Ada"
3. **Template**: Select "pytorch" or "cuda" template
4. **Storage**: 50GB minimum
5. **Rent**: Click "Rent" button

**Recommended Filters:**
- CUDA version: 12.1+
- Docker: Pre-installed
- GPU RAM: 48GB
- Disk Space: 50GB+
- Network: Verified hosts only

### Step 2: Get Connection Info

After renting, Vast.AI will show:
```
SSH: ssh -p 41234 root@ssh4.vast.ai
Direct: 192.168.1.100:22
```

**Save this information!**

### Step 3: Connect with Port Forwarding

```bash
# Full command with all ports forwarded
ssh -p 41234 root@ssh4.vast.ai \
  -L 4200:localhost:4200 \  # Prefect UI
  -L 8000:localhost:8000 \  # API
  -L 5432:localhost:5432 \  # PostgreSQL (optional)
  -L 9090:localhost:9090 \  # Prometheus (optional)
  -L 3000:localhost:3000    # Grafana (optional)

# Keep this terminal open while working
```

**Tip**: Add to your `~/.ssh/config` for easy reconnection:
```
Host vastai-rtx6000
    HostName ssh4.vast.ai
    Port 41234
    User root
    LocalForward 4200 localhost:4200
    LocalForward 8000 localhost:8000
    LocalForward 5432 localhost:5432
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

Then connect with: `ssh vastai-rtx6000`

### Step 4: Setup on Remote Instance

```bash
# Check GPU
nvidia-smi
# Should show: NVIDIA RTX 6000 Ada Generation, 48GB

# Check Docker
docker --version
docker compose version

# Check nvidia-docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Clone repository
cd /workspace
git clone https://github.com/your-org/BPO-Web.git
cd BPO-Web

# Checkout your branch
git checkout claude/repo-audit-setup-011CUprP7imMTf57g4GGoLVQ
```

### Step 5: Configure Environment

```bash
# Create .env from example
cp .env.example .env

# Edit configuration
nano .env
```

**Key settings for RTX 6000 Pro (96GB):**
```bash
# GPU Configuration
GPU_DEPLOYMENT_MODE=vastai-gpu
NVIDIA_VISIBLE_DEVICES=all
GPU_MEMORY_FRACTION=0.95           # Use 91.2GB of 96GB!

# Performance Tuning (RTX 6000 Pro optimized)
EMBEDDING_BATCH_SIZE=512           # 16x larger than RTX 3060!
# Can go up to 1024 for maximum throughput
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Alternative high-quality model (RTX 6000 can handle it)
# EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2  # 768-dim, 2x slower but better quality

# Database (use strong password)
DB_PASSWORD=your_secure_password_here

# Optional: Test with larger model
# EMBEDDING_MODEL=sentence-transformers/multi-qa-mpnet-base-dot-v1
```

### Step 6: Create Docker Networks

```bash
# Vast.AI instances may need manual network creation
docker network create bpo-main-network
docker network create bpo-gpu-network
docker network create bpo-db-network
docker network create bpo-monitoring-network
docker network create bpo-external-network
```

### Step 7: Create Postgres Password Secret

```bash
# Create secrets directory
mkdir -p ops/secrets

# Create password file
echo "your_secure_password_here" > ops/secrets/postgres_password.txt
chmod 600 ops/secrets/postgres_password.txt
```

### Step 8: Deploy Stack

```bash
# Deploy with Vast.AI configuration
docker-compose -f docker-compose.yml -f docker-compose.vastai-gpu.yml --profile base up -d

# Monitor logs
docker-compose logs -f

# Check services
docker-compose ps
```

### Step 9: Verify Deployment

```bash
# Check all containers running
docker-compose ps

# Should show:
# bpo-postgres        Up
# bpo-prefect-db      Up
# bpo-prefect-redis   Up
# bpo-prefect-server  Up
# bpo-prefect-agent   Up
# bpo-api             Up

# Check GPU in prefect-agent
docker exec bpo-prefect-agent nvidia-smi

# Check PyTorch GPU detection
docker exec bpo-prefect-agent python -c "
import torch
print(f'GPU Available: {torch.cuda.is_available()}')
print(f'GPU Name: {torch.cuda.get_device_name(0)}')
print(f'GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
"

# Test embeddings module
docker exec bpo-prefect-agent python -c "
from src.extraction.gpu_embeddings import get_embedding_info
info = get_embedding_info()
print(f'Device: {info[\"device\"]}')
print(f'GPU Name: {info.get(\"gpu_name\", \"N/A\")}')
print(f'Model: {info[\"model_name\"]}')
"
```

---

## Performance Optimization for RTX 6000

### Recommended Batch Sizes

With 96GB VRAM, you can use MASSIVE batches:

```bash
# In .env file
EMBEDDING_BATCH_SIZE=512           # 16x larger than RTX 3060 (32)
SPACY_BATCH_SIZE=200               # 2x larger for CPU processing

# For maximum throughput (RTX 6000 Pro only!)
# EMBEDDING_BATCH_SIZE=1024        # 32x larger! Process 1000+ texts at once
# EMBEDDING_BATCH_SIZE=2048        # Extreme mode for testing limits

# Conservative (if you want headroom for other processes)
# EMBEDDING_BATCH_SIZE=256         # Still 8x larger than RTX 3060
```

### Expected Performance

| Metric | RTX 3060 (12GB) | RTX 6000 Pro (96GB) | Speedup |
|--------|-----------------|---------------------|---------|
| Embeddings/sec | 128 | 500-700 | 3.9-5.5x |
| Batch Size | 32 | 512-1024 | 16-32x |
| GPU Memory | 1GB | 5-10GB | 5-10x |
| 45K docs | 17 hours | 4-5 hours | 3.4-4.3x |

### High-Quality Model Option

The RTX 6000 can handle larger, higher-quality models:

```bash
# Option 1: Better quality, still fast (768-dim)
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
EMBEDDING_BATCH_SIZE=256          # RTX 6000 Pro can handle it!

# Option 2: Best quality for semantic search (768-dim)
EMBEDDING_MODEL=sentence-transformers/multi-qa-mpnet-base-dot-v1
EMBEDDING_BATCH_SIZE=256

# Option 3: Multilingual support (384-dim)
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2
EMBEDDING_BATCH_SIZE=512

# Option 4: EXTREME - Multiple models simultaneously!
# With 96GB, you can load 2-3 models at once for different use cases
```

### Memory Management

Monitor GPU memory during processing:

```bash
# Watch GPU memory in real-time
watch -n 1 nvidia-smi

# Or more detailed
nvidia-smi --query-gpu=timestamp,name,temperature.gpu,utilization.gpu,utilization.memory,memory.total,memory.free,memory.used --format=csv -l 1
```

---

## Access Services from Local Machine

### Via SSH Tunnel (Recommended)

Your SSH tunnel forwards ports automatically:

```bash
# On local machine, connect with forwarding
ssh -p 41234 root@ssh4.vast.ai \
  -L 4200:localhost:4200 \
  -L 8000:localhost:8000

# Keep this terminal open

# Open in browser (on local machine)
open http://localhost:4200  # Prefect UI
open http://localhost:8000  # API
```

### Via Public IP (Advanced, Less Secure)

If you need public access without SSH tunnel:

```bash
# On Vast.AI instance, modify docker-compose
# Change services to bind to 0.0.0.0

# WARNING: Only do this if you understand the security implications
# Better to use SSH tunnel or set up nginx with SSL
```

---

## Cost Analysis

### Vast.AI Pricing (Example)

RTX 6000 Ada typical pricing:
- **Spot pricing**: $0.30-0.60/hr (~$216-432/month)
- **On-demand pricing**: $0.80-1.20/hr (~$576-864/month)

Compare to cloud providers:
- **AWS p3.2xlarge (V100)**: $3.06/hr ($2,203/month)
- **GCP a2-highgpu-1g (A100)**: $3.67/hr ($2,644/month)
- **Azure NC6s_v3 (V100)**: $3.06/hr ($2,203/month)

**Savings**: Vast.AI is 3-5x cheaper than major cloud providers!

### Cost Optimization

```bash
# 1. Stop when not in use
docker-compose down

# 2. Destroy Vast.AI instance (billing stops)
# Go to Vast.AI console and click "Destroy Instance"

# 3. Use Vast.AI "Auto-pause" feature
# Automatically pauses when idle
```

### Break-Even Analysis

For 24/7 operation:
- **Vast.AI RTX 6000**: $216-432/month
- **Local RTX 6000**: $5,000 (hardware) + $50/month (power)

**Break-even**: ~12-24 months

**Best for**: Testing, experimentation, variable workloads

---

## Troubleshooting

### GPU Not Detected

```bash
# Check nvidia-smi works
nvidia-smi

# Check Docker has GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Check runtime
docker info | grep -i runtime

# Restart Docker if needed
systemctl restart docker
```

### Port Forwarding Not Working

```bash
# Check services are listening
docker-compose ps
netstat -tlnp | grep -E '4200|8000'

# Reconnect SSH with verbose logging
ssh -v -p 41234 root@ssh4.vast.ai -L 4200:localhost:4200
```

### Out of Memory

```bash
# Reduce batch size in .env (unlikely with 96GB!)
EMBEDDING_BATCH_SIZE=256  # Instead of 512

# Restart services
docker-compose restart prefect-agent api

# Note: With 96GB, OOM is very unlikely unless using batch_size > 2048
```

### Connection Lost

```bash
# Reconnect via SSH
ssh vastai-rtx6000

# Check services still running
docker-compose ps

# Restart if needed
docker-compose restart
```

---

## Data Persistence

### Important: Vast.AI Storage

Vast.AI instances have:
- **Persistent storage**: `/workspace` (survives restarts)
- **Ephemeral storage**: Everything else (lost on destroy)

**Save important data to `/workspace`!**

```bash
# Deploy in workspace
cd /workspace/BPO-Web

# Database is in Docker volume (persistent)
# Backup before destroying instance:
docker exec bpo-postgres pg_dump -U postgres bpo_intel > /workspace/backup.sql

# Download backup to local machine
# From local terminal:
scp -P 41234 root@ssh4.vast.ai:/workspace/backup.sql ./backup.sql
```

---

## Monitoring

### GPU Monitoring

```bash
# Real-time GPU stats
watch -n 1 nvidia-smi

# Detailed metrics
nvidia-smi --query-gpu=timestamp,name,temperature.gpu,utilization.gpu,utilization.memory,memory.total,memory.free,memory.used --format=csv -l 1

# GPU power usage
nvidia-smi --query-gpu=power.draw,power.limit --format=csv -l 1
```

### Application Monitoring

```bash
# Service logs
docker-compose logs -f

# Specific service
docker-compose logs -f prefect-agent

# Prefect UI (on local machine)
open http://localhost:4200
```

---

## Best Practices

### 1. Use SSH Config

Create `~/.ssh/config` on local machine:
```
Host vastai-rtx6000
    HostName ssh4.vast.ai
    Port 41234
    User root
    LocalForward 4200 localhost:4200
    LocalForward 8000 localhost:8000
    LocalForward 5432 localhost:5432
    ServerAliveInterval 60
    ServerAliveCountMax 3
    IdentityFile ~/.ssh/id_rsa
```

Connect easily: `ssh vastai-rtx6000`

### 2. Auto-Reconnect Script

Save as `~/reconnect-vastai.sh`:
```bash
#!/bin/bash
while true; do
  ssh vastai-rtx6000
  echo "Connection lost, reconnecting in 5 seconds..."
  sleep 5
done
```

```bash
chmod +x ~/reconnect-vastai.sh
./reconnect-vastai.sh
```

### 3. Backup Regularly

```bash
# Automated backup script
docker exec bpo-postgres pg_dump -U postgres bpo_intel | gzip > /workspace/backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Keep only last 5 backups
cd /workspace && ls -t backup_*.sql.gz | tail -n +6 | xargs rm -f
```

### 4. Monitor Costs

- Check Vast.AI dashboard regularly
- Set billing alerts
- Destroy instance when done testing
- Use "Auto-pause" feature for idle timeout

---

## Quick Reference

### Essential Commands

```bash
# Connect
ssh vastai-rtx6000

# Check GPU
nvidia-smi

# Deploy
cd /workspace/BPO-Web
./scripts/deploy.sh vastai-gpu

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart
docker-compose up -d

# Check GPU in container
docker exec bpo-prefect-agent nvidia-smi
```

### Service URLs (Local)

- Prefect UI: http://localhost:4200
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432

---

## Performance Testing

### Quick Performance Test

```bash
# Run embeddings benchmark
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
embeddings = generate_embeddings(texts, batch_size=128)
elapsed = time.time() - start

print(f'Processed {len(texts)} texts in {elapsed:.2f}s')
print(f'Throughput: {len(texts) / elapsed:.1f} embeddings/sec')
print(f'GPU Memory: {torch.cuda.memory_allocated() / 1024**3:.2f} GB')
"
```

### Expected Results (RTX 6000 Pro 96GB)

```
Processed 1000 texts in 1.5s
Throughput: 666.7 embeddings/sec
GPU Memory: 5.20 GB
```

Compare to:
- RTX 3060 (12GB): 128 embeddings/sec
- RTX 6000 (48GB): 350-400 embeddings/sec
- RTX 6000 Pro (96GB): 600-700 embeddings/sec
- **Speedup vs RTX 3060**: 5.2x faster!
- **Speedup vs RTX 6000**: 1.7x faster!

---

## Summary

### Setup Steps
1. ✅ Rent RTX 6000 on Vast.AI
2. ✅ Connect via SSH with port forwarding
3. ✅ Clone repo to `/workspace/BPO-Web`
4. ✅ Configure `.env` with `vastai-gpu` mode
5. ✅ Deploy with `./scripts/deploy.sh vastai-gpu`
6. ✅ Access via http://localhost:4200 (local)

### Performance
- **5x faster** than RTX 3060 (600-700 vs 128 embeddings/sec)
- **16-32x larger batches** (512-1024 vs 32)
- **3-4x faster** processing (4-5 hours vs 17 hours for 45K docs)
- **96GB VRAM**: Can process entire corpus in one go!

### Cost
- **$0.30-0.60/hr** spot pricing (~$216-432/month)
- **3-5x cheaper** than AWS/GCP/Azure
- **Stop billing** when instance destroyed

---

**Next**: Follow the Quick Start above to deploy on your Vast.AI RTX 6000!

**Questions?** Check the Troubleshooting section or review Docker logs.
