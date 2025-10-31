import json
import os
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("BPO Intelligence - Heuristics Validation")
print("=" * 60)
print()

heuristics_dir = r"D:\BPO-Project\Heuristics"
files = {
    "Company Aliases": "company_aliases_clean.json",
    "Countries": "countries.json",
    "NER Relationships": "ner_relationships.json",
    "Tech Terms": "tech_terms.json",
    "Taxonomy Industries": "taxonomy_industries.json",
    "Taxonomy Services": "taxonomy_services.json",
    "Products": "products.json",
    "Partnerships": "partnerships.json",
    "Version": "version.json"
}

for name, filename in files.items():
    filepath = os.path.join(heuristics_dir, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                content = f.read().strip()
                if not content:
                    print(f"[!!] {name:20s}: FILE IS EMPTY")
                else:
                    data = json.loads(content)
                    
                    # Handle nested structures (taxonomy files)
                    if isinstance(data, dict) and 'count' in data:
                        count = data['count']
                    elif isinstance(data, dict) and 'industries' in data:
                        count = len(data['industries'])
                    elif isinstance(data, dict) and 'services' in data:
                        count = len(data['services'])
                    elif isinstance(data, dict) and 'products' in data:
                        count = len(data['products'])
                    elif isinstance(data, dict) and 'relationships' in data:
                        count = len(data['relationships'])
                    elif isinstance(data, dict) and 'tech_terms' in data:
                        count = len(data['tech_terms'])
                    else:
                        count = len(data) if isinstance(data, (list, dict)) else 0
                    
                    print(f"[OK] {name:20s}: {count:6d} items")
                    
                    # Show sample
                    if isinstance(data, dict) and count > 0:
                        if 'industries' in data:
                            sample = [data['industries'][0]['name']] if data['industries'] else []
                        elif 'services' in data:
                            sample = [data['services'][0]['name']] if data['services'] else []
                        elif 'products' in data:
                            sample = [data['products'][0]['name']] if data['products'] else []
                        elif 'relationships' in data:
                            sample = [data['relationships'][0]['relationship_type']] if data['relationships'] else []
                        elif 'tech_terms' in data:
                            sample = [data['tech_terms'][0]['term']] if data['tech_terms'] else []
                        else:
                            sample = list(data.keys())[:3]
                        print(f"     Sample: {', '.join(sample)}")
                    elif isinstance(data, list) and count > 0:
                        sample = data[:3]
                        print(f"     Sample: {sample}")
        except json.JSONDecodeError as e:
            print(f"[!!] {name:20s}: JSON ERROR - {str(e)}")
        except Exception as e:
            print(f"[!!] {name:20s}: ERROR - {str(e)}")
    else:
        print(f"[!!] {name:20s}: FILE NOT FOUND")
    print()

print("=" * 60)
print("Heuristics validation complete!")
print("=" * 60)

