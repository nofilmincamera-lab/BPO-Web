#!/usr/bin/env python3
"""
Import preprocessed documents and predictions to Label Studio via MCP.
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

def load_predictions(predictions_file: str) -> Dict[str, Dict[str, Any]]:
    """Load predictions JSON file (new format with entities, relationships, document_predictions)."""
    with open(predictions_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_task_for_label_studio(doc: Dict[str, Any], extraction_result: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Format a document as a Label Studio task matching project config.
    
    extraction_result format:
    {
        'entities': [...],
        'relationships': [...],
        'document_predictions': {...},
        'stats': {...}
    }
    """
    text = doc.get('text') or doc.get('metadata', {}).get('text', '')
    doc_id = doc.get('id') or doc.get('doc_id') or doc.get('metadata', {}).get('id', '')
    url = doc.get('url') or doc.get('metadata', {}).get('url', '')
    
    # Format predictions for Label Studio
    result = []
    
    if extraction_result:
        # Handle old format (list of entities) for backward compatibility
        if isinstance(extraction_result, list):
            entities = extraction_result
            relationships = []
            doc_predictions = {}
        else:
            entities = extraction_result.get('entities', [])
            relationships = extraction_result.get('relationships', [])
            doc_predictions = extraction_result.get('document_predictions', {})
        
        # Format entity predictions
        for ent in entities:
            label = ent.get('label', '')
            if label in ['ORG', 'PERSON', 'LOC', 'PRODUCT', 'TECHNOLOGY', 'INDUSTRY', 
                        'CATEGORY', 'DATE', 'MONEY', 'PERCENT']:
                result.append({
                    "from_name": "ner_labels",
                    "to_name": "text",
                    "type": "labels",
                    "value": {
                        "start": ent["start"],
                        "end": ent["end"],
                        "text": ent["text"],
                        "labels": [label]
                    }
                })
        
        # Add relationships (if Label Studio config supports it)
        result.extend(relationships)
        
        # Add document-level predictions
        result.extend(list(doc_predictions.values()))
    
    task = {
        "data": {
            "text": text,
            "source_url": url or f"doc_{doc_id}"
        }
    }
    
    if result:
        task["predictions"] = [{
            "result": result,
            "score": 0.85
        }]
    
    return task

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Import documents to Label Studio')
    parser.add_argument('--input', required=True, help='Input JSONL file')
    parser.add_argument('--predictions', help='Predictions JSON file (optional)')
    parser.add_argument('--output', required=True, help='Output JSON file for Label Studio import')
    parser.add_argument('--limit', type=int, default=100, help='Max documents to import (default: 100)')
    parser.add_argument('--project-id', type=int, default=2, help='Label Studio project ID')
    
    args = parser.parse_args()
    
    # Load predictions if provided
    predictions_dict = {}
    if args.predictions:
        predictions_dict = load_predictions(args.predictions)
        print(f"Loaded predictions for {len(predictions_dict)} documents")
    
    # Process documents
    tasks = []
    count = 0
    
    with open(args.input, 'r', encoding='utf-8') as f:
        for line in f:
            if count >= args.limit:
                break
            
            try:
                doc = json.loads(line)
                doc_id = str(doc.get('id') or doc.get('doc_id') or doc.get('metadata', {}).get('id', count))
                extraction_result = predictions_dict.get(doc_id, {})
                
                # Handle old format (list of entities) for backward compatibility
                if isinstance(extraction_result, list):
                    extraction_result = {'entities': extraction_result, 'relationships': [], 'document_predictions': {}}
                
                task = format_task_for_label_studio(doc, extraction_result)
                tasks.append(task)
                count += 1
                
                if count % 100 == 0:
                    print(f"Processed {count} documents...")
                    
            except json.JSONDecodeError as e:
                print(f"Error parsing line: {e}")
                continue
    
    # Save tasks
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    
    print(f"\nCreated {len(tasks)} Label Studio tasks")
    print(f"   Output file: {args.output}")
    print(f"   Project ID: {args.project_id}")
    print(f"\nTo import via MCP:")
    print(f"   Use mcp_label-studio_import_label_studio_project_tasks_tool")
    print(f"   Project ID: {args.project_id}")
    print(f"   Tasks file: {args.output}")

if __name__ == "__main__":
    main()
