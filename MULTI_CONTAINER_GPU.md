# Multi-Container GPU Setup Guide

## Overview

Running multiple processing containers on a single GPU with the RTX 6000 Pro (96GB VRAM).

**Your Setup:**
- 2x Prefect workers (parallel processing)
- 1x API container (embeddings endpoint)
- 1x MCP container (Model Context Protocol)
- All sharing RTX 6000 Pro (96GB VRAM)

---

## GPU Memory Allocation

With 96GB VRAM, here's the recommended allocation:

| Container | Memory | Batch Size | Purpose |
|-----------|--------|------------|---------|
| **Worker 1** | 43.2GB (45%) | 1024 | Primary processing |
| **Worker 2** | 43.2GB (45%) | 1024 | Parallel processing |
| **API** | 9.6GB (10%) | 512 | Embeddings endpoint |
| **MCP** | Shared | Variable | Model context |
| **Total** | 96.0GB (100%) | - | - |

---

## Quick Start

### Option 1: Auto-Deploy (Recommended)

```bash
# On Vast.AI instance
cd /workspace/BPO-Web

# Deploy scaled configuration
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.vastai-gpu-scaled.yml \
  --profile scaled up -d
```

### Option 2: Manual Configuration

```bash
# Edit .env file
nano .env

# Set these values:
EMBEDDING_BATCH_SIZE=1024          # DOUBLED from 512!
GPU_MEMORY_FRACTION=0.45           # Per worker
```

---

## GPU Sharing Strategy

### Method 1: CUDA Default (Automatic)

CUDA natively supports multiple processes accessing the same GPU:
- ✅ **No setup required** - works out of the box
- ✅ Automatic context switching
- ✅ Each container gets full GPU access
- ⚠️ Slight overhead from context switches
- ✅ **Recommended for most users**

### Method 2: NVIDIA MPS (Advanced)

Multi-Process Service for more efficient sharing:

```bash
# On Vast.AI host (run once)
sudo nvidia-cuda-mps-control -d

# Verify MPS is running
ps aux | grep mps

# Check MPS status
nvidia-smi
```

**Benefits:**
- 10-15% better throughput
- Lower latency for small operations
- Better memory utilization

**When to use:**
- High-concurrency workloads
- Many small GPU operations
- Latency-sensitive applications

---

## Deployment Configurations

### Configuration 1: Balanced (2 Workers + API)

```yaml
# docker-compose.vastai-gpu-scaled.yml
services:
  prefect-agent:
    environment:
      - EMBEDDING_BATCH_SIZE=1024
      - GPU_MEMORY_FRACTION=0.45    # 43.2GB

  prefect-agent-2:
    environment:
      - EMBEDDING_BATCH_SIZE=1024
      - GPU_MEMORY_FRACTION=0.45    # 43.2GB

  api:
    environment:
      - EMBEDDING_BATCH_SIZE=512
      - GPU_MEMORY_FRACTION=0.10    # 9.6GB
```

**Performance:**
- Combined: 1200-1400 embeddings/sec
- 2x parallel processing
- API remains responsive

### Configuration 2: Maximum Throughput (2 Workers Only)

```bash
# Increase worker memory allocation
GPU_MEMORY_FRACTION=0.47           # 45.1GB each (94.2GB total)
```

**Performance:**
- Combined: 1400-1600 embeddings/sec
- Maximum batch processing
- API may need to wait for workers

### Configuration 3: API-Heavy (1 Worker + API)

```bash
# Worker 1
GPU_MEMORY_FRACTION=0.60           # 57.6GB
EMBEDDING_BATCH_SIZE=1536

# API
GPU_MEMORY_FRACTION=0.35           # 33.6GB
EMBEDDING_BATCH_SIZE=1024
```

**Performance:**
- Worker: 700-800 embeddings/sec
- API: 600-700 embeddings/sec
- Great for interactive workloads

---

## Performance Testing

### Test Individual Containers

