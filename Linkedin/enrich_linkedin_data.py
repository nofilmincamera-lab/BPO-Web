#!/usr/bin/env python3
"""
LinkedIn Data Enrichment Script

This script enriches LinkedIn profile data by:
- Cross-referencing all companies from work experiences
- Counting current employees per company
- Counting past employees per company
- Aggregating recent posts
- Generating comprehensive analytics
"""

import json
import csv
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any
from collections import defaultdict
import argparse


class LinkedInEnricher:
    """Enriches LinkedIn data with cross-referencing and analytics."""

    def __init__(self, data_dir: str = "Linkedin"):
        self.data_dir = Path(data_dir)
        self.profiles = []
        self.company_analytics = defaultdict(lambda: {
            'current_employees': [],
            'past_employees': [],
            'total_current': 0,
            'total_past': 0,
            'posts': [],
            'company_name': '',
            'normalized_name': ''
        })
        self.profile_index = {}

    def normalize_company_name(self, company_name: str) -> str:
        """Normalize company names for better matching."""
        if not company_name:
            return ""

        # Convert to lowercase and strip
        normalized = company_name.lower().strip()

        # Remove common suffixes
        suffixes = [' inc', ' inc.', ' llc', ' ltd', ' ltd.', ' corporation',
                   ' corp', ' corp.', ' limited', ' co', ' co.', ' company']
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()

        # Remove special characters except spaces
        normalized = ''.join(c if c.isalnum() or c.isspace() else '' for c in normalized)

        # Collapse multiple spaces
        normalized = ' '.join(normalized.split())

        return normalized

    def load_json_data(self, filepath: Path) -> List[Dict]:
        """Load data from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle both single object and array of objects
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
        return []

    def load_csv_data(self, filepath: Path) -> List[Dict]:
        """Load data from CSV file."""
        profiles = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                profiles.append(row)
        return profiles

    def load_all_profiles(self):
        """Load all LinkedIn profiles from the data directory."""
        print(f"📂 Loading profiles from {self.data_dir}...")

        # Load JSON files
        for json_file in self.data_dir.glob('*.json'):
            print(f"  Loading {json_file.name}...")
            profiles = self.load_json_data(json_file)
            self.profiles.extend(profiles)

        # Load CSV files
        for csv_file in self.data_dir.glob('*.csv'):
            print(f"  Loading {csv_file.name}...")
            profiles = self.load_csv_data(csv_file)
            self.profiles.extend(profiles)

        print(f"✅ Loaded {len(self.profiles)} profiles\n")

    def extract_work_experience(self, profile: Dict) -> List[Dict]:
        """Extract work experience from a profile."""
        experiences = []

        # Try different common field names for work experience
        work_fields = ['experience', 'experiences', 'work_experience',
                      'positions', 'employment', 'work_history']

        for field in work_fields:
            if field in profile:
                exp_data = profile[field]
                if isinstance(exp_data, list):
                    experiences = exp_data
                    break
                elif isinstance(exp_data, str):
                    # Try to parse as JSON if it's a string
                    try:
                        experiences = json.loads(exp_data)
                        if isinstance(experiences, list):
                            break
                    except:
                        pass

        return experiences

    def extract_posts(self, profile: Dict) -> List[Dict]:
        """Extract posts from a profile."""
        posts = []

        # Try different common field names for posts
        post_fields = ['posts', 'activities', 'recent_posts', 'activity']

        for field in post_fields:
            if field in profile:
                post_data = profile[field]
                if isinstance(post_data, list):
                    posts = post_data
                    break
                elif isinstance(post_data, str):
                    try:
                        posts = json.loads(post_data)
                        if isinstance(posts, list):
                            break
                    except:
                        pass

        return posts

    def is_current_position(self, experience: Dict) -> bool:
        """Determine if a position is current."""
        # Check for various indicators of current position
        end_date_fields = ['end_date', 'endDate', 'to', 'end']

        for field in end_date_fields:
            if field in experience:
                end_value = experience[field]
                if end_value is None or end_value == '':
                    return True
                if isinstance(end_value, str):
                    if end_value.lower() in ['present', 'current', 'now']:
                        return True

        # Check if explicitly marked as current
        if experience.get('is_current') or experience.get('isCurrent'):
            return True

        return False

    def process_profiles(self):
        """Process all profiles and build company analytics."""
        print("🔍 Processing profiles and cross-referencing companies...")

        for idx, profile in enumerate(self.profiles):
            # Get profile identifiers
            profile_id = profile.get('id') or profile.get('profile_id') or str(idx)
            profile_name = profile.get('name') or profile.get('full_name') or profile.get('fullName') or f"Profile {idx}"
            profile_url = profile.get('url') or profile.get('profile_url') or profile.get('linkedin_url') or ''

            # Index the profile
            self.profile_index[profile_id] = {
                'name': profile_name,
                'url': profile_url,
                'profile': profile
            }

            # Extract and process work experiences
            experiences = self.extract_work_experience(profile)

            for exp in experiences:
                company_name = exp.get('company') or exp.get('company_name') or exp.get('companyName') or ''
                if not company_name:
                    continue

                normalized_name = self.normalize_company_name(company_name)
                is_current = self.is_current_position(exp)

                # Build employee record
                employee_record = {
                    'profile_id': profile_id,
                    'profile_name': profile_name,
                    'profile_url': profile_url,
                    'title': exp.get('title') or exp.get('position') or '',
                    'start_date': exp.get('start_date') or exp.get('startDate') or exp.get('from') or '',
                    'end_date': exp.get('end_date') or exp.get('endDate') or exp.get('to') or '',
                    'duration': exp.get('duration') or '',
                    'description': exp.get('description') or ''
                }

                # Add to company analytics
                company_key = normalized_name
                self.company_analytics[company_key]['company_name'] = company_name
                self.company_analytics[company_key]['normalized_name'] = normalized_name

                if is_current:
                    self.company_analytics[company_key]['current_employees'].append(employee_record)
                    self.company_analytics[company_key]['total_current'] += 1
                else:
                    self.company_analytics[company_key]['past_employees'].append(employee_record)
                    self.company_analytics[company_key]['total_past'] += 1

            # Extract and process posts
            posts = self.extract_posts(profile)
            for post in posts:
                # Try to find company mentions in posts
                post_text = post.get('text') or post.get('content') or ''
                post_data = {
                    'profile_id': profile_id,
                    'profile_name': profile_name,
                    'date': post.get('date') or post.get('posted_date') or post.get('timestamp') or '',
                    'text': post_text,
                    'url': post.get('url') or post.get('post_url') or '',
                    'likes': post.get('likes') or post.get('reactions') or 0,
                    'comments': post.get('comments') or 0,
                    'shares': post.get('shares') or 0
                }

                # Add post to relevant companies based on profile's work history
                for exp in experiences:
                    company_name = exp.get('company') or exp.get('company_name') or ''
                    if company_name:
                        normalized_name = self.normalize_company_name(company_name)
                        self.company_analytics[normalized_name]['posts'].append(post_data)

        print(f"✅ Processed {len(self.profiles)} profiles")
        print(f"✅ Found {len(self.company_analytics)} unique companies\n")

    def generate_company_report(self) -> pd.DataFrame:
        """Generate a summary report of all companies."""
        print("📊 Generating company analytics report...")

        report_data = []
        for company_key, data in sorted(self.company_analytics.items(),
                                       key=lambda x: x[1]['total_current'] + x[1]['total_past'],
                                       reverse=True):
            report_data.append({
                'Company Name': data['company_name'],
                'Normalized Name': data['normalized_name'],
                'Current Employees': data['total_current'],
                'Past Employees': data['total_past'],
                'Total Connections': data['total_current'] + data['total_past'],
                'Recent Posts': len(data['posts'])
            })

        return pd.DataFrame(report_data)

    def export_detailed_company_data(self, output_dir: str = "Linkedin/enriched"):
        """Export detailed data for each company."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"💾 Exporting detailed company data to {output_dir}...")

        for company_key, data in self.company_analytics.items():
            safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_'
                              for c in data['company_name'])
            safe_name = safe_name[:100]  # Limit filename length

            company_file = output_path / f"{safe_name}.json"

            # Prepare export data
            export_data = {
                'company_name': data['company_name'],
                'normalized_name': data['normalized_name'],
                'statistics': {
                    'total_current_employees': data['total_current'],
                    'total_past_employees': data['total_past'],
                    'total_connections': data['total_current'] + data['total_past'],
                    'total_posts': len(data['posts'])
                },
                'current_employees': data['current_employees'],
                'past_employees': data['past_employees'],
                'recent_posts': data['posts']
            }

            with open(company_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Exported {len(self.company_analytics)} company files\n")

    def export_summary_csv(self, output_file: str = "Linkedin/company_summary.csv"):
        """Export summary CSV of all companies."""
        df = self.generate_company_report()
        df.to_csv(output_file, index=False)
        print(f"✅ Saved summary report to {output_file}\n")
        return df

    def export_master_connections(self, output_file: str = "Linkedin/master_connections.csv"):
        """Export a master CSV of all person-company connections."""
        print(f"💾 Exporting master connections to {output_file}...")

        connections = []
        for company_key, data in self.company_analytics.items():
            company_name = data['company_name']

            for emp in data['current_employees']:
                connections.append({
                    'Company': company_name,
                    'Normalized Company': data['normalized_name'],
                    'Status': 'Current',
                    'Person Name': emp['profile_name'],
                    'Person Profile': emp['profile_url'],
                    'Title': emp['title'],
                    'Start Date': emp['start_date'],
                    'End Date': emp['end_date'],
                    'Duration': emp['duration']
                })

            for emp in data['past_employees']:
                connections.append({
                    'Company': company_name,
                    'Normalized Company': data['normalized_name'],
                    'Status': 'Past',
                    'Person Name': emp['profile_name'],
                    'Person Profile': emp['profile_url'],
                    'Title': emp['title'],
                    'Start Date': emp['start_date'],
                    'End Date': emp['end_date'],
                    'Duration': emp['duration']
                })

        df = pd.DataFrame(connections)
        df.to_csv(output_file, index=False)
        print(f"✅ Exported {len(connections)} connections\n")
        return df

    def print_top_companies(self, top_n: int = 20):
        """Print the top companies by connection count."""
        print(f"\n{'='*80}")
        print(f"🏆 TOP {top_n} COMPANIES BY TOTAL CONNECTIONS")
        print(f"{'='*80}\n")

        sorted_companies = sorted(
            self.company_analytics.items(),
            key=lambda x: x[1]['total_current'] + x[1]['total_past'],
            reverse=True
        )[:top_n]

        print(f"{'Rank':<6}{'Company':<40}{'Current':<10}{'Past':<10}{'Total':<10}{'Posts':<8}")
        print("-" * 80)

        for rank, (company_key, data) in enumerate(sorted_companies, 1):
            total = data['total_current'] + data['total_past']
            company_name = data['company_name'][:38]  # Truncate long names
            print(f"{rank:<6}{company_name:<40}{data['total_current']:<10}"
                  f"{data['total_past']:<10}{total:<10}{len(data['posts']):<8}")

        print("\n")

    def run_full_enrichment(self):
        """Run the complete enrichment process."""
        print("\n" + "="*80)
        print("🚀 LINKEDIN DATA ENRICHMENT")
        print("="*80 + "\n")

        # Load profiles
        self.load_all_profiles()

        if not self.profiles:
            print("❌ No profiles found! Please add LinkedIn data files to the Linkedin directory.")
            print("   Supported formats: .json, .csv")
            return

        # Process profiles
        self.process_profiles()

        # Generate reports
        summary_df = self.export_summary_csv()
        connections_df = self.export_master_connections()
        self.export_detailed_company_data()

        # Print top companies
        self.print_top_companies(20)

        print("="*80)
        print("✅ ENRICHMENT COMPLETE!")
        print("="*80)
        print(f"\nGenerated files:")
        print(f"  📄 Linkedin/company_summary.csv - Summary of all companies")
        print(f"  📄 Linkedin/master_connections.csv - All person-company connections")
        print(f"  📁 Linkedin/enriched/ - Detailed JSON files for each company")
        print("\n")


def main():
    parser = argparse.ArgumentParser(description='Enrich LinkedIn profile data')
    parser.add_argument('--data-dir', default='Linkedin',
                       help='Directory containing LinkedIn data files')
    parser.add_argument('--top-n', type=int, default=20,
                       help='Number of top companies to display')

    args = parser.parse_args()

    enricher = LinkedInEnricher(data_dir=args.data_dir)
    enricher.run_full_enrichment()


if __name__ == '__main__':
    main()
