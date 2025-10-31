#!/usr/bin/env python3
"""
Direct extraction without Prefect orchestration
"""
import asyncio
import time
import sys
import os
import json

# Add the src directory to the path
sys.path.append("/app")

from src.flows.extraction_flow import _batched_documents, insert_documents, extract_entities_batch, store_entities

async def main():
    print("=" * 60)
    print("STARTING DIRECT 5000-DOCUMENT EXTRACTION")
    print("=" * 60)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    start_time = time.time()
    total_documents = 0
    total_entities = 0
    total_relationships = 0
    failed_documents = []
    
    try:
        source_path = "/data/preprocessed/test_5000_rich.jsonl"
        heuristics_version = "2.0.0"
        batch_size = 100
        start_offset = 0
        
        print(f"Processing {source_path} with batch size {batch_size}")
        print(f"Starting from offset {start_offset}")
        print()
        
        batch_count = 0
        for batch_start, batch_end, batch in _batched_documents(source_path, start_offset, batch_size):
            batch_count += 1
            print(f"Processing batch {batch_count}: documents {batch_start}-{batch_end} ({len(batch)} docs)")
            
            try:
                # Insert documents
                normalized_batch = await insert_documents(batch)
                print(f"  ✓ Documents inserted: {len(normalized_batch)}")
                
                # Extract entities
                result = await extract_entities_batch(normalized_batch, f"batch-{batch_count}", heuristics_version)
                entities_count = len(result["entities"])
                relationships_count = len(result["relationships"])
                print(f"  ✓ Entities extracted: {entities_count}")
                print(f"  ✓ Relationships extracted: {relationships_count}")
                
                # Store entities and relationships
                stored_counts = await store_entities(result)
                entities_stored = stored_counts["entities"]
                relationships_stored = stored_counts["relationships"]
                print(f"  ✓ Stored: {entities_stored} entities, {relationships_stored} relationships")
                
                total_documents += len(normalized_batch)
                total_entities += entities_stored
                total_relationships += relationships_stored
                
                print(f"  ✓ Batch {batch_count} completed successfully!")
                print()
                
            except Exception as e:
                print(f"  ❌ Batch {batch_count} failed: {e}")
                failed_documents.extend([doc.get("id", "unknown") for doc in batch])
                continue
        
        duration = time.time() - start_time
        success_rate = (total_documents - len(failed_documents)) / total_documents if total_documents > 0 else 0
        
        print("=" * 60)
        print("EXTRACTION COMPLETED!")
        print("=" * 60)
        print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print()
        print("FINAL RESULTS:")
        print(f"  Documents processed: {total_documents:,}")
        print(f"  Entities extracted: {total_entities:,}")
        print(f"  Relationships created: {total_relationships:,}")
        print(f"  Failed documents: {len(failed_documents)}")
        print(f"  Success rate: {success_rate:.1%}")
        print()
        print("PERFORMANCE METRICS:")
        print(f"  Throughput: {total_documents/duration:.2f} docs/sec")
        print(f"  Entities per doc: {total_entities/total_documents:.1f}")
        print(f"  Relationships per doc: {total_relationships/total_documents:.1f}")
        
        return {
            "total_processed": total_documents,
            "total_entities": total_entities,
            "total_relationships": total_relationships,
            "failed_documents": failed_documents,
            "success_rate": success_rate
        }
        
    except Exception as e:
        print(f"\n❌ EXTRACTION FAILED: {e}")
        print(f"Duration before failure: {time.time() - start_time:.1f} seconds")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(main())




