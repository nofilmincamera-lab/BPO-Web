"""
BPO Intelligence Pipeline - Heuristics Loader

Loads and indexes all heuristics files at worker startup for fast entity extraction.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class HeuristicsData:
    """Loaded heuristics data with indexes."""
    # Company aliases
    company_aliases: Dict[str, str]  # alias -> canonical
    company_canonical_set: Set[str]  # All canonical company names
    
    # Countries
    countries: List[Dict[str, str]]  # [{name, code, aliases}, ...]
    country_names: Set[str]  # All country names + aliases
    country_codes: Dict[str, str]  # code -> name
    
    # Tech terms
    tech_terms: List[Dict[str, Any]]  # Full tech term objects
    tech_canonical: Dict[str, Dict[str, Any]]  # canonical -> tech term data
    
    # Taxonomy
    industries: List[Dict[str, Any]]
    industry_lookup: Dict[str, Tuple[Dict[str, Any], str]]
    services: List[Dict[str, Any]]
    service_lookup: Dict[str, Tuple[Dict[str, Any], str]]
    products: List[Dict[str, str]]
    partnerships: List[Dict[str, str]]
    content_types: List[Dict[str, Any]]
    
    # NER relationships
    ner_relationships: Dict[str, Any]
    
    # Version info
    version: str
    version_data: Dict[str, Any]


class HeuristicsLoader:
    """Loads and indexes heuristics files for fast lookup."""
    
    def __init__(self, heuristics_dir: str | None = None):
        """
        Initialize heuristics loader.
        
        Args:
            heuristics_dir: Path to heuristics directory
        """
        resolved_dir = heuristics_dir or os.getenv("HEURISTICS_DIR", "Heuristics")
        self.heuristics_dir = Path(resolved_dir)
        self.data: HeuristicsData | None = None
    
    def load(self) -> HeuristicsData:
        """
        Load all heuristics files and create indexes.
        
        Returns:
            HeuristicsData with all loaded and indexed data
        """
        logger.info(f"Loading heuristics from {self.heuristics_dir}")
        
        # Load version first
        version_data = self._load_json("version.json")
        version = version_data.get("version", "unknown")
        
        # Load company aliases
        company_aliases = self._load_json("company_aliases_clean.json")
        company_canonical_set = set(company_aliases.values())
        logger.info(f"Loaded {len(company_aliases)} company aliases ({len(company_canonical_set)} canonical forms)")
        
        # Load countries
        countries = self._load_json("countries.json")
        country_names = set()
        country_codes = {}
        for country in countries:
            country_names.add(country["name"])
            country_codes[country["code"]] = country["name"]
            # Add aliases if present
            for alias in country.get("aliases", []):
                country_names.add(alias)
        logger.info(f"Loaded {len(countries)} countries")
        
        # Load tech terms
        tech_terms_data = self._load_json("tech_terms.json")
        tech_terms = tech_terms_data.get("tech_terms", [])
        tech_canonical = {}
        for term in tech_terms:
            canonical = term["canonical"]
            tech_canonical[canonical.lower()] = term
            # Index synonyms
            for synonym in term.get("synonyms", []):
                tech_canonical[synonym.lower()] = term
        logger.info(f"Loaded {len(tech_terms)} tech terms")
        
        # Load taxonomy
        industries_data = self._load_json("taxonomy_industries.json")
        industries = industries_data.get("industries", [])
        industry_lookup: Dict[str, Tuple[Dict[str, Any], str]] = {}
        for item in industries:
            name = item.get("name")
            if not name:
                continue
            industry_lookup[name.lower()] = (item, name)
            for alias in item.get("aliases", []):
                industry_lookup[alias.lower()] = (item, alias)
        logger.info(f"Loaded {len(industries)} industries")
        
        services_data = self._load_json("taxonomy_services.json")
        services = services_data.get("services", [])
        service_lookup: Dict[str, Tuple[Dict[str, Any], str]] = {}
        for item in services:
            name = item.get("name")
            if not name:
                continue
            service_lookup[name.lower()] = (item, name)
            for alias in item.get("aliases", []):
                service_lookup[alias.lower()] = (item, alias)
        logger.info(f"Loaded {len(services)} services")
        
        # Load products
        products_data = self._load_json("products.json")
        products = products_data.get("products", [])
        logger.info(f"Loaded {len(products)} products")
        
        # Load partnerships
        partnerships_data = self._load_json("partnerships.json")
        partnerships = partnerships_data.get("relationships", [])
        logger.info(f"Loaded {len(partnerships)} partnership types")
        
        # Load content type rules (optional)
        try:
            content_types_data = self._load_json("content_types.json")
            content_types = content_types_data.get("rules", [])
            logger.info(f"Loaded {len(content_types)} content type rules")
        except FileNotFoundError:
            content_types = []
            logger.warning("content_types.json not found; content classification disabled")

        # Load NER relationships
        ner_relationships = self._load_json("ner_relationships.json")
        
        # Create HeuristicsData object
        self.data = HeuristicsData(
            company_aliases=company_aliases,
            company_canonical_set=company_canonical_set,
            countries=countries,
            country_names=country_names,
            country_codes=country_codes,
            tech_terms=tech_terms,
            tech_canonical=tech_canonical,
            industries=industries,
            industry_lookup=industry_lookup,
            services=services,
            service_lookup=service_lookup,
            products=products,
            partnerships=partnerships,
            content_types=content_types,
            ner_relationships=ner_relationships,
            version=version,
            version_data=version_data,
        )
        
        logger.info(f"Heuristics loaded successfully (version {version})")
        return self.data
    
    def _load_json(self, filename: str) -> Any:
        """Load a JSON file from heuristics directory."""
        filepath = self.heuristics_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Heuristics file not found: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {filename}: {e}")
    
    def get_company_canonical(self, alias: str) -> str | None:
        """
        Get canonical company name for an alias.
        
        Args:
            alias: Company alias or name
        
        Returns:
            Canonical company name or None if not found
        """
        if not self.data:
            raise RuntimeError("Heuristics not loaded. Call load() first.")
        
        return self.data.company_aliases.get(alias)
    
    def is_known_company(self, name: str) -> bool:
        """Check if a company name is known (exact match)."""
        if not self.data:
            raise RuntimeError("Heuristics not loaded. Call load() first.")
        
        # Check aliases
        if name in self.data.company_aliases:
            return True
        
        # Check canonical forms
        if name in self.data.company_canonical_set:
            return True
        
        return False
    
    def get_tech_term_data(self, term: str) -> Dict[str, Any] | None:
        """
        Get tech term data including confidence boosts.
        
        Args:
            term: Technology term (case-insensitive)
        
        Returns:
            Tech term data or None if not found
        """
        if not self.data:
            raise RuntimeError("Heuristics not loaded. Call load() first.")
        
        return self.data.tech_canonical.get(term.lower())
    
    def is_known_country(self, name: str) -> bool:
        """Check if a country name is known."""
        if not self.data:
            raise RuntimeError("Heuristics not loaded. Call load() first.")
        
        return name in self.data.country_names
    
    def get_country_code(self, code: str) -> str | None:
        """Get country name from ISO code."""
        if not self.data:
            raise RuntimeError("Heuristics not loaded. Call load() first.")
        
        return self.data.country_codes.get(code)


# Global heuristics loader instance
_heuristics_loader: HeuristicsLoader | None = None


def get_heuristics_loader(heuristics_dir: str | None = None) -> HeuristicsLoader:
    """
    Get or create the global heuristics loader instance.
    
    Args:
        heuristics_dir: Path to heuristics directory
    
    Returns:
        HeuristicsLoader instance with data loaded
    """
    global _heuristics_loader
    
    if _heuristics_loader is None:
        env_dir = heuristics_dir or os.getenv("HEURISTICS_DIR", "Heuristics")
        _heuristics_loader = HeuristicsLoader(env_dir)
        _heuristics_loader.load()
    
    return _heuristics_loader

