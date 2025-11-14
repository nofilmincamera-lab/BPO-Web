#!/usr/bin/env python3
"""
Process Venmo help center data from raw format to Q&A CSV.
"""

import pandas as pd
import re
from pathlib import Path


def clean_text(text):
    """Clean and normalize text."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove ellipsis character
    text = text.replace('…', '...')
    # Remove special unicode characters
    text = text.replace('\u2028', ' ')
    return text.strip()


def extract_topic_from_url(url):
    """Extract topic/category from URL."""
    url_lower = url.lower()

    topic_mapping = {
        'troubleshooting': 'Troubleshooting',
        'payments': 'Payments & Transfers',
        'transfers': 'Payments & Transfers',
        'profile': 'Accounts & Settings',
        'settings': 'Accounts & Settings',
        'accounts': 'Accounts & Settings',
        'security': 'Security & Privacy',
        'privacy': 'Security & Privacy',
        'wallet': 'Wallet & Cards',
        'debit': 'Wallet & Cards',
        'credit': 'Wallet & Cards',
        'business': 'Business Profiles',
        'charity': 'Charity Profiles',
        'tax': 'Tax Center',
        'dispute': 'Disputes',
        'crypto': 'Cryptocurrency',
        'buying': 'Buying & Selling',
        'selling': 'Buying & Selling',
    }

    for keyword, topic in topic_mapping.items():
        if keyword in url_lower:
            return topic

    return 'General Support'


def generate_question(title):
    """Generate a natural question from page title."""
    # Remove "| Venmo" suffix
    title = re.sub(r'\s*\|\s*Venmo\s*$', '', title)

    # Already a question
    if '?' in title:
        return title

    # FAQ patterns
    if 'FAQ' in title:
        base = title.replace('FAQ', '').strip()
        return f"What are the frequently asked questions about {base}?"

    # How to patterns
    if title.lower().startswith('how to'):
        return title + "?"

    # Specific patterns
    patterns = {
        r'^(.+?)\s+Requirements?$': r'What are the requirements for \1?',
        r'^(.+?)\s+Verification$': r'How do I verify my \1?',
        r'^Using (.+)$': r'How do I use \1?',
        r'^Adding (.+)$': r'How do I add \1?',
        r'^Getting Started with (.+)$': r'How do I get started with \1?',
        r'^(.+?)\s+Troubleshooting$': r'How do I troubleshoot issues with \1?',
        r'^(.+?)\s+Security$': r'How does \1 security work?',
        r'^Setting Up (.+)$': r'How do I set up \1?',
        r'^What (.+)$': r'What \1?',
        r'^Can I (.+)$': r'Can I \1?',
        r'^(.+?)\s+Limits?$': r'What are the limits for \1?',
        r'^(.+?)\s+Fees?$': r'What are the fees for \1?',
        r'^(.+?)\s+Timeline$': r'What is the timeline for \1?',
    }

    for pattern, replacement in patterns.items():
        if re.match(pattern, title, re.IGNORECASE):
            question = re.sub(pattern, replacement, title, flags=re.IGNORECASE)
            return question + ('?' if not question.endswith('?') else '')

    # Default
    return f"What is {title}?"


def extract_answer(fulltext, title):
    """Extract a concise answer from full text."""
    # Clean the text
    text = clean_text(fulltext)

    # Remove navigation elements
    text = re.sub(r'Help Center.*?How can we help you\?', '', text)
    text = re.sub(r'VenmoAccounts.*?Profiles & Settings', '', text)
    text = re.sub(r'article_page\|.*$', '', text)
    text = re.sub(r'section_page.*$', '', text)
    text = re.sub(r'home_page.*$', '', text)
    text = re.sub(r'contact-us.*$', '', text)

    # Remove repeated navigation links
    text = re.sub(r'(Updating your Venmo Profile|Payments & Transfers|All about mo)', '', text, flags=re.IGNORECASE)

    # Clean up
    text = re.sub(r'\s+', ' ', text).strip()

    # If we have substantial content, extract first portion
    if len(text) > 300:
        # Try to get first complete sentence or two
        sentences = re.split(r'(?<=[.!?])\s+', text)
        answer = ''
        for sent in sentences[:3]:
            if len(answer + sent) < 500:
                answer += sent + ' '
            else:
                break
        text = answer.strip()

    # If still too long or too short, provide generic answer
    if len(text) < 50 or len(text) > 600:
        return f"For information about {title.replace('| Venmo', '').strip()}, please visit the Venmo Help Center."

    return text


def extract_keywords(title, url):
    """Extract keywords for categorization."""
    keywords = set()

    # Extract from title
    words = re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', title)
    keywords.update(words)

    # Extract from URL path
    path = url.split('/')[-1] if '/' in url else ''
    path_words = re.sub(r'[-_]', ' ', path).split()
    keywords.update([w.title() for w in path_words if len(w) > 3])

    # Remove common stop words
    stop_words = {'Venmo', 'Help', 'Center', 'Page', 'Article', 'Your', 'With', 'From', 'About', 'Questions'}
    keywords = {k for k in keywords if k not in stop_words}

    return ', '.join(sorted(keywords)[:7])


def extract_article_id(fulltext, url):
    """Extract article ID from fulltext or URL."""
    # Look for vhel pattern in fulltext
    match = re.search(r'vhel\d+', fulltext)
    if match:
        return match.group(0)

    # Look for article number in URL
    match = re.search(r'/articles/(\d+)', url)
    if match:
        return f"article_{match.group(1)}"

    return ''


# Sample data structure based on user's input
RAW_DATA = [
    {
        "url": "https://www.venmo.com/",
        "pageTitle": "Pay Friends | Payments App | Venmo",
        "fullText": "Pay friends. Pay for everything.Easily send money to your friends and pay for everything* you want online, in-store, a...association with this card program. All rights reserved. Standard data rates from your wireless service provider may apply."
    },
    {
        "url": "https://help.venmo.com/hc/en-us/articles/360021199834-Customer-Identification-Document-Requirements",
        "pageTitle": "Customer Identification Document Requirements | Venmo",
        "fullText": "Help CenterHow can we help you?VenmoAccounts, Profiles & SettingsUpdating your Venmo ProfilePayments & TransfersAll about mo...Profile Identity Verification FAQRequesting Updates to Your Tax InformationAccessing Your Tax Documentsarticle_page|vhel168"
    },
    # Add more entries as needed
]


def process_data(data):
    """Process raw data into Q&A format."""
    qa_records = []

    for idx, item in enumerate(data):
        url = item.get('url', '')
        title = item.get('pageTitle', '')
        fulltext = item.get('fullText', '')

        # Skip if missing essential fields
        if not url or not title or not fulltext:
            continue

        # Generate components
        question = generate_question(title)
        answer = extract_answer(fulltext, title)
        topic = extract_topic_from_url(url)
        keywords = extract_keywords(title, url)
        article_id = extract_article_id(fulltext, url)

        # Extract page type
        page_type = 'article'
        if 'section_page' in fulltext:
            page_type = 'section'
        elif 'home_page' in fulltext:
            page_type = 'home'
        elif 'contact-us' in fulltext:
            page_type = 'contact'

        qa_records.append({
            'id': idx + 1,
            'question': question,
            'answer': answer,
            'source_title': title,
            'source_url': url,
            'topic_category': topic,
            'keywords': keywords,
            'article_id': article_id,
            'page_type': page_type,
            'data_source': 'Venmo Help Center',
            'language': 'en-US'
        })

    return pd.DataFrame(qa_records)


def main():
    """Main execution function."""
    print("Processing Venmo help center data...")

    # Process the data
    df = process_data(RAW_DATA)

    # Save to CSV
    output_dir = Path(__file__).parent.parent / 'data'
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / 'venmo_qa_dataset.csv'

    df.to_csv(output_file, index=False, encoding='utf-8')

    print(f"\n✓ Created Q&A dataset with {len(df)} records")
    print(f"✓ Saved to: {output_file}")
    print(f"\nColumns: {', '.join(df.columns.tolist())}")
    print(f"\nTopic distribution:")
    print(df['topic_category'].value_counts())

    # Show sample
    print(f"\n{'='*80}")
    print("SAMPLE Q&A PAIRS:")
    print('='*80)
    for idx, row in df.head(3).iterrows():
        print(f"\nQ: {row['question']}")
        print(f"A: {row['answer'][:150]}...")
        print(f"Topic: {row['topic_category']} | Keywords: {row['keywords']}")
        print('-'*80)

    return df


if __name__ == '__main__':
    main()
