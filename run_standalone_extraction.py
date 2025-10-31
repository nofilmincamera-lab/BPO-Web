#!/usr/bin/env python3
"""
Standalone extraction without any Prefect dependencies
"""
import asyncio
import time
import sys
import os
import json
import asyncpg
from datetime import datetime
from uuid import uuid5, NAMESPACE_DNS
import hashlib

# Add the src directory to the path
sys.path.append("/app")

# Import the core extraction functions without Prefect decorators
from src.heuristics.loader import get_heuristics_loader
from src.heuristics.extractor import extract_entities_heuristics
from src.spacy_extractor import extract_entities_spacy
from src.regex_extractor import extract_entities_regex
from src.flows.extraction_flow import _score_structure_signals, classify_content_type

async def _resolve_document_uuid(doc):
    """Resolve document UUID from various sources"""
    if "id" in doc:
        doc_id = doc["id"]
        try:
            # Try to parse as UUID
            from uuid import UUID
            return str(UUID(doc_id))
        except (ValueError, TypeError):
            # Generate deterministic UUID from string
            return str(uuid5(NAMESPACE_DNS, doc_id))
    
    # Fallback to URL-based UUID
    url = doc.get("url", "unknown")
    return str(uuid5(NAMESPACE_DNS, url))

async def insert_documents_standalone(batch):
    """Insert documents directly without Prefect"""
    conn = await asyncpg.connect(
        host="bpo-postgres",
        port=5432,
        user="postgres",
        password=os.getenv("DB_PASSWORD"),
        database="bpo_intel"
    )
    
    try:
        normalized_batch = []
        
        for raw_doc in batch:
            # Resolve UUID
            doc_uuid = await _resolve_document_uuid(raw_doc)
            
            # Extract fields
            url = raw_doc.get("url", "")
            title = raw_doc.get("title", "")
            text = raw_doc.get("text", "")
            
            # Compute text hash
            text_sha256 = hashlib.sha256(text.encode()).hexdigest()
            
            # Set status
            status = "processed"
            
            # Parse fetched_at
            fetched_at_str = raw_doc.get("fetched_at") or raw_doc.get("metadata", {}).get("extracted_at")
            fetched_at = None
            if fetched_at_str:
                try:
                    fetched_at = datetime.fromisoformat(fetched_at_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    fetched_at = datetime.utcnow()
            
            # Prepare metadata
            metadata = raw_doc.get("metadata", {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    metadata = {}
            
            # Add extracted_at if not present
            if fetched_at and "extracted_at" not in metadata:
                metadata["extracted_at"] = fetched_at.isoformat() + "Z"
            
            # Content type classification
            content_type_value = "Unknown"
            if text:
                try:
                    classification = classify_content_type(url, title, text)
                    content_type_value = classification.get("content_type", "Unknown")
                except Exception:
                    pass
            
            # Language detection (simple)
            lang = "en"  # Default to English
            
            # Insert document
            await conn.execute(
                """
                INSERT INTO documents (id, url, text_sha256, status, content_type, title, fetched_at, lang, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO UPDATE
                SET url = EXCLUDED.url,
                    text_sha256 = EXCLUDED.text_sha256,
                    status = EXCLUDED.status,
                    content_type = EXCLUDED.content_type,
                    title = EXCLUDED.title,
                    fetched_at = EXCLUDED.fetched_at,
                    lang = EXCLUDED.lang,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
                """,
                doc_uuid,
                url,
                text_sha256,
                status,
                content_type_value,
                title,
                fetched_at,
                lang,
                json.dumps(metadata),
            )
            
            # Add to normalized batch
            normalized_doc = {
                "id": doc_uuid,
                "url": url,
                "title": title,
                "text": text,
                "metadata": metadata
            }
            normalized_batch.append(normalized_doc)
        
        return normalized_batch
        
    finally:
        await conn.close()

async def extract_entities_standalone(batch, heuristics_version):
    """Extract entities without Prefect"""
    # Load heuristics
    heuristics_loader = get_heuristics_loader()
    heuristics = heuristics_loader.data
    
    all_entities = []
    all_relationships = []
    
    for doc in batch:
        doc_id = doc["id"]
        text = doc["text"]
        
        # Extract entities from all sources
        entities = []
        
        # Heuristics
        try:
            heur_entities = extract_entities_heuristics(text, heuristics)
            for entity in heur_entities:
                entity["doc_id"] = doc_id
                entity["source"] = "heuristics"
                entity["source_version"] = heuristics_version
                entity["confidence_method"] = "entity_ruler"
                entities.append(entity)
        except Exception as e:
            print(f"  Warning: Heuristics extraction failed: {e}")
        
        # spaCy
        try:
            spacy_entities = extract_entities_spacy(text)
            for entity in spacy_entities:
                entity["doc_id"] = doc_id
                entity["source"] = "spacy"
                entity["source_version"] = "en_core_web_sm_3.8.0"
                entity["confidence_method"] = "spacy_ner"
                entities.append(entity)
        except Exception as e:
            print(f"  Warning: spaCy extraction failed: {e}")
        
        # Regex
        try:
            regex_entities = extract_entities_regex(text)
            for entity in regex_entities:
                entity["doc_id"] = doc_id
                entity["source"] = "regex"
                entity["source_version"] = "1.0.0"
                entity["confidence_method"] = "regex_pattern"
                entities.append(entity)
        except Exception as e:
            print(f"  Warning: Regex extraction failed: {e}")
        
        all_entities.extend(entities)
        
        # Generate relationships (proximity-based)
        relationships = []
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities[i+1:], i+1):
                # Calculate distance
                span1 = entity1.get("span", {})
                span2 = entity2.get("span", {})
                
                if "start" in span1 and "start" in span2:
                    distance = abs(span1["start"] - span2["start"])
                    if distance <= 50:  # Within 50 characters
                        relationship = {
                            "doc_id": doc_id,
                            "head_entity": entity1.get("id", ""),
                            "tail_entity": entity2.get("id", ""),
                            "type": "ORL",
                            "conf": 0.6,
                            "evidence": {
                                "distance": distance,
                                "pattern": "proximity"
                            }
                        }
                        relationships.append(relationship)
        
        all_relationships.extend(relationships)
    
    return {
        "entities": all_entities,
        "relationships": all_relationships
    }

async def store_entities_standalone(result):
    """Store entities and relationships directly"""
    conn = await asyncpg.connect(
        host="bpo-postgres",
        port=5432,
        user="postgres",
        password=os.getenv("DB_PASSWORD"),
        database="bpo_intel"
    )
    
    try:
        entities_stored = 0
        relationships_stored = 0
        
        # Store entities
        for entity in result["entities"]:
            try:
                # Generate span hash
                span = entity.get("span", {})
                span_text = span.get("text", "")
                span_hash = hashlib.sha256(span_text.encode()).hexdigest()[:16]
                
                await conn.execute(
                    """
                    INSERT INTO entities (id, doc_id, type, surface, norm_value, conf, source, source_version, confidence_method, span, span_hash)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (doc_id, type, span_hash) DO NOTHING
                    """,
                    entity.get("id", ""),
                    entity["doc_id"],
                    entity["type"],
                    entity["surface"],
                    json.dumps(entity.get("norm_value", {})),
                    entity["conf"],
                    entity["source"],
                    entity["source_version"],
                    entity["confidence_method"],
                    json.dumps(span),
                    span_hash
                )
                entities_stored += 1
            except Exception as e:
                print(f"  Warning: Failed to store entity: {e}")
        
        # Store relationships
        for rel in result["relationships"]:
            try:
                await conn.execute(
                    """
                    INSERT INTO relationships (id, doc_id, head_entity, tail_entity, type, conf, evidence)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (doc_id, head_entity, tail_entity) DO NOTHING
                    """,
                    rel.get("id", ""),
                    rel["doc_id"],
                    rel["head_entity"],
                    rel["tail_entity"],
                    rel["type"],
                    rel["conf"],
                    json.dumps(rel["evidence"])
                )
                relationships_stored += 1
            except Exception as e:
                print(f"  Warning: Failed to store relationship: {e}")
        
        return {
            "entities": entities_stored,
            "relationships": relationships_stored
        }
        
    finally:
        await conn.close()

def _batched_documents_standalone(source_path, start_offset=0, batch_size=100):
    """Load documents in batches without Prefect"""
    with open(source_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total_lines = len(lines)
    current_offset = start_offset
    
    while current_offset < total_lines:
        batch_end = min(current_offset + batch_size, total_lines)
        batch = []
        
        for i in range(current_offset, batch_end):
            try:
                doc = json.loads(lines[i].strip())
                batch.append(doc)
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line {i}: {e}")
                continue
        
        if batch:
            yield current_offset, batch_end, batch
        
        current_offset = batch_end

async def main():
    print("=" * 60)
    print("STARTING STANDALONE 5000-DOCUMENT EXTRACTION")
    print("=" * 60)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    start_time = time.time()
    total_documents = 0
    total_entities = 0
    total_relationships = 0
    failed_documents = []
    
    try:
        # CANONICAL PRODUCTION DATASET - preprocessed from scripts/preprocess.py
        # Change to test_5000_rich.jsonl for testing only
        source_path = "/data/processed/preprocessed.jsonl"
        heuristics_version = "2.0.0"
        batch_size = 100
        start_offset = 0
        
        print(f"Processing {source_path} with batch size {batch_size}")
        print(f"Starting from offset {start_offset}")
        print()
        
        batch_count = 0
        for batch_start, batch_end, batch in _batched_documents_standalone(source_path, start_offset, batch_size):
            batch_count += 1
            print(f"Processing batch {batch_count}: documents {batch_start}-{batch_end} ({len(batch)} docs)")
            
            try:
                # Insert documents
                normalized_batch = await insert_documents_standalone(batch)
                print(f"  ✓ Documents inserted: {len(normalized_batch)}")
                
                # Extract entities
                result = await extract_entities_standalone(normalized_batch, heuristics_version)
                entities_count = len(result["entities"])
                relationships_count = len(result["relationships"])
                print(f"  ✓ Entities extracted: {entities_count}")
                print(f"  ✓ Relationships extracted: {relationships_count}")
                
                # Store entities and relationships
                stored_counts = await store_entities_standalone(result)
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
