"""
BPO Intelligence Pipeline - Analytics Activity

Generate detailed analytics on heuristics performance.
"""

import json
from dataclasses import dataclass
from typing import Dict, Any, List
from pathlib import Path

from temporalio import activity


@dataclass
class HeuristicsAnalytics:
    """Analytics data for heuristics performance."""
    entity_type_distribution: Dict[str, int]
    tier_usage: Dict[str, int]
    confidence_distribution: Dict[str, int]
    heuristics_hit_rate: float
    company_alias_matches: int
    tech_term_matches: int
    taxonomy_coverage: Dict[str, int]


@activity.defn
async def analyze_heuristics_performance_activity(
    batch_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze heuristics performance from batch test metrics.
    
    Args:
        batch_metrics: Output from run_batch_extraction_activity
    
    Returns:
        Detailed analytics report
    """
    
    analytics = {
        "extraction_summary": {
            "total_documents": batch_metrics.get("total_documents", 0),
            "total_entities": sum(batch_metrics.get("entity_types", {}).values()),
            "avg_entities_per_doc": batch_metrics.get("summary", {}).get("avg_entities_per_doc", 0),
        },
        "entity_type_breakdown": dict(batch_metrics.get("entity_types", {})),
        "extraction_tier_breakdown": dict(batch_metrics.get("extraction_tiers", {})),
        "confidence_distribution": batch_metrics.get("confidence_ranges", {}),
        "heuristics_hit_rate": batch_metrics.get("summary", {}).get("heuristics_hit_rate", 0),
        "unique_extractions": {
            "companies": batch_metrics.get("summary", {}).get("unique_companies", 0),
            "locations": batch_metrics.get("summary", {}).get("unique_locations", 0),
            "tech_terms": batch_metrics.get("summary", {}).get("unique_tech_terms", 0),
        },
        "performance_metrics": {
            "heuristics_effectiveness": batch_metrics.get("summary", {}).get("heuristics_hit_rate", 0),
            "high_confidence_rate": batch_metrics.get("confidence_ranges", {}).get("high", 0) / 
                                    max(sum(batch_metrics.get("confidence_ranges", {}).values()), 1),
        }
    }
    
    activity.logger.info(f"Analytics generated: {analytics['extraction_summary']['total_entities']} entities analyzed")
    
    return analytics

