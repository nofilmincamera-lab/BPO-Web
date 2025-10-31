#!/usr/bin/env python3
"""
⚠️ DEPRECATED: This script bypasses the established heuristics-first extraction pipeline.

USE INSTEAD:
  - run_simple_extraction.py (uses proper multi-tier heuristics → regex → spaCy)
  - queue_extraction_prefect.py (orchestrated with Prefect)

ISSUES WITH THIS SCRIPT:
  1. Loads entire corpus into memory (causes OOM on large datasets)
  2. Uses vanilla spaCy extraction only (ignores heuristics)
  3. Applies synthetic confidence scores (0.8 default) instead of tier-based scoring
  4. Stores shallow entity records without proper source attribution
  5. Contradicts the established pipeline design in src/flows/extraction_flow.py

This script is preserved for reference but should NOT be used for production extraction.
"""
import asyncio
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any
import asyncpg
import hashlib

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.extraction.spacy_pipeline import get_extraction_nlp
from src.heuristics import get_heuristics_loader

class GPUExtractionPipeline:
    """Direct GPU extraction pipeline"""
    
    def __init__(self, source_path: str, batch_size: int = 100):
        self.source_path = source_path
        self.batch_size = batch_size
        self.total_entities = 0
        self.total_relationships = 0
        self.failed_docs = []
        self.processed_docs = 0
        
        # Database connection
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = int(os.getenv("DB_PORT", 5432))
        self.db_name = os.getenv("DB_NAME", "bpo_intel")
        self.db_user = os.getenv("DB_USER", "postgres")
        self.db_password = os.getenv("DB_PASSWORD", "postgres")
        
        # Load models
        print("Loading spaCy model with GPU support...")
        self.nlp = get_extraction_nlp()
        print(f"SUCCESS: spaCy model loaded (GPU: {self.nlp.meta.get('gpu', False)})")
        
        print("Loading heuristics...")
        self.heuristics = get_heuristics_loader()
        self.heuristics_data = self.heuristics.data if self.heuristics else None
        self.industry_lookup = self.heuristics_data.industry_lookup if self.heuristics_data else {}
        self.service_lookup = self.heuristics_data.service_lookup if self.heuristics_data else {}
        print("SUCCESS: Heuristics loaded")
    
    async def process_documents(self):
        """Process all documents with GPU acceleration"""
        print(f"\nStarting GPU extraction pipeline")
        print(f"   Source: {self.source_path}")
        print(f"   Batch size: {self.batch_size}")
        print(f"   GPU enabled: {self.nlp.meta.get('gpu', False)}")
        print("=" * 60)
        
        start_time = time.time()
        
        # Read documents
        documents = self._read_documents()
        total_docs = len(documents)
        print(f"Loaded {total_docs:,} documents")
        
        # Process in batches
        for batch_start in range(0, total_docs, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_docs)
            batch = documents[batch_start:batch_end]
            batch_id = f"batch-{batch_start}-{batch_end}"
            
            print(f"\nProcessing batch {batch_start:,}-{batch_end:,} ({len(batch)} docs)")
            
            try:
                # Process batch
                batch_result = await self._process_batch(batch, batch_id)
                
                # Update totals
                self.total_entities += batch_result["entities"]
                self.total_relationships += batch_result["relationships"]
                self.failed_docs.extend(batch_result["failed_docs"])
                self.processed_docs += len(batch)
                
                # Progress update
                progress = (batch_end / total_docs) * 100
                elapsed = time.time() - start_time
                rate = self.processed_docs / elapsed if elapsed > 0 else 0
                eta = (total_docs - batch_end) / rate if rate > 0 else 0
                
                print(f"   SUCCESS: Batch complete: {batch_result['entities']:,} entities, {batch_result['relationships']:,} relationships")
                print(f"   Progress: {progress:.1f}% | Rate: {rate:.1f} docs/sec | ETA: {eta/60:.1f} min")
                
            except Exception as e:
                print(f"   ERROR: Batch failed: {e}")
                self.failed_docs.extend([{"batch_id": batch_id, "error": str(e)}])
        
        # Final summary
        elapsed = time.time() - start_time
        rate = self.processed_docs / elapsed if elapsed > 0 else 0
        
        summary = {
            "total_processed": self.processed_docs,
            "total_entities": self.total_entities,
            "total_relationships": self.total_relationships,
            "failed_documents": len(self.failed_docs),
            "success_rate": (self.processed_docs - len(self.failed_docs)) / self.processed_docs if self.processed_docs > 0 else 0,
            "processing_time": elapsed,
            "processing_rate": rate,
            "gpu_enabled": self.nlp.meta.get('gpu', False)
        }
        
        print(f"\nEXTRACTION COMPLETE!")
        print(f"   Processed: {summary['total_processed']:,} documents")
        print(f"   Entities: {summary['total_entities']:,}")
        print(f"   Relationships: {summary['total_relationships']:,}")
        print(f"   Failed: {summary['failed_documents']:,}")
        print(f"   Success rate: {summary['success_rate']:.1%}")
        print(f"   Time: {elapsed/60:.1f} minutes")
        print(f"   Rate: {rate:.1f} docs/sec")
        print(f"   GPU: {'Enabled' if summary['gpu_enabled'] else 'Disabled'}")
        
        return summary
    
    def _read_documents(self) -> List[Dict]:
        """Read documents from JSONL file"""
        documents = []
        with open(self.source_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    doc = json.loads(line.strip())
                    documents.append(doc)
                except json.JSONDecodeError as e:
                    print(f"WARNING: Skipping invalid JSON at line {line_num}: {e}")
                    continue
        return documents
    
    async def _process_batch(self, batch: List[Dict], batch_id: str) -> Dict[str, Any]:
        """Process a batch of documents"""
        entities = []
        relationships = []
        failed_docs = []
        
        for doc in batch:
            try:
                # Extract text
                text = doc.get("text") or doc.get("metadata", {}).get("text") or ""
                if not text:
                    continue
                
                # Process with spaCy (GPU accelerated)
                spacy_doc = self.nlp(text)
                
                # Extract entities
                doc_entities = self._extract_entities(spacy_doc, doc)
                entities.extend(doc_entities)
                
                # Extract relationships
                doc_relationships = self._extract_relationships(spacy_doc, doc_entities)
                relationships.extend(doc_relationships)
                
            except Exception as e:
                failed_docs.append({
                    "doc_id": doc.get("id", "unknown"),
                    "error": str(e)
                })
        
        # Store in database
        await self._store_batch_results(entities, relationships, batch_id)
        
        return {
            "entities": len(entities),
            "relationships": len(relationships),
            "failed_docs": failed_docs
        }
    
    def _extract_entities(self, spacy_doc, doc: Dict) -> List[Dict]:
        """Extract entities from spaCy document"""
        entities = []
        
        for ent in spacy_doc.ents:
            entity = {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": 0.8,  # Default confidence
                "doc_id": doc.get("id", "unknown"),
                "source_url": doc.get("url", ""),
                "extracted_at": time.time()
            }
            entities.append(entity)
        
        return entities
    
    def _extract_relationships(self, spacy_doc, entities: List[Dict]) -> List[Dict]:
        """Extract relationships between entities"""
        relationships = []
        
        # Simple co-occurrence based relationships
        for i, ent1 in enumerate(entities):
            for j, ent2 in enumerate(entities[i+1:], i+1):
                if ent1["label"] != ent2["label"]:  # Different entity types
                    relationship = {
                        "source_entity": ent1["text"],
                        "target_entity": ent2["text"],
                        "source_label": ent1["label"],
                        "target_label": ent2["label"],
                        "relationship_type": "co_occurs",
                        "confidence": 0.7,
                        "doc_id": ent1["doc_id"],
                        "extracted_at": time.time()
                    }
                    relationships.append(relationship)
        
        return relationships
    
    async def _store_batch_results(self, entities: List[Dict], relationships: List[Dict], batch_id: str):
        """Store batch results in database"""
        try:
            async with asyncpg.create_pool(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                min_size=1,
                max_size=5,
            ) as pool:
                async with pool.acquire() as conn:
                    # Store entities
                    if entities:
                        await conn.executemany(
                            """INSERT INTO entities (text, label, start_pos, end_pos, confidence, doc_id, source_url, extracted_at)
                               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                               ON CONFLICT (text, label, doc_id) DO NOTHING""",
                            [(e["text"], e["label"], e["start"], e["end"], e["confidence"], e["doc_id"], e["source_url"], e["extracted_at"]) for e in entities]
                        )
                    
                    # Store relationships
                    if relationships:
                        await conn.executemany(
                            """INSERT INTO relationships (source_entity, target_entity, source_label, target_label, relationship_type, confidence, doc_id, extracted_at)
                               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                               ON CONFLICT (source_entity, target_entity, doc_id) DO NOTHING""",
                            [(r["source_entity"], r["target_entity"], r["source_label"], r["target_label"], r["relationship_type"], r["confidence"], r["doc_id"], r["extracted_at"]) for r in relationships]
                        )
                    
                    print(f"   Stored {len(entities):,} entities, {len(relationships):,} relationships")
                    
        except Exception as e:
            print(f"   ERROR: Database error: {e}")

async def main():
    """Main extraction function"""
    print("=" * 80)
    print("⚠️  DEPRECATED SCRIPT - DO NOT USE FOR PRODUCTION")
    print("=" * 80)
    print("")
    print("This script bypasses the established heuristics-first extraction pipeline!")
    print("")
    print("USE THESE INSTEAD:")
    print("  1. run_simple_extraction.py --source /data/processed/preprocessed.jsonl")
    print("     (Uses proper multi-tier: heuristics → regex → spaCy)")
    print("")
    print("  2. python queue_extraction_prefect.py")
    print("     (Orchestrated with Prefect, includes retry/caching)")
    print("")
    print("PROBLEMS WITH THIS SCRIPT:")
    print("  • Loads entire corpus into memory (OOM risk)")
    print("  • Vanilla spaCy only (ignores heuristics data)")
    print("  • Synthetic confidence (0.8) vs proper tier-based scoring")
    print("  • Shallow entity records (missing source attribution)")
    print("=" * 80)
    print("")
    
    response = input("Do you still want to run this deprecated script? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Aborted. Please use run_simple_extraction.py or queue_extraction_prefect.py")
        return
    
    print("\nBPO GPU Extraction Pipeline (DEPRECATED)")
    print("========================================")
    print("Bypassing Prefect for direct GPU processing")
    print()
    
    # Configuration - CANONICAL PRODUCTION DATASET
    # Use preprocessed JSONL from scripts/preprocess.py output
    source_path = "data/processed/preprocessed.jsonl"
    batch_size = 100
    
    # Check if source file exists
    if not os.path.exists(source_path):
        print(f"ERROR: Source file not found: {source_path}")
        return
    
    # Create and run pipeline
    pipeline = GPUExtractionPipeline(source_path, batch_size)
    
    try:
        summary = await pipeline.process_documents()
        
        # Save summary
        with open("extraction_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nSummary saved to: extraction_summary.json")
        
    except Exception as e:
        print(f"ERROR: Extraction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
