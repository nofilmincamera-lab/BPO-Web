#!/usr/bin/env python3
"""
Direct converter for Venmo data - paste your raw data here and run.
"""

import pandas as pd
import re
from pathlib import Path

# PASTE YOUR RAW DATA HERE (or load from file)
# Format: Each line like: 0\t{ url: "...", pageTitle: "...", fullText: "..." }
RAW_DATA_STRING = """
Place your raw data here, or the script will look for data/venmo_raw_paste.txt
"""


def parse_raw_line(line: str) -> dict:
    """Parse a single line of raw data."""
    # Remove leading number and tab
    line = re.sub(r'^\d+\s+', '', line)

    # Extract url
    url_match = re.search(r'url:\s*"([^"]+)"', line)
    url = url_match.group(1) if url_match else ''

    # Extract pageTitle
    title_match = re.search(r'pageTitle:\s*"([^"]+)"', line)
    title = title_match.group(1) if title_match else ''

    # Extract fullText - handle escaped quotes and special chars
    fulltext_match = re.search(r'fullText:\s*["`]([^"`]+?)["`](?:,|\s*…|\s*})', line, re.DOTALL)
    fulltext = fulltext_match.group(1) if fulltext_match else ''

    # Clean up escaped characters
    fulltext = fulltext.replace('\\u2028', ' ').replace('…', '...').replace('\u2028', ' ')

    return {
        'url': url,
        'pageTitle': title,
        'fullText': fulltext
    }


