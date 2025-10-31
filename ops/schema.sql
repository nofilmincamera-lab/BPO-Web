-- BPO Intelligence Pipeline - Manual Schema Creation
-- This creates all tables when Alembic migrations fail

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL,
    canonical_url TEXT,
    text_sha256 VARCHAR(64) NOT NULL UNIQUE,
    status INTEGER NOT NULL,
    content_type TEXT,
    title TEXT,
    fetched_at TIMESTAMPTZ,
    lang VARCHAR(10),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_documents_url ON documents(url);
CREATE INDEX IF NOT EXISTS idx_documents_canonical_url ON documents(canonical_url);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_lang ON documents(lang);
CREATE INDEX IF NOT EXISTS idx_documents_fetched_at ON documents(fetched_at);

-- Document chunks table
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    seq INTEGER NOT NULL,
    text TEXT NOT NULL,
    text_sha256 VARCHAR(64) NOT NULL,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(doc_id, seq)
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_doc_id ON document_chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_text_sha256 ON document_chunks(text_sha256);

-- Entities table
CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES document_chunks(id) ON DELETE SET NULL,
    type VARCHAR(50) NOT NULL,
    surface TEXT NOT NULL,
    norm_value JSONB,
    span JSONB NOT NULL,
    span_hash BYTEA GENERATED ALWAYS AS (digest(span::text, 'sha256')) STORED,
    conf FLOAT NOT NULL,
    source TEXT,
    source_version TEXT,
    heuristics_version TEXT,
    confidence_method TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(doc_id, type, span_hash)
);

CREATE INDEX IF NOT EXISTS idx_entities_doc_id ON entities(doc_id);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_surface ON entities(surface);
CREATE INDEX IF NOT EXISTS idx_entities_conf ON entities(conf);
CREATE INDEX IF NOT EXISTS idx_entities_source ON entities(source);
CREATE INDEX IF NOT EXISTS idx_entities_chunk_id ON entities(chunk_id);

-- Relationships table
CREATE TABLE IF NOT EXISTS relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES document_chunks(id) ON DELETE SET NULL,
    head_entity UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    tail_entity UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    conf FLOAT,
    evidence JSONB,
    source TEXT,
    source_version TEXT,
    heuristics_version TEXT,
    confidence_method TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_relationships_doc_id ON relationships(doc_id);
CREATE INDEX IF NOT EXISTS idx_relationships_head ON relationships(head_entity);
CREATE INDEX IF NOT EXISTS idx_relationships_tail ON relationships(tail_entity);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(type);
CREATE INDEX IF NOT EXISTS idx_relationships_chunk_id ON relationships(chunk_id);

-- Taxonomy labels table
CREATE TABLE IF NOT EXISTS taxonomy_labels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    industry TEXT,
    service TEXT,
    technology TEXT,
    category TEXT,
    source TEXT,
    conf FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(doc_id, industry, service, technology, category, source)
);

CREATE INDEX IF NOT EXISTS idx_taxonomy_labels_doc_id ON taxonomy_labels(doc_id);
CREATE INDEX IF NOT EXISTS idx_taxonomy_labels_industry ON taxonomy_labels(industry);
CREATE INDEX IF NOT EXISTS idx_taxonomy_labels_service ON taxonomy_labels(service);
CREATE INDEX IF NOT EXISTS idx_taxonomy_labels_source ON taxonomy_labels(source);

-- Entity embeddings table (simplified, no vector type for now)
CREATE TABLE IF NOT EXISTS entity_embeddings (
    entity_id UUID PRIMARY KEY REFERENCES entities(id) ON DELETE CASCADE,
    embedding FLOAT[] NOT NULL,
    model_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Pipeline checkpoints table
CREATE TABLE IF NOT EXISTS pipeline_checkpoints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    doc_offset INTEGER NOT NULL DEFAULT 0,
    state JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(workflow_id, run_id, phase)
);

CREATE INDEX IF NOT EXISTS idx_checkpoints_workflow_id ON pipeline_checkpoints(workflow_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_phase ON pipeline_checkpoints(phase);

-- Schema version table
CREATE TABLE IF NOT EXISTS schema_version (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    description TEXT
);

INSERT INTO schema_version (version, description) 
VALUES ('001_initial_schema', 'Phase 2 - Complete BPO Intelligence Schema')
ON CONFLICT DO NOTHING;

