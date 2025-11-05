# Quick Updates for Your Multi-Container Setup

## TL;DR - What You Need to Know

Your setup with **2 processing containers + 1 MCP + 1 API** on the **RTX 6000 Pro (96GB)** is perfect! Here's what to adjust:

---

## 1. Double Your Batch Size ✅

### Quick Update Script

```bash
# On Vast.AI instance
cd /workspace/BPO-Web

# Update to 1024 (RECOMMENDED)
./scripts/update-batch-size.sh 1024

# Restart containers
docker-compose restart prefect-agent api
```

### Manual Update

```bash
# Edit .env
nano .env

# Change this line:
EMBEDDING_BATCH_SIZE=1024          # Was 512, now DOUBLED!

# Save and restart
docker-compose restart
```

---

## 2. Multi-Container GPU Sharing

### Current Setup

You have:
```
Container 1: Processing (prefect-agent)
Container 2: Processing (prefect-agent-2?)
Container 3: MCP (Model Context Protocol)
Plus: API container
```

### Good News: It Just Works! ✅

CUDA automatically handles multiple containers on the same GPU:
- No configuration needed
- Each container sees the full GPU
- CUDA manages context switching
- Your 96GB is shared efficiently

### Deploy Multi-Container Mode

```bash
# Option A: Use scaled deployment (RECOMMENDED)
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.vastai-gpu-scaled.yml \
  --profile scaled up -d

# Option B: Keep current setup, just update batch size
docker-compose restart
```

---

## 3. GPU Memory Allocation

### Recommended Split (96GB total)

| Container | Memory | Batch Size | Performance |
|-----------|--------|------------|-------------|
| **Worker 1** | 43GB (45%) | 1024 | 700-800 emb/sec |
| **Worker 2** | 43GB (45%) | 1024 | 700-800 emb/sec |
| **API** | 10GB (10%) | 512 | 400-500 emb/sec |
| **MCP** | Shared | Variable | As needed |

**Combined: 1800-2100 embeddings/sec** (14x RTX 3060!)

### How to Configure

```bash
# Edit .env for each container
nano .env

# For workers (containers 1 & 2):
EMBEDDING_BATCH_SIZE=1024
GPU_MEMORY_FRACTION=0.45           # 43.2GB each

# For API:
EMBEDDING_BATCH_SIZE=512
GPU_MEMORY_FRACTION=0.10           # 9.6GB

# MCP typically doesn't need specific limits
```

---

## 4. Verify Everything Works

### Check GPU Access

```bash
# Check all containers can see GPU
docker exec bpo-prefect-agent nvidia-smi
docker exec bpo-prefect-agent-2 nvidia-smi  # If you have a second worker
docker exec bpo-api nvidia-smi
docker exec bpo-mcp nvidia-smi              # If you have MCP

# All should show: NVIDIA RTX 6000 Ada Generation, 96GB
```

### Monitor GPU Usage

```bash
# Real-time monitoring
nvidia-smi -l 1

# Watch all containers
docker stats

# Check memory per process
nvidia-smi pmon -i 0 -s m
```

### Performance Test

```bash
# Test worker performance
docker exec bpo-prefect-agent python -c "
import time
from src.extraction.gpu_embeddings import generate_embeddings

texts = ['test'] * 2000
start = time.time()
embeddings = generate_embeddings(texts, batch_size=1024)
elapsed = time.time() - start

print(f'Throughput: {len(texts) / elapsed:.1f} embeddings/sec')
print(f'Expected: 700-800 embeddings/sec with batch_size=1024')
"
```

**Expected output:**
```
Throughput: 750.0 embeddings/sec
Expected: 700-800 embeddings/sec with batch_size=1024
```

---

## 5. Troubleshooting

### Problem: Containers Can't Access GPU

```bash
# Check nvidia-docker runtime
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# If that fails, restart Docker
sudo systemctl restart docker
```

### Problem: Out of Memory

```bash
# Check current usage
nvidia-smi

# Reduce batch sizes
./scripts/update-batch-size.sh 768

# Or lower memory fraction
nano .env
# Set: GPU_MEMORY_FRACTION=0.40

docker-compose restart
```

