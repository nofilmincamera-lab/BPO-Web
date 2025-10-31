#!/usr/bin/env python3
"""
Convert JSONL dataset to Label Studio task format with optional predictions.

Input JSONL lines should contain a `text` field (or metadata.text) and optional
extraction predictions saved from GPU run in `extraction_summary.json` is NOT used;
instead, you can pass a predictions file mapping doc_id -> spans if available.
"""
import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any, List


def load_predictions(pred_path: str | None) -> Dict[str, List[Dict[str, Any]]]:
    if not pred_path:
        return {}
    with open(pred_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def to_ls_result(spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for s in spans:
        # expected: {start, end, label}
        start = s.get('start')
        end = s.get('end')
        label = s.get('label')
        if start is None or end is None or not label:
            continue
        results.append({
            "from_name": "label",
            "to_name": "text",
            "type": "labels",
            "value": {
                "start": start,
                "end": end,
                "text": s.get('text', ''),
                "labels": [label]
            }
        })
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='Path to input JSONL file')
    ap.add_argument('--output', required=True, help='Output tasks JSON file')
    ap.add_argument('--limit', type=int, default=1000, help='Max tasks to export')
    ap.add_argument('--predictions', default=None, help='Optional predictions JSON (doc_id->spans)')
    args = ap.parse_args()

    preds = load_predictions(args.predictions)
    tasks: List[Dict[str, Any]] = []
    n = 0

    with open(args.input, 'r', encoding='utf-8') as f:
        for line in f:
            if args.limit and n >= args.limit:
                break
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            text = obj.get('text') or obj.get('metadata', {}).get('text')
            if not text:
                continue

            doc_id = obj.get('id') or obj.get('doc_id') or obj.get('metadata', {}).get('id')
            task: Dict[str, Any] = {
                "data": {
                    "text": text,
                    "source_url": obj.get('url') or obj.get('metadata', {}).get('url')
                }
            }

            # add predictions if available
            if doc_id and doc_id in preds:
                task["predictions"] = [{
                    "result": to_ls_result(preds[doc_id])
                }]

            tasks.append(task)
            n += 1

    Path(os.path.dirname(args.output) or '.').mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as out:
        json.dump(tasks, out, ensure_ascii=False)

    print(f"Wrote {len(tasks)} tasks to {args.output}")


if __name__ == '__main__':
    main()



