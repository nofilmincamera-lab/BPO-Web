"""Constants used by the extraction flow."""
from __future__ import annotations

import re

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