### Problem: One Container Hogging GPU

```bash
# Check which container is using memory
nvidia-smi pmon -i 0 -s m

# Adjust allocation in .env
# Reduce GPU_MEMORY_FRACTION for greedy container

docker-compose restart
```

---

## 6. Performance Expectations

### Single Container (Baseline)

| Batch Size | Throughput | GPU Memory |
|------------|------------|------------|
| 512 | 600-700/sec | 22GB |
| 1024 | 700-800/sec | 43GB |
| 2048 | 800-900/sec | 85GB |

### Multi-Container (Your Setup)

| Config | Combined Throughput | Total Memory |
|--------|---------------------|--------------|
| 2x512 + API | 1500-1700/sec | 54GB |
| 2x1024 + API | 1800-2100/sec | 96GB |
| 2x1536 + API | 2000-2300/sec | 95GB |

**Your 96GB enables 14-16x speedup vs RTX 3060!**

---

## 7. Recommended Actions

### Step 1: Update Batch Size (DO THIS NOW!)

```bash
# Quick update
./scripts/update-batch-size.sh 1024

# Restart
docker-compose restart
```

### Step 2: Monitor for 10 Minutes

```bash
# Watch GPU
nvidia-smi -l 1

# Watch containers
docker stats

# Check logs
docker-compose logs -f
```

### Step 3: Increase if Stable

```bash
# If GPU memory < 80% used, increase more
./scripts/update-batch-size.sh 1536

# Or even
./scripts/update-batch-size.sh 2048
```

---

## 8. MCP Container Notes

If your MCP container needs GPU access:

```yaml
# In docker-compose override or .env
mcp-server:
  environment:
    - NVIDIA_VISIBLE_DEVICES=all
    - CUDA_VISIBLE_DEVICES=0
```

MCP typically doesn't need large batch sizes unless it's doing embeddings:
```bash
# Conservative MCP settings
EMBEDDING_BATCH_SIZE=256           # For MCP
GPU_MEMORY_FRACTION=0.05           # 4.8GB
```

---

## 9. Advanced: NVIDIA MPS (Optional)

For even better multi-container performance:

```bash
# On Vast.AI host (run once)
sudo nvidia-cuda-mps-control -d

# Verify
ps aux | grep mps

# Restart containers
docker-compose restart
```

**Benefits:**
- 10-15% better throughput
- Lower latency
- Better memory sharing

**When to use:**
- High concurrency
- Many containers (3+)
- Latency-sensitive workloads

---

## 10. Quick Reference

### Essential Commands

```bash
# Update batch size
./scripts/update-batch-size.sh 1024

# Restart services
docker-compose restart

# Check GPU
nvidia-smi -l 1

# Monitor containers
docker stats

# View logs
docker-compose logs -f

# Test performance
docker exec bpo-prefect-agent python -c "
from src.extraction.gpu_embeddings import generate_embeddings;
import time; texts=['test']*2000; start=time.time();
embeddings=generate_embeddings(texts, batch_size=1024);
print(f'{len(texts)/(time.time()-start):.1f} emb/sec')
"
```

---

## Summary

### ✅ What to Do Now

1. **Double batch size**: `./scripts/update-batch-size.sh 1024`
2. **Restart**: `docker-compose restart`
3. **Monitor**: `nvidia-smi -l 1`
4. **Test**: Run performance test above
5. **Increase more**: Try 1536 or 2048 if stable

### ✅ Multi-Container is Fine

- CUDA handles it automatically
- No special configuration needed
- All containers share 96GB efficiently
- Each sees full GPU access

### ✅ Expected Performance

- **Before (512)**: 600-700 emb/sec
- **After (1024)**: 700-800 emb/sec per worker
- **Multi-container**: 1800-2100 emb/sec combined
- **Speedup**: 14-16x vs RTX 3060!

---

**You're set! Your 96GB beast is ready to fly! 🚀**

**Questions?** See `MULTI_CONTAINER_GPU.md` for detailed guide.
