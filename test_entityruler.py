#!/usr/bin/env python3
"""Test EntityRuler extraction."""
from src.extraction.spacy_pipeline import get_extraction_nlp

text = 'Microsoft Corporation operates in India and uses Azure cloud services with artificial intelligence.'
nlp = get_extraction_nlp()
doc = nlp(text)

print(f'Found {len(doc.ents)} entities:')
for ent in doc.ents:
    source = ent.ent_id_ if ent.ent_id_ else 'NER'
    print(f'  {ent.text:20s} ({ent.label_:12s}) - {source}')