def clean_text(text):
    """Clean and normalize text."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', str(text))
    text = text.replace('…', '...')
    return text.strip()


def get_topic(url):
    """Determine topic from URL."""
    url_lower = url.lower()

    if 'troubleshooting' in url_lower:
        return 'Troubleshooting'
    elif 'payment' in url_lower or 'transfer' in url_lower:
        return 'Payments & Transfers'
    elif 'account' in url_lower or 'profile' in url_lower or 'setting' in url_lower:
        return 'Accounts & Settings'
    elif 'security' in url_lower or 'privacy' in url_lower:
        return 'Security & Privacy'
    elif 'debit' in url_lower or 'credit' in url_lower or 'wallet' in url_lower or 'card' in url_lower:
        return 'Wallet & Cards'
    elif 'business' in url_lower:
        return 'Business Profiles'
    elif 'charity' in url_lower:
        return 'Charity Profiles'
    elif 'tax' in url_lower:
        return 'Tax Center'
    elif 'dispute' in url_lower:
        return 'Disputes'
    elif 'crypto' in url_lower:
        return 'Cryptocurrency'
    elif 'buy' in url_lower or 'sell' in url_lower:
        return 'Buying & Selling'
    elif 'bank' in url_lower:
        return 'Banking'
    else:
        return 'General Support'


def make_question(title):
    """Convert title to question."""
    # Remove | Venmo
    title = re.sub(r'\s*\|\s*Venmo\s*$', '', title).strip()

    if '?' in title:
        return title

    # Question patterns
    patterns = [
        (r'^How to (.+)', r'How do I \1?'),
        (r'^(.+?) FAQ', r'What should I know about \1?'),
        (r'^(.+?) Requirements?', r'What are the requirements for \1?'),
        (r'^(.+?) Verification', r'How do I verify \1?'),
        (r'^Using (.+)', r'How do I use \1?'),
        (r'^Adding (.+)', r'How do I add \1?'),
        (r'^Getting Started with (.+)', r'How do I get started with \1?'),
        (r'^(.+?) Troubleshooting', r'How do I troubleshoot \1?'),
        (r'^(.+?) Security', r'How secure is \1?'),
        (r'^Setting Up (.+)', r'How do I set up \1?'),
        (r'^(.+?) Limits?', r'What are the limits for \1?'),
        (r'^(.+?) Fees?', r'What are the fees for \1?'),
        (r'^Can I (.+)', r'Can I \1?'),
        (r'^What (.+)', r'What \1?'),
        (r'^I\'?m? (.+)', r'What should I do if I\'m \1?'),
    ]

    for pattern, replacement in patterns:
        if re.match(pattern, title, re.IGNORECASE):
            q = re.sub(pattern, replacement, title, flags=re.IGNORECASE)
            return q if q.endswith('?') else q + '?'

    return f"What is {title}?"


def extract_answer(fulltext, title):
    """Extract answer from full text."""
    text = clean_text(fulltext)

    # Remove navigation cruft
    text = re.sub(r'Help Center.*?help you\?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Venmo.*?Settings', '', text)
    text = re.sub(r'article_page\|.*', '', text)
    text = re.sub(r'section_page.*', '', text)
    text = re.sub(r'home_page.*', '', text)

    text = clean_text(text)

    # Get first substantial part
    if len(text) > 150:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        result = []
        length = 0

        for sent in sentences[:4]:
            if length + len(sent) < 450:
                result.append(sent)
                length += len(sent)
            else:
                break

        if result:
            return ' '.join(result)

    if len(text) < 50:
        return f"For information about {title.replace('| Venmo', '').strip()}, visit the Venmo Help Center."

    return text[:450] + ('...' if len(text) > 450 else '')


def get_keywords(title, url):
    """Extract keywords."""
    words = set()

    # From title
    title_words = re.findall(r'\b[A-Z][a-z]{2,}\b', title)
    words.update([w for w in title_words if w not in ['Venmo', 'Help', 'Center', 'Your', 'The']])

    # From URL
    if '/' in url:
        path = url.split('/')[-1]
        url_words = re.sub(r'[-_]', ' ', path).split()
        words.update([w.title() for w in url_words if len(w) > 3 and w.lower() not in ['help', 'venmo', 'articles']])

    return ', '.join(sorted(words)[:6])


def get_article_id(fulltext, url):
    """Get article ID."""
    match = re.search(r'vhel\d+', fulltext)
    if match:
        return match.group(0)

    match = re.search(r'/articles/(\d+)', url)
    if match:
        return f"article_{match.group(1)}"

    return ''


def convert_to_qa_csv(input_file=None, output_file=None):
    """Main conversion function."""

    # Read input
    if input_file and Path(input_file).exists():
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_data = f.read()
    else:
        raw_data = RAW_DATA_STRING

    # Parse lines
    lines = [line.strip() for line in raw_data.split('\n') if line.strip()]
    print(f"Processing {len(lines)} lines...")

    records = []
    for idx, line in enumerate(lines):
        try:
            data = parse_raw_line(line)

            if not data['url'] or not data['pageTitle']:
                continue

            record = {
                'id': idx + 1,
                'question': make_question(data['pageTitle']),
                'answer': extract_answer(data['fullText'], data['pageTitle']),
                'source_title': data['pageTitle'],
                'source_url': data['url'],
                'topic_category': get_topic(data['url']),
                'keywords': get_keywords(data['pageTitle'], data['url']),
                'article_id': get_article_id(data['fullText'], data['url']),
                'data_source': 'Venmo Help Center',
                'language': 'en-US'
            }

            records.append(record)

        except Exception as e:
            print(f"Error processing line {idx}: {e}")
            continue

    # Create DataFrame
    df = pd.DataFrame(records)

    # Save
    if output_file is None:
        output_file = Path(__file__).parent.parent / 'data' / 'venmo_qa_dataset.csv'

    output_file = Path(output_file)
    output_file.parent.mkdir(exist_ok=True)
    df.to_csv(output_file, index=False, encoding='utf-8')

    # Report
    print(f"\n{'='*80}")
    print(f"✓ Successfully converted {len(df)} records to Q&A format")
    print(f"✓ Saved to: {output_file}")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nTopic Distribution:")
    print(df['topic_category'].value_counts())
    print(f"\n{'='*80}")
    print("Sample Q&A:")
    print('='*80)

    for idx, row in df.head(3).iterrows():
        print(f"\nQ: {row['question']}")
        print(f"A: {row['answer'][:150]}...")
        print(f"   Topic: {row['topic_category']} | ID: {row['article_id']}")
        print('-'*80)

    return df


if __name__ == '__main__':
    # Check for input file
    input_file = Path(__file__).parent.parent / 'data' / 'venmo_raw_paste.txt'

    if not input_file.exists():
        print(f"Place your raw data in: {input_file}")
        print("Or paste it directly in the RAW_DATA_STRING variable in this script.")
        print("\nCreating sample input file...")
        input_file.parent.mkdir(exist_ok=True)
        with open(input_file, 'w') as f:
            f.write('0\t{ url: "https://www.venmo.com/", pageTitle: "Pay Friends | Venmo", fullText: "Pay friends easily..." }\n')
        print(f"Sample created at: {input_file}")
    else:
        df = convert_to_qa_csv(input_file)
        print(f"\n✅ Done! Check data/venmo_qa_dataset.csv")
