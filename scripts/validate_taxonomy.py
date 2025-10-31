"""
Comprehensive validation of taxonomy, heuristics, and NER rules.
Checks structure, data integrity, and relationships.
"""
import json
import os
import sys
from pathlib import Path
from collections import defaultdict

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

HEURISTICS_DIR = Path("Heuristics")

def validate_company_aliases():
    """Validate company aliases structure and deduplication."""
    print("\n[1] Validating Company Aliases...")
    
    with open(HEURISTICS_DIR / "company_aliases_clean.json", 'r', encoding='utf-8') as f:
        aliases = json.load(f)
    
    errors = []
    warnings = []
    
    # Check structure (dict: alias -> canonical)
    if not isinstance(aliases, dict):
        errors.append("Expected dict structure")
        return False, errors, warnings
    
    # Check duplicates in normalized form
    normalized_canonicals = defaultdict(set)
    for alias, canonical in aliases.items():
        normalized = alias.lower().strip()
        normalized_canonicals[normalized].add(canonical)
    
    duplicates = {k: v for k, v in normalized_canonicals.items() if len(v) > 1}
    if duplicates:
        warnings.append(f"Normalized duplicates: {len(duplicates)}")
    
    # Check empty values
    empty_values = [k for k, v in aliases.items() if not v]
    if empty_values:
        errors.append(f"Empty canonical values: {len(empty_values)}")
    
    print(f"  ✓ Structure: dict")
    print(f"  ✓ Total aliases: {len(aliases)}")
    print(f"  ✓ Unique canonical forms: {len(set(aliases.values()))}")
    if warnings:
        print(f"  ⚠ {', '.join(warnings)}")
    
    return len(errors) == 0, errors, warnings

def validate_countries():
    """Validate countries structure and ISO codes."""
    print("\n[2] Validating Countries...")
    
    with open(HEURISTICS_DIR / "countries.json", 'r', encoding='utf-8') as f:
        countries = json.load(f)
    
    errors = []
    warnings = []
    
    # Check structure (list of dicts)
    if not isinstance(countries, list):
        errors.append("Expected list structure")
        return False, errors, warnings
    
    # Validate each country
    iso_codes = set()
    for country in countries:
        if not isinstance(country, dict):
            errors.append("Each country must be a dict")
            continue
        
        required_fields = ['name', 'code']
        for field in required_fields:
            if field not in country:
                errors.append(f"Missing required field: {field}")
        
        # Check ISO code uniqueness
        if 'code' in country:
            code = country['code']
            if code in iso_codes:
                warnings.append(f"Duplicate ISO code: {code}")
            iso_codes.add(code)
    
    print(f"  ✓ Structure: list")
    print(f"  ✓ Total countries: {len(countries)}")
    print(f"  ✓ Unique ISO codes: {len(iso_codes)}")
    if warnings:
        print(f"  ⚠ {', '.join(warnings)}")
    
    return len(errors) == 0, errors, warnings

