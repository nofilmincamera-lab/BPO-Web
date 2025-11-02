"""
MWE-Aware (Multi-Word Expression) entity matcher.

This module provides intelligent matching for multi-word expressions,
prioritizing longer, more specific matches (e.g., "Business Process Outsourcing"
should match as one entity, not as separate words).

Uses industry heuristics as a guide for better entity recognition.
"""
import re
from typing import List, Dict, Any, Tuple, Set, Iterable


def normalize_phrase(phrase: str) -> str:
    """
    Normalize phrase for matching (lowercase, strip whitespace).
    
    Args:
        phrase: Input phrase string
        
    Returns:
        Normalized phrase
    """
    return phrase.lower().strip()


def create_mwe_pattern(phrase: str, case_sensitive: bool = False) -> re.Pattern:
    """
    Create a regex pattern for a multi-word expression.
    
    Ensures whole-word matching with proper word boundaries,
    handling punctuation and special characters.
    
    Args:
        phrase: The phrase to create a pattern for
        case_sensitive: Whether matching should be case-sensitive
        
    Returns:
        Compiled regex pattern
    """
    # Escape special regex characters
    escaped = re.escape(phrase)
    # Replace escaped spaces with flexible whitespace pattern
    escaped = escaped.replace(r'\ ', r'\s+')
    # Use word boundaries for whole-word matching
    pattern = rf'\b{escaped}\b'
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(pattern, flags)


def find_mwe_matches(text: str, phrases: List[str], case_sensitive: bool = False) -> Iterable[Tuple[int, int, str]]:
    """
    Find all matches for a list of phrases in text, prioritizing longer matches.
    
    This function is MWE-aware: it will match "Business Process Outsourcing"
    before matching "Business" or "Process" separately when those are in the list.
    
    Args:
        text: Text to search
        phrases: List of phrases to match (should be sorted by length, longest first)
        case_sensitive: Whether matching should be case-sensitive
        
    Yields:
        Tuples of (start, end, matched_phrase) for each match
    """
    if not phrases:
        return
    
    # Sort phrases by length (longest first) to prioritize longer MWEs
    sorted_phrases = sorted(phrases, key=len, reverse=True)
    
    # Track matched positions to avoid overlapping matches
    matched_positions: Set[Tuple[int, int]] = set()
    
    for phrase in sorted_phrases:
        if not phrase or not phrase.strip():
            continue
            
        pattern = create_mwe_pattern(phrase, case_sensitive)
        
        for match in pattern.finditer(text):
            start, end = match.start(), match.end()
            
            # Check if this position overlaps with a longer match
            overlaps = False
            for existing_start, existing_end in matched_positions:
                # Check if matches overlap (not just adjacent)
                if not (end <= existing_start or start >= existing_end):
                    overlaps = True
                    break
            
            if not overlaps:
                matched_positions.add((start, end))
                yield (start, end, phrase)


def iter_phrase_matches_mwe(text: str, phrase: str, case_sensitive: bool = False) -> Iterable[Tuple[int, int]]:
    """
    Yield start/end offsets for case-insensitive whole-phrase matches (MWE-aware).
    
    Enhanced version that handles multi-word expressions properly.
    
    Args:
        text: Text to search
        phrase: Phrase to match
        case_sensitive: Whether matching should be case-sensitive
        
    Yields:
        Tuples of (start, end) offsets for each match
    """
    if not phrase or not phrase.strip():
        return
    
    pattern = create_mwe_pattern(phrase, case_sensitive)
    for match in pattern.finditer(text):
        yield match.start(), match.end()


def build_industry_mwe_index(industries: List[Dict[str, Any]]) -> Dict[str, List[Tuple[Dict[str, Any], str]]]:
    """
    Build an index of industry names and aliases for efficient MWE-aware matching.
    
    Organizes industries by normalized surface form, handling both names and aliases.
    Prioritizes longer, more specific terms.
    
    Args:
        industries: List of industry dictionaries with 'name' and optional 'aliases'
        
    Returns:
        Dictionary mapping normalized surface forms to (industry_dict, original_phrase) tuples
    """
    index: Dict[str, List[Tuple[Dict[str, Any], str]]] = {}
    
    for industry in industries:
        if not industry:
            continue
        
        # Add primary name
        name = industry.get("name", "").strip()
        if name:
            normalized = normalize_phrase(name)
            if normalized not in index:
                index[normalized] = []
            index[normalized].append((industry, name))
        
        # Add aliases
        aliases = industry.get("aliases", [])
        if isinstance(aliases, list):
            for alias in aliases:
                if alias and isinstance(alias, str):
                    alias = alias.strip()
                    if alias:
                        normalized = normalize_phrase(alias)
                        if normalized not in index:
                            index[normalized] = []
                        index[normalized].append((industry, alias))
    
    return index


def extract_industry_mwes(
    text: str,
    industry_index: Dict[str, List[Tuple[Dict[str, Any], str]]],
    existing_spans: List[Tuple[int, int]] = None
) -> List[Dict[str, Any]]:
    """
    Extract industry entities using MWE-aware matching.
    
    Prioritizes longer, more specific industry names (e.g., "Business Process Outsourcing"
    matches before "Business" if both are in the index).
    
    Args:
        text: Text to extract from
        industry_index: Industry index built with build_industry_mwe_index
        existing_spans: List of (start, end) tuples for existing entity spans to avoid
        
    Returns:
        List of entity dictionaries with industry information
    """
    if existing_spans is None:
        existing_spans = []
    
    entities = []
    matched_spans: Set[Tuple[int, int]] = set()
    
    # Collect all phrases from index, sorted by length (longest first)
    all_phrases = []
    phrase_to_data = {}
    
    for normalized, industry_tuples in industry_index.items():
        # Use the original phrase (case-preserved) for matching
        for industry, original_phrase in industry_tuples:
            all_phrases.append(original_phrase)
            phrase_to_data[original_phrase] = industry_tuples[0]  # Use first match
    
    # Find matches using MWE-aware matching
    for start, end, matched_phrase in find_mwe_matches(text, all_phrases, case_sensitive=False):
        # Check overlap with existing spans
        overlaps = False
        for existing_start, existing_end in existing_spans:
            if not (end <= existing_start or start >= existing_end):
                overlaps = True
                break
        
        if overlaps:
            continue
        
        # Check overlap with other MWE matches
        if (start, end) in matched_spans:
            continue
        
        matched_spans.add((start, end))
        
        # Get industry data
        industry_data = phrase_to_data.get(matched_phrase)
        if not industry_data:
            continue
        
        industry, _ = industry_data
        surface_text = text[start:end]
        
        entities.append({
            "start": start,
            "end": end,
            "surface": surface_text,
            "industry": industry,
            "matched_phrase": matched_phrase,
        })
    
    return entities


def span_overlaps(start: int, end: int, existing_spans: List[Tuple[int, int]]) -> bool:
    """
    Check if a span overlaps with any existing spans (MWE-aware).
    
    Args:
        start: Start position of span
        end: End position of span
        existing_spans: List of (start, end) tuples for existing spans
        
    Returns:
        True if overlap detected, False otherwise
    """
    for existing_start, existing_end in existing_spans:
        # Overlap exists if spans are not completely separate
        if not (end <= existing_start or start >= existing_end):
            return True
    return False
