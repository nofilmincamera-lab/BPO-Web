"""
spaCy pipeline with taxonomy-aware EntityRuler.
"""
import spacy
from spacy.pipeline import EntityRuler
from spacy.tokens import Span
from typing import Optional
import logging

logger = logging.getLogger(__name__)

_extraction_nlp: Optional[spacy.Language] = None


def get_extraction_nlp() -> spacy.Language:
    """
    Get or create spaCy pipeline with EntityRuler containing taxonomy.
    
    Pipeline:
    1. EntityRuler (taxonomy patterns) - runs BEFORE NER
    2. NER (statistical)
    3. Parser (for relationships)
    
    Loaded once per worker process, cached globally.
    """
    global _extraction_nlp
    
    if _extraction_nlp is not None:
        return _extraction_nlp
    
    logger.info("Building extraction spaCy pipeline with taxonomy EntityRuler")
    
    # Check for GPU availability
    gpu_available = False
    gpu_device = None
    try:
        import torch
        if torch.cuda.is_available():
            gpu_available = True
            gpu_device = torch.cuda.current_device()
            logger.info(f"GPU available - using GPU acceleration (device {gpu_device})")
        else:
            logger.info("GPU not available - using CPU")
    except ImportError:
        logger.info("PyTorch not available - using CPU")
    except Exception as e:
        logger.warning(f"Could not check GPU availability: {e}")
    
    # Load base model, exclude lemmatizer (not needed)
    nlp = spacy.load("en_core_web_sm", exclude=["lemmatizer"])
    
    # Add custom attributes for provenance
    if not Span.has_extension("extraction_source"):
        Span.set_extension("extraction_source", default="unknown")
    if not Span.has_extension("extraction_confidence"):
        Span.set_extension("extraction_confidence", default=0.70)
    if not Span.has_extension("canonical_form"):
        Span.set_extension("canonical_form", default=None)
    
    # Create EntityRuler and add BEFORE ner
    ruler = nlp.add_pipe("entity_ruler", before="ner")
    
    # Load taxonomy patterns
    patterns = _build_taxonomy_patterns()
    ruler.add_patterns(patterns)
    
    logger.info(f"Loaded {len(patterns)} taxonomy patterns into EntityRuler")
    
    # Add GPU metadata
    nlp.meta["gpu"] = gpu_available
    nlp.meta["gpu_device"] = gpu_device
    
    _extraction_nlp = nlp
    return _extraction_nlp


def _build_taxonomy_patterns() -> list:
    """Build EntityRuler patterns from all taxonomy files."""
    from src.heuristics import get_heuristics_loader
    
    heuristics = get_heuristics_loader()
    patterns = []
    
    # 1. Company aliases (3,361 entries)
    for alias, canonical in heuristics.data.company_aliases.items():
        patterns.append({
            "label": "COMPANY",
            "pattern": alias,
            "id": canonical,  # Store canonical form
        })
    
    # 2. Countries (52 entries)
    for country in heuristics.data.countries:
        patterns.append({
            "label": "LOCATION",
            "pattern": country["name"],
            "id": country["code"],
        })
        # Add aliases
        for alias in country.get("aliases", []):
            patterns.append({
                "label": "LOCATION",
                "pattern": alias,
                "id": country["code"],
            })
    
    # 3. Products (1,072 entries)
    for product in heuristics.data.products:
        patterns.append({
            "label": "PRODUCT",
            "pattern": product["name"],
            "id": product.get("category", "Unknown"),
        })
    
    # 4. Tech terms (20 entries)
    for term in heuristics.data.tech_terms:
        canonical = term["canonical"]
        patterns.append({
            "label": "TECHNOLOGY",
            "pattern": canonical,
            "id": canonical,
        })
        # Add synonyms
        for synonym in term.get("synonyms", []):
            patterns.append({
                "label": "TECHNOLOGY",
                "pattern": synonym,
                "id": canonical,
            })
    
    return patterns
