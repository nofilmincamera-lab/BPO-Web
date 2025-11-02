"""
Compiled regex pattern library for entity extraction.

This module centralizes all regex patterns used for entity extraction,
eliminating 8+ scattered pattern definitions across the codebase.
"""
import re


MONEY_PATTERN = re.compile(r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?')
PERCENT_PATTERN = re.compile(r'\d{1,3}(?:\.\d{1,2})?\s*%')
NUMBER_PATTERN = re.compile(r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b')
QUANTITY_PATTERN = re.compile(
    r'\b\d+\s+(?:units?|employees?|customers?|users?|clients?|staff|people|workers?|agents?|members?)\b',
    re.IGNORECASE
)
METRIC_PATTERN = re.compile(
    r'\b\d+\.?\d*\s*%?\s*(?:uptime|SLA|availability|accuracy|efficiency|satisfaction|NPS|CSAT|FCR|AHT|MTTR|MTBF)\b',
    re.IGNORECASE
)
DURATION_PATTERN = re.compile(
    r'\b\d+\s+(?:seconds?|minutes?|hours?|days?|weeks?|months?|years?)\b',
    re.IGNORECASE
)
TIME_RANGE_PATTERN = re.compile(
    r"(?:Q[1-4]\s*\d{4}|\d+\s+(?:day|week|month|year)s?|next\s+(?:quarter|year)|past\s+\d+\s+(?:months|years))",
    re.IGNORECASE
)
TEMPORAL_PATTERN = re.compile(
    r'\b(?:pre|post|mid)-(?:launch|merger|acquisition|pandemic)\b',
    re.IGNORECASE
)

# Backward compatibility aliases
TIME_RANGE_REGEX = TIME_RANGE_PATTERN
TEMPORAL_REGEX = TEMPORAL_PATTERN
