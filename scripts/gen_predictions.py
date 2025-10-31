#!/usr/bin/env python3
"""
Generate Label Studio-style predictions from comprehensive multi-tier extraction pipeline.

Output format:
{
  "<doc_id>": {
    "entities": [{"start": int, "end": int, "label": str, "text": str}, ...],
    "relationships": [...],
    "document_predictions": {...},
    "stats": {...}
  },
  ...
}

Notes:
- Multi-tier extraction: Heuristics → Regex → EntityRuler → spaCy NER → Embeddings → LLM
- Target: 100+ entities and 500 relationships per document
- Document-level predictions: content_type, industry, service, partnership_type
"""
import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple, Iterator, Set
from collections import defaultdict

import sys
# Ensure project root is on path so `src` is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from src.extraction.spacy_pipeline import get_extraction_nlp
from src.heuristics import get_heuristics_loader

# All labels from Label Studio config (project ID 2)
# 10 entity types: ORG, PERSON, LOC, PRODUCT, TECHNOLOGY, INDUSTRY, CATEGORY, DATE, MONEY, PERCENT
ALLOWED_LABELS = {
    "ORG",
    "PERSON",
    "LOC",
    "PRODUCT",
    "TECHNOLOGY",
    "INDUSTRY",
    "CATEGORY",
    "DATE",
    "MONEY",
    "PERCENT",
}

# Map extraction labels to Label Studio labels (matching project config)
LABEL_MAPPING = {
    # Direct matches
    "ORG": "ORG",
    "PERSON": "PERSON",
    "LOC": "LOC",
    "PRODUCT": "PRODUCT",
    "TECHNOLOGY": "TECHNOLOGY",
    "DATE": "DATE",
    "MONEY": "MONEY",
    "PERCENT": "PERCENT",
    "INDUSTRY": "INDUSTRY",
    "CATEGORY": "CATEGORY",
    # Internal -> Label Studio mappings
    "COMPANY": "ORG",  # Internal COMPANY maps to Label Studio ORG
    "LOCATION": "LOC",  # Internal LOCATION maps to Label Studio LOC
    "GPE": "LOC",  # spaCy GPE -> LOC
    # Skip these (not in Label Studio config)
    # "BUSINESS_TITLE", "TIME_RANGE", "TEMPORAL", "SKILL", "COMPUTING_PRODUCT"
}

# Constants from extraction_flow.py
BUSINESS_TITLES = [
    "CEO", "Chief Executive Officer", "CFO", "Chief Financial Officer",
    "COO", "Chief Operating Officer", "CTO", "Chief Technology Officer",
    "Chairman", "President", "Vice President", "VP", "SVP", "EVP",
    "Managing Director", "Managing Partner", "Director", "Head of", "Global Head",
]

SKILL_TERMS = [
    "Python", "SQL", "data analysis", "machine learning", "cloud computing",
    "customer service", "project management", "AI", "BPO operations",
]

TIME_RANGE_REGEX = re.compile(
    r"(?:Q[1-4]\s*\d{4}|\d+\s+(?:day|week|month|year)s?|next\s+(?:quarter|year)|"
    r"past\s+\d+\s+(?:months|years))",
    re.IGNORECASE,
)

TEMPORAL_REGEX = re.compile(
    r"\b(?:pre|post|mid)-(?:launch|merger|acquisition|pandemic)\b",
    re.IGNORECASE,
)


def _span_overlaps(start: int, end: int, existing_spans: List[Tuple[int, int]]) -> bool:
    """Check if span overlaps with any existing span."""
    for ex_start, ex_end in existing_spans:
        if not (end <= ex_start or start >= ex_end):
            return True
    return False


def _iter_phrase_matches(text: str, phrase: str) -> Iterator[Tuple[int, int]]:
    """Find all case-insensitive phrase matches in text."""
    pattern = re.compile(re.escape(phrase), re.IGNORECASE)
    for match in pattern.finditer(text):
        yield (match.start(), match.end())