def validate_tech_terms():
    """Validate tech terms structure and context arrays."""
    print("\n[3] Validating Tech Terms...")
    
    with open(HEURISTICS_DIR / "tech_terms.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tech_terms = data.get('tech_terms', [])
    
    errors = []
    warnings = []
    
    # Check structure
    if not isinstance(tech_terms, list):
        errors.append("Expected tech_terms array")
        return False, errors, warnings
    
    # Validate each term
    canonicals = set()
    for term in tech_terms:
        if not isinstance(term, dict):
            errors.append("Each term must be a dict")
            continue
        
        required_fields = ['term', 'canonical', 'confidence_base', 'synonyms', 'context_boosters', 'context_detractors']
        for field in required_fields:
            if field not in term:
                errors.append(f"Missing required field: {field}")
        
        # Check canonical uniqueness
        if 'canonical' in term:
            canonical = term['canonical']
            if canonical in canonicals:
                warnings.append(f"Duplicate canonical: {canonical}")
            canonicals.add(canonical)
        
        # Check confidence range
        if 'confidence_base' in term:
            conf = term['confidence_base']
            if not 0 <= conf <= 1:
                errors.append(f"Invalid confidence: {conf}")
        
        # Check arrays
        for array_field in ['synonyms', 'context_boosters', 'context_detractors']:
            if array_field in term and not isinstance(term[array_field], list):
                errors.append(f"{array_field} must be a list")
    
    print(f"  ✓ Structure: list")
    print(f"  ✓ Total terms: {len(tech_terms)}")
    print(f"  ✓ Unique canonicals: {len(canonicals)}")
    if warnings:
        print(f"  ⚠ {', '.join(warnings)}")
    
    return len(errors) == 0, errors, warnings

def validate_taxonomy_industries():
    """Validate industry taxonomy hierarchy."""
    print("\n[4] Validating Taxonomy Industries...")
    
    with open(HEURISTICS_DIR / "taxonomy_industries.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    industries = data.get('industries', [])
    
    errors = []
    warnings = []
    
    # Check structure
    if not isinstance(industries, list):
        errors.append("Expected industries array")
        return False, errors, warnings
    
    # Build hierarchy map
    by_id = {}
    by_parent = defaultdict(list)
    
    for industry in industries:
        if not isinstance(industry, dict):
            errors.append("Each industry must be a dict")
            continue
        
        required_fields = ['id', 'name', 'level', 'path']
        for field in required_fields:
            if field not in industry:
                errors.append(f"Missing required field: {field}")
        
        # Check ID uniqueness
        industry_id = industry.get('id')
        if industry_id:
            if industry_id in by_id:
                warnings.append(f"Duplicate ID: {industry_id}")
            by_id[industry_id] = industry
        
        # Check parent references
        parent_id = industry.get('parent_id')
        if parent_id:
            by_parent[parent_id].append(industry_id)
    
    # Validate parent references exist
    for industry in industries:
        parent_id = industry.get('parent_id')
        if parent_id and parent_id not in by_id:
            errors.append(f"Invalid parent_id: {parent_id}")
    
    # Validate level matches path length
    for industry in industries:
        level = industry.get('level', 0)
        path = industry.get('path', [])
        if isinstance(path, list) and len(path) != level:
            warnings.append(f"Level mismatch for {industry.get('id')}: level={level}, path_len={len(path)}")
    
    print(f"  ✓ Structure: list")
    print(f"  ✓ Total industries: {len(industries)}")
    print(f"  ✓ Root industries: {len([i for i in industries if i.get('parent_id') is None])}")
    if warnings:
        print(f"  ⚠ {len(warnings)} warnings")
    
    return len(errors) == 0, errors, warnings

def validate_taxonomy_services():
    """Validate service taxonomy hierarchy."""
    print("\n[5] Validating Taxonomy Services...")
    
    with open(HEURISTICS_DIR / "taxonomy_services.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    services = data.get('services', [])
    
    errors = []
    warnings = []
    
    # Check structure
    if not isinstance(services, list):
        errors.append("Expected services array")
        return False, errors, warnings
    
    # Build hierarchy map
    by_id = {}
    
    for service in services:
        if not isinstance(service, dict):
            errors.append("Each service must be a dict")
            continue
        
        required_fields = ['id', 'name', 'level', 'path']
        for field in required_fields:
            if field not in service:
                errors.append(f"Missing required field: {field}")
        
        # Check ID uniqueness
        service_id = service.get('id')
        if service_id:
            if service_id in by_id:
                warnings.append(f"Duplicate ID: {service_id}")
            by_id[service_id] = service
    
    print(f"  ✓ Structure: list")
    print(f"  ✓ Total services: {len(services)}")
    print(f"  ✓ Root services: {len([s for s in services if s.get('parent_id') is None])}")
    if warnings:
        print(f"  ⚠ {len(warnings)} warnings")
    
    return len(errors) == 0, errors, warnings

def validate_products():
    """Validate products taxonomy."""
    print("\n[6] Validating Products...")
    
    with open(HEURISTICS_DIR / "products.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    products = data.get('products', [])
    
    errors = []
    warnings = []
    
    # Check structure
    if not isinstance(products, list):
        errors.append("Expected products array")
        return False, errors, warnings
    
    # Validate each product
    names = set()
    for product in products:
        if not isinstance(product, dict):
            errors.append("Each product must be a dict")
            continue
        
        required_fields = ['name', 'category', 'canonical', 'confidence_base']
        for field in required_fields:
            if field not in product:
                errors.append(f"Missing required field: {field}")
        
        # Check name uniqueness
        if 'name' in product:
            name = product['name']
            if name in names:
                warnings.append(f"Duplicate product name: {name}")
            names.add(name)
        
        # Check confidence range
        if 'confidence_base' in product:
            conf = product['confidence_base']
            if not 0 <= conf <= 1:
                errors.append(f"Invalid confidence: {conf}")
    
    print(f"  ✓ Structure: list")
    print(f"  ✓ Total products: {len(products)}")
    print(f"  ✓ Unique names: {len(names)}")
    if warnings:
        print(f"  ⚠ {len(warnings)} warnings")
    
    return len(errors) == 0, errors, warnings

def validate_partnerships():
    """Validate partnerships taxonomy."""
    print("\n[7] Validating Partnerships...")
    
    with open(HEURISTICS_DIR / "partnerships.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    relationships = data.get('relationships', [])
    
    errors = []
    warnings = []
    
    # Check structure
    if not isinstance(relationships, list):
        errors.append("Expected relationships array")
        return False, errors, warnings
    
    # Validate each relationship
    types = set()
    for rel in relationships:
        if not isinstance(rel, dict):
            errors.append("Each relationship must be a dict")
            continue
        
        required_fields = ['relationship_type', 'confidence']
        for field in required_fields:
            if field not in rel:
                errors.append(f"Missing required field: {field}")
        
        # Check type uniqueness
        if 'relationship_type' in rel:
            rel_type = rel['relationship_type']
            if rel_type in types:
                warnings.append(f"Duplicate relationship type: {rel_type}")
            types.add(rel_type)
        
        # Check confidence range
        if 'confidence' in rel:
            conf = rel['confidence']
            if not 0 <= conf <= 1:
                errors.append(f"Invalid confidence: {conf}")
    
    print(f"  ✓ Structure: list")
    print(f"  ✓ Total relationship types: {len(relationships)}")
    print(f"  ✓ Unique types: {len(types)}")
    if warnings:
        print(f"  ⚠ {len(warnings)} warnings")
    
    return len(errors) == 0, errors, warnings

def validate_ner_relationships():
    """Validate NER relationship patterns."""
    print("\n[8] Validating NER Relationships...")
    
    with open(HEURISTICS_DIR / "ner_relationships.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    errors = []
    warnings = []
    
    # Check structure (dict with keys: entities, relationships, relationship_strings)
    if not isinstance(data, dict):
        errors.append("Expected dict structure")
        return False, errors, warnings
    
    # Check required keys
    required_keys = ['entities', 'relationships', 'relationship_strings']
    for key in required_keys:
        if key not in data:
            warnings.append(f"Missing key: {key}")
    
    print(f"  ✓ Structure: dict")
    print(f"  ✓ Keys: {list(data.keys())}")
    if warnings:
        print(f"  ⚠ {', '.join(warnings)}")
    
    return len(errors) == 0, errors, warnings

def main():
    """Run all validations."""
    print("=" * 70)
    print("BPO Intelligence - Comprehensive Taxonomy Validation")
    print("=" * 70)
    
    results = []
    
    # Run all validations
    results.append(("Company Aliases", validate_company_aliases()))
    results.append(("Countries", validate_countries()))
    results.append(("Tech Terms", validate_tech_terms()))
    results.append(("Taxonomy Industries", validate_taxonomy_industries()))
    results.append(("Taxonomy Services", validate_taxonomy_services()))
    results.append(("Products", validate_products()))
    results.append(("Partnerships", validate_partnerships()))
    results.append(("NER Relationships", validate_ner_relationships()))
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for name, (success, errors, warnings) in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}  {name}")
        if errors:
            for error in errors[:3]:  # Show first 3 errors
                print(f"      ERROR: {error}")
        if warnings and len(warnings) <= 3:
            for warning in warnings:
                print(f"      WARNING: {warning}")
        elif warnings:
            print(f"      WARNING: {len(warnings)} warnings")
        
        if success:
            passed += 1
        else:
            failed += 1
    
    print("=" * 70)
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
    print("=" * 70)
    
    return failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

