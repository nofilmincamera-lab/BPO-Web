#!/usr/bin/env python3
"""
Test GPU extraction on a small sample
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.extraction.spacy_pipeline import get_extraction_nlp

def test_gpu_extraction():
    """Test GPU extraction capabilities"""
    print("Testing GPU Extraction")
    print("=" * 30)
    
    # Test spaCy GPU
    print("Loading spaCy model...")
    nlp = get_extraction_nlp()
    
    print(f"SUCCESS: Model loaded")
    print(f"   GPU enabled: {nlp.meta.get('gpu', False)}")
    print(f"   GPU device: {nlp.meta.get('gpu_device', 'N/A')}")
    
    # Test processing
    test_text = "Microsoft Corporation is a technology company based in Redmond, Washington. They develop software products like Windows and Office."
    
    print(f"\nProcessing test text...")
    print(f"Text: {test_text}")
    
    doc = nlp(test_text)
    
    print(f"\nExtracted entities:")
    for ent in doc.ents:
        print(f"  - {ent.text} ({ent.label_})")
    
    print(f"\nSUCCESS: GPU extraction test complete!")
    return nlp.meta.get('gpu', False)

if __name__ == "__main__":
    gpu_enabled = test_gpu_extraction()
    
    if gpu_enabled:
        print("\nGPU is working! Ready for full extraction.")
    else:
        print("\nWARNING: GPU not detected. Will use CPU.")
