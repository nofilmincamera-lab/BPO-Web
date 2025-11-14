#!/usr/bin/env python3
"""
Parse raw Venmo data from user input and transform to Q&A CSV format.
Handles the specific format provided by the user.
"""

import pandas as pd
import re
import json
from pathlib import Path
from typing import List, Dict


class VenmoQATransformer:
    """Transform Venmo help center data into Q&A format."""

    def __init__(self):
        self.topic_mapping = {
            'troubleshooting': 'Troubleshooting',
            'payments': 'Payments & Transfers',
            'transfers': 'Payments & Transfers',
            'profile': 'Accounts & Settings',
            'settings': 'Accounts & Settings',
            'accounts': 'Accounts & Settings',
            'security': 'Security & Privacy',
            'privacy': 'Security & Privacy',
            'wallet': 'Wallet & Cards',
            'debit-card': 'Wallet & Cards',
            'credit-card': 'Wallet & Cards',
            'business': 'Business Profiles',
            'charity': 'Charity Profiles',
            'tax': 'Tax Center',
            'dispute': 'Disputes',
            'crypto': 'Cryptocurrency',
            'buying': 'Buying & Selling',
            'selling': 'Buying & Selling',
            'bank': 'Banking',
            'payment-method': 'Payment Methods',
        }

    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', str(text))
        text = text.replace('…', '...')
        text = text.replace('\u2028', ' ')
        text = text.replace('\xa0', ' ')
        return text.strip()

    def extract_topic(self, url: str) -> str:
        """Extract topic category from URL."""
        url_lower = url.lower()
        for keyword, topic in self.topic_mapping.items():
            if keyword in url_lower:
                return topic
        return 'General Support'

    def generate_question(self, title: str) -> str:
        """Generate natural question from page title."""
        # Remove Venmo suffix
        title = re.sub(r'\s*\|\s*Venmo\s*$', '', title).strip()

        # Already a question
        if title.endswith('?'):
            return title

        # Patterns for transformation
        transformations = [
            (r'^How to (.+)$', r'How do I \1?'),
            (r'^(.+?)\s+FAQ$', r'What are the frequently asked questions about \1?'),
            (r'^(.+?)\s+Requirements?$', r'What are the requirements for \1?'),
            (r'^(.+?)\s+Verification$', r'How do I verify \1?'),
            (r'^Using (.+)$', r'How do I use \1?'),
            (r'^Adding (.+)$', r'How do I add \1?'),
            (r'^Getting Started with (.+)$', r'How do I get started with \1?'),
            (r'^(.+?)\s+Troubleshooting$', r'How do I troubleshoot \1?'),
            (r'^(.+?)\s+Security$', r'How secure is \1?'),
            (r'^Setting[- ]?Up (.+)$', r'How do I set up \1?'),
            (r'^(.+?)\s+Limits?$', r'What are the limits for \1?'),
            (r'^(.+?)\s+Fees?$', r'What are the fees for \1?'),
            (r'^(.+?)\s+Timeline$', r'What is the timeline for \1?'),
            (r'^(.+?)\s+Guide$', r'What is the guide for \1?'),
            (r'^What (.+)$', r'What \1?'),
            (r'^Can I (.+)$', r'Can I \1?'),
            (r'^I(.+)$', r'What should I do if I\1?'),
        ]

        for pattern, replacement in transformations:
            if re.match(pattern, title, re.IGNORECASE):
                question = re.sub(pattern, replacement, title, flags=re.IGNORECASE)
                return question if question.endswith('?') else question + '?'

        # Default transformation
        return f"What is {title}?"

    def extract_answer(self, fulltext: str, title: str) -> str:
        """Extract concise answer from full text."""
        text = self.clean_text(fulltext)

        # Remove navigation and boilerplate
        patterns_to_remove = [
            r'Help Center.*?How can we help you\?',
            r'VenmoAccounts.*?Settings',
            r'Updating your Venmo Profile',
            r'Payments & Transfers',
            r'All about mo.*?',
            r'article_page\|.*$',
            r'section_page.*$',
            r'home_page.*$',
            r'contact-us.*$',
            r'TopicsAccounts.*?Settings',
        ]

        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        text = re.sub(r'\s+', ' ', text).strip()

        # Extract meaningful content
        if len(text) > 100:
            # Get first few sentences
            sentences = re.split(r'(?<=[.!?])\s+', text)
            answer_parts = []
            total_length = 0

            for sent in sentences:
                if total_length + len(sent) < 400 and len(answer_parts) < 4:
                    answer_parts.append(sent)
                    total_length += len(sent)
                else:
                    break

            if answer_parts:
                return ' '.join(answer_parts)

        # Fallback answer
        clean_title = title.replace('| Venmo', '').strip()
        return f"For detailed information about {clean_title}, please refer to the Venmo Help Center documentation."

    def extract_keywords(self, title: str, url: str) -> str:
        """Extract relevant keywords."""
        keywords = set()

        # From title
        title_words = re.findall(r'\b[A-Z][a-z]{2,}\b', title)
        keywords.update(title_words[:10])

        # From URL path
        if '/' in url:
            path = url.split('/')[-1]
            path_words = re.sub(r'[-_]', ' ', path).split()
            keywords.update([w.title() for w in path_words if len(w) > 3])

        # Remove stop words
        stop_words = {
            'Venmo', 'Help', 'Center', 'Page', 'Article', 'Your', 'With',
            'From', 'About', 'Questions', 'There', 'This', 'That', 'Have'
        }
        keywords = {k for k in keywords if k not in stop_words}

        return ', '.join(sorted(keywords)[:8])

    def extract_article_id(self, fulltext: str, url: str) -> str:
        """Extract article identifier."""
        # Look for vhel pattern
        match = re.search(r'vhel\d+', fulltext)
        if match:
            return match.group(0)

        # Look for article number in URL
        match = re.search(r'/articles/(\d+)', url)
        if match:
            return f"article_{match.group(1)}"

        return ''

    def determine_page_type(self, fulltext: str, url: str) -> str:
        """Determine the type of help page."""
        if 'section_page' in fulltext:
            return 'Section Index'
        elif 'home_page' in fulltext:
            return 'Home Page'
        elif 'contact' in fulltext.lower():
            return 'Contact Page'
        elif '/cs/articles/' in url or '/hc/en-us/articles/' in url:
            return 'Article'
        else:
            return 'General'

    def parse_raw_input(self, input_file: str) -> List[Dict]:
        """
        Parse the raw input file.
        Expected format: JSON array of objects with url, pageTitle, fullText
        """
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Try to parse as JSON
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

        # If not valid JSON, try to extract objects manually
        # This handles the format shown in user's message
        objects = []
        # Pattern to match objects like: { url: "...", pageTitle: "...", fullText: "..." }
        pattern = r'\{\s*url:\s*"([^"]+)",\s*pageTitle:\s*"([^"]+)",\s*fullText:\s*"([^"]+)".*?\}'

        matches = re.findall(pattern, content, re.DOTALL)
        for match in matches:
            objects.append({
                'url': match[0],
                'pageTitle': match[1],
                'fullText': match[2]
            })

        return objects

    def transform_to_qa(self, data: List[Dict]) -> pd.DataFrame:
        """Transform data to Q&A format."""
        qa_records = []

        for idx, item in enumerate(data):
            url = item.get('url', '')
            title = item.get('pageTitle', '')
            fulltext = item.get('fullText', '')

            if not url or not title:
                continue

            qa_record = {
                'id': idx + 1,
                'question': self.generate_question(title),
                'answer': self.extract_answer(fulltext, title),
                'source_title': title,
                'source_url': url,
                'topic_category': self.extract_topic(url),
                'keywords': self.extract_keywords(title, url),
                'article_id': self.extract_article_id(fulltext, url),
                'page_type': self.determine_page_type(fulltext, url),
                'data_source': 'Venmo Help Center',
                'language': 'en-US',
                'context_type': 'customer_support'
            }

            qa_records.append(qa_record)

        return pd.DataFrame(qa_records)


