# Product Context

## Problem

BPO industry research requires extracting structured entities from thousands of web documents. Manual extraction is slow and inconsistent.

## Solution

Automated NER pipeline with:
- Heuristics-first extraction (company aliases, tech terms, taxonomy)
- GPU-accelerated NLP (spaCy, embeddings)
- LLM fallback for edge cases
- Prefect orchestration for reliability (bypassable when needed)
- Docker work pool architecture

### Entity Coverage (Tiered)
- COMPANY, PERSON, DATE
- TECHNOLOGY, MONEY, PERCENT
- PRODUCT / COMPUTING_PRODUCT (merged handling)
- BUSINESS_TITLE, LOCATION, TIME_RANGE
- ORL (organizational relationships), TEMPORAL context spans, SKILL statements

## User Experience

- Queue work via API or run direct GPU script
- Monitor progress in Prefect UI (when using Prefect)
- Review validation reports
- Query extracted entities

## Goals

- Autonomous operation (background agent support) or direct GPU execution
- Overnight validation workflows
- Comprehensive analytics
- Self-updating documentation

