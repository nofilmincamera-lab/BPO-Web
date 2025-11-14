#!/usr/bin/env python3
"""Convert JSON array to JSONL format."""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='Input JSON file')
    ap.add_argument('--output', required=True, help='Output JSONL file')
    args = ap.parse_args()

    # Load JSON data
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Write as JSONL
    Path(os.path.dirname(args.output) or '.').mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"Converted {len(data)} items to {args.output}")


if __name__ == '__main__':
    import os
    main()

