"""
Consolidate taxonomy backup data from Heuristics/Taxonomy folder into main Heuristics structure.
Deduplicates entries, creates new taxonomy files, and updates version tracking.
"""
import json
import re
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Set, Any

# Paths
TAXONOMY_DIR = Path("Heuristics/Taxonomy")
HEURISTICS_DIR = Path("Heuristics")
SCRIPTS_DIR = Path("scripts")

def parse_sql_insert(filename: str) -> List[Dict[str, Any]]:
    """Parse SQL INSERT statement into list of dicts using regex."""
    sql_path = TAXONOMY_DIR / filename
    if not sql_path.exists():
        print(f"[WARN] {filename} not found")
        return []
    
    with open(sql_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    parsed_rows = []
    
    # Split into individual INSERT values
    # Remove INSERT INTO clause, extract VALUES tuples
    values_match = re.search(r'VALUES\s+(.+)$', content, re.DOTALL)
    if not values_match:
        return []
    
    values_str = values_match.group(1).strip()
    
    # Split by ), ( or ),( to get individual rows
    rows = re.split(r'\),\s*\(', values_str)
    
    for row in rows:
        # Remove surrounding parentheses
        row = row.strip('()')
        
        # Parse values handling escaped quotes ('',)
        values = []
        current = ""
        in_quotes = False
        
        i = 0
        while i < len(row):
            char = row[i]
            
            if char == "'":
                # Check if next char is also quote (escaped quote '')
                if i + 1 < len(row) and row[i + 1] == "'":
                    current += "'"
                    i += 2
                    continue
                else:
                    in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                # End of value
                clean = current.strip()
                if clean.startswith("'") and clean.endswith("'"):
                    clean = clean[1:-1]
                values.append(clean)
                current = ""
            else:
                current += char
            
            i += 1
        
        # Add last value
        if current.strip():
            clean = current.strip()
            if clean.startswith("'") and clean.endswith("'"):
                clean = clean[1:-1]
            values.append(clean)
        
        # Extract key fields based on filename
        if 'providers' in filename and len(values) >= 2:
            parsed_rows.append({
                'provider_name': values[1],
                'provider_type': values[2] if len(values) > 2 else 'Unknown'
            })
        elif 'products' in filename and len(values) >= 2:
            parsed_rows.append({
                'product_name': values[1],
                'category': values[2] if len(values) > 2 else 'Other',
                'description': values[3] if len(values) > 3 else ''
            })
        elif 'partnerships' in filename and len(values) >= 4:
            parsed_rows.append({
                'partnership_type': values[3],
                'description': values[4] if len(values) > 4 else ''
            })
    
    return parsed_rows

def normalize_company_name(name: str) -> str:
    """Normalize company name for deduplication."""
    if not name:
        return ""
    
    # Common suffixes to strip
    suffixes = [
        'Inc.', 'Inc', 'LLC', 'Ltd.', 'Ltd', 'Corporation', 'Corp.', 'Corp',
        'LLP', 'L.P.', 'LP', 'Limited', 'Co.', 'Company', 'Co'
    ]
    
    normalized = name.strip()
    for suffix in suffixes:
        # Match suffix at end of string (case insensitive)
        normalized = re.sub(
            r'\b' + re.escape(suffix) + r'\.?$',
            '',
            normalized,
            flags=re.IGNORECASE
        )
    
    # Strip extra whitespace and punctuation
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized.lower()

def merge_company_aliases():
    """Merge providers into company_aliases."""
    print("\n[1] Merging company aliases...")
    
    # Read existing aliases (dict: alias -> canonical)
    aliases_path = HEURISTICS_DIR / "company_aliases_clean.json"
    with open(aliases_path, 'r', encoding='utf-8') as f:
        existing_aliases = json.load(f)
    
    print(f"  Existing aliases: {len(existing_aliases)}")
    
    # Extract canonical forms
    canonicals = set(existing_aliases.values())
    
    # Build normalization map
    normalized_map = {}
    for alias, canonical in existing_aliases.items():
        normalized = normalize_company_name(alias)
        if normalized:
            normalized_map[normalized] = canonical
    
    # Parse providers
    providers = parse_sql_insert("providers_rows.sql")
    print(f"  Providers found: {len(providers)}")
    
    # Merge new providers
    added = 0
    for provider in providers:
        name = provider.get('provider_name', '').strip()
        if not name:
            continue
        
        normalized = normalize_company_name(name)
        
        if normalized and normalized not in normalized_map:
            # Add as both alias and canonical
            canonical = name  # Use provider name as canonical
            existing_aliases[name] = canonical
            existing_aliases[name.lower()] = canonical
            normalized_map[normalized] = canonical
            added += 1
    
    # Write updated aliases
    with open(aliases_path, 'w', encoding='utf-8') as f:
        json.dump(existing_aliases, f, indent=2, ensure_ascii=False)
    
    print(f"  Added: {added}, Total: {len(existing_aliases)}")
    return len(existing_aliases)

def merge_tech_terms():
    """Merge tech term synonyms."""
    print("\n[2] Merging tech terms...")
    
    # Read existing tech terms
    tech_path = HEURISTICS_DIR / "tech_terms.json"
    with open(tech_path, 'r', encoding='utf-8') as f:
        tech_data = json.load(f)
    
    # Extract tech_terms array
    existing_terms = tech_data.get('tech_terms', [])
    print(f"  Existing terms: {len(existing_terms)}")
    
    # Read backup data
    backup_path = TAXONOMY_DIR / "tech_terms_rows.json"
    if backup_path.exists():
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_content = f.read().strip()
            if backup_content:
                backup_terms = json.loads(backup_content)
                print(f"  Backup terms: {len(backup_terms)}")
                
                # Merge synonyms (already in existing structure)
                canonical_map = {term['canonical'].lower(): term for term in existing_terms}
                
                for backup_term in backup_terms:
                    if isinstance(backup_term, dict):
                        canonical = backup_term.get('canonical', '').lower()
                        if canonical in canonical_map:
                            # Add any new synonyms
                            existing_syns = set(canonical_map[canonical].get('synonyms', []))
                            backup_syns = set(backup_term.get('synonyms', []))
                            new_syns = backup_syns - existing_syns
                            if new_syns:
                                canonical_map[canonical]['synonyms'].extend(list(new_syns))
                                print(f"    Added synonyms to {canonical}: {new_syns}")
    
    # Update tech_data with merged terms
    tech_data['tech_terms'] = existing_terms
    
    # Write updated terms
    with open(tech_path, 'w', encoding='utf-8') as f:
        json.dump(tech_data, f, indent=2, ensure_ascii=False)
    
    print(f"  Final count: {len(existing_terms)}")
    return len(existing_terms)

def create_industries_taxonomy():
    """Create industries taxonomy file."""
    print("\n[3] Creating industries taxonomy...")
    
    industries_path = TAXONOMY_DIR / "taxonomy_industries_rows.json"
    if not industries_path.exists():
        print("  [ERROR] taxonomy_industries_rows.json not found")
        return 0
    
    with open(industries_path, 'r', encoding='utf-8') as f:
        industries_data = json.loads(f.read().strip())
    
    # Extract industries
    industries = []
    for item in industries_data:
        if isinstance(item, dict):
            industries.append({
                'id': item.get('id', ''),
                'name': item.get('name', ''),
                'description': item.get('description', ''),
                'level': item.get('level', 1),
                'parent_id': item.get('parent_id'),
                'path': item.get('path', [])
            })
    
    # Write taxonomy file
    output = {
        'version': '1.0.0',
        'updated_at': datetime.utcnow().isoformat() + 'Z',
        'count': len(industries),
        'industries': industries
    }
    
    with open(HEURISTICS_DIR / "taxonomy_industries.json", 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"  Created: {len(industries)} industries")
    return len(industries)

def create_services_taxonomy():
    """Create services taxonomy file."""
    print("\n[4] Creating services taxonomy...")
    
    services_path = TAXONOMY_DIR / "taxonomy_services_rows.json"
    if not services_path.exists():
        print("  [ERROR] taxonomy_services_rows.json not found")
        return 0
    
    with open(services_path, 'r', encoding='utf-8') as f:
        services_data = json.loads(f.read().strip())
    
    # Extract services
    services = []
    for item in services_data:
        if isinstance(item, dict):
            services.append({
                'id': item.get('id', ''),
                'name': item.get('name', ''),
                'description': item.get('description', ''),
                'level': item.get('level', 1),
                'parent_id': item.get('parent_id'),
                'path': item.get('path', [])
            })
    
    # Write taxonomy file
    output = {
        'version': '1.0.0',
        'updated_at': datetime.utcnow().isoformat() + 'Z',
        'count': len(services),
        'services': services
    }
    
    with open(HEURISTICS_DIR / "taxonomy_services.json", 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"  Created: {len(services)} services")
    return len(services)

def create_products_taxonomy():
    """Create products taxonomy file."""
    print("\n[5] Creating products taxonomy...")
    
    products = parse_sql_insert("products_rows.sql")
    
    # Normalize products
    normalized_products = []
    seen = set()
    
    for product in products:
        name = product.get('product_name', '').strip()
        if not name or name.lower() in seen:
            continue
        
        seen.add(name.lower())
        normalized_products.append({
            'name': name,
            'category': product.get('category', 'Other'),
            'description': product.get('description', ''),
            'canonical': name,
            'confidence_base': 0.85,
            'aliases': []
        })
    
    # Write taxonomy file
    output = {
        'version': '1.0.0',
        'updated_at': datetime.utcnow().isoformat() + 'Z',
        'count': len(normalized_products),
        'products': normalized_products
    }
    
    with open(HEURISTICS_DIR / "products.json", 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"  Created: {len(normalized_products)} products")
    return len(normalized_products)

def create_partnerships_taxonomy():
    """Create partnerships taxonomy file."""
    print("\n[6] Creating partnerships taxonomy...")
    
    partnerships = parse_sql_insert("partnerships_rows.sql")
    
    # Extract unique relationship types
    relationships = []
    seen_types = set()
    
    for partner in partnerships:
        rel_type = partner.get('partnership_type', '').strip()
        if rel_type and rel_type not in seen_types:
            seen_types.add(rel_type)
            relationships.append({
                'relationship_type': rel_type,
                'description': partner.get('description', ''),
                'confidence': 0.9
            })
    
    # Write taxonomy file
    output = {
        'version': '1.0.0',
        'updated_at': datetime.utcnow().isoformat() + 'Z',
        'count': len(relationships),
        'relationships': relationships
    }
    
    with open(HEURISTICS_DIR / "partnerships.json", 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"  Created: {len(relationships)} unique relationship types")
    return len(relationships)

def update_version_json(stats: Dict[str, int]):
    """Update version.json with new component counts."""
    print("\n[7] Updating version.json...")
    
    version_path = HEURISTICS_DIR / "version.json"
    with open(version_path, 'r', encoding='utf-8') as f:
        version_data = json.load(f)
    
    # Update version
    version_data['version'] = '2.0.0'
    version_data['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    version_data['description'] = 'Consolidated taxonomy backup data from Taxonomy folder'
    
    # Update component counts
    if 'company_aliases' in version_data['components']:
        version_data['components']['company_aliases']['count'] = stats.get('company_aliases', 0)
        version_data['components']['company_aliases']['last_updated'] = datetime.utcnow().isoformat() + 'Z'
    
    if 'tech_terms' in version_data['components']:
        version_data['components']['tech_terms']['count'] = stats.get('tech_terms', 0)
        version_data['components']['tech_terms']['last_updated'] = datetime.utcnow().isoformat() + 'Z'
    
    # Add new components
    version_data['components']['taxonomy_industries'] = {
        'file': 'taxonomy_industries.json',
        'count': stats.get('industries', 0),
        'last_updated': datetime.utcnow().isoformat() + 'Z'
    }
    
    version_data['components']['taxonomy_services'] = {
        'file': 'taxonomy_services.json',
        'count': stats.get('services', 0),
        'last_updated': datetime.utcnow().isoformat() + 'Z'
    }
    
    version_data['components']['products'] = {
        'file': 'products.json',
        'count': stats.get('products', 0),
        'last_updated': datetime.utcnow().isoformat() + 'Z'
    }
    
    version_data['components']['partnerships'] = {
        'file': 'partnerships.json',
        'count': stats.get('partnerships', 0),
        'last_updated': datetime.utcnow().isoformat() + 'Z'
    }
    
    # Add changelog entry
    changelog_entry = {
        'version': '2.0.0',
        'date': datetime.utcnow().strftime('%Y-%m-%d'),
        'changes': f"Consolidated taxonomy backup: industries ({stats.get('industries', 0)}), services ({stats.get('services', 0)}), products ({stats.get('products', 0)}), partnerships ({stats.get('partnerships', 0)}), providers merged into company_aliases"
    }
    if 'changelog' not in version_data:
        version_data['changelog'] = []
    version_data['changelog'].insert(0, changelog_entry)
    
    # Write updated version
    with open(version_path, 'w', encoding='utf-8') as f:
        json.dump(version_data, f, indent=2, ensure_ascii=False)
    
    print("  Version updated to 2.0.0")

def main():
    """Main consolidation process."""
    print("=" * 60)
    print("BPO Intelligence - Taxonomy Consolidation")
    print("=" * 60)
    
    # Ensure directories exist
    HEURISTICS_DIR.mkdir(exist_ok=True)
    
    # Execute consolidation steps
    stats = {}
    stats['company_aliases'] = merge_company_aliases()
    stats['tech_terms'] = merge_tech_terms()
    stats['industries'] = create_industries_taxonomy()
    stats['services'] = create_services_taxonomy()
    stats['products'] = create_products_taxonomy()
    stats['partnerships'] = create_partnerships_taxonomy()
    update_version_json(stats)
    
    print("\n" + "=" * 60)
    print("Consolidation complete!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  Company aliases: {stats['company_aliases']}")
    print(f"  Tech terms: {stats['tech_terms']}")
    print(f"  Industries: {stats['industries']}")
    print(f"  Services: {stats['services']}")
    print(f"  Products: {stats['products']}")
    print(f"  Partnerships: {stats['partnerships']}")
    print(f"\nNext steps:")
    print(f"  1. Run validation: python test_heuristics_simple.py")
    print(f"  2. Review output files in Heuristics/")
    print(f"  3. Delete Taxonomy folder after validation")

if __name__ == '__main__':
    main()

