#!/usr/bin/env python3
"""
LinkedIn Advanced Data Enrichment Script

This script provides warm introduction intelligence by:
- Identifying who can introduce you to target companies
- Scoring connections by recency, seniority, and relationship strength
- Detecting role levels and departments
- Analyzing profile quality
- Recommending optimal introduction paths
"""

import json
import csv
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Set, Any, Optional
from collections import defaultdict
import argparse
import re
from dateutil import parser as date_parser


class IntroductionIntelligence:
    """Advanced LinkedIn data enrichment for warm introductions."""

    # Seniority level keywords (ordered from highest to lowest)
    SENIORITY_LEVELS = {
        'C-Level': ['ceo', 'cto', 'cfo', 'coo', 'cmo', 'cio', 'chief', 'founder', 'co-founder', 'president'],
        'VP': ['vp', 'vice president', 'svp', 'evp'],
        'Director': ['director', 'head of'],
        'Manager': ['manager', 'mgr', 'lead', 'team lead'],
        'Senior': ['senior', 'sr', 'principal', 'staff'],
        'Mid-Level': ['engineer', 'developer', 'designer', 'analyst', 'specialist', 'consultant'],
        'Junior': ['junior', 'jr', 'associate', 'assistant', 'entry', 'intern']
    }

    # Department keywords
    DEPARTMENTS = {
        'Engineering': ['engineer', 'software', 'developer', 'dev', 'technical', 'architect', 'sre', 'devops', 'qa', 'test'],
        'Product': ['product', 'pm', 'product manager'],
        'Design': ['design', 'ux', 'ui', 'creative'],
        'Sales': ['sales', 'account executive', 'ae', 'business development', 'bd'],
        'Marketing': ['marketing', 'growth', 'content', 'social media', 'seo', 'sem'],
        'Customer Success': ['customer success', 'cs', 'customer support', 'support'],
        'Operations': ['operations', 'ops', 'supply chain', 'logistics'],
        'Finance': ['finance', 'accounting', 'controller', 'financial'],
        'HR': ['human resources', 'hr', 'people', 'talent', 'recruiter', 'recruiting'],
        'Legal': ['legal', 'counsel', 'attorney', 'compliance'],
        'Data': ['data', 'analytics', 'data science', 'ml', 'machine learning', 'ai'],
        'Executive': ['ceo', 'cto', 'cfo', 'coo', 'president', 'chief']
    }

    def __init__(self, data_dir: str = "Linkedin"):
        self.data_dir = Path(data_dir)
        self.profiles = []
        self.company_analytics = defaultdict(lambda: {
            'current_employees': [],
            'past_employees': [],
            'all_connections': [],
            'total_current': 0,
            'total_past': 0,
            'posts': [],
            'company_name': '',
            'normalized_name': '',
            'best_intros': []
        })
        self.profile_index = {}

    def normalize_company_name(self, company_name: str) -> str:
        """Normalize company names for better matching."""
        if not company_name:
            return ""

        normalized = company_name.lower().strip()
        suffixes = [' inc', ' inc.', ' llc', ' ltd', ' ltd.', ' corporation',
                   ' corp', ' corp.', ' limited', ' co', ' co.', ' company']
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()

        normalized = ''.join(c if c.isalnum() or c.isspace() else '' for c in normalized)
        normalized = ' '.join(normalized.split())
        return normalized

    def detect_seniority(self, title: str) -> tuple[str, int]:
        """
        Detect seniority level from job title.
        Returns (level_name, score) where higher score = more senior.
        """
        if not title:
            return ('Unknown', 0)

        title_lower = title.lower()

        # Check each seniority level (ordered from highest to lowest)
        for idx, (level, keywords) in enumerate(self.SENIORITY_LEVELS.items()):
            for keyword in keywords:
                if keyword in title_lower:
                    score = 7 - idx  # C-Level=7, VP=6, Director=5, etc.
                    return (level, score)

        return ('Mid-Level', 3)

    def detect_departments(self, title: str) -> List[str]:
        """Detect department(s) from job title."""
        if not title:
            return ['Unknown']

        title_lower = title.lower()
        departments = []

        for dept, keywords in self.DEPARTMENTS.items():
            for keyword in keywords:
                if keyword in title_lower:
                    departments.append(dept)
                    break

        return departments if departments else ['General']

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats."""
        if not date_str or date_str in ['', 'None', 'null']:
            return None

        # Handle "Present", "Current", etc.
        if isinstance(date_str, str) and date_str.lower() in ['present', 'current', 'now']:
            return datetime.now()

        try:
            # Try parsing with dateutil
            return date_parser.parse(date_str)
        except:
            # Try manual parsing for common formats
            try:
                # Try YYYY-MM
                if re.match(r'^\d{4}-\d{2}$', date_str):
                    year, month = date_str.split('-')
                    return datetime(int(year), int(month), 1)
                # Try YYYY
                elif re.match(r'^\d{4}$', date_str):
                    return datetime(int(date_str), 1, 1)
            except:
                pass

        return None

    def calculate_recency_score(self, end_date: Optional[datetime]) -> float:
        """
        Calculate recency score for alumni connections.
        More recent = higher score.

        Current: 1.0
        <1 year: 0.9
        1-2 years: 0.7
        2-5 years: 0.5
        5+ years: 0.3
        """
        if end_date is None:
            return 1.0  # Current position

        now = datetime.now()
        years_ago = (now - end_date).days / 365.25

        if years_ago < 1:
            return 0.9
        elif years_ago < 2:
            return 0.7
        elif years_ago < 5:
            return 0.5
        else:
            return 0.3

    def calculate_profile_quality(self, profile: Dict) -> Dict[str, Any]:
        """
        Analyze profile completeness and quality.

        Returns dict with:
        - completeness_score (0-100)
        - has_photo (bool)
        - has_summary (bool)
        - position_count (int)
        - has_education (bool)
        - has_skills (bool)
        - post_count (int)
        - engagement_level (str)
        """
        score = 0
        max_score = 100

        quality = {
            'completeness_score': 0,
            'has_photo': False,
            'has_summary': False,
            'position_count': 0,
            'has_education': False,
            'has_skills': False,
            'post_count': 0,
            'engagement_level': 'Unknown'
        }

        # Check for photo (15 points)
        if profile.get('photo') or profile.get('profile_photo') or profile.get('photo_url'):
            quality['has_photo'] = True
            score += 15

        # Check for summary/about (20 points)
        if profile.get('summary') or profile.get('about') or profile.get('description'):
            quality['has_summary'] = True
            score += 20

        # Check positions (25 points)
        exp_fields = ['experience', 'experiences', 'work_experience', 'positions']
        for field in exp_fields:
            if field in profile and profile[field]:
                try:
                    exp_data = profile[field]
                    if isinstance(exp_data, str):
                        exp_data = json.loads(exp_data)
                    if isinstance(exp_data, list):
                        quality['position_count'] = len(exp_data)
                        if len(exp_data) > 0:
                            score += 15
                        if len(exp_data) >= 3:
                            score += 10
                        break
                except:
                    pass

        # Check education (15 points)
        edu_fields = ['education', 'schools']
        for field in edu_fields:
            if field in profile and profile[field]:
                quality['has_education'] = True
                score += 15
                break

        # Check skills (10 points)
        skill_fields = ['skills', 'skill_list']
        for field in skill_fields:
            if field in profile and profile[field]:
                quality['has_skills'] = True
                score += 10
                break

        # Check posts/activity (15 points)
        post_fields = ['posts', 'activities', 'recent_posts']
        for field in post_fields:
            if field in profile and profile[field]:
                try:
                    posts = profile[field]
                    if isinstance(posts, str):
                        posts = json.loads(posts)
                    if isinstance(posts, list):
                        quality['post_count'] = len(posts)
                        if len(posts) > 0:
                            score += 10
                        if len(posts) >= 5:
                            score += 5
                        break
                except:
                    pass

        quality['completeness_score'] = score

        # Determine engagement level
        if quality['post_count'] >= 10:
            quality['engagement_level'] = 'High'
        elif quality['post_count'] >= 5:
            quality['engagement_level'] = 'Medium'
        elif quality['post_count'] > 0:
            quality['engagement_level'] = 'Low'
        else:
            quality['engagement_level'] = 'None'

        return quality

    def calculate_intro_score(self, connection: Dict, profile_quality: Dict) -> float:
        """
        Calculate overall introduction score.

        Factors:
        - Recency: 40% (current vs alumni, how recent)
        - Seniority: 30% (higher = better connector)
        - Profile Quality: 20% (more active = better)
        - Engagement: 10% (posts, activity)
        """
        recency_weight = 0.4
        seniority_weight = 0.3
        quality_weight = 0.2
        engagement_weight = 0.1

        # Recency score (0-1)
        recency_score = connection.get('recency_score', 0.5)

        # Seniority score (0-1, normalized from 0-7 scale)
        seniority_score = connection.get('seniority_score', 3) / 7.0

        # Quality score (0-1, normalized from 0-100 scale)
        quality_score = profile_quality.get('completeness_score', 50) / 100.0

        # Engagement score (0-1)
        post_count = profile_quality.get('post_count', 0)
        engagement_score = min(post_count / 10.0, 1.0)  # Cap at 10 posts

        # Calculate weighted total
        total_score = (
            recency_score * recency_weight +
            seniority_score * seniority_weight +
            quality_score * quality_weight +
            engagement_score * engagement_weight
        )

        return total_score

    def load_json_data(self, filepath: Path) -> List[Dict]:
        """Load data from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
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

        for json_file in self.data_dir.glob('*.json'):
            print(f"  Loading {json_file.name}...")
            profiles = self.load_json_data(json_file)
            self.profiles.extend(profiles)

        for csv_file in self.data_dir.glob('*.csv'):
            print(f"  Loading {csv_file.name}...")
            profiles = self.load_csv_data(csv_file)
            self.profiles.extend(profiles)

        print(f"✅ Loaded {len(self.profiles)} profiles\n")

    def extract_work_experience(self, profile: Dict) -> List[Dict]:
        """Extract work experience from a profile."""
        experiences = []
        work_fields = ['experience', 'experiences', 'work_experience',
                      'positions', 'employment', 'work_history']

        for field in work_fields:
            if field in profile:
                exp_data = profile[field]
                if isinstance(exp_data, list):
                    experiences = exp_data
                    break
                elif isinstance(exp_data, str):
                    try:
                        experiences = json.loads(exp_data)
                        if isinstance(experiences, list):
                            break
                    except:
                        pass

        return experiences

    def is_current_position(self, experience: Dict) -> bool:
        """Determine if a position is current."""
        end_date_fields = ['end_date', 'endDate', 'to', 'end']

        for field in end_date_fields:
            if field in experience:
                end_value = experience[field]
                if end_value is None or end_value == '':
                    return True
                if isinstance(end_value, str):
                    if end_value.lower() in ['present', 'current', 'now']:
                        return True

        if experience.get('is_current') or experience.get('isCurrent'):
            return True

        return False

    def process_profiles(self):
        """Process all profiles and build enriched company analytics."""
        print("🔍 Processing profiles with advanced analytics...")

        for idx, profile in enumerate(self.profiles):
            # Get profile identifiers
            profile_id = profile.get('id') or profile.get('profile_id') or str(idx)
            profile_name = profile.get('name') or profile.get('full_name') or profile.get('fullName') or f"Profile {idx}"
            profile_url = profile.get('url') or profile.get('profile_url') or profile.get('linkedin_url') or ''

            # Calculate profile quality
            profile_quality = self.calculate_profile_quality(profile)

            # Index the profile
            self.profile_index[profile_id] = {
                'name': profile_name,
                'url': profile_url,
                'profile': profile,
                'quality': profile_quality
            }

            # Extract and process work experiences
            experiences = self.extract_work_experience(profile)

            for exp in experiences:
                company_name = exp.get('company') or exp.get('company_name') or exp.get('companyName') or ''
                if not company_name:
                    continue

                normalized_name = self.normalize_company_name(company_name)
                title = exp.get('title') or exp.get('position') or ''

                # Detect seniority and departments
                seniority_level, seniority_score = self.detect_seniority(title)
                departments = self.detect_departments(title)

                # Parse dates
                start_date_str = exp.get('start_date') or exp.get('startDate') or exp.get('from') or ''
                end_date_str = exp.get('end_date') or exp.get('endDate') or exp.get('to') or ''

                start_date = self.parse_date(start_date_str)
                end_date = self.parse_date(end_date_str) if end_date_str else None

                # Determine if current and calculate recency
                is_current = self.is_current_position(exp)
                if is_current:
                    end_date = None

                recency_score = self.calculate_recency_score(end_date)

                # Build enriched connection record
                connection_record = {
                    'profile_id': profile_id,
                    'profile_name': profile_name,
                    'profile_url': profile_url,
                    'title': title,
                    'start_date': start_date_str,
                    'end_date': end_date_str,
                    'start_date_parsed': start_date,
                    'end_date_parsed': end_date,
                    'is_current': is_current,
                    'duration': exp.get('duration') or '',
                    'description': exp.get('description') or '',
                    'seniority_level': seniority_level,
                    'seniority_score': seniority_score,
                    'departments': departments,
                    'recency_score': recency_score,
                    'profile_quality': profile_quality,
                    'intro_score': 0.0  # Will calculate after
                }

                # Calculate intro score
                connection_record['intro_score'] = self.calculate_intro_score(connection_record, profile_quality)

                # Add to company analytics
                company_key = normalized_name
                self.company_analytics[company_key]['company_name'] = company_name
                self.company_analytics[company_key]['normalized_name'] = normalized_name

                if is_current:
                    self.company_analytics[company_key]['current_employees'].append(connection_record)
                    self.company_analytics[company_key]['total_current'] += 1
                else:
                    self.company_analytics[company_key]['past_employees'].append(connection_record)
                    self.company_analytics[company_key]['total_past'] += 1

                self.company_analytics[company_key]['all_connections'].append(connection_record)

        # Sort connections by intro score for each company
        for company_key, data in self.company_analytics.items():
            data['all_connections'].sort(key=lambda x: x['intro_score'], reverse=True)
            data['best_intros'] = data['all_connections'][:10]  # Top 10 best intro paths

        print(f"✅ Processed {len(self.profiles)} profiles")
        print(f"✅ Found {len(self.company_analytics)} unique companies\n")

    def generate_introduction_report(self, company_name: str) -> Dict:
        """Generate detailed introduction intelligence for a specific company."""
        normalized = self.normalize_company_name(company_name)

        if normalized not in self.company_analytics:
            return {'error': f"Company '{company_name}' not found in network"}

        data = self.company_analytics[normalized]

        return {
            'company_name': data['company_name'],
            'total_connections': len(data['all_connections']),
            'current_employees': data['total_current'],
            'past_employees': data['total_past'],
            'best_intro_paths': data['best_intros'],
            'by_department': self._group_by_department(data['all_connections']),
            'by_seniority': self._group_by_seniority(data['all_connections'])
        }

    def _group_by_department(self, connections: List[Dict]) -> Dict:
        """Group connections by department."""
        by_dept = defaultdict(list)
        for conn in connections:
            for dept in conn['departments']:
                by_dept[dept].append(conn)
        return dict(by_dept)

    def _group_by_seniority(self, connections: List[Dict]) -> Dict:
        """Group connections by seniority level."""
        by_seniority = defaultdict(list)
        for conn in connections:
            by_seniority[conn['seniority_level']].append(conn)
        return dict(by_seniority)

    def export_company_intelligence(self, company_name: str, output_file: str = None):
        """Export detailed introduction intelligence for a company."""
        intel = self.generate_introduction_report(company_name)

        if 'error' in intel:
            print(f"❌ {intel['error']}")
            return

        if not output_file:
            safe_name = "".join(c if c.isalnum() else '_' for c in company_name)
            output_file = f"Linkedin/intro_intel_{safe_name}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(intel, f, indent=2, default=str, ensure_ascii=False)

        print(f"✅ Exported introduction intelligence to {output_file}")

    def export_master_intelligence(self, output_dir: str = "Linkedin/enriched_advanced"):
        """Export detailed intelligence for all companies."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"💾 Exporting advanced introduction intelligence...")

        for company_key, data in self.company_analytics.items():
            safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_'
                              for c in data['company_name'])
            safe_name = safe_name[:100]

            company_file = output_path / f"{safe_name}.json"

            export_data = {
                'company_name': data['company_name'],
                'normalized_name': data['normalized_name'],
                'statistics': {
                    'total_connections': len(data['all_connections']),
                    'current_employees': data['total_current'],
                    'past_employees': data['total_past']
                },
                'best_intro_paths': data['best_intros'][:5],  # Top 5
                'current_employees': data['current_employees'],
                'past_employees': data['past_employees'],
                'by_department': self._group_by_department(data['all_connections']),
                'by_seniority': self._group_by_seniority(data['all_connections'])
            }

            with open(company_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str, ensure_ascii=False)

        print(f"✅ Exported {len(self.company_analytics)} company intelligence files\n")

    def export_introduction_csv(self, output_file: str = "Linkedin/introduction_intelligence.csv"):
        """Export CSV with introduction recommendations."""
        print(f"💾 Exporting introduction intelligence CSV...")

        rows = []
        for company_key, data in self.company_analytics.items():
            for conn in data['best_intros']:
                rows.append({
                    'Company': data['company_name'],
                    'Intro Score': f"{conn['intro_score']:.2f}",
                    'Status': 'Current' if conn['is_current'] else 'Past',
                    'Recency Score': f"{conn['recency_score']:.2f}",
                    'Contact Name': conn['profile_name'],
                    'Contact Profile': conn['profile_url'],
                    'Title': conn['title'],
                    'Seniority': conn['seniority_level'],
                    'Seniority Score': conn['seniority_score'],
                    'Departments': ', '.join(conn['departments']),
                    'Profile Quality': f"{conn['profile_quality']['completeness_score']}/100",
                    'Engagement': conn['profile_quality']['engagement_level'],
                    'Start Date': conn['start_date'],
                    'End Date': conn['end_date'] or 'Present'
                })

        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False)
        print(f"✅ Exported introduction intelligence to {output_file}\n")
        return df

    def print_top_intro_opportunities(self, top_n: int = 20):
        """Print the top companies with best introduction opportunities."""
        print(f"\n{'='*100}")
        print(f"🎯 TOP {top_n} COMPANIES FOR WARM INTRODUCTIONS")
        print(f"{'='*100}\n")

        # Sort companies by best intro score
        sorted_companies = sorted(
            self.company_analytics.items(),
            key=lambda x: x[1]['best_intros'][0]['intro_score'] if x[1]['best_intros'] else 0,
            reverse=True
        )[:top_n]

        print(f"{'Rank':<6}{'Company':<35}{'Curr':<6}{'Past':<6}{'Best Intro':<25}{'Score':<8}{'Level':<12}")
        print("-" * 100)

        for rank, (company_key, data) in enumerate(sorted_companies, 1):
            company_name = data['company_name'][:33]
            best = data['best_intros'][0] if data['best_intros'] else None

            if best:
                intro_name = best['profile_name'][:23]
                intro_score = f"{best['intro_score']:.2f}"
                seniority = best['seniority_level'][:10]
            else:
                intro_name = "N/A"
                intro_score = "0.00"
                seniority = "N/A"

            print(f"{rank:<6}{company_name:<35}{data['total_current']:<6}"
                  f"{data['total_past']:<6}{intro_name:<25}{intro_score:<8}{seniority:<12}")

        print("\n")

    def search_company(self, search_term: str):
        """Search for companies and show intro intelligence."""
        search_lower = search_term.lower()
        matches = []

        for company_key, data in self.company_analytics.items():
            if search_lower in data['company_name'].lower():
                matches.append(data)

        if not matches:
            print(f"❌ No companies found matching '{search_term}'")
            return

        print(f"\n🔍 Found {len(matches)} companies matching '{search_term}':\n")

        for data in matches:
            print(f"\n{'='*80}")
            print(f"🏢 {data['company_name']}")
            print(f"{'='*80}")
            print(f"  Total Connections: {len(data['all_connections'])}")
            print(f"  Current Employees: {data['total_current']}")
            print(f"  Past Employees: {data['total_past']}")
            print(f"\n  🎯 Best Introduction Paths:")

            for idx, intro in enumerate(data['best_intros'][:5], 1):
                status = "✅ CURRENT" if intro['is_current'] else f"📅 Left {intro['end_date'] or 'Unknown'}"
                print(f"\n  {idx}. {intro['profile_name']} - Score: {intro['intro_score']:.2f}")
                print(f"     {status}")
                print(f"     Title: {intro['title']}")
                print(f"     Seniority: {intro['seniority_level']} | Depts: {', '.join(intro['departments'])}")
                print(f"     Profile: {intro['profile_url']}")

            print("\n")

    def run_full_enrichment(self):
        """Run the complete advanced enrichment process."""
        print("\n" + "="*100)
        print("🚀 LINKEDIN ADVANCED INTRODUCTION INTELLIGENCE")
        print("="*100 + "\n")

        # Load profiles
        self.load_all_profiles()

        if not self.profiles:
            print("❌ No profiles found! Please add LinkedIn data files to the Linkedin directory.")
            return

        # Process profiles
        self.process_profiles()

        # Generate reports
        self.export_introduction_csv()
        self.export_master_intelligence()

        # Print top opportunities
        self.print_top_intro_opportunities(20)

        print("="*100)
        print("✅ ADVANCED ENRICHMENT COMPLETE!")
        print("="*100)
        print(f"\nGenerated files:")
        print(f"  📄 Linkedin/introduction_intelligence.csv - All introduction recommendations")
        print(f"  📁 Linkedin/enriched_advanced/ - Detailed intelligence for each company")
        print(f"\nTo search for a specific company:")
        print(f"  python -c 'from enrich_linkedin_advanced import *; intel = IntroductionIntelligence(); intel.load_all_profiles(); intel.process_profiles(); intel.search_company(\"Google\")'")
        print("\n")


def main():
    parser = argparse.ArgumentParser(description='LinkedIn Advanced Introduction Intelligence')
    parser.add_argument('--data-dir', default='Linkedin',
                       help='Directory containing LinkedIn data files')
    parser.add_argument('--search', type=str,
                       help='Search for a specific company')
    parser.add_argument('--top-n', type=int, default=20,
                       help='Number of top companies to display')

    args = parser.parse_args()

    intel = IntroductionIntelligence(data_dir=args.data_dir)
    intel.load_all_profiles()
    intel.process_profiles()

    if args.search:
        intel.search_company(args.search)
    else:
        intel.run_full_enrichment()


if __name__ == '__main__':
    main()
