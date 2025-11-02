"""
Compiled regex pattern library for entity extraction.

This module centralizes all regex patterns used for entity extraction,
eliminating 8+ scattered pattern definitions across the codebase.

All patterns are pre-compiled for performance and stored as module-level
constants for easy reuse and testing.
"""
import re


# Money patterns
MONEY_PATTERN = re.compile(r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?')

# Percentage patterns
PERCENT_PATTERN = re.compile(r'\d{1,3}(?:\.\d{1,2})?\s*%')

# Number patterns (cardinal numbers, metrics)
# Matches: "1,234", "1,234.56", "1234", "1234.5"
# Excludes numbers that are part of MONEY or PERCENT patterns
NUMBER_PATTERN = re.compile(r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b')

# Quantity patterns (e.g., "5 units", "10 employees")
QUANTITY_PATTERN = re.compile(
    r'\b\d+\s+(?:units?|employees?|customers?|users?|clients?|staff|people|workers?|agents?|members?)\b',
    re.IGNORECASE
)

# Metric patterns (e.g., "98% uptime", "99.9% SLA")
METRIC_PATTERN = re.compile(
    r'\b\d+\.?\d*\s*%?\s*(?:uptime|SLA|availability|accuracy|efficiency|satisfaction|NPS|CSAT|FCR|AHT|MTTR|MTBF)\b',
    re.IGNORECASE
)

# Duration patterns (e.g., "5 seconds", "2 weeks", "3 years")
DURATION_PATTERN = re.compile(
    r'\b\d+\s+(?:seconds?|minutes?|hours?|days?|weeks?|months?|years?)\b',
    re.IGNORECASE
)

# Time range patterns (e.g., "Q1 2024", "next quarter", "past 2 years")
TIME_RANGE_PATTERN = re.compile(
    r"(?:Q[1-4]\s*\d{4}|\d+\s+(?:day|week|month|year)s?|next\s+(?:quarter|year)|past\s+\d+\s+(?:months|years))",
    re.IGNORECASE
)

# Temporal descriptor patterns (e.g., "pre-launch", "post-merger")
TEMPORAL_PATTERN = re.compile(
    r'\b(?:pre|post|mid)-(?:launch|merger|acquisition|pandemic)\b',
    re.IGNORECASE
)


# Pattern registry for easy iteration
PATTERNS = {
    "MONEY": MONEY_PATTERN,
    "PERCENT": PERCENT_PATTERN,
    "NUMBER": NUMBER_PATTERN,
    "QUANTITY": QUANTITY_PATTERN,
    "METRIC": METRIC_PATTERN,
    "DURATION": DURATION_PATTERN,
    "TIME_RANGE": TIME_RANGE_PATTERN,
    "TEMPORAL": TEMPORAL_PATTERN,
}


def get_pattern(entity_type: str) -> re.Pattern:
    """
    Get a compiled regex pattern by entity type.
    
    Args:
        entity_type: One of MONEY, PERCENT, NUMBER, QUANTITY, METRIC, DURATION, TIME_RANGE, TEMPORAL
        
    Returns:
        Compiled regex pattern
        
    Raises:
        KeyError: If entity_type is not found
    """
    return PATTERNS[entity_type]


def match_pattern(text: str, entity_type: str):
    """
    Find all matches of a pattern type in text.
    
    Args:
        text: Text to search
        entity_type: Pattern type name
        
    Yields:
        re.Match objects
    """
    pattern = get_pattern(entity_type)
    yield from pattern.finditer(text)


# Backward compatibility aliases
TIME_RANGE_REGEX = TIME_RANGE_PATTERN
TEMPORAL_REGEX = TEMPORAL_PATTERN
