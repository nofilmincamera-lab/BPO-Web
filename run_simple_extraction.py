#!/usr/bin/env python3
"""
Simple extraction without Prefect dependencies

⚠️ NOTE: This is a SIMPLIFIED extraction pipeline using basic regex patterns.
For PRODUCTION extraction with full heuristics-first multi-tier pipeline:
  - Use: python queue_extraction_prefect.py (orchestrated)
  - Or: run_direct_extraction.py (direct, uses proper extraction_flow)

This script:
  ✓ Uses canonical dataset (data/processed/preprocessed.jsonl)
  ✓ Direct database insertion (no Prefect overhead)
  ⚠️ Basic regex extraction (NOT full heuristics pipeline)
  ⚠️ Simplified confidence scoring

Good for: Testing, development, minimal dependency environments
Not for: Production extraction requiring full heuristics accuracy
"""
import asyncio
import time
import sys
import os
import json
import asyncpg
import re
import argparse
from datetime import datetime
from uuid import uuid5, NAMESPACE_DNS
import hashlib

# Add the src directory to the path
sys.path.append("/app")

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

def _span_overlaps(start, end, existing_spans):
    """Check if a span overlaps with existing spans"""
    for existing_start, existing_end in existing_spans:
        if not (end <= existing_start or start >= existing_end):
            return True
    return False

