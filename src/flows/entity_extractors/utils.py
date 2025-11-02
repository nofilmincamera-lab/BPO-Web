"""Utility helpers for entity extraction."""
from __future__ import annotations

from typing import Dict, Iterator, List, Tuple
import re

from ..document_resolver import get_doc_id


def span_overlaps(start: int, end: int, existing: List[Tuple[int, int]]) -> bool:
    return any(not (end <= s or start >= e) for s, e in existing)


def iter_phrase_matches(text: str, phrase: str) -> Iterator[Tuple[int, int]]:
    """Yield start/end offsets for case-insensitive whole-phrase matches."""
    if not phrase:
        return
    pattern = re.compile(r"(?<!\w){}(?!\w)".format(re.escape(phrase)), re.IGNORECASE)
    for match in pattern.finditer(text):
        yield match.start(), match.end()


def ensure_doc_id(doc: Dict[str, Any]) -> str:
    return get_doc_id(doc)
