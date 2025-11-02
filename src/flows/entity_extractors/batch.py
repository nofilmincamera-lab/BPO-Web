"""Entity extraction batch task."""
from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple
import json
import re

from prefect import task, get_run_logger

from src.heuristics import get_heuristics_loader

from ..constants import BUSINESS_TITLES, SKILL_TERMS, TEMPORAL_REGEX, TIME_RANGE_REGEX
from .utils import ensure_doc_id, iter_phrase_matches, span_overlaps
from ..relationship_extractor import build_relationships


@task(
    retries=2,
    retry_delay_seconds=5,
    cache_key_fn=lambda ctx, params: f"extract_{params['batch_id']}",
    persist_result=True,
    tags=["extraction", "ner"],
)
async def extract_entities_batch(
    batch: List[Dict[str, Any]],
    batch_id: str,
    heuristics_version: str,
) -> Dict[str, Any]:
    """Extract entities and relationships using comprehensive heuristics."""
    from src.extraction.spacy_pipeline import get_extraction_nlp

    logger = get_run_logger()
    logger.info(f"Processing batch {batch_id} with {len(batch)} documents")

    nlp = get_extraction_nlp()
    heuristics = get_heuristics_loader()
    heuristics_data = heuristics.data if heuristics else None
    industry_lookup = heuristics_data.industry_lookup if heuristics_data else {}
    service_lookup = heuristics_data.service_lookup if heuristics_data else {}
    taxonomy_version = heuristics_data.version if heuristics_data else "unknown"

    products = heuristics_data.products if heuristics_data else []
    ner_relationships = heuristics_data.ner_relationships if heuristics_data else {}
    partnerships = heuristics_data.partnerships if heuristics_data else []
    relationship_strings = ner_relationships.get("relationship_strings", [])
    ner_orgs = set(ner_relationships.get("entities", {}).get("ORG", []))
    ner_products = set(ner_relationships.get("entities", {}).get("PRODUCT", []))
    ner_categories = set(ner_relationships.get("entities", {}).get("CATEGORY", []))

    label_studio_map = {
        "COMPANY": "ORG",
        "LOCATION": "LOC",
        "GPE": "LOC",
        "ORG": "ORG",
        "PERSON": "PERSON",
        "PRODUCT": "PRODUCT",
        "TECHNOLOGY": "TECHNOLOGY",
        "CARDINAL": "NUMBER",
        "ORDINAL": "NUMBER",
        "QUANTITY": "QUANTITY",
        "DATE": "DATE",
        "TIME": "TIME",
        "EVENT": "MISC",
        "WORK_OF_ART": "MISC",
        "LAW": "MISC",
        "LANGUAGE": "MISC",
    }

    entities: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    failed_docs: List[str] = []

    for doc in batch:
        try:
            text = doc.get("text") or doc.get("metadata", {}).get("text", "")
            if not text:
                continue
            doc_id = ensure_doc_id(doc)
            doc_entities: List[Dict[str, Any]] = []

            spacy_doc = nlp(text)
            existing_spans: List[Tuple[int, int]] = []

            for ent in spacy_doc.ents:
                if ent.label_ in ["COMPANY", "LOCATION", "PRODUCT", "TECHNOLOGY"]:
                    source = "heuristics"
                    conf = 0.90
                    canonical = ent.ent_id_ if ent.ent_id_ else ent.text
                elif ent.label_ in ["PERSON", "DATE"]:
                    source = "spacy"
                    conf = 0.75
                    canonical = ent.text
                elif ent.label_ in ["CARDINAL", "ORDINAL", "QUANTITY", "TIME"]:
                    source = "spacy"
                    conf = 0.85
                    canonical = ent.text
                else:
                    source = "spacy"
                    conf = 0.70
                    canonical = ent.text

                entity_type = label_studio_map.get(ent.label_, ent.label_)

                doc_entities.append(
                    {
                        "doc_id": doc_id,
                        "type": entity_type,
                        "surface": ent.text,
                        "norm_value": json.dumps({"canonical": canonical}),
                        "span": json.dumps(
                            {
                                "start": ent.start_char,
                                "end": ent.end_char,
                                "text": ent.text,
                            }
                        ),
                        "conf": conf,
                        "source": source,
                        "source_version": "en_core_web_sm_3.8.0" if source == "spacy" else "taxonomy",
                        "heuristics_version": heuristics_version,
                        "confidence_method": "entity_ruler" if source == "heuristics" else "spacy_ner",
                    }
                )
                existing_spans.append((ent.start_char, ent.end_char))

            money_pattern = r"\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?"
            for match in re.finditer(money_pattern, text):
                if not span_overlaps(match.start(), match.end(), existing_spans):
                    doc_entities.append(
                        {
                            "doc_id": doc_id,
                            "type": "MONEY",
                            "surface": match.group(0),
                            "norm_value": json.dumps({"currency": "USD", "surface": match.group(0)}),
                            "span": json.dumps(
                                {
                                    "start": match.start(),
                                    "end": match.end(),
                                    "text": match.group(0),
                                }
                            ),
                            "conf": 0.92,
                            "source": "regex",
                            "source_version": "money_pattern_v1",
                            "heuristics_version": heuristics_version,
                            "confidence_method": "regex_pattern",
                        }
                    )
                    existing_spans.append((match.start(), match.end()))

            percent_pattern = r"\d{1,3}(?:\.\d{1,2})?\s*%"
            for match in re.finditer(percent_pattern, text):
                if not span_overlaps(match.start(), match.end(), existing_spans):
                    doc_entities.append(
                        {
                            "doc_id": doc_id,
                            "type": "PERCENT",
                            "surface": match.group(0),
                            "norm_value": json.dumps({"surface": match.group(0)}),
                            "span": json.dumps(
                                {
                                    "start": match.start(),
                                    "end": match.end(),
                                    "text": match.group(0),
                                }
                            ),
                            "conf": 0.90,
                            "source": "regex",
                            "source_version": "percent_pattern_v1",
                            "heuristics_version": heuristics_version,
                            "confidence_method": "regex_pattern",
                        }
                    )
                    existing_spans.append((match.start(), match.end()))

            for title in BUSINESS_TITLES:
                for match in re.finditer(rf"\b{re.escape(title)}\b", text):
                    if span_overlaps(match.start(), match.end(), existing_spans):
                        continue
                    doc_entities.append(
                        {
                            "doc_id": doc_id,
                            "type": "MISC",
                            "surface": match.group(0),
                            "norm_value": json.dumps({"canonical": title}),
                            "span": json.dumps(
                                {
                                    "start": match.start(),
                                    "end": match.end(),
                                    "text": match.group(0),
                                }
                            ),
                            "conf": 0.85,
                            "source": "pattern",
                            "source_version": "business_title_v1",
                            "heuristics_version": heuristics_version,
                            "confidence_method": "pattern_match",
                        }
                    )
                    existing_spans.append((match.start(), match.end()))

            for skill in SKILL_TERMS:
                for match in re.finditer(rf"\b{re.escape(skill)}\b", text, flags=re.IGNORECASE):
                    if span_overlaps(match.start(), match.end(), existing_spans):
                        continue
                    doc_entities.append(
                        {
                            "doc_id": doc_id,
                            "type": "MISC",
                            "surface": match.group(0),
                            "norm_value": json.dumps({"canonical": skill}),
                            "span": json.dumps(
                                {
                                    "start": match.start(),
                                    "end": match.end(),
                                    "text": match.group(0),
                                }
                            ),
                            "conf": 0.82,
                            "source": "pattern",
                            "source_version": "skill_v1",
                            "heuristics_version": heuristics_version,
                            "confidence_method": "pattern_match",
                        }
                    )
                    existing_spans.append((match.start(), match.end()))

            for match in TIME_RANGE_REGEX.finditer(text):
                if span_overlaps(match.start(), match.end(), existing_spans):
                    continue
                doc_entities.append(
                    {
                        "doc_id": doc_id,
                        "type": "TIME",
                        "surface": match.group(0),
                        "norm_value": json.dumps({"surface": match.group(0)}),
                        "span": json.dumps(
                            {
                                "start": match.start(),
                                "end": match.end(),
                                "text": match.group(0),
                            }
                        ),
                        "conf": 0.8,
                        "source": "pattern",
                        "source_version": "time_range_v1",
                        "heuristics_version": heuristics_version,
                        "confidence_method": "pattern_match",
                    }
                )
                existing_spans.append((match.start(), match.end()))

            for match in TEMPORAL_REGEX.finditer(text):
                if span_overlaps(match.start(), match.end(), existing_spans):
                    continue
                doc_entities.append(
                    {
                        "doc_id": doc_id,
                        "type": "TIME",
                        "surface": match.group(0),
                        "norm_value": json.dumps({"surface": match.group(0)}),
                        "span": json.dumps(
                            {
                                "start": match.start(),
                                "end": match.end(),
                                "text": match.group(0),
                            }
                        ),
                        "conf": 0.78,
                        "source": "pattern",
                        "source_version": "temporal_v1",
                        "heuristics_version": heuristics_version,
                        "confidence_method": "pattern_match",
                    }
                )
                existing_spans.append((match.start(), match.end()))

            if industry_lookup:
                seen_industry_spans: Set[Tuple[str, int, int]] = set()
                for _, (industry, surface) in industry_lookup.items():
                    for start, end in iter_phrase_matches(text, surface):
                        if span_overlaps(start, end, existing_spans):
                            continue
                        key = (industry.get("id", surface.lower()), start, end)
                        if key in seen_industry_spans:
                            continue
                        seen_industry_spans.add(key)
                        surface_text = text[start:end]
                        doc_entities.append(
                            {
                                "doc_id": doc_id,
                                "type": "MISC",
                                "surface": surface_text,
                                "norm_value": json.dumps(
                                    {
                                        "id": industry.get("id"),
                                        "name": industry.get("name"),
                                        "level": industry.get("level"),
                                        "path": industry.get("path"),
                                    }
                                ),
                                "span": json.dumps(
                                    {
                                        "start": start,
                                        "end": end,
                                        "text": surface_text,
                                    }
                                ),
                                "conf": 0.88,
                                "source": "heuristics",
                                "source_version": f"taxonomy_industries_{taxonomy_version}",
                                "heuristics_version": heuristics_version,
                                "confidence_method": "taxonomy_match",
                            }
                        )
                        existing_spans.append((start, end))

            if service_lookup:
                seen_service_spans: Set[Tuple[str, int, int]] = set()
                for _, (service, surface) in service_lookup.items():
                    for start, end in iter_phrase_matches(text, surface):
                        if span_overlaps(start, end, existing_spans):
                            continue
                        key = (service.get("id", surface.lower()), start, end)
                        if key in seen_service_spans:
                            continue
                        seen_service_spans.add(key)
                        surface_text = text[start:end]
                        doc_entities.append(
                            {
                                "doc_id": doc_id,
                                "type": "MISC",
                                "surface": surface_text,
                                "norm_value": json.dumps(
                                    {
                                        "id": service.get("id"),
                                        "name": service.get("name"),
                                        "level": service.get("level"),
                                        "path": service.get("path"),
                                    }
                                ),
                                "span": json.dumps(
                                    {
                                        "start": start,
                                        "end": end,
                                        "text": surface_text,
                                    }
                                ),
                                "conf": 0.86,
                                "source": "heuristics",
                                "source_version": f"taxonomy_services_{taxonomy_version}",
                                "heuristics_version": heuristics_version,
                                "confidence_method": "taxonomy_match",
                            }
                        )
                        existing_spans.append((start, end))

            if products:
                for product in products:
                    product_name = product.get("name")
                    if not product_name:
                        continue
                    pattern = re.compile(rf"\b{re.escape(product_name)}\b", re.IGNORECASE)
                    for match in pattern.finditer(text):
                        if span_overlaps(match.start(), match.end(), existing_spans):
                            continue
                        doc_entities.append(
                            {
                                "doc_id": doc_id,
                                "type": "PRODUCT",
                                "surface": match.group(0),
                                "norm_value": json.dumps(product),
                                "span": json.dumps(
                                    {
                                        "start": match.start(),
                                        "end": match.end(),
                                        "text": match.group(0),
                                    }
                                ),
                                "conf": 0.88,
                                "source": "heuristics",
                                "source_version": f"taxonomy_products_{taxonomy_version}",
                                "heuristics_version": heuristics_version,
                                "confidence_method": "taxonomy_match",
                            }
                        )
                        existing_spans.append((match.start(), match.end()))

            if partnerships:
                for partnership in partnerships:
                    companies = partnership.get("companies", [])
                    if len(companies) < 2:
                        continue
                    company_patterns = [
                        re.compile(rf"\b{re.escape(company)}\b", re.IGNORECASE)
                        for company in companies
                        if company
                    ]
                    matches = [list(pattern.finditer(text)) for pattern in company_patterns]
                    if all(matches):
                        for combo in zip(*matches):
                            span_positions = [(m.start(), m.end()) for m in combo]
                            if any(span_overlaps(start, end, existing_spans) for start, end in span_positions):
                                continue
                            relationships.append(
                                {
                                    "doc_id": doc_id,
                                    "type": "PARTNERSHIP",
                                    "conf": 0.80,
                                    "head_span": {
                                        "start": span_positions[0][0],
                                        "end": span_positions[0][1],
                                        "text": combo[0].group(0),
                                    },
                                    "tail_span": {
                                        "start": span_positions[1][0],
                                        "end": span_positions[1][1],
                                        "text": combo[1].group(0),
                                    },
                                    "evidence": json.dumps(
                                        {
                                            "pattern": "partnership",
                                            "companies": companies,
                                        }
                                    ),
                                    "heuristics_version": heuristics_version,
                                }
                            )

            if ner_orgs:
                for org_name in ner_orgs:
                    pattern = re.compile(rf"\b{re.escape(org_name)}\b", re.IGNORECASE)
                    for match in pattern.finditer(text):
                        if span_overlaps(match.start(), match.end(), existing_spans):
                            continue
                        doc_entities.append(
                            {
                                "doc_id": doc_id,
                                "type": "ORG",
                                "surface": match.group(0),
                                "norm_value": json.dumps({"canonical": org_name}),
                                "span": json.dumps(
                                    {
                                        "start": match.start(),
                                        "end": match.end(),
                                        "text": match.group(0),
                                    }
                                ),
                                "conf": 0.87,
                                "source": "heuristics",
                                "source_version": "ner_relationships_json",
                                "heuristics_version": heuristics_version,
                                "confidence_method": "ner_org_match",
                            }
                        )
                        existing_spans.append((match.start(), match.end()))

            if ner_products:
                for product_name in ner_products:
                    pattern = re.compile(rf"\b{re.escape(product_name)}\b", re.IGNORECASE)
                    for match in pattern.finditer(text):
                        if not span_overlaps(match.start(), match.end(), existing_spans):
                            doc_entities.append(
                                {
                                    "doc_id": doc_id,
                                    "type": "PRODUCT",
                                    "surface": match.group(0),
                                    "norm_value": json.dumps({"canonical": product_name}),
                                    "span": json.dumps(
                                        {
                                            "start": match.start(),
                                            "end": match.end(),
                                            "text": match.group(0),
                                        }
                                    ),
                                    "conf": 0.86,
                                    "source": "heuristics",
                                    "source_version": "ner_relationships_json",
                                    "heuristics_version": heuristics_version,
                                    "confidence_method": "ner_product_match",
                                }
                            )
                            existing_spans.append((match.start(), match.end()))

            if ner_categories:
                for category_name in ner_categories:
                    pattern = re.compile(rf"\b{re.escape(category_name)}\b", re.IGNORECASE)
                    for match in pattern.finditer(text):
                        if not span_overlaps(match.start(), match.end(), existing_spans):
                            doc_entities.append(
                                {
                                    "doc_id": doc_id,
                                    "type": "MISC",
                                    "surface": match.group(0),
                                    "norm_value": json.dumps({"canonical": category_name}),
                                    "span": json.dumps(
                                        {
                                            "start": match.start(),
                                            "end": match.end(),
                                            "text": match.group(0),
                                        }
                                    ),
                                    "conf": 0.84,
                                    "source": "heuristics",
                                    "source_version": "ner_relationships_json",
                                    "heuristics_version": heuristics_version,
                                    "confidence_method": "ner_category_match",
                                }
                            )
                            existing_spans.append((match.start(), match.end()))

            number_pattern = r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b"
            for match in re.finditer(number_pattern, text):
                if not span_overlaps(match.start(), match.end(), existing_spans):
                    matched_text = match.group(0)
                    if not (matched_text.startswith("$") or matched_text.endswith("%")):
                        doc_entities.append(
                            {
                                "doc_id": doc_id,
                                "type": "NUMBER",
                                "surface": matched_text,
                                "norm_value": json.dumps({"value": matched_text}),
                                "span": json.dumps(
                                    {
                                        "start": match.start(),
                                        "end": match.end(),
                                        "text": matched_text,
                                    }
                                ),
                                "conf": 0.80,
                                "source": "regex",
                                "source_version": "number_pattern_v1",
                                "heuristics_version": heuristics_version,
                                "confidence_method": "regex_pattern",
                            }
                        )
                        existing_spans.append((match.start(), match.end()))

            quantity_pattern = r"\b\d+\s+(?:units?|employees?|customers?|users?|clients?|staff|people|workers?|agents?|members?)\b"
            for match in re.finditer(quantity_pattern, text, re.IGNORECASE):
                if not span_overlaps(match.start(), match.end(), existing_spans):
                    doc_entities.append(
                        {
                            "doc_id": doc_id,
                            "type": "QUANTITY",
                            "surface": match.group(0),
                            "norm_value": json.dumps({"surface": match.group(0)}),
                            "span": json.dumps(
                                {
                                    "start": match.start(),
                                    "end": match.end(),
                                    "text": match.group(0),
                                }
                            ),
                            "conf": 0.82,
                            "source": "regex",
                            "source_version": "quantity_pattern_v1",
                            "heuristics_version": heuristics_version,
                            "confidence_method": "regex_pattern",
                        }
                    )
                    existing_spans.append((match.start(), match.end()))

            metric_pattern = r"\b\d+\.?\d*\s*%?\s*(?:uptime|SLA|availability|accuracy|efficiency|satisfaction|NPS|CSAT|FCR|AHT|MTTR|MTBF)\b"
            for match in re.finditer(metric_pattern, text, re.IGNORECASE):
                if not span_overlaps(match.start(), match.end(), existing_spans):
                    doc_entities.append(
                        {
                            "doc_id": doc_id,
                            "type": "METRIC",
                            "surface": match.group(0),
                            "norm_value": json.dumps({"surface": match.group(0)}),
                            "span": json.dumps(
                                {
                                    "start": match.start(),
                                    "end": match.end(),
                                    "text": match.group(0),
                                }
                            ),
                            "conf": 0.83,
                            "source": "regex",
                            "source_version": "metric_pattern_v1",
                            "heuristics_version": heuristics_version,
                            "confidence_method": "regex_pattern",
                        }
                    )
                    existing_spans.append((match.start(), match.end()))

            duration_pattern = r"\b\d+\s+(?:seconds?|minutes?|hours?|days?|weeks?|months?|years?)\b"
            for match in re.finditer(duration_pattern, text, re.IGNORECASE):
                if not span_overlaps(match.start(), match.end(), existing_spans):
                    doc_entities.append(
                        {
                            "doc_id": doc_id,
                            "type": "DURATION",
                            "surface": match.group(0),
                            "norm_value": json.dumps({"surface": match.group(0)}),
                            "span": json.dumps(
                                {
                                    "start": match.start(),
                                    "end": match.end(),
                                    "text": match.group(0),
                                }
                            ),
                            "conf": 0.81,
                            "source": "regex",
                            "source_version": "duration_pattern_v1",
                            "heuristics_version": heuristics_version,
                            "confidence_method": "regex_pattern",
                        }
                    )
                    existing_spans.append((match.start(), match.end()))

            relationships.extend(
                build_relationships(
                    doc_id=doc_id,
                    text=text,
                    entities=doc_entities,
                    heuristics_version=heuristics_version,
                    relationship_strings=relationship_strings,
                )
            )

            entities.extend(doc_entities)

        except Exception as exc:
            doc_id = ensure_doc_id(doc)
            logger.error(f"Failed to extract from doc {doc_id}: {exc}")
            failed_docs.append(str(doc_id))
            continue

    logger.info(f"Extracted {len(entities)} entities and {len(relationships)} relationships")

    return {
        "entities": entities,
        "relationships": relationships,
        "failed_docs": failed_docs,
        "doc_count": len(batch),
        "heuristics_version": heuristics_version,
    }
