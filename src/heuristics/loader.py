"""Heuristics loader with validation and indexing utilities."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

from pydantic import BaseModel, ConfigDict, Field, RootModel

logger = logging.getLogger(__name__)


@dataclass
class HeuristicsData:
    """Loaded heuristics data with indexes."""

    company_aliases: Dict[str, str]
    company_canonical_set: Set[str]
    countries: List[Dict[str, str]]
    country_names: Set[str]
    country_codes: Dict[str, str]
    tech_terms: List[Dict[str, Any]]
    tech_canonical: Dict[str, Dict[str, Any]]
    industries: List[Dict[str, Any]]
    industry_lookup: Dict[str, Tuple[Dict[str, Any], str]]
    services: List[Dict[str, Any]]
    service_lookup: Dict[str, Tuple[Dict[str, Any], str]]
    products: List[Dict[str, str]]
    partnerships: List[Dict[str, Any]]
    content_types: List[Dict[str, Any]]
    ner_relationships: Dict[str, Any]
    version: str
    version_data: Dict[str, Any]


class VersionMeta(BaseModel):
    version: str = "unknown"
    model_config = ConfigDict(extra="allow")


class CountryModel(BaseModel):
    name: str
    code: str
    aliases: List[str] = Field(default_factory=list)
    model_config = ConfigDict(extra="allow")


class CountriesPayload(RootModel[List[CountryModel]]):
    root: List[CountryModel]


class TechTerm(BaseModel):
    canonical: str
    synonyms: List[str] = Field(default_factory=list)
    model_config = ConfigDict(extra="allow")


class TechTermsPayload(BaseModel):
    tech_terms: List[TechTerm] = Field(default_factory=list)
    model_config = ConfigDict(extra="allow")


class TaxonomyItem(BaseModel):
    name: str
    aliases: List[str] = Field(default_factory=list)
    model_config = ConfigDict(extra="allow")


class IndustriesPayload(BaseModel):
    industries: List[TaxonomyItem] = Field(default_factory=list)
    model_config = ConfigDict(extra="allow")


class ServicesPayload(BaseModel):
    services: List[TaxonomyItem] = Field(default_factory=list)
    model_config = ConfigDict(extra="allow")


class ProductsPayload(BaseModel):
    products: List[Dict[str, Any]] = Field(default_factory=list)
    model_config = ConfigDict(extra="allow")


class PartnershipsPayload(BaseModel):
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    model_config = ConfigDict(extra="allow")


class ContentRule(BaseModel):
    label: str
    url_patterns: List[str] = Field(default_factory=list)
    title_patterns: List[str] = Field(default_factory=list)
    content_patterns: List[str] = Field(default_factory=list)
    min_patterns: int = 0
    pattern_weight: float = 1.0
    url_weight: float = 10.0
    title_weight: float = 5.0
    structure_signals: Dict[str, Any] = Field(default_factory=dict)
    min_score: float | None = None
    model_config = ConfigDict(extra="allow")


class ContentTypesPayload(BaseModel):
    rules: List[ContentRule] = Field(default_factory=list)
    model_config = ConfigDict(extra="allow")


class NERRelationshipsPayload(BaseModel):
    model_config = ConfigDict(extra="allow")


class HeuristicsIndexer:
    """Utility helpers for building heuristics indexes."""

    @staticmethod
    def company_canonical_set(company_aliases: Dict[str, str]) -> Set[str]:
        return {canonical for canonical in company_aliases.values() if canonical}

    @staticmethod
    def country_indexes(countries: Iterable[Dict[str, Any]]) -> Tuple[Set[str], Dict[str, str]]:
        names: Set[str] = set()
        codes: Dict[str, str] = {}
        for country in countries:
            names.add(country["name"])
            codes[country["code"]] = country["name"]
            for alias in country.get("aliases", []):
                names.add(alias)
        return names, codes

    @staticmethod
    def tech_canonical_index(tech_terms: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        canonical: Dict[str, Dict[str, Any]] = {}
        for term in tech_terms:
            name = term.get("canonical")
            if not name:
                continue
            canonical[name.lower()] = term
            for synonym in term.get("synonyms", []) or []:
                canonical[synonym.lower()] = term
        return canonical

    @staticmethod
    def taxonomy_lookup(items: Iterable[Dict[str, Any]]) -> Dict[str, Tuple[Dict[str, Any], str]]:
        lookup: Dict[str, Tuple[Dict[str, Any], str]] = {}
        for item in items:
            name = item.get("name")
            if not name:
                continue
            lookup[name.lower()] = (item, name)
            for alias in item.get("aliases", []) or []:
                lookup[alias.lower()] = (item, alias)
        return lookup


class HeuristicsLoader:
    """Loads and indexes heuristics files for fast lookup."""

    def __init__(self, heuristics_dir: str | None = None):
        resolved_dir = heuristics_dir or os.getenv("HEURISTICS_DIR", "Heuristics")
        self.heuristics_dir = Path(resolved_dir)
        self.data: HeuristicsData | None = None
        self._cache_signature: Tuple[Tuple[str, float], ...] | None = None

    def load(self, *, force_reload: bool = False) -> HeuristicsData:
        """Load all heuristics files and create indexes."""
        files = self._list_target_files()
        signature = self._snapshot_signature(files)
        if not force_reload and self.data and signature == self._cache_signature:
            logger.debug("Heuristics cache hit; returning existing data")
            return self.data

        logger.info(f"Loading heuristics from {self.heuristics_dir}")

        version_meta = VersionMeta.model_validate(self._load_json("version.json"))
        version = version_meta.version

        company_aliases_raw = self._load_json("company_aliases_clean.json")
        company_aliases = self._validate_company_aliases(company_aliases_raw)
        company_canonical_set = HeuristicsIndexer.company_canonical_set(company_aliases)
        logger.info(
            "Loaded %s company aliases (%s canonical forms)",
            len(company_aliases),
            len(company_canonical_set),
        )

        countries_payload = CountriesPayload.model_validate(self._load_json("countries.json"))
        countries = [country.model_dump() for country in countries_payload.root]
        country_names, country_codes = HeuristicsIndexer.country_indexes(countries)
        logger.info("Loaded %s countries", len(countries))

        tech_payload = TechTermsPayload.model_validate(self._load_json("tech_terms.json"))
        tech_terms = [term.model_dump() for term in tech_payload.tech_terms]
        tech_canonical = HeuristicsIndexer.tech_canonical_index(tech_terms)
        logger.info("Loaded %s tech terms", len(tech_terms))

        industries_payload = IndustriesPayload.model_validate(
            self._load_json("taxonomy_industries.json")
        )
        industries = [item.model_dump() for item in industries_payload.industries]
        industry_lookup = HeuristicsIndexer.taxonomy_lookup(industries)
        logger.info("Loaded %s industries", len(industries))

        services_payload = ServicesPayload.model_validate(
            self._load_json("taxonomy_services.json")
        )
        services = [item.model_dump() for item in services_payload.services]
        service_lookup = HeuristicsIndexer.taxonomy_lookup(services)
        logger.info("Loaded %s services", len(services))

        products_payload = ProductsPayload.model_validate(self._load_json("products.json"))
        products = products_payload.products
        logger.info("Loaded %s products", len(products))

        partnerships_payload = PartnershipsPayload.model_validate(
            self._load_json("partnerships.json")
        )
        partnerships = partnerships_payload.relationships
        logger.info("Loaded %s partnership types", len(partnerships))

        content_types = self._load_content_rules()
        if content_types:
            logger.info("Loaded %s content type rules", len(content_types))
        else:
            logger.warning("content_types.json not found; content classification disabled")

        ner_relationships_payload = NERRelationshipsPayload.model_validate(
            self._load_json("ner_relationships.json")
        )
        ner_relationships = ner_relationships_payload.model_dump()

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
            version_data=version_meta.model_dump(),
        )
        self._cache_signature = signature

        logger.info("Heuristics loaded successfully (version %s)", version)
        return self.data

    async def watch_for_changes(self, interval: float = 5.0):
        """Yield updated heuristics data whenever source files change."""
        while True:
            await asyncio.sleep(interval)
            current_signature = self._snapshot_signature(self._list_target_files())
            if current_signature != self._cache_signature:
                logger.info("Detected heuristics change; reloading")
                yield self.load(force_reload=True)

    def _load_content_rules(self) -> List[Dict[str, Any]]:
        try:
            payload = ContentTypesPayload.model_validate(self._load_json("content_types.json"))
            return [rule.model_dump() for rule in payload.rules]
        except FileNotFoundError:
            return []

    def _validate_company_aliases(self, payload: Any) -> Dict[str, str]:
        if not isinstance(payload, dict):
            raise ValueError("company_aliases_clean.json must be a JSON object")
        validated: Dict[str, str] = {}
        for alias, canonical in payload.items():
            if not isinstance(alias, str) or not isinstance(canonical, str):
                raise ValueError("All company aliases must map strings to strings")
            validated[alias] = canonical
        return validated

    def _load_json(self, filename: str) -> Any:
        filepath = self.heuristics_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Heuristics file not found: {filepath}")
        try:
            with open(filepath, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {filename}: {exc}") from exc

    def _list_target_files(self) -> List[Path]:
        filenames = [
            "version.json",
            "company_aliases_clean.json",
            "countries.json",
            "tech_terms.json",
            "taxonomy_industries.json",
            "taxonomy_services.json",
            "products.json",
            "partnerships.json",
            "ner_relationships.json",
        ]
        optional_files = ["content_types.json"]
        files = [self.heuristics_dir / name for name in filenames]
        for name in optional_files:
            path = self.heuristics_dir / name
            if path.exists():
                files.append(path)
        return files

    def _snapshot_signature(self, files: Iterable[Path]) -> Tuple[Tuple[str, float], ...]:
        signature = tuple(sorted((str(path), path.stat().st_mtime) for path in files if path.exists()))
        return signature

    def get_company_canonical(self, alias: str) -> str | None:
        if not self.data:
            raise RuntimeError("Heuristics not loaded. Call load() first.")
        return self.data.company_aliases.get(alias)

    def is_known_company(self, name: str) -> bool:
        if not self.data:
            raise RuntimeError("Heuristics not loaded. Call load() first.")
        return name in self.data.company_aliases or name in self.data.company_canonical_set

    def get_tech_term_data(self, term: str) -> Dict[str, Any] | None:
        if not self.data:
            raise RuntimeError("Heuristics not loaded. Call load() first.")
        return self.data.tech_canonical.get(term.lower())

    def is_known_country(self, name: str) -> bool:
        if not self.data:
            raise RuntimeError("Heuristics not loaded. Call load() first.")
        return name in self.data.country_names

    def get_country_code(self, code: str) -> str | None:
        if not self.data:
            raise RuntimeError("Heuristics not loaded. Call load() first.")
        return self.data.country_codes.get(code)


_heuristics_loader: HeuristicsLoader | None = None


def get_heuristics_loader(heuristics_dir: str | None = None) -> HeuristicsLoader:
    global _heuristics_loader
    if _heuristics_loader is None:
        env_dir = heuristics_dir or os.getenv("HEURISTICS_DIR", "Heuristics")
        _heuristics_loader = HeuristicsLoader(env_dir)
        _heuristics_loader.load()
    return _heuristics_loader
