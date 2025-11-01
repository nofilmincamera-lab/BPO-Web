# GPU Verification Testing Guide

## Overview

The `test_gpu_extraction.py` script provides comprehensive verification that GPU acceleration is properly engaged during the BPO document extraction pipeline.

## Test Components

### 1. GPU Availability Check
- Detects CUDA-capable GPUs
- Reports GPU model, CUDA version, and memory
- Validates PyTorch GPU support

### 2. GPU Memory Monitoring
- Tracks memory allocation during model loading
- Monitors memory usage during document processing
- Detects memory leaks
- Verifies GPU is actively used (not just available)

### 3. GPU Utilization Test
- Processes realistic document batch
- Verifies GPU memory increases during processing
- Confirms entities are successfully extracted
- Validates GPU is actively processing

### 4. Performance Comparison
- Benchmarks extraction throughput
- Compares GPU performance against CPU baseline
- Reports docs/second and speedup ratio
- Expected: 2-5x speedup with GPU

### 5. Integration Test
- Tests actual extraction flow (`extract_entities_batch`)
- Verifies GPU usage in full pipeline
- Validates entity and relationship extraction
- Monitors GPU memory during real workload

### 6. Stress Test
- Processes 200+ documents in batches
- Monitors sustained GPU utilization
- Detects memory leaks over time
- Validates production-scale performance

## Usage

### Basic Usage

Run all tests:
```bash
python test_gpu_extraction.py
```

### Quick Tests Only

Skip integration and stress tests (faster):
```bash
python test_gpu_extraction.py --quick
```

### Verbose Output

Enable detailed output:
```bash
python test_gpu_extraction.py --verbose
```

### Docker Usage

Run inside GPU-enabled container:
```bash
docker exec bpo-prefect-agent python /app/test_gpu_extraction.py
```

Run from Docker API container:
```bash
docker exec bpo-api python /app/test_gpu_extraction.py
```

## Expected Output

### Successful GPU Test

```
========================================
GPU VERIFICATION TEST SUITE
BPO Document Extraction Pipeline
========================================

============================================================
[1/6] GPU AVAILABILITY CHECK
============================================================
✓ PyTorch version: 2.0.1
✓ GPU detected: NVIDIA GeForce RTX 3060
✓ Device count: 1
✓ CUDA version: 11.8
✓ Total GPU memory: 12.00 GB

============================================================
[2/6] GPU MEMORY MONITORING
============================================================
Initial GPU memory: 0.0 MB allocated
Loading spaCy model...
After model load: 512.3 MB allocated
Processing test documents...
During processing: 1024.5 MB allocated
Peak memory: 1024.5 MB
✓ GPU memory increased by 1024.5 MB
✓ GPU is being actively used
After cleanup: 0.0 MB allocated

============================================================
[3/6] GPU UTILIZATION TEST
============================================================
Loading model and processing batch...
Model GPU flag: True
✓ Processed 20 documents
✓ Extracted 245 entities
Memory delta: 512.3 MB
✓ GPU is actively processing (memory increased and entities extracted)

============================================================
[4/6] GPU vs CPU PERFORMANCE COMPARISON
============================================================
Testing with 50 documents...

Benchmarking current configuration...
✓ GPU throughput: 12.35 docs/sec
✓ GPU time: 4.05 seconds
✓ Entities extracted: 623

✓ Estimated CPU throughput: ~3.53 docs/sec
✓ Estimated speedup: ~3.5x
  (Note: Actual CPU benchmark requires CPU-only spaCy installation)

============================================================
[5/6] INTEGRATION TEST WITH EXTRACTION FLOW
============================================================
Testing extraction flow with 10 documents...
✓ Extraction completed successfully
✓ Entities extracted: 156
✓ Relationships extracted: 89
GPU memory used: 256.7 MB
✓ GPU was engaged during extraction

============================================================
[6/6] GPU STRESS TEST
============================================================
Stress testing with 200 documents...
  Processed 100/200 documents...
✓ Processed 200 documents in 16.2 seconds
✓ Throughput: 12.35 docs/sec
✓ Total entities: 2468
✓ Entities per doc: 12.3
✓ No memory leaks detected

============================================================
GPU VERIFICATION TEST SUMMARY
============================================================
✓ GPU Available: NVIDIA GeForce RTX 3060
✓ GPU Memory: Increased during processing
✓ GPU Utilization: Active (245 entities)
✓ Performance: GPU 3.5x faster than CPU
✓ Integration: 156 entities, 89 relationships
✓ Stress Test: 200 docs @ 12.35 docs/sec
============================================================
✓✓✓ TEST RESULT: PASS ✓✓✓
GPU is properly engaged in extraction!
============================================================
```

### No GPU Available

