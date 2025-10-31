#!/usr/bin/env python3
"""
BPO Intelligence Pipeline - Preprocessing Script

Processes large raw JSON files into clean, deduped JSON Lines format.
Handles 854MB+ files via streaming parser (no memory loading).

Input: data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310 (1).json
Output: data/processed/preprocessed.jsonl (one document per line)

Usage:
    python scripts/preprocess.py --input <raw_file> --output <preprocessed_file>
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, Set, Optional
from urllib.parse import urlparse, parse_qs, urlunparse

import ijson
from pybloom_live import BloomFilter
from tldextract import extract as tld_extract
from tqdm import tqdm

# Import extraction libraries (already in requirements.txt)
try:
    import trafilatura
except ImportError:
    trafilatura = None

try:
    from readability import Document
except ImportError:
    Document = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


def canonicalize_url(url: str, aggressive: bool = False) -> str:
    """
    Canonicalize URL by:
    1. Extracting domain (tldextract)
    2. Removing query parameters (except whitelist) - only if aggressive=True
    3. Normalizing scheme and path
    
    Args:
        url: URL to canonicalize
        aggressive: If False, preserves all query parameters and path details (default)
    """
    try:
        parsed = urlparse(url.lower().strip())
        
        # Extract domain components
        tld_info = tld_extract(url)
        domain = f"{tld_info.domain}.{tld_info.suffix}"
        
        if aggressive:
            # Aggressive mode: remove most query parameters (old behavior)
            ALLOWED_PARAMS = ['id', 'page', 'year']
            clean_query = None
            if parsed.query:
                params = parse_qs(parsed.query, keep_blank_values=False)
                allowed_params = {k: v for k, v in params.items() if k in ALLOWED_PARAMS}
                if allowed_params:
                    clean_query = '&'.join(f"{k}={v[0]}" for k, v in allowed_params.items())
            path = parsed.path.rstrip('/') or '/'
        else:
            # Less aggressive: keep all query parameters and path details
            clean_query = parsed.query
            path = parsed.path
        
        canonical = urlunparse((
            parsed.scheme or 'https',
            domain,
            path,
            '',
            clean_query or '',
            ''
        ))
        
        return canonical
    except Exception as e:
        print(f"[WARN] URL canonicalization failed for {url}: {e}")
        return url.lower().strip()


def extract_text(html: str, url: str) -> tuple[str, str]:
    """
    Extract text from HTML using trafilatura (primary) or readability (fallback).
    
    Returns:
        (text, title) tuple
    """
    text = ""
    title = ""
    
    # Try trafilatura first (best for clean extraction)
    if trafilatura:
        try:
            extracted = trafilatura.extract(html, include_comments=False, output_format='text')
            if extracted:
                text = extracted.strip()
                
            # Get title
            doc = trafilatura.extract(html, output_format='xml')
            if doc:
                from lxml import etree
                root = etree.fromstring(doc.encode())
                title_elem = root.find('.//title')
                if title_elem is not None:
                    title = title_elem.text or ""
        except Exception as e:
            print(f"[WARN] trafilatura extraction failed: {e}")
    
    # Fallback to readability
    if not text and Document:
        try:
            doc = Document(html)
            title = doc.title() or ""
            text = doc.summary()
            if text and BeautifulSoup:
                # Remove HTML tags
                soup = BeautifulSoup(text, 'lxml')
                text = soup.get_text(separator=' ', strip=True)
        except Exception as e:
            print(f"[WARN] readability extraction failed: {e}")
    
    # Last resort: basic BeautifulSoup
    if not text and BeautifulSoup:
        try:
            soup = BeautifulSoup(html, 'lxml')
            text = soup.get_text(separator=' ', strip=True)
            title_elem = soup.find('title')
            if title_elem:
                title = title_elem.get_text(strip=True)
        except Exception as e:
            print(f"[WARN] BeautifulSoup extraction failed: {e}")
    
    return text or "", title or ""


def is_thin_content(text: str, min_chars: int = 500) -> bool:
    """Check if content is too thin/sparse."""
    return len(text) < min_chars


def is_soft_404(title: str, text: str) -> bool:
    """Detect soft 404 pages (not found, error, etc.)."""
    soft_404_patterns = [
        r'not found',
        r'404',
        r'page not available',
        r'error occurred',
        r'access denied',
        r'forbidden',
        r'under construction',
        r'coming soon'
    ]
    
    combined = f"{title} {text}".lower()
    return any(re.search(pattern, combined) for pattern in soft_404_patterns)


def is_non_content_page(title: str, text: str) -> bool:
    """Detect non-content pages (login, search, etc.)."""
    non_content_patterns = [
        r'login',
        r'sign in',
        r'search results',
        r'no results found',
        r'privacy policy',
        r'terms of service',
        r'cookie policy'
    ]
    
    combined = f"{title} {text}".lower()
    return any(re.search(pattern, combined) for pattern in non_content_patterns)


def preprocess_file(
    input_path: Path,
    output_path: Path,
    bloom_size: int = 500000,
    dedupe_content: bool = True,
    dedupe_url: bool = True,
    aggressive_url_dedup: bool = False
) -> Dict[str, int]:
    """
    Process raw JSON file into clean JSON Lines format.
    
    Args:
        input_path: Path to input JSON file
        output_path: Path to output JSONL file
        bloom_size: Size of Bloom filter for URL deduplication
        dedupe_content: Whether to deduplicate by content hash
        dedupe_url: Whether to deduplicate by URL (default: True)
        aggressive_url_dedup: If True, uses aggressive URL canonicalization (default: False)
    
    Returns:
        Dictionary with processing statistics
    """
    stats = {
        'total_records': 0,
        'filtered_404': 0,
        'filtered_soft_404': 0,
        'filtered_thin_content': 0,
        'filtered_non_content': 0,
        'deduped_url': 0,
        'deduped_content': 0,
        'final_output': 0,
        'errors': 0
    }
    
    # Initialize Bloom filter for URL deduplication
    url_filter = BloomFilter(capacity=bloom_size, error_rate=0.001)
    
    # Content hash set for content deduplication
    content_hashes: Set[str] = set()
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"[INFO] Starting preprocessing...")
    print(f"[INFO] Input: {input_path}")
    print(f"[INFO] Output: {output_path}")
    print(f"[INFO] Bloom filter size: {bloom_size}")
    
    # Stream parse JSON array
    try:
        with open(input_path, 'rb') as input_file, \
             open(output_path, 'w', encoding='utf-8') as output_file:
            
            # Parse JSON array items using ijson
            items = ijson.items(input_file, 'item')
            
            # Initialize progress bar
            with tqdm(desc="Processing", unit=" docs") as pbar:
                for idx, item in enumerate(items):
                    stats['total_records'] += 1
                    pbar.update(1)
                    
                    try:
                        # Extract fields
                        url = item.get('url', '')
                        status = item.get('status')
                        if status is None:
                            status = item.get('crawl', {}).get('httpStatusCode', 0)
                        html = item.get('html')
                        raw_text = item.get('text') or ''
                        markdown = item.get('markdown') or ''
                        fetched_at = item.get('fetched_at') or item.get('crawl', {}).get('loadedTime', '')
                        content_type = (
                            item.get('content_type')
                            or item.get('metadata', {}).get('headers', {}).get('content-type')
                            or ''
                        )
                        
                        # Filter hard 404s
                        try:
                            status_code = int(status)
                        except (TypeError, ValueError):
                            status_code = 0
                        if status_code != 200:
                            stats['filtered_404'] += 1
                            continue
                        
                        # Canonicalize URL (for display/storage)
                        canonical_url = canonicalize_url(url, aggressive=aggressive_url_dedup)
                        
                        # Check URL deduplication (optional)
                        if dedupe_url:
                            dedup_key = canonical_url
                            if dedup_key in url_filter:
                                stats['deduped_url'] += 1
                                continue
                            url_filter.add(dedup_key)
                        
                        # Extract text/title using available fields
                        text = ''
                        title = ''

                        if html:
                            text, title = extract_text(html, url)

                        if not text and raw_text:
                            text = raw_text

                        if not title:
                            title = item.get('metadata', {}).get('title', '')

                        if not text and markdown:
                            text = markdown

                        if not text:
                            stats['filtered_non_content'] += 1
                            continue
                        
                        # Filter thin content
                        if is_thin_content(text):
                            stats['filtered_thin_content'] += 1
                            continue
                        
                        # Filter soft 404s
                        if is_soft_404(title, text):
                            stats['filtered_soft_404'] += 1
                            continue
                        
                        # Filter non-content pages
                        if is_non_content_page(title, text):
                            stats['filtered_non_content'] += 1
                            continue
                        
                        # Content deduplication
                        if dedupe_content:
                            text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
                            if text_hash in content_hashes:
                                stats['deduped_content'] += 1
                                continue
                            content_hashes.add(text_hash)
                        else:
                            text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
                        
                        # Create output document
                        doc = {
                            'url': url,
                            'canonical_url': canonical_url,
                            'title': title,
                            'text': text,
                            'text_sha256': text_hash,
                            'lang': 'en',  # TODO: Add language detection
                            'fetched_at': fetched_at,
                            'status': status_code,
                            'content_type': content_type
                        }
                        
                        # Write to JSONL
                        output_file.write(json.dumps(doc, ensure_ascii=False) + '\n')
                        stats['final_output'] += 1
                        
                    except Exception as e:
                        print(f"[ERROR] Processing record {idx}: {e}")
                        stats['errors'] += 1
                        continue
    
    except Exception as e:
        print(f"[ERROR] Fatal error during preprocessing: {e}")
        stats['errors'] += 1
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Preprocess raw JSON files into clean JSON Lines format'
    )
    parser.add_argument(
        '--input',
        type=Path,
        required=True,
        help='Input JSON file path'
    )
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Output JSONL file path'
    )
    parser.add_argument(
        '--bloom-size',
        type=int,
        default=500000,
        help='Bloom filter capacity (default: 500000)'
    )
    parser.add_argument(
        '--no-content-dedupe',
        action='store_true',
        help='Disable content-based deduplication'
    )
    parser.add_argument(
        '--url-dedupe',
        action='store_true',
        default=False,
        help='Enable URL-based deduplication (disabled by default - less aggressive)'
    )
    parser.add_argument(
        '--aggressive-url-dedup',
        action='store_true',
        help='Use aggressive URL canonicalization (removes most query params)'
    )
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not args.input.exists():
        print(f"[ERROR] Input file not found: {args.input}")
        sys.exit(1)
    
    # Run preprocessing (URL deduplication disabled by default for less aggressive deduping)
    stats = preprocess_file(
        input_path=args.input,
        output_path=args.output,
        bloom_size=args.bloom_size,
        dedupe_content=not args.no_content_dedupe,
        dedupe_url=args.url_dedupe,  # Default False - less aggressive
        aggressive_url_dedup=args.aggressive_url_dedup
    )
    
    # Print statistics
    print("\n" + "=" * 60)
    print("PREPROCESSING STATISTICS")
    print("=" * 60)
    print(f"Total records:     {stats['total_records']:>8}")
    print(f"Filtered (404):    {stats['filtered_404']:>8}")
    print(f"Filtered (soft):    {stats['filtered_soft_404']:>8}")
    print(f"Filtered (thin):   {stats['filtered_thin_content']:>8}")
    print(f"Filtered (non-content): {stats['filtered_non_content']:>8}")
    print(f"Deduped (URL):      {stats['deduped_url']:>8}")
    print(f"Deduped (content): {stats['deduped_content']:>8}")
    print(f"Final output:       {stats['final_output']:>8}")
    print(f"Errors:             {stats['errors']:>8}")
    print("=" * 60)
    
    # Exit with error code if no output generated
    if stats['final_output'] == 0:
        print("[ERROR] No documents output!")
        sys.exit(1)
    
    print(f"\n[SUCCESS] Preprocessing complete: {stats['final_output']} documents")


if __name__ == '__main__':
    main()

