#!/usr/bin/env python3
"""Validate Label Studio tasks with predictions."""
import argparse
import json
from pathlib import Path


def validate_tasks(file_path: str) -> bool:
    """Validate Label Studio tasks file structure."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load file: {e}")
        return False
    
    if not isinstance(tasks, list):
        print(f"❌ Expected JSON array, got {type(tasks)}")
        return False
    
    print(f"Loaded {len(tasks)} tasks")
    
    # Expected labels from config
    expected_labels = {
        "COMPANY", "PERSON", "DATE", "TECHNOLOGY", "MONEY", "PERCENT",
        "PRODUCT", "COMPUTING_PRODUCT", "BUSINESS_TITLE", "LOCATION",
        "TIME_RANGE", "ORL", "TEMPORAL", "SKILL"
    }
    
    tasks_with_predictions = 0
    total_predictions = 0
    label_counts = {}
    
    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            print(f"❌ Task {i} is not a dict")
            return False
        
        # Check required fields
        if 'data' not in task:
            print(f"❌ Task {i} missing 'data' field")
            return False
        
        if 'text' not in task['data']:
            print(f"❌ Task {i} missing 'data.text' field")
            return False
        
        # Check predictions
        if 'predictions' in task:
            tasks_with_predictions += 1
            for pred in task['predictions']:
                if 'result' in pred:
                    total_predictions += len(pred['result'])
                    
                    # Validate prediction structure
                    for result in pred['result']:
                        if result.get('from_name') != 'label':
                            print(f"❌ Task {i}: from_name should be 'label', got '{result.get('from_name')}'")
                            return False
                        
                        if result.get('to_name') != 'text':
                            print(f"❌ Task {i}: to_name should be 'text', got '{result.get('to_name')}'")
                            return False
                        
                        if result.get('type') != 'labels':
                            print(f"❌ Task {i}: type should be 'labels', got '{result.get('type')}'")
                            return False
                        
                        # Check label values
                        value = result.get('value', {})
                        labels = value.get('labels', [])
                        for label in labels:
                            if label not in expected_labels:
                                print(f"❌ Task {i}: unexpected label '{label}'")
                                return False
                            label_counts[label] = label_counts.get(label, 0) + 1
    
    print(f"{tasks_with_predictions}/{len(tasks)} tasks have predictions")
    print(f"Total predictions: {total_predictions}")
    print(f"Average predictions per task: {total_predictions/len(tasks):.1f}")
    
    print("\nLabel distribution:")
    for label, count in sorted(label_counts.items()):
        print(f"  {label}: {count}")
    
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', required=True, help='Label Studio tasks file to validate')
    args = ap.parse_args()
    
    if not Path(args.file).exists():
        print(f"❌ File not found: {args.file}")
        return 1
    
    print(f"Validating {args.file}...")
    
    if validate_tasks(args.file):
        print("\nValidation passed! File is ready for Label Studio import.")
        return 0
    else:
        print("\nValidation failed! Fix issues before importing.")
        return 1


if __name__ == '__main__':
    exit(main())