```bash
# Test Worker 1
docker exec bpo-prefect-agent-1 python -c "
import time
import torch
from src.extraction.gpu_embeddings import generate_embeddings

texts = ['Test'] * 2000
start = time.time()
embeddings = generate_embeddings(texts, batch_size=1024)
elapsed = time.time() - start

print(f'Worker 1: {len(texts) / elapsed:.1f} embeddings/sec')
print(f'GPU Memory: {torch.cuda.memory_allocated() / 1024**3:.2f} GB')
"

# Test Worker 2
docker exec bpo-prefect-agent-2 python -c "
import time
import torch
from src.extraction.gpu_embeddings import generate_embeddings

texts = ['Test'] * 2000
start = time.time()
embeddings = generate_embeddings(texts, batch_size=1024)
elapsed = time.time() - start

print(f'Worker 2: {len(texts) / elapsed:.1f} embeddings/sec')
print(f'GPU Memory: {torch.cuda.memory_allocated() / 1024**3:.2f} GB')
"

# Test API
docker exec bpo-api python -c "
import time
import torch
from src.extraction.gpu_embeddings import generate_embeddings

texts = ['Test'] * 1000
start = time.time()
embeddings = generate_embeddings(texts, batch_size=512)
elapsed = time.time() - start

print(f'API: {len(texts) / elapsed:.1f} embeddings/sec')
print(f'GPU Memory: {torch.cuda.memory_allocated() / 1024**3:.2f} GB')
"
```

### Test Concurrent Processing

```bash
# Run all three simultaneously in background
docker exec bpo-prefect-agent-1 python /app/benchmark.py &
docker exec bpo-prefect-agent-2 python /app/benchmark.py &
docker exec bpo-api python /app/benchmark.py &

# Monitor GPU usage
nvidia-smi -l 1
```

**Expected Results:**
```
Worker 1: 700 embeddings/sec (43GB used)
Worker 2: 700 embeddings/sec (43GB used)
API:      400 embeddings/sec (10GB used)
Total:    1800 embeddings/sec
```

---

## Monitoring

### Real-Time GPU Monitoring

```bash
# Overall GPU stats
nvidia-smi -l 1

# Detailed memory breakdown
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu --format=csv -l 1

# Per-process memory
nvidia-smi pmon -i 0 -s m -c 100

# GPU utilization percentage
watch -n 1 'nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader'
```

### Container-Level Monitoring

```bash
# All containers resource usage
docker stats

# Just GPU containers
docker stats bpo-prefect-agent-1 bpo-prefect-agent-2 bpo-api

# Logs from all workers
docker-compose logs -f prefect-agent prefect-agent-2 api
```

### Prefect Monitoring

- **UI**: http://localhost:4200
- **Worker Status**: Check both worker-1 and worker-2
- **Task Distribution**: See load balancing in action

---

## Troubleshooting

### Problem: Out of Memory

```bash
# Check current GPU memory
nvidia-smi

# Reduce batch sizes in .env
EMBEDDING_BATCH_SIZE=768           # Instead of 1024
GPU_MEMORY_FRACTION=0.40           # Instead of 0.45

# Restart containers
docker-compose restart
```

### Problem: Containers Fighting for GPU

```bash
# Enable MPS for better sharing
sudo nvidia-cuda-mps-control -d

# Verify MPS running
ps aux | grep mps

# Restart containers to use MPS
docker-compose restart
```

### Problem: One Container Hogging GPU

```bash
# Check which containers are using GPU
nvidia-smi pmon -i 0 -s m

# Adjust GPU_MEMORY_FRACTION in .env
# Worker 1: 0.40 (38.4GB)
# Worker 2: 0.40 (38.4GB)
# API:      0.15 (14.4GB)
# Reserve:  0.05 (4.8GB buffer)

docker-compose restart
```

### Problem: Poor Performance with Multiple Containers

```bash
# Disable one worker temporarily
docker-compose stop prefect-agent-2

# Or scale down API
docker-compose stop api

# Test with single worker
docker exec bpo-prefect-agent-1 python /app/benchmark.py
```

---

