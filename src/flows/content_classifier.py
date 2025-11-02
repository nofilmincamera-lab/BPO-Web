"""Content classification utilities used within the extraction flow."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import re


def score_structure_signals(signals: Dict[str, Any], raw_text: str, lower_text: str, markdown: str) -> float:
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
        if re.search(r"\d+\s*(?:%|percent|percentage|bps)", lower_text):
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
        if re.search(r"[\"“”]", raw_text):
            score += 2.0

    if signals.get("has_code_blocks"):
        markdown_lower = markdown.lower()
        if "```" in markdown_lower or "<code" in markdown_lower:
            score += 3.0

    if signals.get("has_cta"):
        if re.search(r"\b(get started|sign up|try free|request demo|contact (us|sales))\b", lower_text):
            score += 2.0

    if signals.get("has_form"):
        md_lower = markdown.lower()
        if "<form" in md_lower or re.search(r"\bfill out\b", lower_text):
            score += 1.5

    if signals.get("has_date"):
        if re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december|\d{1,2}/\d{1,2}/\d{2,4}|20\d{2})\b", lower_text):
            score += 2.0

    if signals.get("has_registration"):
        if re.search(r"\b(register|registration|rsvp|save your spot)\b", lower_text):
            score += 2.0

    if signals.get("has_pricing_table"):
        if "<table" in markdown.lower() or re.search(r"\b(per month|per user|pricing plan|pricing tier)\b", lower_text):
            score += 2.5

    if signals.get("has_currency"):
        if re.search(r"[$£€¥]\s?\d|\b(usd|eur|gbp|cad|aud)\b", lower_text):
            score += 1.5

    if signals.get("has_requirements_list"):
        if re.search(r"\b(requirements|qualifications|responsibilities):", lower_text):
            score += 2.0

    if signals.get("has_names"):
        if re.search(r"\b(ceo|cfo|cto|coo|vp|vice president|manager|director)\b", lower_text):
            score += 1.5

    if signals.get("has_list"):
        if re.search(r"(^|\n)\s*(?:[-*•]|\d+\.)\s", markdown):
            score += 2.0

    if signals.get("has_steps"):
        if re.search(r"\bstep\s+\d+", lower_text):
            score += 1.5

    return score


def classify_content_type(
    url: str,
    title: Optional[str],
    body: str,
    rules: List[Dict[str, Any]],
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

        rule_score += score_structure_signals(
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
    confidence = (
        min(max_score / max(float(min_threshold), 30.0), 1.0)
        if meets_threshold
        else min(max_score / max(float(min_threshold or 30), 30.0), 0.6)
    )
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
