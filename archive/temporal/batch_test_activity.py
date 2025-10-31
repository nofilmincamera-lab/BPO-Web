"""
BPO Intelligence Pipeline - Batch Test Activity

Run NER extraction on test batch and track metrics.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict

from temporalio import activity


@activity.defn
async def run_batch_extraction_activity(
    input_file: str,
    heuristics_dir: str = "/heuristics"
) -> Dict[str, Any]:
    """
    Run NER extraction on preprocessed batch.
    
    This is a simplified version that tracks extraction metrics
    without full heuristics/spaCy implementation.
    
    Args:
        input_file: Path to preprocessed JSONL file
        heuristics_dir: Directory containing heuristics files
    
    Returns:
        Extraction metrics and statistics
    """
    
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Load heuristics (simplified)
    heuristics_path = Path(heuristics_dir)
    
    # Track metrics
    metrics = {
        "total_documents": 0,
        "extraction_tiers": defaultdict(int),
        "entity_types": defaultdict(int),
        "confidence_ranges": {
            "high": 0,  # > 0.8
            "medium": 0,  # 0.5-0.8
            "low": 0,  # < 0.5
        },
        "companies_found": [],
        "locations_found": [],
        "tech_terms_found": [],
    }
    
    activity.logger.info(f"Running batch extraction on {input_file}")
    
    # Process documents
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                doc = json.loads(line)
                metrics["total_documents"] += 1
                
                # Simulate extraction (in production, this would use actual heuristics)
                text = doc.get('text', '').lower()
                
                # Simulate company extraction
                if 'infosys' in text or 'accenture' in text or 'tcs' in text:
                    metrics["extraction_tiers"]["heuristics"] += 1
                    metrics["entity_types"]["COMPANY"] += 1
                    metrics["confidence_ranges"]["high"] += 1
                    metrics["companies_found"].append("infosys")
                
                # Simulate location extraction
                if 'india' in text or 'usa' in text or 'philippines' in text:
                    metrics["extraction_tiers"]["heuristics"] += 1
                    metrics["entity_types"]["LOCATION"] += 1
                    metrics["confidence_ranges"]["high"] += 1
                    metrics["locations_found"].append("india")
                
                # Simulate tech term extraction
                if 'ai' in text or 'machine learning' in text or 'nlp' in text:
                    metrics["extraction_tiers"]["heuristics"] += 1
                    metrics["entity_types"]["TECHNOLOGY"] += 1
                    metrics["confidence_ranges"]["high"] += 1
                    metrics["tech_terms_found"].append("ai")
                
                # Heartbeat every 100 documents
                if line_num % 100 == 0:
                    activity.heartbeat(f"Processed {line_num} documents")
            
            except json.JSONDecodeError as e:
                activity.logger.warning(f"Invalid JSON on line {line_num}: {e}")
                continue
    
    # Calculate aggregate statistics
    total_entities = sum(metrics["entity_types"].values())
    
    metrics["summary"] = {
        "total_documents": metrics["total_documents"],
        "total_entities_extracted": total_entities,
        "avg_entities_per_doc": total_entities / metrics["total_documents"] if metrics["total_documents"] > 0 else 0,
        "heuristics_hit_rate": metrics["extraction_tiers"]["heuristics"] / total_entities if total_entities > 0 else 0,
        "unique_companies": len(set(metrics["companies_found"])),
        "unique_locations": len(set(metrics["locations_found"])),
        "unique_tech_terms": len(set(metrics["tech_terms_found"])),
    }
    
    activity.logger.info(
        f"Batch extraction complete: {metrics['total_documents']} docs, "
        f"{total_entities} entities extracted"
    )
    
    return metrics

