# GPU Test Quick Reference

## Quick Commands

```bash
# Run all tests
python test_gpu_extraction.py

# Quick tests only (faster)
python test_gpu_extraction.py --quick

# In Docker (GPU agent)
docker exec bpo-prefect-agent python /app/test_gpu_extraction.py

# In Docker (API)
docker exec bpo-api python /app/test_gpu_extraction.py
```

## What Gets Tested

1. ✓ GPU Available? (CUDA, device name, memory)
2. ✓ GPU Memory Increases? (model load + processing)
3. ✓ GPU Actually Used? (entities extracted, memory delta)
4. ✓ GPU Fast Enough? (throughput, speedup)
5. ✓ Integration Works? (extraction flow end-to-end)
6. ✓ No Memory Leaks? (stress test 200 docs)

## Expected Results

### PASS ✓
- GPU detected: NVIDIA GeForce RTX 3060
- Memory increases: >500 MB during processing
- Throughput: 10-15 docs/sec
- Speedup: 2-5x vs CPU
- Entities extracted: 100+ per batch
- No memory leaks

### FAIL ✗
- GPU not detected
- No memory increase
- Low throughput (<3 docs/sec)
- Integration test fails
- Memory leaks detected

## Troubleshooting

### GPU Not Detected
```bash
# Check GPU
nvidia-smi

# Check Docker GPU
docker run --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Check container has GPU
docker exec bpo-prefect-agent nvidia-smi
```

### GPU Not Used
```bash
# Check PyTorch CUDA
docker exec bpo-prefect-agent python -c "import torch; print(torch.cuda.is_available())"

# Monitor during test
nvidia-smi -l 1
```

## Key Metrics

| Metric | Expected (RTX 3060) |
|--------|---------------------|
| Model load | ~500 MB |
| Processing | +200-500 MB |
| Throughput | 10-15 docs/sec |
| Speedup | 3-5x |

## Documentation

- Full guide: `docs/GPU_TESTING.md`
- Implementation: `docs/GPU_TEST_IMPLEMENTATION.md`
- Code: `test_gpu_extraction.py`

