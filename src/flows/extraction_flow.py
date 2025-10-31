"""Prefect flow for document extraction pipeline."""
from prefect import flow, task, get_run_logger
from prefect.context import get_run_context
from prefect.task_runners import ConcurrentTaskRunner
from typing import List, Dict, Any, Iterable, Tuple, Optional, Set
import asyncpg
import hashlib
import json
import os
import re

from src.heuristics import get_heuristics_loader
import uuid


def _resolve_document_uuid(doc: Dict[str, Any]) -> uuid.UUID:
    """
    Resolve (or deterministically derive) a UUID for a document.
    Prefers explicit UUID values, then falls back to deterministic uuid5 variants.
    """
    candidates = [
        doc.get("id"),
        doc.get("doc_id"),
        doc.get("metadata", {}).get("id"),
        doc.get("metadata", {}).get("doc_id"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return uuid.UUID(str(candidate))
        except (ValueError, TypeError):
            return uuid.uuid5(uuid.NAMESPACE_URL, str(candidate))

    url = doc.get("url") or doc.get("metadata", {}).get("url")
    if url:
        return uuid.uuid5(uuid.NAMESPACE_URL, url)

    text = doc.get("text") or doc.get("metadata", {}).get("text") or ""
    if text:
        return uuid.uuid5(uuid.NAMESPACE_OID, text[:1024])

    return uuid.uuid4()


def _get_doc_id(doc: Dict[str, Any]) -> str:
    """Best-effort retrieval of document ID."""
    doc_id = (
        doc.get("id")
        or doc.get("doc_id")
        or doc.get("metadata", {}).get("doc_id")
        or doc.get("metadata", {}).get("id")
    )
    if doc_id:
        return str(doc_id)

    # Fall back to deterministic UUID so downstream tables remain consistent.
    derived = _resolve_document_uuid(doc)
    doc["id"] = str(derived)
    return doc["id"]


def _batched_documents(
    source_path: str, start_offset: int, batch_size: int
) -> Iterable[Tuple[int, int, list]]:
    """
    Stream documents from file, yielding (batch_start_index, batch_end_index, batch_docs).
    """
    batch = []
    batch_start = None
    last_idx = -1
    with open(source_path, "r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle):
            if idx < start_offset:
                continue
            doc = json.loads(line)
            if batch_start is None:
                batch_start = idx
            batch.append(doc)
            if len(batch) == batch_size:
                yield batch_start, idx + 1, batch
                batch = []
                batch_start = None
            last_idx = idx

    if batch:
        end_idx = last_idx + 1 if last_idx >= 0 else start_offset + len(batch)
        start_idx = batch_start if batch_start is not None else max(end_idx - len(batch), start_offset)
        yield start_idx, end_idx, batch


def _span_overlaps(start: int, end: int, existing: list[Tuple[int, int]]) -> bool:
    return any(not (end <= s or start >= e) for s, e in existing)


def _iter_phrase_matches(text: str, phrase: str) -> Iterable[Tuple[int, int]]:
    """Yield start/end offsets for case-insensitive whole-phrase matches."""
    if not phrase:
        return
    pattern = re.compile(r'(?<!\w){}(?!\w)'.format(re.escape(phrase)), re.IGNORECASE)
    for match in pattern.finditer(text):
        yield match.start(), match.end()


def _score_structure_signals(signals: Dict[str, Any], raw_text: str, lower_text: str, markdown: str) -> float:
    """Compute structural signal contribution for content classification."""
    score = 0.0
    word_count = len(lower_text.split()) if lower_text else 0

    min_length = signals.get("min_length")
    if isinstance(min_length, (int, float)) and word_count >= min_length:
        score += 2.0

    max_length = signals.get("max_length")
    if isinstance(max_length, (int, float)) and word_count and word_count <= max_length:
        score += 1.0

    if signals.get("has_metrics"):
        if re.search(r'\d+\s*(?:%|percent|percentage|bps)', lower_text):
            score += 3.0

    if signals.get("has_sections"):
        found = 0
        for section in signals["has_sections"]:
            if section and section.lower() in lower_text:
                found += 1
        if found >= len(signals["has_sections"]):
            score += 4.0
        elif found:
            score += 2.0

    if signals.get("has_quotes"):
        if re.search(r'[\"“”]', raw_text):
            score += 2.0

    if signals.get("has_code_blocks"):
        markdown_lower = markdown.lower()
        if "```" in markdown_lower or "<code" in markdown_lower:
            score += 3.0

    if signals.get("has_cta"):
        if re.search(r'\b(get started|sign up|try free|request demo|contact (us|sales))\b', lower_text):
            score += 2.0

    if signals.get("has_form"):
        md_lower = markdown.lower()
        if "<form" in md_lower or re.search(r'\bfill out\b', lower_text):
            score += 1.5

    if signals.get("has_date"):
        if re.search(r'\b(january|february|march|april|may|june|july|august|september|october|november|december|\d{1,2}/\d{1,2}/\d{2,4}|20\d{2})\b', lower_text):
            score += 2.0

    if signals.get("has_registration"):
        if re.search(r'\b(register|registration|rsvp|save your spot)\b', lower_text):
            score += 2.0

    if signals.get("has_pricing_table"):
        if '<table' in markdown.lower() or re.search(r'\b(per month|per user|pricing plan|pricing tier)\b', lower_text):
            score += 2.5

    if signals.get("has_currency"):
        if re.search(r'[$£€¥]\s?\d|\b(usd|eur|gbp|cad|aud)\b', lower_text):
            score += 1.5

    if signals.get("has_requirements_list"):
        if re.search(r'\b(requirements|qualifications|responsibilities):', lower_text):
            score += 2.0

    if signals.get("has_names"):
        if re.search(r'\b(ceo|cfo|cto|coo|vp|vice president|manager|director)\b', lower_text):
            score += 1.5

    if signals.get("has_list"):
        if re.search(r'(^|\n)\s*(?:[-*•]|\d+\.)\s', markdown):
            score += 2.0

    if signals.get("has_steps"):
        if re.search(r'\bstep\s+\d+', lower_text):
            score += 1.5

    return score


def classify_content_type(
    url: str,
    title: Optional[str],
    body: str,
    rules: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Classify a document against content-type rules."""
    if not rules:
        return None

    url_lower = (url or "").lower()
    title = title or ""
    title_lower = title.lower()
    body = body or ""
    body_lower = body.lower()

    scores: Dict[str, float] = {}

    for rule in rules:
        label = rule.get("label", "Unknown")
        rule_score = 0.0

        for pattern in rule.get("url_patterns", []):
            try:
                if re.search(pattern, url_lower, re.IGNORECASE):
                    rule_score += rule.get("url_weight", 10)
                    break
            except re.error:
                continue

        for pattern in rule.get("title_patterns", []):
            try:
                if re.search(pattern, title_lower, re.IGNORECASE):
                    rule_score += rule.get("title_weight", 5)
                    break
            except re.error:
                continue

        pattern_matches = 0
        for pattern in rule.get("content_patterns", []):
            try:
                if re.search(pattern, body, re.IGNORECASE):
                    pattern_matches += 1
            except re.error:
                continue
        min_patterns = rule.get("min_patterns", 0)
        if pattern_matches >= min_patterns:
            rule_score += pattern_matches * rule.get("pattern_weight", 1)
        elif min_patterns > 0:
            rule_score *= 0.6

        rule_score += _score_structure_signals(
            rule.get("structure_signals", {}),
            body,
            body_lower,
            body,
        )

        scores[label] = round(rule_score, 2)

    if not scores:
        return None

    predicted_label = max(scores, key=scores.get)
    max_score = scores[predicted_label]
    matched_rule = next((r for r in rules if r.get("label") == predicted_label), None)
    min_threshold = matched_rule.get("min_score", 30) if matched_rule else 30

    meets_threshold = max_score >= min_threshold
    label = predicted_label if meets_threshold else "Other"
    confidence = min(max_score / max(float(min_threshold), 30.0), 1.0) if meets_threshold else min(max_score / max(float(min_threshold or 30), 30.0), 0.6)
    needs_review = (not meets_threshold) or confidence < 0.65

    return {
        "label": label,
        "raw_label": predicted_label,
        "score": max_score,
        "confidence": round(confidence, 3),
        "needs_review": needs_review,
        "scores": scores,
        "threshold": min_threshold,
    }
async def _lookup_entity_id(conn, doc_id: str, span: Dict[str, Any]):
    return await conn.fetchval(
        """
        SELECT id
        FROM entities
        WHERE doc_id = $1
          AND (span->>'start')::int = $2
          AND (span->>'end')::int = $3
          AND span->>'text' = $4
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        doc_id,
        int(span["start"]),
        int(span["end"]),
        span["text"],
    )


BUSINESS_TITLES = [
    "CEO",
    "Chief Executive Officer",
    "CFO",
    "Chief Financial Officer",
    "COO",
    "Chief Operating Officer",
    "CTO",
    "Chief Technology Officer",
    "Chairman",
    "President",
    "Vice President",
    "VP",
    "SVP",
    "EVP",
    "Managing Director",
    "Managing Partner",
    "Director",
    "Head of",
    "Global Head",
]

SKILL_TERMS = [
    "Python",
    "SQL",
    "data analysis",
    "machine learning",
    "cloud computing",
    "customer service",
    "project management",
    "AI",
    "BPO operations",
]

TIME_RANGE_REGEX = re.compile(
    r"(?:Q[1-4]\s*\d{4}|\d+\s+(?:day|week|month|year)s?|next\s+(?:quarter|year)|"
    r"past\s+\d+\s+(?:months|years))",
    re.IGNORECASE,
)

TEMPORAL_REGEX = re.compile(r"\b(?:pre|post|mid)-(?:launch|merger|acquisition|pandemic)\b", re.IGNORECASE)


@task(
    retries=3,
    retry_delay_seconds=10,
    cache_key_fn=lambda ctx, params: f"load_checkpoint_{params['workflow_id']}",
    persist_result=True,
    tags=["checkpoint"],
)
async def load_checkpoint(workflow_id: str) -> Dict[str, Any]:
    """Load checkpoint from database."""
    query = """
        SELECT doc_offset, state
        FROM pipeline_checkpoints
        WHERE workflow_id = $1 AND phase = 'extraction'
        ORDER BY updated_at DESC
        LIMIT 1
    """
    try:
        async with asyncpg.create_pool(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME", "bpo_intel"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
        ) as pool:
            async with pool.acquire() as conn:
                result = await conn.fetchrow(query, workflow_id)
                if not result:
                    return {}
                state = result["state"] or {}
                state["offset"] = result["doc_offset"]
                return state
    except Exception as e:
        get_run_logger().warning(f"Failed to load checkpoint: {e}")
        return {}


@task(
    retries=3,
    retry_delay_seconds=5,
    tags=["database", "documents"]
)
async def insert_documents(batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ensure documents exist in the database prior to entity persistence.

    Returns a normalized batch with UUID identifiers and lifted text/title fields.
    """
    logger = get_run_logger()
    heuristics_loader = get_heuristics_loader()
    heuristics_data = heuristics_loader.data if heuristics_loader else None
    content_rules = heuristics_data.content_types if heuristics_data else []

    db_host = os.getenv("DB_HOST", "postgres")
    db_port = int(os.getenv("DB_PORT", 5432))
    db_name = os.getenv("DB_NAME", "bpo_intel")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")

    normalized_docs: List[Dict[str, Any]] = []

    async with asyncpg.create_pool(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password,
        min_size=1,
        max_size=5,
    ) as pool:
        async with pool.acquire() as conn:
            for raw_doc in batch:
                doc_uuid = _resolve_document_uuid(raw_doc)
                url = raw_doc.get("url") or raw_doc.get("metadata", {}).get("url") or f"synthetic://{doc_uuid}"
                title = raw_doc.get("title") or raw_doc.get("metadata", {}).get("title")
                text = raw_doc.get("text") or raw_doc.get("metadata", {}).get("text") or ""
                status = int(raw_doc.get("status", 200))
                content_type = raw_doc.get("content_type") or raw_doc.get("metadata", {}).get("content_type")
                fetched_at = raw_doc.get("fetched_at") or raw_doc.get("metadata", {}).get("extracted_at")
                lang = raw_doc.get("lang") or raw_doc.get("metadata", {}).get("lang")

                text_sha256 = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest() if text else hashlib.sha256(url.encode("utf-8")).hexdigest()

                raw_metadata = raw_doc.get("metadata")
                if isinstance(raw_metadata, dict):
                    metadata = dict(raw_metadata)
                elif isinstance(raw_metadata, str):
                    try:
                        metadata = json.loads(raw_metadata)
                    except json.JSONDecodeError:
                        metadata = {"raw": raw_metadata}
                else:
                    metadata = {}

                metadata.setdefault("source_url", url)
                metadata.setdefault("raw_id", raw_doc.get("id") or raw_doc.get("doc_id"))
                if fetched_at and "extracted_at" not in metadata:
                    metadata["extracted_at"] = fetched_at

                content_type_value = content_type
                if content_rules:
                    classification = classify_content_type(url, title, text, content_rules)
                    if classification:
                        auto_meta = metadata.setdefault("auto_classification", {})
                        auto_meta["content_type"] = classification["label"]
                        auto_meta["content_type_raw"] = classification["raw_label"]
                        auto_meta["score"] = classification["score"]
                        auto_meta["confidence"] = classification["confidence"]
                        auto_meta["needs_review"] = classification["needs_review"]
                        auto_meta["scores"] = classification["scores"]
                        auto_meta["threshold"] = classification["threshold"]
                        if (not content_type_value or content_type_value.lower() == "unknown") and classification["label"] != "Other":
                            content_type_value = classification["label"]

                try:
                    await conn.execute(
                        """
                        INSERT INTO documents (id, url, text_sha256, status, content_type, title, fetched_at, lang, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (id) DO UPDATE
                        SET url = EXCLUDED.url,
                            text_sha256 = EXCLUDED.text_sha256,
                            status = EXCLUDED.status,
                            content_type = EXCLUDED.content_type,
                            title = EXCLUDED.title,
                            fetched_at = EXCLUDED.fetched_at,
                            lang = EXCLUDED.lang,
                            metadata = EXCLUDED.metadata,
                            updated_at = NOW()
                        """,
                        doc_uuid,
                        url,
                        text_sha256,
                        status,
                        content_type_value,
                        title,
                        fetched_at,
                        lang,
                        metadata,
                    )
                except Exception as exc:
                    logger.error(f"Failed to insert document {doc_uuid}: {exc}")
                    raise

                normalized_doc = dict(raw_doc)
                normalized_doc["id"] = str(doc_uuid)
                normalized_doc["url"] = url
                normalized_doc["text"] = text
                normalized_doc["title"] = title
                normalized_doc["metadata"] = metadata
                normalized_doc["content_type"] = content_type_value
                normalized_doc["text_sha256"] = text_sha256
                normalized_docs.append(normalized_doc)

    return normalized_docs


@task(
    retries=2,
    retry_delay_seconds=5,
    cache_key_fn=lambda ctx, params: f"extract_{params['batch_id']}",
    persist_result=True,
    tags=["extraction", "ner"]
)
async def extract_entities_batch(
    batch: List[Dict],
    batch_id: str,
    heuristics_version: str
) -> Dict[str, Any]:
    """Extract entities and relationships using comprehensive heuristics."""
    from src.extraction.spacy_pipeline import get_extraction_nlp
    
    logger = get_run_logger()
    logger.info(f"Processing batch {batch_id} with {len(batch)} documents")
    
    # Load models once per task
    nlp = get_extraction_nlp()
    heuristics = get_heuristics_loader()
    heuristics_data = heuristics.data if heuristics else None
    industry_lookup = heuristics_data.industry_lookup if heuristics_data else {}
    service_lookup = heuristics_data.service_lookup if heuristics_data else {}
    taxonomy_version = heuristics_data.version if heuristics_data else "unknown"
    
    # Load comprehensive heuristics data
    products = heuristics_data.products if heuristics_data else []
    ner_relationships = heuristics_data.ner_relationships if heuristics_data else {}
    partnerships = heuristics_data.partnerships if heuristics_data else []
    relationship_strings = ner_relationships.get("relationship_strings", [])
    ner_orgs = set(ner_relationships.get("entities", {}).get("ORG", []))
    ner_products = set(ner_relationships.get("entities", {}).get("PRODUCT", []))
    ner_categories = set(ner_relationships.get("entities", {}).get("CATEGORY", []))
    
    # Map entity types for Label Studio compatibility
    LABEL_STUDIO_MAP = {
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
    
    entities = []
    relationships = []
    failed_docs = []
    
    for doc in batch:
        try:
            text = doc.get("text") or doc.get("metadata", {}).get("text", "")
            if not text:
                continue
            doc_id = _get_doc_id(doc)
            
            # Extract entities using spaCy pipeline
            spacy_doc = nlp(text)
            existing_spans = []
            
            for ent in spacy_doc.ents:
                # Determine source and confidence
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
                
                # Map entity type for Label Studio compatibility
                entity_type = LABEL_STUDIO_MAP.get(ent.label_, ent.label_)
                
                entities.append({
                    "doc_id": doc_id,
                    "type": entity_type,
                    "surface": ent.text,
                    "norm_value": json.dumps({"canonical": canonical}),
                    "span": json.dumps({
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "text": ent.text
                    }),
                    "conf": conf,
                    "source": source,
                    "source_version": "en_core_web_sm_3.8.0" if source == "spacy" else "taxonomy",
                    "heuristics_version": heuristics_version,
                    "confidence_method": "entity_ruler" if source == "heuristics" else "spacy_ner"
                })
                existing_spans.append((ent.start_char, ent.end_char))
            
            # Add regex patterns for MONEY and PERCENT
            money_pattern = r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
            for match in re.finditer(money_pattern, text):
                if not _span_overlaps(match.start(), match.end(), existing_spans):
                    entities.append({
                        "doc_id": doc_id,
                        "type": "MONEY",
                        "surface": match.group(0),
                        "norm_value": json.dumps({"currency": "USD", "surface": match.group(0)}),
                        "span": json.dumps({"start": match.start(), "end": match.end(), "text": match.group(0)}),
                        "conf": 0.92,
                        "source": "regex",
                        "source_version": "money_pattern_v1",
                        "heuristics_version": heuristics_version,
                        "confidence_method": "regex_pattern"
                    })
                    existing_spans.append((match.start(), match.end()))
            
            percent_pattern = r'\d{1,3}(?:\.\d{1,2})?\s*%'
            for match in re.finditer(percent_pattern, text):
                if not _span_overlaps(match.start(), match.end(), existing_spans):
                    entities.append({
                        "doc_id": doc_id,
                        "type": "PERCENT",
                        "surface": match.group(0),
                        "norm_value": json.dumps({"surface": match.group(0)}),
                        "span": json.dumps({"start": match.start(), "end": match.end(), "text": match.group(0)}),
                        "conf": 0.90,
                        "source": "regex",
                        "source_version": "percent_pattern_v1",
                        "heuristics_version": heuristics_version,
                        "confidence_method": "regex_pattern"
                    })
                    existing_spans.append((match.start(), match.end()))

            # Business titles
            for title in BUSINESS_TITLES:
                for match in re.finditer(rf"\b{re.escape(title)}\b", text):
                    if _span_overlaps(match.start(), match.end(), existing_spans):
                        continue
                    entities.append({
                        "doc_id": doc_id,
                        "type": "MISC",  # Map to Label Studio MISC
                        "surface": match.group(0),
                        "norm_value": json.dumps({"canonical": title}),
                        "span": json.dumps({"start": match.start(), "end": match.end(), "text": match.group(0)}),
                        "conf": 0.85,
                        "source": "pattern",
                        "source_version": "business_title_v1",
                        "heuristics_version": heuristics_version,
                        "confidence_method": "pattern_match"
                })
                existing_spans.append((match.start(), match.end()))
            
            # Skills
            for skill in SKILL_TERMS:
                for match in re.finditer(rf"\b{re.escape(skill)}\b", text, flags=re.IGNORECASE):
                    if _span_overlaps(match.start(), match.end(), existing_spans):
                        continue
                    entities.append({
                        "doc_id": doc_id,
                        "type": "MISC",  # Map to Label Studio MISC
                        "surface": match.group(0),
                        "norm_value": json.dumps({"canonical": skill}),
                        "span": json.dumps({"start": match.start(), "end": match.end(), "text": match.group(0)}),
                        "conf": 0.82,
                        "source": "pattern",
                        "source_version": "skill_v1",
                        "heuristics_version": heuristics_version,
                        "confidence_method": "pattern_match"
                    })
                    existing_spans.append((match.start(), match.end()))

            # Time ranges
            for match in TIME_RANGE_REGEX.finditer(text):
                if _span_overlaps(match.start(), match.end(), existing_spans):
                    continue
                entities.append({
                    "doc_id": doc_id,
                    "type": "TIME",  # Map to Label Studio TIME
                    "surface": match.group(0),
                    "norm_value": json.dumps({"surface": match.group(0)}),
                    "span": json.dumps({"start": match.start(), "end": match.end(), "text": match.group(0)}),
                    "conf": 0.8,
                    "source": "pattern",
                    "source_version": "time_range_v1",
                    "heuristics_version": heuristics_version,
                    "confidence_method": "pattern_match"
                })
                existing_spans.append((match.start(), match.end()))

            # Temporal descriptors
            for match in TEMPORAL_REGEX.finditer(text):
                if _span_overlaps(match.start(), match.end(), existing_spans):
                    continue
                entities.append({
                    "doc_id": doc_id,
                    "type": "TIME",  # Map to Label Studio TIME
                    "surface": match.group(0),
                    "norm_value": json.dumps({"surface": match.group(0)}),
                    "span": json.dumps({"start": match.start(), "end": match.end(), "text": match.group(0)}),
                    "conf": 0.78,
                    "source": "pattern",
                    "source_version": "temporal_v1",
                    "heuristics_version": heuristics_version,
                    "confidence_method": "pattern_match",
                })
                existing_spans.append((match.start(), match.end()))

            if industry_lookup:
                seen_industry_spans: Set[Tuple[str, int, int]] = set()
                for _, (industry, surface) in industry_lookup.items():
                    for start, end in _iter_phrase_matches(text, surface):
                        if _span_overlaps(start, end, existing_spans):
                            continue
                        key = (industry.get("id", surface.lower()), start, end)
                        if key in seen_industry_spans:
                            continue
                        seen_industry_spans.add(key)
                        surface_text = text[start:end]
                        entities.append({
                            "doc_id": doc_id,
                            "type": "MISC",  # Map to Label Studio MISC
                            "surface": surface_text,
                            "norm_value": json.dumps({
                                "id": industry.get("id"),
                                "name": industry.get("name"),
                                "level": industry.get("level"),
                                "path": industry.get("path"),
                            }),
                            "span": json.dumps({"start": start, "end": end, "text": surface_text}),
                            "conf": 0.88,
                            "source": "heuristics",
                            "source_version": f"taxonomy_industries_{taxonomy_version}",
                            "heuristics_version": heuristics_version,
                            "confidence_method": "taxonomy_match",
                        })
                        existing_spans.append((start, end))

            if service_lookup:
                seen_service_spans: Set[Tuple[str, int, int]] = set()
                for _, (service, surface) in service_lookup.items():
                    for start, end in _iter_phrase_matches(text, surface):
                        if _span_overlaps(start, end, existing_spans):
                            continue
                        key = (service.get("id", surface.lower()), start, end)
                        if key in seen_service_spans:
                            continue
                        seen_service_spans.add(key)
                        surface_text = text[start:end]
                        entities.append({
                            "doc_id": doc_id,
                            "type": "MISC",  # Map to Label Studio MISC
                            "surface": surface_text,
                            "norm_value": json.dumps({
                                "id": service.get("id"),
                                "name": service.get("name"),
                                "level": service.get("level"),
                                "path": service.get("path"),
                            }),
                            "span": json.dumps({"start": start, "end": end, "text": surface_text}),
                            "conf": 0.86,
                            "source": "heuristics",
                            "source_version": f"taxonomy_services_{taxonomy_version}",
                            "heuristics_version": heuristics_version,
                            "confidence_method": "taxonomy_match",
                        })
                        existing_spans.append((start, end))

            # Extract products with aliases from heuristics (comprehensive)
            if products:
                for product in products:
                    product_name = product.get("name", "")
                    if not product_name:
                        continue
                    
                    # Match product name
                    pattern = re.compile(rf'\b{re.escape(product_name)}\b', re.IGNORECASE)
                    for match in pattern.finditer(text):
                        if not _span_overlaps(match.start(), match.end(), existing_spans):
                            entities.append({
                                "doc_id": doc_id,
                                "type": "PRODUCT",
                                "surface": match.group(0),
                                "norm_value": json.dumps({
                                    "canonical": product_name,
                                    "category": product.get("category", ""),
                                    "description": product.get("description", "")
                                }),
                                "span": json.dumps({"start": match.start(), "end": match.end(), "text": match.group(0)}),
                                "conf": 0.88,
                                "source": "heuristics",
                                "source_version": "products_json",
                                "heuristics_version": heuristics_version,
                                "confidence_method": "product_match"
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
                                    "doc_id": doc_id,
                                    "type": "PRODUCT",
                                    "surface": match.group(0),
                                    "norm_value": json.dumps({
                                        "canonical": product_name,
                                        "category": product.get("category", ""),
                                        "alias": alias
                                    }),
                                    "span": json.dumps({"start": match.start(), "end": match.end(), "text": match.group(0)}),
                                    "conf": 0.85,
                                    "source": "heuristics",
                                    "source_version": "products_json",
                                    "heuristics_version": heuristics_version,
                                    "confidence_method": "product_alias_match"
                                })
                                existing_spans.append((match.start(), match.end()))
            
            # Extract entities from ner_relationships.json entities lists
            if ner_orgs:
                for org_name in ner_orgs:
                    pattern = re.compile(rf'\b{re.escape(org_name)}\b', re.IGNORECASE)
                    for match in pattern.finditer(text):
                        if not _span_overlaps(match.start(), match.end(), existing_spans):
                            entities.append({
                                "doc_id": doc_id,
                                "type": "ORG",
                                "surface": match.group(0),
                                "norm_value": json.dumps({"canonical": org_name}),
                                "span": json.dumps({"start": match.start(), "end": match.end(), "text": match.group(0)}),
                                "conf": 0.87,
                                "source": "heuristics",
                                "source_version": "ner_relationships_json",
                                "heuristics_version": heuristics_version,
                                "confidence_method": "ner_org_match"
                            })
                            existing_spans.append((match.start(), match.end()))
            
            if ner_products:
                for product_name in ner_products:
                    pattern = re.compile(rf'\b{re.escape(product_name)}\b', re.IGNORECASE)
                    for match in pattern.finditer(text):
                        if not _span_overlaps(match.start(), match.end(), existing_spans):
                            entities.append({
                                "doc_id": doc_id,
                                "type": "PRODUCT",
                                "surface": match.group(0),
                                "norm_value": json.dumps({"canonical": product_name}),
                                "span": json.dumps({"start": match.start(), "end": match.end(), "text": match.group(0)}),
                                "conf": 0.86,
                                "source": "heuristics",
                                "source_version": "ner_relationships_json",
                                "heuristics_version": heuristics_version,
                                "confidence_method": "ner_product_match"
                            })
                            existing_spans.append((match.start(), match.end()))
            
            if ner_categories:
                for category_name in ner_categories:
                    pattern = re.compile(rf'\b{re.escape(category_name)}\b', re.IGNORECASE)
                    for match in pattern.finditer(text):
                        if not _span_overlaps(match.start(), match.end(), existing_spans):
                            entities.append({
                                "doc_id": doc_id,
                                "type": "MISC",
                                "surface": match.group(0),
                                "norm_value": json.dumps({"canonical": category_name}),
                                "span": json.dumps({"start": match.start(), "end": match.end(), "text": match.group(0)}),
                                "conf": 0.84,
                                "source": "heuristics",
                                "source_version": "ner_relationships_json",
                                "heuristics_version": heuristics_version,
                                "confidence_method": "ner_category_match"
                            })
                            existing_spans.append((match.start(), match.end()))
            
            # Extract NUMBER entities (cardinal numbers, metrics)
            number_pattern = r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b'
            for match in re.finditer(number_pattern, text):
                if not _span_overlaps(match.start(), match.end(), existing_spans):
                    # Skip if it's already captured as MONEY or PERCENT
                    matched_text = match.group(0)
                    if not (matched_text.startswith('$') or matched_text.endswith('%')):
                        entities.append({
                            "doc_id": doc_id,
                            "type": "NUMBER",
                            "surface": matched_text,
                            "norm_value": json.dumps({"value": matched_text}),
                            "span": json.dumps({"start": match.start(), "end": match.end(), "text": matched_text}),
                            "conf": 0.80,
                            "source": "regex",
                            "source_version": "number_pattern_v1",
                            "heuristics_version": heuristics_version,
                            "confidence_method": "regex_pattern"
                        })
                        existing_spans.append((match.start(), match.end()))
            
            # Extract QUANTITY patterns (e.g., "5 units", "10 employees")
            quantity_pattern = r'\b\d+\s+(?:units?|employees?|customers?|users?|clients?|staff|people|workers?|agents?|members?)\b'
            for match in re.finditer(quantity_pattern, text, re.IGNORECASE):
                if not _span_overlaps(match.start(), match.end(), existing_spans):
                    entities.append({
                        "doc_id": doc_id,
                        "type": "QUANTITY",
                        "surface": match.group(0),
                        "norm_value": json.dumps({"surface": match.group(0)}),
                        "span": json.dumps({"start": match.start(), "end": match.end(), "text": match.group(0)}),
                        "conf": 0.82,
                        "source": "regex",
                        "source_version": "quantity_pattern_v1",
                        "heuristics_version": heuristics_version,
                        "confidence_method": "regex_pattern"
                    })
                    existing_spans.append((match.start(), match.end()))
            
            # Extract METRIC patterns (e.g., "98% uptime", "99.9% SLA")
            metric_pattern = r'\b\d+\.?\d*\s*%?\s*(?:uptime|SLA|availability|accuracy|efficiency|satisfaction|NPS|CSAT|FCR|AHT|MTTR|MTBF)\b'
            for match in re.finditer(metric_pattern, text, re.IGNORECASE):
                if not _span_overlaps(match.start(), match.end(), existing_spans):
                    entities.append({
                        "doc_id": doc_id,
                        "type": "METRIC",
                        "surface": match.group(0),
                        "norm_value": json.dumps({"surface": match.group(0)}),
                        "span": json.dumps({"start": match.start(), "end": match.end(), "text": match.group(0)}),
                        "conf": 0.83,
                        "source": "regex",
                        "source_version": "metric_pattern_v1",
                        "heuristics_version": heuristics_version,
                        "confidence_method": "regex_pattern"
                    })
                    existing_spans.append((match.start(), match.end()))
            
            # Extract DURATION patterns
            duration_pattern = r'\b\d+\s+(?:seconds?|minutes?|hours?|days?|weeks?|months?|years?)\b'
            for match in re.finditer(duration_pattern, text, re.IGNORECASE):
                if not _span_overlaps(match.start(), match.end(), existing_spans):
                    entities.append({
                        "doc_id": doc_id,
                        "type": "DURATION",
                        "surface": match.group(0),
                        "norm_value": json.dumps({"surface": match.group(0)}),
                        "span": json.dumps({"start": match.start(), "end": match.end(), "text": match.group(0)}),
                        "conf": 0.81,
                        "source": "regex",
                        "source_version": "duration_pattern_v1",
                        "heuristics_version": heuristics_version,
                        "confidence_method": "regex_pattern"
                    })
                    existing_spans.append((match.start(), match.end()))
            
            # Extract relationships using relationship_strings patterns
            if relationship_strings:
                for rel_str in relationship_strings:
                    if " belongs to " in rel_str:
                        parts = rel_str.split(" belongs to ")
                        if len(parts) == 2:
                            product_name = parts[0].strip()
                            company_name = parts[1].strip()
                            
                            product_pattern = re.compile(rf'\b{re.escape(product_name)}\b', re.IGNORECASE)
                            company_pattern = re.compile(rf'\b{re.escape(company_name)}\b', re.IGNORECASE)
                            
                            product_matches = list(product_pattern.finditer(text))
                            company_matches = list(company_pattern.finditer(text))
                            
                            for prod_match in product_matches:
                                for comp_match in company_matches:
                                    distance = abs(prod_match.start() - comp_match.start())
                                    if distance < 500:
                                        relationships.append({
                                            "doc_id": doc_id,
                                            "type": "BELONGS_TO",
                                            "conf": 0.85,
                                            "head_span": {"start": prod_match.start(), "end": prod_match.end(), "text": prod_match.group(0)},
                                            "tail_span": {"start": comp_match.start(), "end": comp_match.end(), "text": comp_match.group(0)},
                                            "evidence": json.dumps({"pattern": "relationship_string", "string": rel_str, "distance": distance}),
                                            "heuristics_version": heuristics_version,
                                        })

            # Extract comprehensive relationships between all entities
            entity_spans = []
            for entity in entities:
                span_data = json.loads(entity["span"])
                entity_spans.append({
                    "entity": entity,
                    "start": span_data["start"],
                    "end": span_data["end"],
                    "type": entity["type"]
                })
            
            # Extract relationships between entity pairs (comprehensive - targeting 250+ per doc)
            for i, ent1_span in enumerate(entity_spans):
                for ent2_span in entity_spans[i + 1:]:
                    distance = abs(ent1_span["start"] - ent2_span["start"])
                    
                    if distance < 300:  # Within 300 characters
                        rel_type = "ORL"
                        conf = 0.60
                        
                        # Type-specific relationships
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
                        
                        relationships.append({
                            "doc_id": doc_id,
                            "type": rel_type,
                            "conf": conf,
                            "head_span": {"start": ent1_span["start"], "end": ent1_span["end"], "text": ent1_span["entity"]["surface"]},
                            "tail_span": {"start": ent2_span["start"], "end": ent2_span["end"], "text": ent2_span["entity"]["surface"]},
                            "evidence": json.dumps({
                                "pattern": "proximity",
                                "distance": distance,
                                "head_type": ent1_span["type"],
                                "tail_type": ent2_span["type"]
                            }),
                            "heuristics_version": heuristics_version,
                        })
        
        except Exception as e:
            doc_id = _get_doc_id(doc)
            logger.error(f"Failed to extract from doc {doc_id}: {e}")
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


@task(
    retries=5,
    retry_delay_seconds=2,
    tags=["database", "storage"]
)
async def store_entities(extraction_result: Dict[str, Any]) -> Dict[str, int]:
    """Store extracted entities (and derived relationships) in database."""
    logger = get_run_logger()
    result_heuristics_version = extraction_result.get("heuristics_version")
    
    async with asyncpg.create_pool(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME", "bpo_intel"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres")
    ) as pool:
        async with pool.acquire() as conn:
            # Insert entities
            entity_count = 0
            for entity in extraction_result["entities"]:
                try:
                    await conn.execute(
                        """
                        INSERT INTO entities (doc_id, type, surface, norm_value, span, conf, source, source_version, heuristics_version, confidence_method)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT (doc_id, type, span_hash) DO NOTHING
                        """,
                        entity["doc_id"],
                        entity["type"],
                        entity["surface"],
                        entity["norm_value"],
                        entity["span"],
                        entity["conf"],
                        entity["source"],
                        entity["source_version"],
                        entity["heuristics_version"],
                        entity["confidence_method"]
                    )
                    entity_count += 1
                except Exception as e:
                    logger.warning(f"Failed to insert entity: {e}")
                    continue
            
            relationship_count = 0
            for rel in extraction_result.get("relationships", []):
                try:
                    head_id = await _lookup_entity_id(conn, rel["doc_id"], rel["head_span"])
                    tail_id = await _lookup_entity_id(conn, rel["doc_id"], rel["tail_span"])
                    if not head_id or not tail_id:
                        continue
                    await conn.execute(
                        """
                        INSERT INTO relationships (doc_id, head_entity, tail_entity, type, conf, evidence, heuristics_version)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT DO NOTHING
                        """,
                        rel["doc_id"],
                        head_id,
                        tail_id,
                        rel["type"],
                        rel["conf"],
                        rel["evidence"],
                        rel.get("heuristics_version", result_heuristics_version),
                    )
                    relationship_count += 1
                except Exception as e:
                    logger.warning(f"Failed to insert relationship: {e}")
                    continue
            
            logger.info(f"Stored {entity_count} entities and {relationship_count} relationships in database")
            return {"entities": entity_count, "relationships": relationship_count}


@task(
    retries=3,
    retry_delay_seconds=5,
    tags=["checkpoint"]
)
async def save_checkpoint(workflow_id: str, run_id: str, checkpoint_data: Dict) -> None:
    """Save checkpoint to database."""
    logger = get_run_logger()
    
    async with asyncpg.create_pool(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME", "bpo_intel"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres")
    ) as pool:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pipeline_checkpoints (workflow_id, run_id, phase, doc_offset, state, created_at, updated_at)
                VALUES ($1, $2, 'extraction', $3, $4, NOW(), NOW())
                ON CONFLICT (workflow_id, run_id, phase) DO UPDATE 
                SET doc_offset = EXCLUDED.doc_offset,
                    state = EXCLUDED.state,
                    updated_at = NOW()
                """,
                workflow_id,
                run_id,
                checkpoint_data.get("offset", 0),
                json.dumps(checkpoint_data),
            )
    
    logger.info(f"Checkpoint saved at offset {checkpoint_data.get('offset', 0)}")


@flow(
    name="document-extraction-pipeline",
    task_runner=ConcurrentTaskRunner(),
    retries=1,
    retry_delay_seconds=30,
    log_prints=True,
    timeout_seconds=7200  # 2 hour timeout
)
async def extract_documents_flow(
    source_path: str,
    heuristics_version: str = "2.0.0",
    batch_size: int = 100,
    start_offset: int = 0
):
    """
    Main extraction flow for processing documents with spaCy EntityRuler.
    
    Args:
        source_path: Path to JSONL file with documents
        heuristics_version: Version of heuristics to use
        batch_size: Number of documents per batch
        start_offset: Starting document offset
    
    Returns:
        Dict with processing summary
    """
    logger = get_run_logger()
    run_context = get_run_context()
    flow_run = getattr(run_context, "flow_run", None)
    flow_run_id = flow_run.id if flow_run else "local-run"
    workflow_id = f"extraction-{os.path.basename(source_path)}"
    
    logger.info(f"Starting extraction flow: {workflow_id}")
    logger.info(f"Source: {source_path}, Batch size: {batch_size}, Offset: {start_offset}")
    
    # Load checkpoint
    checkpoint = await load_checkpoint(workflow_id)
    current_offset = checkpoint.get("offset", start_offset)
    
    logger.info(f"Resuming from offset {current_offset}")
    
    total_entities = 0
    total_relationships = 0
    all_failed_docs = []
    total_docs_seen = current_offset
    
    # Process in batches
    for batch_start, batch_end, batch in _batched_documents(source_path, current_offset, batch_size):
        batch_id = f"{workflow_id}-batch-{batch_start}"
        
        logger.info(f"Processing batch {batch_start}-{batch_end}")
        
        normalized_batch = await insert_documents(batch)

        # Extract entities
        result = await extract_entities_batch(normalized_batch, batch_id, heuristics_version)
        
        # Store entities
        stored_counts = await store_entities(result)
        
        total_entities += stored_counts["entities"]
        total_relationships += stored_counts["relationships"]
        all_failed_docs.extend(result["failed_docs"])
        total_docs_seen = max(total_docs_seen, batch_end)
        
        # Save checkpoint every 1000 docs
        docs_since_start = batch_end - start_offset
        if docs_since_start > 0 and docs_since_start % 1000 == 0:
            await save_checkpoint(workflow_id, flow_run_id, {
                "offset": batch_end,
                "total_entities": total_entities,
                "total_relationships": total_relationships
            })
    
    # Final summary
    processed_docs = max(total_docs_seen - start_offset, 0)
    summary = {
        "workflow_id": workflow_id,
        "flow_run_id": flow_run_id,
        "total_processed": processed_docs,
        "total_entities": total_entities,
        "total_relationships": total_relationships,
        "failed_documents": all_failed_docs,
        "success_rate": ((processed_docs - len(all_failed_docs)) / processed_docs) if processed_docs else 0
    }
    
    logger.info(f"Extraction complete: {summary}")
    
    return summary
