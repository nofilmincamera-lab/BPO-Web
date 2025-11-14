#!/usr/bin/env python3
"""
Merge Label Studio tasks with predictions to create tasks with pre-annotations.
"""
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def convert_spans_to_labelstudio(spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert our span format to Label Studio format."""
    result = []
    for span in spans:
        result.append({
            "value": {
                "start": span["start"],
                "end": span["end"],
                "text": span["text"],
                "labels": [span["label"]]
            },
            "from_name": "ner_labels",
            "to_name": "text",
            "type": "labels"
        })
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tasks', required=True, help='Label Studio tasks JSON file')
    ap.add_argument('--predictions', required=True, help='Predictions JSON file')
    ap.add_argument('--output', required=True, help='Output tasks with predictions JSON file')
    args = ap.parse_args()

    # Load tasks
    with open(args.tasks, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    # Load predictions
    with open(args.predictions, 'r', encoding='utf-8') as f:
        predictions = json.load(f)
    
    # Merge predictions into tasks
    prediction_keys = list(predictions.keys())
    for idx, task in enumerate(tasks):
        # Use prediction key by index since tasks don't have IDs
        if idx < len(prediction_keys):
            pred_key = prediction_keys[idx]
            if pred_key in predictions:
                # Convert our spans to Label Studio format
                labelstudio_spans = convert_spans_to_labelstudio(predictions[pred_key])
                
                # Add predictions to task
                task['predictions'] = [{
                    'result': labelstudio_spans,
                    'score': 0.8,  # Default confidence score
                    'model_version': 'spacy-extraction'
                }]
    
    # Save merged tasks
    Path(os.path.dirname(args.output) or '.').mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    
    print(f"Created {len(tasks)} tasks with predictions in {args.output}")


if __name__ == '__main__':
    import os
    main()
