#!/usr/bin/env python3
"""Analyze the raw dataset structure"""
import json

def analyze_dataset():
    with open('D:/BPO-Project/data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310 (1).json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Total documents: {len(data):,}")
    
    # Analyze first document
    doc = data[0]
    print(f"\nSample document structure:")
    print(f"URL: {doc['url']}")
    print(f"Text length: {len(doc['text']):,} characters")
    print(f"Has metadata: {'metadata' in doc}")
    print(f"Has crawl: {'crawl' in doc}")
    print(f"Has markdown: {'markdown' in doc}")
    
    # Check text content
    text_sample = doc['text'][:200]
    print(f"\nText sample: {text_sample}...")
    
    # Check if we need to convert format
    print(f"\nDocument keys: {list(doc.keys())}")
    
    # Check a few more documents for consistency
    print(f"\nChecking document consistency...")
    for i in range(min(5, len(data))):
        doc = data[i]
        print(f"Doc {i}: URL={doc['url'][:50]}..., Text length={len(doc['text']):,}")

if __name__ == "__main__":
    analyze_dataset()




