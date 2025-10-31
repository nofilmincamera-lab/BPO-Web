#!/usr/bin/env python3
"""
Direct extraction script for 5000 documents
"""
import asyncio
import time
import sys
import os

# Add the src directory to the path
sys.path.append("/app")

from src.flows.extraction_flow import extract_documents_flow

async def main():
    print("=" * 60)
    print("STARTING FRESH 5000-DOCUMENT EXTRACTION")
    print("=" * 60)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    start_time = time.time()
    
    try:
        # CANONICAL PRODUCTION DATASET - preprocessed from scripts/preprocess.py
        # Change to test_5000_rich.jsonl for testing only
        result = await extract_documents_flow(
            source_path="/data/processed/preprocessed.jsonl",
            heuristics_version="2.0.0",
            batch_size=100,
            start_offset=0
        )
        
        duration = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("EXTRACTION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print()
        print("FINAL RESULTS:")
        print(f"  Documents processed: {result['total_processed']:,}")
        print(f"  Entities extracted: {result['total_entities']:,}")
        print(f"  Relationships created: {result['total_relationships']:,}")
        print(f"  Failed documents: {len(result.get('failed_documents', []))}")
        print(f"  Success rate: {result.get('success_rate', 0):.1%}")
        print()
        print("PERFORMANCE METRICS:")
        print(f"  Throughput: {result['total_processed']/duration:.2f} docs/sec")
        print(f"  Entities per doc: {result['total_entities']/result['total_processed']:.1f}")
        print(f"  Relationships per doc: {result['total_relationships']/result['total_processed']:.1f}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ EXTRACTION FAILED: {e}")
        print(f"Duration before failure: {time.time() - start_time:.1f} seconds")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(main())