def main():
    """Main execution."""
    print("="*80)
    print("VENMO Q&A DATASET TRANSFORMER")
    print("="*80)

    transformer = VenmoQATransformer()

    # Instructions for user
    print("\nInstructions:")
    print("1. Save your raw Venmo data to: data/venmo_raw_input.json")
    print("2. Format: JSON array of objects with url, pageTitle, fullText")
    print("3. Run this script to generate Q&A dataset\n")

    input_file = Path(__file__).parent.parent / 'data' / 'venmo_raw_input.json'
    output_file = Path(__file__).parent.parent / 'data' / 'venmo_qa_dataset.csv'

    if not input_file.exists():
        print(f"⚠ Input file not found: {input_file}")
        print("\nCreating sample format file...")

        # Create sample
        sample_data = [
            {
                "url": "https://help.venmo.com/cs/articles/example-123",
                "pageTitle": "How to Send Money | Venmo",
                "fullText": "Help Center. Learn how to send money to friends. You can send money easily using the Venmo app."
            }
        ]

        input_file.parent.mkdir(exist_ok=True)
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2)

        print(f"✓ Sample created at: {input_file}")
        print("  Please replace with your actual data and run again.")
        return

    # Parse and transform
    print(f"Reading from: {input_file}")
    data = transformer.parse_raw_input(str(input_file))
    print(f"✓ Parsed {len(data)} records")

    print("Transforming to Q&A format...")
    df = transformer.transform_to_qa(data)

    # Save output
    output_file.parent.mkdir(exist_ok=True)
    df.to_csv(output_file, index=False, encoding='utf-8')

    print(f"✓ Q&A dataset created: {output_file}")
    print(f"  Total records: {len(df)}")
    print(f"\nColumns: {', '.join(df.columns.tolist())}")

    # Statistics
    print("\n" + "="*80)
    print("DATASET STATISTICS")
    print("="*80)
    print(f"\nTopic Distribution:")
    print(df['topic_category'].value_counts().to_string())
    print(f"\nPage Type Distribution:")
    print(df['page_type'].value_counts().to_string())

    # Sample output
    print("\n" + "="*80)
    print("SAMPLE Q&A PAIRS")
    print("="*80)
    for idx, row in df.head(5).iterrows():
        print(f"\n[{row['id']}] Topic: {row['topic_category']}")
        print(f"Q: {row['question']}")
        print(f"A: {row['answer'][:200]}{'...' if len(row['answer']) > 200 else ''}")
        print(f"Keywords: {row['keywords']}")
        print("-"*80)

    return df


if __name__ == '__main__':
    main()
