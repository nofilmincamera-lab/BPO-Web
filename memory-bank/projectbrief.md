# BPO Intelligence Pipeline - Project Brief

## Purpose

Automated NER (Named Entity Recognition) extraction pipeline for BPO industry intelligence, processing web-scraped documents to extract companies, locations, technologies, and relationships.

## Core Requirements

- Extract entities: COMPANY, LOCATION, PERSON, TECHNOLOGY, MONEY, PERCENT, DATE, PRODUCT/COMPUTING_PRODUCT, BUSINESS_TITLE, TIME_RANGE, ORL, TEMPORAL, SKILL
- Use heuristics-first approach with fallback tiers
- Store in PostgreSQL with pgvector for embeddings
- Orchestrate via Prefect for reliability (optional; direct GPU path supported)
- Support GPU acceleration (NVIDIA RTX 3060)
- Provide API endpoints for extraction
- Automated overnight validation

## Success Criteria

- 90%+ autonomous extraction (heuristics/spaCy/embeddings)
- <15% LLM fallback rate
- GPU-accelerated processing
- Prefect-based workflow orchestration or equivalent direct GPU pipeline
- Comprehensive taxonomy coverage