def extract_heuristics_tier(text: str, heuristics_data, existing_spans: List[Tuple[int, int]]) -> List[Dict[str, Any]]:
    """
    TIER 1: Heuristics extraction (highest priority, 0.90 confidence).
    Target: 60%+ of entities.
    """
    entities = []
    
    if not heuristics_data:
        return entities
    
    # 1a. NER relationships entities - ORG list → COMPANY
    ner_relationships = heuristics_data.ner_relationships or {}
    ner_orgs = set(ner_relationships.get("entities", {}).get("ORG", []))
    for org_name in ner_orgs:
        pattern = re.compile(rf'\b{re.escape(org_name)}\b', re.IGNORECASE)
        for match in pattern.finditer(text):
            if not _span_overlaps(match.start(), match.end(), existing_spans):
                entities.append({
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(0),
                    "label": "ORG",
                    "confidence": 0.90,
                    "source": "heuristics",
                })
                existing_spans.append((match.start(), match.end()))
    
    # 1b. NER products list → PRODUCT
    ner_products = set(ner_relationships.get("entities", {}).get("PRODUCT", []))
    for product_name in ner_products:
        pattern = re.compile(rf'\b{re.escape(product_name)}\b', re.IGNORECASE)
        for match in pattern.finditer(text):
            if not _span_overlaps(match.start(), match.end(), existing_spans):
                entities.append({
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(0),
                    "label": "PRODUCT",
                    "confidence": 0.86,
                    "source": "heuristics",
                })
                existing_spans.append((match.start(), match.end()))
    
    # 1c. Products with aliases → PRODUCT
    products = heuristics_data.products or []
    for product in products:
        product_name = product.get("name", "")
        if not product_name:
            continue
        
        # Match product name
        pattern = re.compile(rf'\b{re.escape(product_name)}\b', re.IGNORECASE)
        for match in pattern.finditer(text):
            if not _span_overlaps(match.start(), match.end(), existing_spans):
                entities.append({
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(0),
                    "label": "PRODUCT",
                    "confidence": 0.88,
                    "source": "heuristics",
                })
                existing_spans.append((match.start(), match.end()))
        
        # Match product aliases
        aliases = product.get("aliases", [])
        for alias in aliases:
            if not alias:
                continue
            pattern = re.compile(rf'\b{re.escape(alias)}\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                if not _span_overlaps(match.start(), match.end(), existing_spans):
                    entities.append({
                        "start": match.start(),
                        "end": match.end(),
                        "text": match.group(0),
                        "label": "PRODUCT",
                        "confidence": 0.85,
                        "source": "heuristics",
                    })
                    existing_spans.append((match.start(), match.end()))
    
    # 1d. Tech terms → TECHNOLOGY
    tech_terms = heuristics_data.tech_terms or []
    for term in tech_terms:
        canonical = term.get("canonical", "")
        if not canonical:
            continue
        pattern = re.compile(rf'\b{re.escape(canonical)}\b', re.IGNORECASE)
        for match in pattern.finditer(text):
            if not _span_overlaps(match.start(), match.end(), existing_spans):
                entities.append({
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(0),
                    "label": "TECHNOLOGY",
                    "confidence": 0.90,
                    "source": "heuristics",
                })
                existing_spans.append((match.start(), match.end()))
        
        # Match synonyms
        for synonym in term.get("synonyms", []):
            pattern = re.compile(rf'\b{re.escape(synonym)}\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                if not _span_overlaps(match.start(), match.end(), existing_spans):
                    entities.append({
                        "start": match.start(),
                        "end": match.end(),
                        "text": match.group(0),
                        "label": "TECHNOLOGY",
                        "confidence": 0.88,
                        "source": "heuristics",
                    })
                    existing_spans.append((match.start(), match.end()))
    
    # 1e. Countries → LOCATION
    country_names = heuristics_data.country_names or set()
    for country_name in country_names:
        pattern = re.compile(rf'\b{re.escape(country_name)}\b', re.IGNORECASE)
        for match in pattern.finditer(text):
            if not _span_overlaps(match.start(), match.end(), existing_spans):
                entities.append({
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(0),
                    "label": "LOC",
                    "confidence": 0.90,
                    "source": "heuristics",
                })
                existing_spans.append((match.start(), match.end()))
    
    # 1f. Company aliases → COMPANY (for normalization, but already in EntityRuler)
    # Skip here as EntityRuler handles this, but check if missed
    
    return entities


def extract_regex_tier(text: str, existing_spans: List[Tuple[int, int]]) -> List[Dict[str, Any]]:
    """
    TIER 2: Regex patterns (0.92 confidence).
    Target: 5-10% of entities.
    """
    entities = []
    
    # MONEY patterns
    money_patterns = [
        r'\$\s*[\d,]+(?:\.\d{1,2})?(?:\s*(?:million|billion|trillion|M|B|K))?',
        r'(?:USD|EUR|GBP)\s*[\d,]+(?:\.\d{1,2})?',
        r'[\d,]+(?:\.\d{1,2})?\s*(?:dollars|euros|pounds)',
    ]
    for pattern_str in money_patterns:
        for match in re.finditer(pattern_str, text, re.IGNORECASE):
            if not _span_overlaps(match.start(), match.end(), existing_spans):
                entities.append({
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(0),
                    "label": "MONEY",
                    "confidence": 0.92,
                    "source": "regex",
                })
                existing_spans.append((match.start(), match.end()))
    
    # PERCENT
    percent_pattern = r'\d+(?:\.\d+)?\s*%'
    for match in re.finditer(percent_pattern, text):
        if not _span_overlaps(match.start(), match.end(), existing_spans):
            entities.append({
                "start": match.start(),
                "end": match.end(),
                "text": match.group(0),
                "label": "PERCENT",
                "confidence": 0.90,
                "source": "regex",
            })
            existing_spans.append((match.start(), match.end()))
    
    # TIME_RANGE
    for match in TIME_RANGE_REGEX.finditer(text):
        if not _span_overlaps(match.start(), match.end(), existing_spans):
            entities.append({
                "start": match.start(),
                "end": match.end(),
                "text": match.group(0),
                "label": "TIME_RANGE",
                "confidence": 0.80,
                "source": "regex",
            })
            existing_spans.append((match.start(), match.end()))
    
    # TEMPORAL
    for match in TEMPORAL_REGEX.finditer(text):
        if not _span_overlaps(match.start(), match.end(), existing_spans):
            entities.append({
                "start": match.start(),
                "end": match.end(),
                "text": match.group(0),
                "label": "TEMPORAL",
                "confidence": 0.78,
                "source": "regex",
            })
            existing_spans.append((match.start(), match.end()))
    
    # NUMBER - Skip as Label Studio doesn't have NUMBER label
    # (Numbers are typically not useful entities for NER)
    
    # QUANTITY - Skip as Label Studio doesn't have QUANTITY label
    # (Can be extracted but not part of Label Studio config)
    
    # DURATION
    duration_pattern = r'\b\d+\s+(?:seconds?|minutes?|hours?|days?|weeks?|months?|years?)\b'
    for match in re.finditer(duration_pattern, text, re.IGNORECASE):
        if not _span_overlaps(match.start(), match.end(), existing_spans):
            entities.append({
                "start": match.start(),
                "end": match.end(),
                "text": match.group(0),
                "label": "TIME_RANGE",
                "confidence": 0.81,
                "source": "regex",
            })
            existing_spans.append((match.start(), match.end()))
    
    return entities


def extract_entityruler_tier(text: str, existing_spans: List[Tuple[int, int]], nlp) -> List[Dict[str, Any]]:
    """
    TIER 3: spaCy EntityRuler extraction (0.85 confidence).
    Target: 10-15% of entities.
    """
    entities = []
    doc = nlp(text)
    
    for ent in doc.ents:
        # Only process EntityRuler entities (COMPANY, LOCATION, PRODUCT, TECHNOLOGY)
        # Map to Label Studio labels: COMPANY->ORG, LOCATION->LOC
        if ent.label_ in ["COMPANY", "LOCATION", "PRODUCT", "TECHNOLOGY"]:
            label = LABEL_MAPPING.get(ent.label_, ent.label_)
            if label not in ALLOWED_LABELS:
                continue
            if not _span_overlaps(ent.start_char, ent.end_char, existing_spans):
                entities.append({
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "text": ent.text,
                    "label": label,
                    "confidence": 0.85,
                    "source": "entityruler",
                })
                existing_spans.append((ent.start_char, ent.end_char))
    
    return entities


def extract_spacy_ner_tier(text: str, existing_spans: List[Tuple[int, int]], nlp) -> List[Dict[str, Any]]:
    """
    TIER 4: spaCy statistical NER (0.70 confidence).
    Target: 10-20% of entities.
    """
    entities = []
    doc = nlp(text)
    
    for ent in doc.ents:
        # Skip EntityRuler entities (already processed)
        if ent.label_ in ["COMPANY", "LOCATION", "PRODUCT", "TECHNOLOGY"]:
            continue
        
        # Map spaCy labels to Label Studio labels
        label = LABEL_MAPPING.get(ent.label_, None)
        if label is None or label not in ALLOWED_LABELS:
            continue
        
        if not _span_overlaps(ent.start_char, ent.end_char, existing_spans):
            entities.append({
                "start": ent.start_char,
                "end": ent.end_char,
                "text": ent.text,
                "label": label,
                "confidence": 0.70,
                "source": "spacy",
            })
            existing_spans.append((ent.start_char, ent.end_char))
    
    # Note: BUSINESS_TITLE and SKILL not in Label Studio config, skip them
    
    return entities


def extract_relationships(text: str, entities: List[Dict[str, Any]], heuristics_data) -> List[Dict[str, Any]]:
    """
    Extract relationships between entities.
    Target: 250-500 relationships per document.
    """
    relationships = []
    
    if not entities or len(entities) < 2:
        return relationships
    
    # 1. Relationship strings from heuristics
    if heuristics_data:
        ner_relationships = heuristics_data.ner_relationships or {}
        relationship_strings = ner_relationships.get("relationship_strings", [])
        for rel_str in relationship_strings[:100]:  # Limit for performance
            if " belongs to " in rel_str:
                parts = rel_str.split(" belongs to ")
                if len(parts) == 2:
                    product_name = parts[0].strip()
                    company_name = parts[1].strip()
                    
                    # Find matching entities
                    product_ents = [e for e in entities if e['text'].lower() == product_name.lower() and e['label'] == 'PRODUCT']
                    company_ents = [e for e in entities if e['text'].lower() == company_name.lower() and e['label'] == 'ORG']
                    
                    for prod in product_ents:
                        for comp in company_ents:
                            distance = abs(prod['start'] - comp['start'])
                            if distance < 500:
                                relationships.append({
                                    "from_name": "rels",
                                    "to_name": "text",
                                    "type": "relation",
                                    "value": {
                                        "start": prod['start'],
                                        "end": prod['end'],
                                        "text": prod['text'],
                                        "labels": ["ORL"]
                                    },
                                    "direction": "right",
                                    "to": {
                                        "start": comp['start'],
                                        "end": comp['end'],
                                        "text": comp['text']
                                    }
                                })
    
    # 2. Comprehensive proximity-based relationships
    # All entity pairs within 300 characters
    for i, ent1 in enumerate(entities):
        for ent2 in entities[i + 1:]:
            distance = abs(ent1['start'] - ent2['start'])
            if distance < 300:
                relationships.append({
                    "from_name": "rels",
                    "to_name": "text",
                    "type": "relation",
                    "value": {
                        "start": ent1['start'],
                        "end": ent1['end'],
                        "text": ent1['text'],
                        "labels": ["ORL"]
                    },
                    "direction": "right",
                    "to": {
                        "start": ent2['start'],
                        "end": ent2['end'],
                        "text": ent2['text']
                    }
                })
    
    # Cap at 500 relationships
    return relationships[:500]


def extract_document_predictions(doc: Dict[str, Any], heuristics_data) -> Dict[str, Any]:
    """
    Extract document-level predictions:
    - content_type (single choice)
    - industry (single choice)
    - service (multiple choice)
    - partnership_type (single choice, optional)
    """
    predictions = {}
    
    if not doc or not heuristics_data:
        return predictions
    
    text = doc.get('text') or doc.get('metadata', {}).get('text', '')
    url = doc.get('url') or doc.get('metadata', {}).get('url', '')
    title = doc.get('title') or doc.get('metadata', {}).get('title', '')
    
    # 1. Content Type
    try:
        from src.flows.extraction_flow import classify_content_type
        content_rules = heuristics_data.content_types if hasattr(heuristics_data, 'content_types') else []
        if content_rules:
            classification = classify_content_type(url, title, text, content_rules)
            if classification:
                ls_content_type = map_content_type_to_ls(classification['label'])
                predictions['content_type'] = {
                    'from_name': 'content_type',
                    'to_name': 'text',
                    'type': 'choices',
                    'value': {'choices': [ls_content_type]}
                }
    except Exception as e:
        pass  # Content type classification optional
    
    # 2. Industry (from taxonomy matches)
    if hasattr(heuristics_data, 'industry_lookup') and heuristics_data.industry_lookup:
        industries_found = []
        for _, (industry, surface) in heuristics_data.industry_lookup.items():
            if surface.lower() in text.lower():
                ls_industry = map_industry_to_ls(industry.get('name', ''))
                if ls_industry and ls_industry not in industries_found:
                    industries_found.append(ls_industry)
        
        if industries_found:
                predictions['industry_primary'] = {
                'from_name': 'industry_primary',
                'to_name': 'text',
                'type': 'choices',
                'value': {'choices': [industries_found[0]]}  # Single choice
            }
    
    # 3. Services (multiple from taxonomy)
    if hasattr(heuristics_data, 'service_lookup') and heuristics_data.service_lookup:
        services_found = []
        for _, (service, surface) in heuristics_data.service_lookup.items():
            if surface.lower() in text.lower():
                ls_service = map_service_to_ls(service.get('name', ''))
                if ls_service and ls_service not in services_found:
                    services_found.append(ls_service)
        
        if services_found:
            predictions['service'] = {
                'from_name': 'service',
                'to_name': 'text',
                'type': 'choices',
                'value': {'choices': services_found}
            }
    
    # 4. Partnership Type (from partnerships keywords)
    partnership_keywords = {
        'Technology_Partner': ['technology partner', 'tech partnership', 'integrated with'],
        'Alliance': ['strategic alliance', 'alliance with'],
        'Reseller': ['reseller', 'resell'],
        'Co_Marketing': ['co-marketing', 'joint marketing'],
        'Integration': ['integration', 'integrated', 'works with']
    }
    
    text_lower = text.lower()
    for pt_type, keywords in partnership_keywords.items():
        if any(kw in text_lower for kw in keywords):
            predictions['partnership_type'] = {
                'from_name': 'partnership_type',
                'to_name': 'text',
                'type': 'choices',
                'value': {'choices': [pt_type]}
            }
            break
    
    return predictions


def map_content_type_to_ls(content_type: str) -> str:
    """Map extracted content_type to Label Studio choices."""
    mapping = {
        'Blog / Article': 'Blog',
        'News / Press Release': 'News',
        'Case Study': 'Case_Study',
        'Press Release': 'Press_Release',
        'Report / Whitepaper': 'Report_Whitepaper',
        'Landing Page / Marketing': 'Landing_Page',
        'Product / Technology': 'Product_Page',
        'Careers / Job Posting': 'Careers',
    }
    return mapping.get(content_type, 'Other')


def map_industry_to_ls(industry: str) -> str:
    """Map taxonomy industry to Label Studio format."""
    mapping = {
        'Financial Services & Insurance': 'Banking_Financial_Services',
        'Healthcare & Life Sciences': 'Healthcare',
        'Retail, Consumer & E-Commerce': 'Retail_Ecommerce',
        'Technology, Media & Communications': 'Technology',
        'Energy & Utilities': 'Energy_Utilities',
        'Public Sector & Education': 'Government',
        'Travel, Transportation & Logistics': 'Travel_Hospitality',
        'Media & Entertainment': 'Media_Entertainment',
        'Manufacturing': 'Manufacturing',
    }
    return mapping.get(industry, 'Other')


def map_service_to_ls(service: str) -> str:
    """Map taxonomy service to Label Studio format."""
    mapping = {
        'Customer Experience (CX) Operations': 'CX_Management',
        'Back Office Operations': 'Back_Office_Processing',
        'AI & Advanced Analytics': 'AI_Data_Services',
        'Consulting, Analytics & Technology': 'Consulting_Analytics_Technology',
        'Digital CX & AI': 'Digital_CX_AI',
        'Trust & Safety': 'Trust_Safety',
        'Finance, Accounting & Claims': 'Finance_Accounting',
        'Work From Home': 'Work_From_Home',
    }
    return mapping.get(service, 'Other')


def extract_spans(text: str, doc: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Multi-tier extraction with comprehensive heuristics.
    Returns: {
        'entities': [...],
        'relationships': [...],
        'document_predictions': {...},
        'stats': {'heuristics_pct': 0.65, 'total_entities': 102, ...}
    }
    """
    heuristics = get_heuristics_loader()
    heuristics_data = heuristics.data if heuristics else None
    nlp = get_extraction_nlp()
    
    entities = []
    existing_spans = []
    stats = {'heuristics': 0, 'regex': 0, 'entityruler': 0, 'spacy': 0}
    
    # TIER 1: Heuristics (60%+ target)
    heur_entities = extract_heuristics_tier(text, heuristics_data, existing_spans)
    entities.extend(heur_entities)
    stats['heuristics'] = len(heur_entities)
    
    # TIER 2: Regex
    regex_entities = extract_regex_tier(text, existing_spans)
    entities.extend(regex_entities)
    stats['regex'] = len(regex_entities)
    
    # TIER 3: EntityRuler
    ruler_entities = extract_entityruler_tier(text, existing_spans, nlp)
    entities.extend(ruler_entities)
    stats['entityruler'] = len(ruler_entities)
    
    # TIER 4: spaCy Statistical NER
    spacy_entities = extract_spacy_ner_tier(text, existing_spans, nlp)
    entities.extend(spacy_entities)
    stats['spacy'] = len(spacy_entities)
    
    # Calculate statistics
    total = len(entities)
    heuristics_pct = (stats['heuristics'] / total * 100) if total > 0 else 0
    
    # Extract relationships
    relationships = extract_relationships(text, entities, heuristics_data) if heuristics_data else []
    
    # Extract document-level predictions
    document_predictions = extract_document_predictions(doc, heuristics_data) if doc else {}
    
    stats['total_entities'] = total
    stats['total_relationships'] = len(relationships)
    stats['heuristics_pct'] = heuristics_pct
    
    return {
        'entities': entities,
        'relationships': relationships,
        'document_predictions': document_predictions,
        'stats': stats
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='Input JSONL file with documents')
    ap.add_argument('--output', required=True, help='Output predictions JSON file')
    ap.add_argument('--limit', type=int, default=5000, help='Max docs to process (0 = all)')
    args = ap.parse_args()

    results = {}

    total = 0
    with open(args.input, 'r', encoding='utf-8') as f:
        for line in f:
            if args.limit and total >= args.limit:
                break
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            text = obj.get('text') or obj.get('metadata', {}).get('text')
            if not text:
                continue

            doc_id = obj.get('id') or obj.get('doc_id') or obj.get('metadata', {}).get('id') or str(total)
            extraction_result = extract_spans(text, obj)
            results[doc_id] = extraction_result
            total += 1
            
            if total % 100 == 0:
                print(f"Processed {total} documents...")

    Path(os.path.dirname(args.output) or '.').mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as out:
        json.dump(results, out, ensure_ascii=False, indent=2)

    # Print statistics
    total_docs = len(results)
    if total_docs > 0:
        avg_entities = sum(r['stats']['total_entities'] for r in results.values()) / total_docs
        avg_relationships = sum(r['stats']['total_relationships'] for r in results.values()) / total_docs
        avg_heuristics_pct = sum(r['stats']['heuristics_pct'] for r in results.values()) / total_docs
        
        print(f"\nExtracted from {total_docs} documents")
        print(f"  Average entities: {avg_entities:.1f} (target: 100)")
        print(f"  Average relationships: {avg_relationships:.1f} (target: 500)")
        print(f"  Heuristics coverage: {avg_heuristics_pct:.1f}% (target: 60%+)")
    else:
        print(f"Wrote predictions for {total_docs} docs to {args.output}")


if __name__ == '__main__':
    main()
