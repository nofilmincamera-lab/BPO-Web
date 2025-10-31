"""
BPO Intelligence Pipeline - Preprocessing Activity

Streaming preprocessing for batch validation.
"""

import ijson
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List

from temporalio import activity


@activity.defn
async def preprocess_sample_activity(
    input_file: str,
    output_file: str,
    record_limit: int = 1000
) -> Dict[str, Any]:
    """
    Preprocess N records from raw JSON for testing.
    
    Args:
        input_file: Path to raw JSON file
        output_file: Path to output JSONL file
        record_limit: Maximum number of records to process
    
    Returns:
        Statistics about preprocessing
    """
    
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    processed_count = 0
    skipped_count = 0
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    activity.logger.info(f"Preprocessing {record_limit} records from {input_file}")
    
    with open(output_path, 'w', encoding='utf-8') as outfile:
        with open(input_path, 'rb') as infile:
            # Stream JSON items
            items = ijson.items(infile, 'item')
            
            for doc in items:
                if processed_count >= record_limit:
                    break
                
                # Extract basic fields
                url = doc.get('url', '')
                html_content = doc.get('raw', {}).get('html', '')
                
                if not url or not html_content:
                    skipped_count += 1
                    continue
                
                # Create minimal output document
                output_doc = {
                    "url": url,
                    "title": doc.get('title', ''),
                    "text": html_content[:1000],  # Truncate for testing
                    "fetched_at": doc.get('fetched_at', ''),
                    "status": doc.get('status', 200),
                }
                
                outfile.write(json.dumps(output_doc) + '\n')
                processed_count += 1
                
                # Heartbeat every 100 records
                if processed_count % 100 == 0:
                    activity.heartbeat(f"Processed {processed_count}/{record_limit} records")
    
    activity.logger.info(
        f"Preprocessing complete: {processed_count} processed, {skipped_count} skipped"
    )
    
    return {
        "processed": processed_count,
        "skipped": skipped_count,
        "output_file": str(output_path),
        "output_size_bytes": output_path.stat().st_size if output_path.exists() else 0
    }