async def insert_documents_simple(batch):
    """Insert documents directly"""
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
            text_sha256 = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
            
            # Set status (1 = processed)
            status = 1
            
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
            
            # Simple content type
            content_type_value = "Unknown"
            if "case study" in text.lower() or "case study" in title.lower():
                content_type_value = "Case Study"
            elif "press release" in text.lower() or "announces" in title.lower():
                content_type_value = "News / Press Release"
            elif "blog" in text.lower() or "article" in text.lower():
                content_type_value = "Blog / Article"
            
            # Language detection (simple)
            lang = "en"  # Default to English
            
            # Insert/Update document metadata
            await conn.execute(
                """
                INSERT INTO documents (id, url, text_sha256, status, content_type, title, fetched_at, lang, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (text_sha256) DO UPDATE
                SET url = EXCLUDED.url,
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
            
            # Create document chunk with the full text
            chunk_id = str(uuid5(NAMESPACE_DNS, f"{doc_uuid}_chunk_0"))
            await conn.execute(
                """
                INSERT INTO document_chunks (id, doc_id, seq, text, text_sha256, meta)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (doc_id, seq) DO UPDATE
                SET text = EXCLUDED.text,
                    text_sha256 = EXCLUDED.text_sha256,
                    meta = EXCLUDED.meta
                """,
                chunk_id,
                doc_uuid,
                0,  # First chunk
                text,
                text_sha256,
                json.dumps({"chunk_type": "full_document"})
            )
            
            sanitized_metadata = metadata if isinstance(metadata, dict) else {}
            
            normalized_batch.append({
                "id": doc_uuid,
                "url": url,
                "title": title,
                "text": text,
                "metadata": sanitized_metadata
            })
        
        return normalized_batch
        
    finally:
        await conn.close()

async def extract_entities_simple(batch, heuristics_version):
    """Extract entities using simple patterns"""
    all_entities = []
    all_relationships = []

    # Connect to database to get document text
    conn = await asyncpg.connect(
        host="bpo-postgres",
        port=5432,
        user="postgres",
        password=os.getenv("DB_PASSWORD"),
        database="bpo_intel"
    )

    try:
        for doc in batch:
            doc_id = doc["id"]

            # Get text from document chunks
            chunk_rows = await conn.fetch(
                "SELECT id, text FROM document_chunks WHERE doc_id = $1 ORDER BY seq",
                doc_id
            )

            if not chunk_rows:
                print(f"  ??  No text found for document {doc_id}")
                text = doc.get("text", "") or ""
                chunk_id = None
            else:
                chunk_id = str(chunk_rows[0]["id"])
                text = " ".join(row["text"] for row in chunk_rows)

            if not text.strip():
                print(f"  ??  Skipping document {doc_id} - empty text")
                continue

            entities = []
            existing_spans = []

            # Simple entity extraction using regex patterns
            # Companies (capitalized words that might be company names)
            company_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
            for match in re.finditer(company_pattern, text):
                if not _span_overlaps(match.start(), match.end(), existing_spans):
                    entity_text = match.group(0)
                    if len(entity_text) > 3 and entity_text.lower() not in {'the', 'this', 'that', 'there', 'then', 'they'}:
                        entity_id = str(uuid5(NAMESPACE_DNS, f"{doc_id}_{entity_text}_{match.start()}"))
                        entities.append({
                            "id": entity_id,
                            "doc_id": doc_id,
                            "chunk_id": chunk_id,
                            "type": "COMPANY",
                            "surface": entity_text,
                            "norm_value": json.dumps({"canonical": entity_text}),
                            "span": json.dumps({
                                "start": match.start(),
                                "end": match.end(),
                                "text": entity_text
                            }),
                            "conf": 0.85,
                            "source": "regex",
                            "source_version": "company_pattern_v1",
                            "heuristics_version": heuristics_version,
                            "confidence_method": "regex_pattern"
                        })
                        existing_spans.append((match.start(), match.end()))

            # Money amounts
            money_pattern = r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
            for match in re.finditer(money_pattern, text):
                if not _span_overlaps(match.start(), match.end(), existing_spans):
                    entity_id = str(uuid5(NAMESPACE_DNS, f"{doc_id}_money_{match.start()}"))
                    entities.append({
                        "id": entity_id,
                        "doc_id": doc_id,
                        "chunk_id": chunk_id,
                        "type": "MONEY",
                        "surface": match.group(0),
                        "norm_value": json.dumps({"currency": "USD", "surface": match.group(0)}),
                        "span": json.dumps({"start": match.start(), "end": match.end(), "text": match.group(0)}),
                        "conf": 0.92,
                        "source": "regex",
                        "source_version": "money_pattern_v1",
                        "heuristics_version": heuristics_version,
                        "confidence_method": "regex_pattern"
                    })
                    existing_spans.append((match.start(), match.end()))

            # Percentages
            percent_pattern = r'\d{1,3}(?:\.\d{1,2})?\s*%'
            for match in re.finditer(percent_pattern, text):
                if not _span_overlaps(match.start(), match.end(), existing_spans):
                    entity_id = str(uuid5(NAMESPACE_DNS, f"{doc_id}_percent_{match.start()}"))
                    entities.append({
                        "id": entity_id,
                        "doc_id": doc_id,
                        "chunk_id": chunk_id,
                        "type": "PERCENT",
                        "surface": match.group(0),
                        "norm_value": json.dumps({"surface": match.group(0)}),
                        "span": json.dumps({"start": match.start(), "end": match.end(), "text": match.group(0)}),
                        "conf": 0.90,
                        "source": "regex",
                        "source_version": "percent_pattern_v1",
                        "heuristics_version": heuristics_version,
                        "confidence_method": "regex_pattern"
                    })
                    existing_spans.append((match.start(), match.end()))

            # Technologies (common tech terms)
            tech_terms = ['AI', 'Machine Learning', 'Cloud', 'Data Analytics', 'Blockchain', 'IoT', 'API', 'SaaS', 'PaaS', 'IaaS']
            for term in tech_terms:
                pattern = re.escape(term)
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    if not _span_overlaps(match.start(), match.end(), existing_spans):
                        entity_id = str(uuid5(NAMESPACE_DNS, f"{doc_id}_tech_{term}_{match.start()}"))
                        entities.append({
                            "id": entity_id,
                            "doc_id": doc_id,
                            "chunk_id": chunk_id,
                            "type": "TECHNOLOGY",
                            "surface": match.group(0),
                            "norm_value": json.dumps({"canonical": term}),
                            "span": json.dumps({"start": match.start(), "end": match.end(), "text": match.group(0)}),
                            "conf": 0.88,
                            "source": "regex",
                            "source_version": "tech_pattern_v1",
                            "heuristics_version": heuristics_version,
                            "confidence_method": "regex_pattern"
                        })
                        existing_spans.append((match.start(), match.end()))

            all_entities.extend(entities)

            # Generate relationships (proximity-based)
            if entities:
                relationships = []
                for i, entity1 in enumerate(entities):
                    for entity2 in entities[i + 1:]:
                        span1 = json.loads(entity1["span"])
                        span2 = json.loads(entity2["span"])

                        distance = abs(span1["start"] - span2["start"])
                        if distance <= 100:  # Within 100 characters
                            relationship_id = str(uuid5(NAMESPACE_DNS, f"{doc_id}_rel_{entity1['id']}_{entity2['id']}"))
                            relationships.append({
                                "id": relationship_id,
                                "doc_id": doc_id,
                                "chunk_id": chunk_id,
                                "head_entity": entity1["id"],
                                "tail_entity": entity2["id"],
                                "type": "ORL",
                                "conf": 0.6,
                                "evidence": {
                                    "distance": distance,
                                    "pattern": "proximity"
                                },
                                "source": "regex",
                                "source_version": "proximity_v1",
                                "heuristics_version": heuristics_version,
                                "confidence_method": "regex_proximity"
                            })

                all_relationships.extend(relationships)

    finally:
        await conn.close()

    return {
        "entities": all_entities,
        "relationships": all_relationships
    }

async def store_entities_simple(result):
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
                await conn.execute(
                    """
                    INSERT INTO entities (id, doc_id, chunk_id, type, surface, norm_value, span, conf, source, source_version, heuristics_version, confidence_method)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (doc_id, type, span_hash) DO NOTHING
                    """,
                    entity.get("id", ""),
                    entity["doc_id"],
                    entity.get("chunk_id"),
                    entity["type"],
                    entity["surface"],
                    entity["norm_value"],
                    entity["span"],
                    entity["conf"],
                    entity.get("source"),
                    entity.get("source_version"),
                    entity.get("heuristics_version"),
                    entity.get("confidence_method")
                )
                entities_stored += 1
            except Exception as e:
                print(f"  Warning: Failed to store entity: {e}")
        
        # Store relationships
        for rel in result["relationships"]:
            try:
                await conn.execute(
                    """
                    INSERT INTO relationships (id, doc_id, chunk_id, head_entity, tail_entity, type, conf, evidence, source, source_version, heuristics_version, confidence_method)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    rel["id"],
                    rel["doc_id"],
                    rel.get("chunk_id"),
                    rel["head_entity"],
                    rel["tail_entity"],
                    rel["type"],
                    rel.get("conf"),
                    json.dumps(rel.get("evidence", {})),
                    rel.get("source"),
                    rel.get("source_version"),
                    rel.get("heuristics_version"),
                    rel.get("confidence_method")
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

def _batched_documents_simple(source_path, start_offset=0, batch_size=100):
    """Load documents in batches"""
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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Simple extraction without Prefect dependencies')
    # CANONICAL PRODUCTION DATASET - preprocessed from scripts/preprocess.py
    parser.add_argument('--source', default='/data/processed/preprocessed.jsonl',
                       help='Path to JSONL dataset file (default: /data/processed/preprocessed.jsonl - CANONICAL PRODUCTION DATASET)')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Batch size for processing (default: 100)')
    parser.add_argument('--start-offset', type=int, default=0,
                       help='Starting offset for processing (default: 0)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("STARTING SIMPLE EXTRACTION")
    print("=" * 60)
    print(f"Dataset: {args.source}")
    print(f"Batch size: {args.batch_size}")
    print(f"Start offset: {args.start_offset}")
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    start_time = time.time()
    total_documents = 0
    total_entities = 0
    total_relationships = 0
    failed_documents = []
    
    try:
        source_path = args.source
        heuristics_version = "2.0.0"
        batch_size = args.batch_size
        start_offset = args.start_offset
        
        print(f"Processing {source_path} with batch size {batch_size}")
        print(f"Starting from offset {start_offset}")
        print()
        
        batch_count = 0
        for batch_start, batch_end, batch in _batched_documents_simple(source_path, start_offset, batch_size):
            batch_count += 1
            print(f"Processing batch {batch_count}: documents {batch_start}-{batch_end} ({len(batch)} docs)")
            
            try:
                # Insert documents
                normalized_batch = await insert_documents_simple(batch)
                print(f"  ✓ Documents inserted: {len(normalized_batch)}")
                
                # Extract entities
                result = await extract_entities_simple(normalized_batch, heuristics_version)
                entities_count = len(result["entities"])
                relationships_count = len(result["relationships"])
                print(f"  ✓ Entities extracted: {entities_count}")
                print(f"  ✓ Relationships extracted: {relationships_count}")
                
                # Store entities and relationships
                stored_counts = await store_entities_simple(result)
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
        if duration > 0:
            print(f"  Throughput: {total_documents/duration:.2f} docs/sec")
        else:
            print(f"  Throughput: 0 docs/sec")
        if total_documents > 0:
            print(f"  Entities per doc: {total_entities/total_documents:.1f}")
            print(f"  Relationships per doc: {total_relationships/total_documents:.1f}")
        else:
            print(f"  Entities per doc: 0")
            print(f"  Relationships per doc: 0")
        
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
