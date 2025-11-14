#!/usr/bin/env python3
"""
Refactor web scraped data into Question-Answer format for AI training.
Transforms Venmo help center data into structured Q&A pairs with context.
"""

import pandas as pd
import json
import re
from urllib.parse import urlparse
from pathlib import Path


def extract_topic_from_url(url):
    """Extract topic/category from URL path."""
    path = urlparse(url).path
    parts = [p for p in path.split('/') if p]

    # Common Venmo help topics
    if 'troubleshooting' in path:
        return 'Troubleshooting'
    elif 'payments' in path or 'transfers' in path:
        return 'Payments & Transfers'
    elif 'accounts' in path or 'settings' in path or 'profile' in path:
        return 'Accounts & Settings'
    elif 'security' in path or 'privacy' in path:
        return 'Security & Privacy'
    elif 'wallet' in path or 'debit' in path or 'credit' in path:
        return 'Wallet & Cards'
    elif 'business' in path or 'charity' in path:
        return 'Business & Charity'
    elif 'tax' in path:
        return 'Tax Center'
    elif 'dispute' in path:
        return 'Disputes'
    elif 'crypto' in path:
        return 'Cryptocurrency'
    else:
        return 'General'


def generate_question_from_title(title):
    """Convert page title into a natural question."""
    # Remove "| Venmo" suffix
    title = re.sub(r'\s*\|\s*Venmo\s*$', '', title)

    # Common patterns
    patterns = [
        (r'^(.+?)\s+FAQ$', r'What do I need to know about \1?'),
        (r'^How to (.+)$', r'How do I \1?'),
        (r'^What (.+)$', r'What \1?'),
        (r'^Can I (.+)\?$', r'Can I \1?'),
        (r'^(.+) Requirements$', r'What are the requirements for \1?'),
        (r'^(.+) Security$', r'How does \1 security work?'),
        (r'^(.+) Verification$', r'How do I verify \1?'),
        (r'^Using (.+)$', r'How do I use \1?'),
        (r'^Adding (.+)$', r'How do I add \1?'),
        (r'^Getting Started with (.+)$', r'How do I get started with \1?'),
        (r'^(.+) Troubleshooting$', r'How do I troubleshoot \1?'),
    ]

    for pattern, replacement in patterns:
        match = re.match(pattern, title, re.IGNORECASE)
        if match:
            return re.sub(pattern, replacement, title, flags=re.IGNORECASE)

    # Default: convert title to question
    if '?' not in title:
        return f"What is {title}?"
    return title


def extract_answer_from_fulltext(fulltext, max_length=500):
    """Extract meaningful answer from full text."""
    # Remove "Help Center" header and navigation
    text = re.sub(r'Help Center.*?VenmoAccounts.*?section_page', '', fulltext)
    text = re.sub(r'article_page\|.*$', '', text)

    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Extract first meaningful paragraph (up to max_length chars)
    if len(text) > max_length:
        # Try to cut at sentence boundary
        cutoff = text[:max_length].rfind('.')
        if cutoff > 100:  # Ensure we have substantial content
            text = text[:cutoff + 1]
        else:
            text = text[:max_length] + '...'

    return text if text else "Please refer to the Venmo Help Center for detailed information."


def extract_keywords(title, url):
    """Extract relevant keywords for context."""
    keywords = set()

    # From title
    title_words = re.findall(r'\b[A-Z][a-z]+\b', title)
    keywords.update(title_words)

    # From URL
    url_parts = urlparse(url).path.split('/')
    for part in url_parts:
        # Convert kebab-case to words
        words = part.replace('-', ' ').replace('_', ' ').split()
        keywords.update([w.capitalize() for w in words if len(w) > 3])

    # Remove common words
    stop_words = {'Help', 'Center', 'Venmo', 'Page', 'Article', 'Home'}
    keywords = keywords - stop_words

    return ', '.join(sorted(keywords)[:5]) if keywords else ''


def parse_raw_data(data_string):
    """Parse the raw data string into structured format."""
    # This would parse the actual data provided by the user
    # For now, return empty list - will be populated with actual data
    return []


def create_qa_dataset(input_file, output_file):
    """Main function to create Q&A dataset from scraped data."""

    # Read input data (assuming it's saved as JSON)
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Input file {input_file} not found.")
        return

    qa_records = []

    for idx, item in enumerate(data):
        url = item.get('url', '')
        title = item.get('pageTitle', '')
        fulltext = item.get('fullText', '')

        # Skip empty or invalid entries
        if not url or not title:
            continue

        # Generate Q&A pair
        question = generate_question_from_title(title)
        answer = extract_answer_from_fulltext(fulltext)
        topic = extract_topic_from_url(url)
        keywords = extract_keywords(title, url)

        # Extract article ID from URL or fullText
        article_id = ''
        id_match = re.search(r'vhel\d+', fulltext) or re.search(r'articles/(\d+)', url)
        if id_match:
            article_id = id_match.group(0) if 'vhel' in id_match.group(0) else f'vhel{id_match.group(1)}'

        qa_records.append({
            'id': idx,
            'question': question,
            'answer': answer,
            'source_title': title,
            'source_url': url,
            'topic_category': topic,
            'keywords': keywords,
            'article_id': article_id,
            'data_source': 'Venmo Help Center'
        })

    # Create DataFrame
    df = pd.DataFrame(qa_records)

    # Save to CSV
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Created Q&A dataset with {len(df)} records")
    print(f"Saved to: {output_file}")

    # Print sample
    print("\nSample records:")
    print(df[['question', 'topic_category', 'keywords']].head(3))

    return df


def create_sample_qa_structure():
    """Create a sample Q&A structure to demonstrate the format."""

    sample_data = [
        {
            "url": "https://www.venmo.com/",
            "pageTitle": "Pay Friends | Payments App | Venmo",
            "fullText": "Pay friends. Pay for everything.Easily send money to your friends and pay for everything you want online, in-store..."
        },
        {
            "url": "https://help.venmo.com/hc/en-us/articles/360021199834-Customer-Identification-Document-Requirements",
            "pageTitle": "Customer Identification Document Requirements | Venmo",
            "fullText": "Help Center... Customer Identification Document Requirements... article_page|vhel168"
        },
        {
            "url": "https://help.venmo.com/cs/topic/troubleshooting",
            "pageTitle": "Troubleshooting | Venmo",
            "fullText": "VenmoAccounts, Profiles & SettingsUpdating your Venmo ProfilePayments & TransfersAll about money movement..."
        }
    ]

    qa_records = []
    for idx, item in enumerate(sample_data):
        question = generate_question_from_title(item['pageTitle'])
        answer = extract_answer_from_fulltext(item['fullText'])
        topic = extract_topic_from_url(item['url'])
        keywords = extract_keywords(item['pageTitle'], item['url'])

        qa_records.append({
            'id': idx,
            'question': question,
            'answer': answer,
            'source_title': item['pageTitle'],
            'source_url': item['url'],
            'topic_category': topic,
            'keywords': keywords,
            'article_id': f'sample_{idx}',
            'data_source': 'Venmo Help Center'
        })

    df = pd.DataFrame(qa_records)
    output_path = Path(__file__).parent.parent / 'data' / 'venmo_qa_sample.csv'
    output_path.parent.mkdir(exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8')

    print(f"Sample Q&A structure created: {output_path}")
    print("\nColumns:")
    print(df.columns.tolist())
    print("\nSample:")
    print(df.head())

    return df


if __name__ == '__main__':
    # Create sample structure
    print("Creating sample Q&A structure...\n")
    create_sample_qa_structure()