```
============================================================
[1/6] GPU AVAILABILITY CHECK
============================================================
✓ PyTorch version: 2.0.1
✗ GPU not available (CUDA not detected)

⚠ GPU not available. Remaining tests will be skipped or limited.

...

============================================================
GPU VERIFICATION TEST SUMMARY
============================================================
✗ GPU Not Available: CUDA not available
- GPU Memory: Skipped (no GPU)
- GPU Utilization: Skipped (no GPU)
- Performance: Skipped (no GPU)
...
============================================================
✗✗✗ TEST RESULT: NO GPU DETECTED ✗✗✗
Extraction will run on CPU (slower)
============================================================
```

## Success Criteria

The test **PASSES** if:
1. ✓ GPU is detected and available
2. ✓ GPU memory increases by >10MB during processing
3. ✓ Entities are successfully extracted
4. ✓ GPU throughput > 5 docs/sec
5. ✓ Integration test completes successfully
6. ✓ No memory leaks detected

The test **WARNS** if:
- ⚠ GPU available but memory doesn't increase significantly
- ⚠ GPU performance not better than expected
- ⚠ Possible memory leaks detected

The test **FAILS** if:
- ✗ GPU not detected when expected
- ✗ Integration test fails
- ✗ Severe errors during processing

## Troubleshooting

### GPU Not Detected

**Problem**: `✗ GPU not available (CUDA not detected)`

**Solutions**:
1. Verify NVIDIA drivers installed: `nvidia-smi`
2. Check Docker GPU runtime: `docker run --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi`
3. Ensure container has GPU access: Check `docker-compose.yml` has `runtime: nvidia`
4. Verify CUDA toolkit installed in container

### GPU Available but Not Used

**Problem**: `⚠ GPU memory only increased by X MB`

**Solutions**:
1. Check spaCy GPU configuration in `src/extraction/spacy_pipeline.py`
2. Verify PyTorch CUDA build: `python -c "import torch; print(torch.cuda.is_available())"`
3. Check for CPU fallback in logs
4. Ensure spaCy models support GPU acceleration

### Low Performance

**Problem**: GPU throughput < 5 docs/sec

**Solutions**:
1. Check GPU utilization during test: `nvidia-smi -l 1`
2. Verify batch size is appropriate
3. Check for CPU bottlenecks
4. Monitor system resources (RAM, CPU)
5. Ensure no thermal throttling

### Memory Leaks

**Problem**: `⚠ Possible memory leak detected`

**Solutions**:
1. Verify proper cleanup in extraction code
2. Check for unreleased GPU tensors
3. Add `torch.cuda.empty_cache()` calls
4. Review spaCy pipeline for memory leaks

## Integration with CI/CD

### Pytest Integration

Add to `conftest.py`:
```python
import pytest

@pytest.mark.gpu
def test_gpu_extraction():
    """GPU extraction test marker."""
    from test_gpu_extraction import run_comprehensive_tests
    import asyncio
    
    results = asyncio.run(run_comprehensive_tests(quick=True))
    assert results["gpu_availability"]["available"]
    assert results["utilization"]["utilized"]
```

Run GPU tests:
```bash
pytest -m gpu -v
```

### Docker Compose Health Check

Add to `docker-compose.yml`:
```yaml
services:
  prefect-agent:
    healthcheck:
      test: ["CMD", "python", "/app/test_gpu_extraction.py", "--quick"]
      interval: 5m
      timeout: 30s
      retries: 2
      start_period: 1m
```

## Performance Benchmarks

### Expected Throughput (RTX 3060)

| Document Size | GPU (docs/sec) | CPU (docs/sec) | Speedup |
|---------------|----------------|----------------|---------|
| Small (< 1KB) | 20-30          | 8-12           | 2.5x    |
| Medium (1-5KB)| 10-15          | 3-5            | 3.5x    |
| Large (> 5KB) | 5-8            | 1-2            | 4-5x    |

### Memory Requirements

- Model loading: ~500 MB GPU memory
- Active processing: +200-500 MB per batch
- Peak usage: ~1-2 GB for standard workloads

## Next Steps

After verifying GPU is engaged:

1. **Run Full Extraction**: `python queue_extraction_prefect.py`
2. **Monitor GPU**: `nvidia-smi -l 1` during extraction
3. **Check Logs**: Review extraction logs for GPU confirmation
4. **Validate Results**: Check database for extracted entities

## Related Documentation

- [COMMANDS.md](../COMMANDS.md) - Full command reference
- [README.md](../README.md) - Project overview
- [src/extraction/spacy_pipeline.py](../src/extraction/spacy_pipeline.py) - GPU pipeline implementation
- [docker-compose.yml](../docker-compose.yml) - GPU container configuration

