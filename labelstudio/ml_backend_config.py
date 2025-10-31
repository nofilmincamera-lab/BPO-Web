#!/usr/bin/env python3
"""
Label Studio ML Backend for BPO Entity Extraction

This provides a simple ML backend that can be attached to Label Studio
for pre-annotations and active learning.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import sys
# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from src.extraction.spacy_pipeline import get_extraction_nlp

logger = logging.getLogger(__name__)


class BPOMLBackend:
    """Simple ML backend for BPO entity extraction."""
    
    def __init__(self):
        self.nlp = None
        self._load_model()
    
    def _load_model(self):
        """Load the spaCy model."""
        try:
            self.nlp = get_extraction_nlp()
            logger.info("Loaded spaCy model successfully")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            raise
    
    def predict(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate predictions for tasks."""
        results = []
        
        for task in tasks:
            try:
                # Extract text from task
                text = task.get('data', {}).get('text', '')
                if not text:
                    results.append({'predictions': []})
                    continue
                
                # Run extraction
                doc = self.nlp(text)
                predictions = []
                
                for ent in doc.ents:
                    predictions.append({
                        'value': {
                            'start': ent.start_char,
                            'end': ent.end_char,
                            'text': ent.text,
                            'labels': [ent.label_]
                        },
                        'from_name': 'label',
                        'to_name': 'text',
                        'type': 'labels'
                    })
                
                results.append({
                    'predictions': [{
                        'result': predictions,
                        'score': 0.8,
                        'model_version': 'spacy-bpo-extraction'
                    }]
                })
                
            except Exception as e:
                logger.error(f"Error processing task: {e}")
                results.append({'predictions': []})
        
        return results
    
    def fit(self, annotations: List[Dict[str, Any]], **kwargs):
        """Train/update the model with new annotations."""
        # For now, this is a no-op since we're using a rule-based model
        # In a real ML backend, you would retrain the model here
        logger.info(f"Received {len(annotations)} annotations for training")
        pass


def main():
    """Simple CLI for testing the ML backend."""
    import argparse
    
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='Input tasks JSON file')
    ap.add_argument('--output', help='Output predictions JSON file')
    args = ap.parse_args()
    
    # Load tasks
    with open(args.input, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    # Initialize backend
    backend = BPOMLBackend()
    
    # Generate predictions
    predictions = backend.predict(tasks)
    
    # Save results
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(predictions, f, ensure_ascii=False, indent=2)
        print(f"Saved predictions to {args.output}")
    else:
        print(json.dumps(predictions, indent=2))


if __name__ == '__main__':
    main()

