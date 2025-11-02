"""Relationship extraction helpers for entity batches."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List
import json
import re


def build_relationships(
    *,
    doc_id: str,
    text: str,
    entities: Iterable[Dict[str, Any]],
    heuristics_version: str,
    relationship_strings: Iterable[str],
) -> List[Dict[str, object]]:
    """Derive relationships for a document based on extracted entities."""
    relationships: List[Dict[str, object]] = []

    for rel_str in relationship_strings or []:
        if " belongs to " not in rel_str:
            continue
        parts = rel_str.split(" belongs to ")
        if len(parts) != 2:
            continue
        product_name = parts[0].strip()
        company_name = parts[1].strip()
        if not product_name or not company_name:
            continue

        product_pattern = re.compile(rf"\b{re.escape(product_name)}\b", re.IGNORECASE)
        company_pattern = re.compile(rf"\b{re.escape(company_name)}\b", re.IGNORECASE)

        product_matches = list(product_pattern.finditer(text))
        company_matches = list(company_pattern.finditer(text))
        for prod_match in product_matches:
            for comp_match in company_matches:
                distance = abs(prod_match.start() - comp_match.start())
                if distance >= 500:
                    continue
                relationships.append(
                    {
                        "doc_id": doc_id,
                        "type": "BELONGS_TO",
                        "conf": 0.85,
                        "head_span": {
                            "start": prod_match.start(),
                            "end": prod_match.end(),
                            "text": prod_match.group(0),
                        },
                        "tail_span": {
                            "start": comp_match.start(),
                            "end": comp_match.end(),
                            "text": comp_match.group(0),
                        },
                        "evidence": json.dumps(
                            {
                                "pattern": "relationship_string",
                                "string": rel_str,
                                "distance": distance,
                            }
                        ),
                        "heuristics_version": heuristics_version,
                    }
                )

    entity_spans: List[Dict[str, object]] = []
    for entity in entities:
        span_data = json.loads(entity["span"])
        entity_spans.append(
            {
                "entity": entity,
                "start": span_data["start"],
                "end": span_data["end"],
                "type": entity["type"],
            }
        )

    for i, ent1_span in enumerate(entity_spans):
        for ent2_span in entity_spans[i + 1 :]:
            distance = abs(ent1_span["start"] - ent2_span["start"])
            if distance >= 300:
                continue

            rel_type = "ORL"
            conf = 0.60

            if ent1_span["type"] == "PRODUCT" and ent2_span["type"] == "ORG":
                rel_type = "BELONGS_TO"
                conf = 0.75
            elif ent1_span["type"] == "ORG" and ent2_span["type"] == "PRODUCT":
                rel_type = "HAS_PRODUCT"
                conf = 0.75
            elif ent1_span["type"] == "PERSON" and ent2_span["type"] == "ORG":
                rel_type = "WORKS_FOR"
                conf = 0.65
            elif ent1_span["type"] == "TECHNOLOGY" and ent2_span["type"] == "PRODUCT":
                rel_type = "USES_TECHNOLOGY"
                conf = 0.70
            elif ent1_span["type"] == "ORG" and ent2_span["type"] == "LOC":
                rel_type = "LOCATED_IN"
                conf = 0.70
            elif ent1_span["type"] == "PRODUCT" and ent2_span["type"] == "TECHNOLOGY":
                rel_type = "IMPLEMENTS"
                conf = 0.70

            relationships.append(
                {
                    "doc_id": doc_id,
                    "type": rel_type,
                    "conf": conf,
                    "head_span": {
                        "start": ent1_span["start"],
                        "end": ent1_span["end"],
                        "text": ent1_span["entity"]["surface"],
                    },
                    "tail_span": {
                        "start": ent2_span["start"],
                        "end": ent2_span["end"],
                        "text": ent2_span["entity"]["surface"],
                    },
                    "evidence": json.dumps(
                        {
                            "pattern": "proximity",
                            "distance": distance,
                            "head_type": ent1_span["type"],
                            "tail_type": ent2_span["type"],
                        }
                    ),
                    "heuristics_version": heuristics_version,
                }
            )

    return relationships
