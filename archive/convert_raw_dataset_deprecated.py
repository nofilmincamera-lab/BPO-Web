#!/usr/bin/env python3
"""Convert raw dataset to extraction format"""
import json
import uuid
from datetime import datetime

def convert_dataset():
    print("=" * 60)
    print("DEPRECATED: This script is deprecated!")
    print("=" * 60)
    print("")
    print("Use scripts/preprocess.py instead for proper preprocessing:")
    print("  python scripts/preprocess.py \\")
    print("    --input 'data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310 (1).json' \\")
    print("    --output 'data/processed/preprocessed.jsonl'")
    print("")
    print("The scripts/preprocess.py includes:")
    print("  - Streaming JSON parser (handles large files)")
    print("  - Deduplication via Bloom filters")
    print("  - URL canonicalization")
    print("  - Proper text extraction")
    print("=" * 60)
    return
    
    # OLD BROKEN CODE BELOW - DO NOT USE
    print("Loading raw dataset...")
    with open('data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310 (1).json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    print(f"Converting {len(raw_data):,} documents...")
    
    converted_docs = []
    for i, doc in enumerate(raw_data):
        if i % 1000 == 0:
            print(f"Processed {i:,} documents...")
        
        # Extract title from URL or metadata
        title = doc.get('metadata', {}).get('title', '')
        if not title:
            # Extract from URL
            url = doc['url']
            title = url.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
        
        # Create converted document
        converted_doc = {
            "id": str(uuid.uuid4()),
            "url": doc['url'],
            "title": title,
            "text": doc['text'],
            "metadata": {
                "crawl": doc.get('crawl', {}),
                "screenshotUrl": doc.get('screenshotUrl', ''),
                "markdown": doc.get('markdown', ''),
                "extracted_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        converted_docs.append(converted_doc)
    
    # Save as JSONL
    output_file = 'data/processed/preprocessed.jsonl'
    print(f"Saving to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for doc in converted_docs:
            f.write(json.dumps(doc, ensure_ascii=False) + '\n')
    
    print(f"Conversion complete! {len(converted_docs):,} documents saved to {output_file}")
    
    # Show sample
    print(f"\nSample converted document:")
    sample = converted_docs[0]
    print(f"ID: {sample['id']}")
    print(f"URL: {sample['url']}")
    print(f"Title: {sample['title']}")
    print(f"Text length: {len(sample['text']):,}")

if __name__ == "__main__":
    convert_dataset()