## MCP Container Integration

If using Model Context Protocol server:

### MCP Configuration

```yaml
# docker-compose.vastai-gpu-scaled.yml
mcp-server:
  environment:
    - EMBEDDING_BATCH_SIZE=256      # Conservative
    - GPU_MEMORY_FRACTION=0.05      # 4.8GB
```

### Access MCP

```bash
# Check MCP is running
curl http://localhost:8100/health

# MCP endpoints (example)
curl http://localhost:8100/api/context
curl http://localhost:8100/api/embeddings
```

---

## Best Practices

### 1. Start Conservative

```bash
# Begin with lower batch sizes
EMBEDDING_BATCH_SIZE=512

# Monitor for 10 minutes
watch -n 10 nvidia-smi

# Gradually increase if stable
EMBEDDING_BATCH_SIZE=768
EMBEDDING_BATCH_SIZE=1024
```

### 2. Load Balancing

```bash
# Prefect automatically load balances across workers
# Monitor work distribution in Prefect UI
open http://localhost:4200

# Check task counts per worker
docker exec bpo-prefect-agent-1 prefect work-queue inspect default
docker exec bpo-prefect-agent-2 prefect work-queue inspect default
```

### 3. Memory Headroom

Always leave 5-10% GPU memory free:
- **Total allocation**: 90-95% max
- **Reserve**: 5-10% for CUDA overhead
- **Buffer**: Prevents OOM crashes

### 4. Concurrent Workloads

```bash
# Process different document batches simultaneously
# Worker 1: Batch 1-1000
# Worker 2: Batch 1001-2000
# Both run in parallel = 2x throughput
```

---

## Performance Expectations

### Single Worker (Baseline)

| Batch Size | Throughput | GPU Memory |
|------------|------------|------------|
| 512 | 600-700/sec | 22GB |
| 1024 | 700-800/sec | 43GB |
| 2048 | 800-900/sec | 85GB |

### Dual Workers (Scaled)

| Config | Combined Throughput | Total GPU Memory |
|--------|---------------------|------------------|
| 2x512 | 1200-1400/sec | 44GB |
| 2x1024 | 1400-1600/sec | 86GB |
| 1x1024 + 1x512 | 1300-1500/sec | 65GB |

### With API Active

| Workers | API | Combined | GPU Usage |
|---------|-----|----------|-----------|
| 2x1024 | 512 | 1800-2000/sec | 96GB |
| 2x768 | 512 | 1600-1800/sec | 80GB |
| 1x1024 | 512 | 1200-1400/sec | 55GB |

---

## Scaling Recommendations

### For 45,000 Documents

**Single Worker:**
- Time: 4-5 hours
- Throughput: 700-800 embeddings/sec

**Dual Workers:**
- Time: 2-2.5 hours
- Throughput: 1400-1600 embeddings/sec
- **2x faster!**

**Dual Workers + API:**
- Time: 2-2.5 hours (batch processing)
- API: Responsive during processing
- Best for interactive + batch workloads

---

## Summary

### Quick Commands

```bash
# Deploy scaled (2 workers + API)
docker-compose -f docker-compose.yml -f docker-compose.vastai-gpu-scaled.yml --profile scaled up -d

# Monitor GPU
nvidia-smi -l 1

# Check all containers
docker stats

# View logs
docker-compose logs -f

# Stop one worker
docker-compose stop prefect-agent-2

# Restart with new settings
docker-compose restart
```

### Key Settings for Your 96GB GPU

```bash
# .env file
EMBEDDING_BATCH_SIZE=1024          # DOUBLED!
GPU_MEMORY_FRACTION=0.45           # Per worker (43.2GB)

# For maximum throughput
EMBEDDING_BATCH_SIZE=1536          # 1.5x
GPU_MEMORY_FRACTION=0.47           # 45GB

# For extreme testing
EMBEDDING_BATCH_SIZE=2048          # 2x
GPU_MEMORY_FRACTION=0.47           # Uses 90GB
```

---

**You have 96GB - use it! 🚀**
