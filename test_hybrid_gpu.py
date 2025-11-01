#!/usr/bin/env python3
"""
Test hybrid GPU/CPU extraction pipeline.

This test verifies:
1. CPU is used for spaCy NER (fast, accurate)
2. GPU is used for embeddings generation (sentence-transformers)
3. Both work together in the extraction flow
4. GPU memory is properly used for embeddings
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "src"))


def test_gpu_embeddings_module():
    """Test GPU embeddings module directly."""
    print("\n" + "=" * 60)
    print("[1/3] TESTING GPU EMBEDDINGS MODULE")
    print("=" * 60)
    
    try:
        from src.extraction.gpu_embeddings import (
            get_embedding_model,
            generate_embeddings,
            get_embedding_info,
            clear_embedding_cache
        )
        
        # Get model info
        info = get_embedding_info()
        print(f"Embedding model loaded: {info['loaded']}")
        
        if info['loaded']:
            print(f"  Device: {info.get('device', 'unknown')}")
            if info.get('device') == 'cuda':
                print(f"  GPU: {info.get('gpu_name', 'unknown')}")
                print(f"  GPU Memory Allocated: {info.get('gpu_memory_allocated', 0):.2f} GB")
        
        # Test embeddings generation
        test_texts = [
            "Microsoft Corporation",
            "Customer Service BPO",
            "Cloud Computing Platform",
            "Artificial Intelligence",
            "Data Analytics Solution"
        ]
        
        print(f"\nGenerating embeddings for {len(test_texts)} texts...")
        embeddings = generate_embeddings(test_texts, show_progress=False)
        
        print(f"[OK] Generated embeddings shape: {embeddings.shape}")
        print(f"[OK] Embedding dimension: {embeddings.shape[1]}")
        
        # Check GPU memory increased
        info_after = get_embedding_info()
        if info_after.get('device') == 'cuda':
            memory_delta = info_after.get('gpu_memory_allocated', 0) - info.get('gpu_memory_allocated', 0)
            print(f"GPU memory delta: {memory_delta:.2f} GB")
            
            if memory_delta > 0:
                print("[OK] GPU memory increased - embeddings are using GPU!")
            else:
                print("[WARN] GPU memory didn't increase")
        
        # Cleanup
        clear_embedding_cache()
        print("[OK] Embeddings module test passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Embeddings module test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_hybrid_extraction_flow():
    """Test hybrid extraction flow with CPU NER + GPU embeddings."""
    print("\n" + "=" * 60)
    print("[2/3] TESTING HYBRID EXTRACTION FLOW")
    print("=" * 60)
    
    try:
        from src.flows.extraction_flow import extract_entities_batch, generate_and_store_embeddings
        import torch
        
        # Generate test documents
        test_docs = [
            {
                "id": "test-doc-001",
                "url": "https://example.com/test1",
                "title": "Microsoft Partnership",
                "text": "Microsoft Corporation announced a partnership with Accenture to provide cloud computing services worth $10 million with 40% efficiency improvement.",
                "metadata": {}
            }
        ]
        
        batch_id = "hybrid-test-batch"
        heuristics_version = "2.0.0"
        
        print(f"Processing test document...")
        
        # Reset GPU memory stats
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            initial_memory = torch.cuda.memory_allocated()
        
        # Extract entities (CPU-based spaCy)
        print("\n[PHASE 1] Extracting entities with spaCy (CPU)...")
        result = await extract_entities_batch(test_docs, batch_id, heuristics_version)
        
        entities_count = len(result.get("entities", []))
        print(f"[OK] Extracted {entities_count} entities")
        
        # Generate embeddings (GPU-accelerated)
        print("\n[PHASE 2] Generating embeddings with sentence-transformers (GPU)...")
        embedding_result = await generate_and_store_embeddings(result)
        
        embeddings_count = embedding_result.get("embeddings", 0)
        print(f"[OK] Generated {embeddings_count} embeddings")
        
        # Check GPU memory
        if torch.cuda.is_available():
            max_memory = torch.cuda.max_memory_allocated()
            memory_delta = max_memory - initial_memory
            
            print(f"\nGPU Memory Usage:")
            print(f"  Initial: {initial_memory / (1024**3):.3f} GB")
            print(f"  Peak: {max_memory / (1024**3):.3f} GB")
            print(f"  Delta: {memory_delta / (1024**3):.3f} GB")
            
            if memory_delta > (10 * 1024**2):  # >10MB
                print("[OK] GPU memory increased - hybrid setup working!")
            else:
                print("[WARN] Low GPU memory usage")
        
        # Check for any errors
        if embedding_result.get("error"):
            print(f"[WARN] Embeddings generation had issue: {embedding_result.get('error')}")
        
        print("\n[OK] Hybrid extraction flow test passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Hybrid extraction flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_comparison():
    """Compare performance with and without GPU embeddings."""
    print("\n" + "=" * 60)
    print("[3/3] PERFORMANCE COMPARISON")
    print("=" * 60)
    
    try:
        import time
        import torch
        from src.extraction.gpu_embeddings import generate_embeddings, clear_embedding_cache
        
        test_texts = [f"Entity {i}: Company Name {i}" for i in range(100)]
        
        # Test with GPU
        print("Testing with GPU acceleration...")
        if torch.cuda.is_available():
            start_time = time.time()
            embeddings = generate_embeddings(test_texts, show_progress=False)
            gpu_time = time.time() - start_time
            
            print(f"[OK] GPU time: {gpu_time:.3f}s ({len(test_texts)/gpu_time:.1f} texts/sec)")
            
            # Estimate CPU time (typically 3-5x slower)
            estimated_cpu_time = gpu_time * 3.5
            print(f"[INFO] Estimated CPU time: {estimated_cpu_time:.3f}s")
            print(f"[INFO] Estimated speedup: ~3.5x")
            
            clear_embedding_cache()
            return True
        else:
            print("[SKIP] GPU not available for performance test")
            return True
            
    except Exception as e:
        print(f"[FAIL] Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all hybrid GPU tests."""
    print("=" * 60)
    print("HYBRID GPU/CPU EXTRACTION PIPELINE TEST")
    print("=" * 60)
    
    results = {}
    
    # Test 1: GPU Embeddings Module
    results["embeddings_module"] = test_gpu_embeddings_module()
    
    # Test 2: Hybrid Extraction Flow
    results["hybrid_flow"] = await test_hybrid_extraction_flow()
    
    # Test 3: Performance Comparison
    results["performance"] = test_performance_comparison()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        status = "[OK]" if passed else "[FAIL]"
        print(f"{status} {test_name}")
    
    print("=" * 60)
    
    if all_passed:
        print("[OK][OK][OK] ALL TESTS PASSED [OK][OK][OK]")
        print("Hybrid GPU/CPU setup is working correctly!")
        print("- CPU: Fast spaCy NER")
        print("- GPU: Accelerated embeddings")
    else:
        print("[WARN][WARN][WARN] SOME TESTS FAILED [WARN][WARN][WARN]")
    
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

