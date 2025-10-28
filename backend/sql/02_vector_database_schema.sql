-- ============================================================================
-- AdVisor Vector Database Schema (pgvector)
-- ============================================================================
-- This schema enables semantic search and similarity matching for personas,
-- communities, and content using vector embeddings.
-- ============================================================================

-- Enable pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- VECTOR EMBEDDING TABLES
-- ============================================================================

-- Persona Embeddings: Vector representations of persona summaries
CREATE TABLE IF NOT EXISTS persona_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    embedding VECTOR(1536), -- OpenAI ada-002 produces 1536-dim vectors
    model_name VARCHAR(100) DEFAULT 'text-embedding-ada-002',
    embedding_text TEXT, -- The text that was embedded
    metadata JSONB, -- Additional context (e.g., source communities, topics)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(persona_id, model_name)
);

-- Community Embeddings: Vector representations of community descriptions
CREATE TABLE IF NOT EXISTS community_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    community_id UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    embedding VECTOR(1536),
    model_name VARCHAR(100) DEFAULT 'text-embedding-ada-002',
    embedding_text TEXT,
    metadata JSONB, -- Top posts, sentiment, activity patterns, etc.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(community_id, model_name)
);

-- Content Cluster Embeddings: Vector representations of Reddit post/comment groups
CREATE TABLE IF NOT EXISTS content_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id VARCHAR(255), -- Reddit post ID or cluster ID
    content_type VARCHAR(50), -- 'post', 'comment_cluster', 'thread'
    embedding VECTOR(1536),
    model_name VARCHAR(100) DEFAULT 'text-embedding-ada-002',
    embedding_text TEXT, -- Original text or cluster summary
    community_name VARCHAR(255),
    metadata JSONB, -- upvotes, sentiment, keywords, etc.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ad Creative Embeddings: Vector representations of ad creatives
CREATE TABLE IF NOT EXISTS ad_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ad_id VARCHAR(255) UNIQUE,
    embedding VECTOR(1536),
    model_name VARCHAR(100) DEFAULT 'text-embedding-ada-002',
    embedding_text TEXT, -- Ad copy, description, or multimodal summary
    ad_type VARCHAR(50), -- 'image', 'video', 'text'
    metadata JSONB, -- visual features, performance metrics, brand info
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR VECTOR SIMILARITY SEARCH
-- ============================================================================

-- IVFFlat indexes for approximate nearest neighbor search
-- Lists parameter: use sqrt(num_rows) as a rule of thumb, or 100-200 for medium datasets

-- Index for persona embeddings
CREATE INDEX IF NOT EXISTS idx_persona_embeddings_vector
ON persona_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index for community embeddings
CREATE INDEX IF NOT EXISTS idx_community_embeddings_vector
ON community_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index for content embeddings
CREATE INDEX IF NOT EXISTS idx_content_embeddings_vector
ON content_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 200);

-- Index for ad embeddings
CREATE INDEX IF NOT EXISTS idx_ad_embeddings_vector
ON ad_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Regular indexes for filtering
CREATE INDEX IF NOT EXISTS idx_persona_embeddings_persona_id ON persona_embeddings(persona_id);
CREATE INDEX IF NOT EXISTS idx_community_embeddings_community_id ON community_embeddings(community_id);
CREATE INDEX IF NOT EXISTS idx_content_embeddings_content_type ON content_embeddings(content_type);
CREATE INDEX IF NOT EXISTS idx_content_embeddings_community ON content_embeddings(community_name);
CREATE INDEX IF NOT EXISTS idx_ad_embeddings_type ON ad_embeddings(ad_type);

-- ============================================================================
-- RPC FUNCTIONS FOR SIMILARITY SEARCH
-- ============================================================================

-- Match similar personas based on query embedding
CREATE OR REPLACE FUNCTION match_personas(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    persona_id UUID,
    persona_name TEXT,
    similarity FLOAT,
    embedding_text TEXT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id AS persona_id,
        p.name AS persona_name,
        1 - (pe.embedding <=> query_embedding) AS similarity,
        pe.embedding_text,
        pe.metadata
    FROM persona_embeddings pe
    JOIN personas p ON pe.persona_id = p.id
    WHERE 1 - (pe.embedding <=> query_embedding) > match_threshold
    ORDER BY pe.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Match similar communities based on query embedding
CREATE OR REPLACE FUNCTION match_communities(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    community_id UUID,
    community_name TEXT,
    similarity FLOAT,
    embedding_text TEXT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id AS community_id,
        c.name AS community_name,
        1 - (ce.embedding <=> query_embedding) AS similarity,
        ce.embedding_text,
        ce.metadata
    FROM community_embeddings ce
    JOIN communities c ON ce.community_id = c.id
    WHERE 1 - (ce.embedding <=> query_embedding) > match_threshold
    ORDER BY ce.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Match similar content (posts/comments) based on query embedding
CREATE OR REPLACE FUNCTION match_content(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 20,
    filter_content_type TEXT DEFAULT NULL,
    filter_community TEXT DEFAULT NULL
)
RETURNS TABLE (
    content_id VARCHAR,
    content_type VARCHAR,
    similarity FLOAT,
    embedding_text TEXT,
    community_name VARCHAR,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ce.content_id,
        ce.content_type,
        1 - (ce.embedding <=> query_embedding) AS similarity,
        ce.embedding_text,
        ce.community_name,
        ce.metadata
    FROM content_embeddings ce
    WHERE
        1 - (ce.embedding <=> query_embedding) > match_threshold
        AND (filter_content_type IS NULL OR ce.content_type = filter_content_type)
        AND (filter_community IS NULL OR ce.community_name = filter_community)
    ORDER BY ce.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Match similar ad creatives based on query embedding
CREATE OR REPLACE FUNCTION match_ads(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 10,
    filter_ad_type TEXT DEFAULT NULL
)
RETURNS TABLE (
    ad_id VARCHAR,
    ad_type VARCHAR,
    similarity FLOAT,
    embedding_text TEXT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ae.ad_id,
        ae.ad_type,
        1 - (ae.embedding <=> query_embedding) AS similarity,
        ae.embedding_text,
        ae.metadata
    FROM ad_embeddings ae
    WHERE
        1 - (ae.embedding <=> query_embedding) > match_threshold
        AND (filter_ad_type IS NULL OR ae.ad_type = filter_ad_type)
    ORDER BY ae.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Hybrid search: Find personas with both semantic similarity AND relational filters
CREATE OR REPLACE FUNCTION match_personas_hybrid(
    query_embedding VECTOR(1536),
    filter_community_name TEXT DEFAULT NULL,
    filter_interest_label TEXT DEFAULT NULL,
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    persona_id UUID,
    persona_name TEXT,
    similarity FLOAT,
    communities TEXT[],
    interests TEXT[],
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id AS persona_id,
        p.name AS persona_name,
        1 - (pe.embedding <=> query_embedding) AS similarity,
        ARRAY_AGG(DISTINCT c.name) AS communities,
        ARRAY_AGG(DISTINCT i.label) AS interests,
        pe.metadata
    FROM persona_embeddings pe
    JOIN personas p ON pe.persona_id = p.id
    LEFT JOIN persona_community pc ON p.id = pc.persona_id
    LEFT JOIN communities c ON pc.community_id = c.id
    LEFT JOIN persona_interest pi ON p.id = pi.persona_id
    LEFT JOIN interests i ON pi.interest_id = i.id
    WHERE
        1 - (pe.embedding <=> query_embedding) > match_threshold
        AND (filter_community_name IS NULL OR c.name = filter_community_name)
        AND (filter_interest_label IS NULL OR i.label = filter_interest_label)
    GROUP BY p.id, p.name, pe.embedding, pe.metadata, query_embedding
    ORDER BY pe.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Calculate cosine similarity between two vectors
CREATE OR REPLACE FUNCTION cosine_similarity(a VECTOR, b VECTOR)
RETURNS FLOAT AS $$
BEGIN
    RETURN 1 - (a <=> b);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Get persona with full context (KG + Vector)
CREATE OR REPLACE FUNCTION get_persona_context(persona_id_input UUID)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'persona', (SELECT row_to_json(p.*) FROM personas p WHERE p.id = persona_id_input),
        'communities', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'name', c.name,
                    'relevance_score', pc.relevance_score,
                    'context', pc.context
                )
            )
            FROM persona_community pc
            JOIN communities c ON pc.community_id = c.id
            WHERE pc.persona_id = persona_id_input
        ),
        'interests', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'label', i.label,
                    'affinity_score', pi.affinity_score,
                    'context', pi.context
                )
            )
            FROM persona_interest pi
            JOIN interests i ON pi.interest_id = i.id
            WHERE pi.persona_id = persona_id_input
        ),
        'creative_prefs', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'label', cp.label,
                    'importance_score', pp.importance_score,
                    'rationale', pp.rationale
                )
            )
            FROM persona_pref pp
            JOIN creative_prefs cp ON pp.pref_id = cp.id
            WHERE pp.persona_id = persona_id_input
        ),
        'embedding', (
            SELECT row_to_json(pe.*)
            FROM persona_embeddings pe
            WHERE pe.persona_id = persona_id_input
            LIMIT 1
        )
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

CREATE TRIGGER update_persona_embeddings_updated_at BEFORE UPDATE ON persona_embeddings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_community_embeddings_updated_at BEFORE UPDATE ON community_embeddings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_content_embeddings_updated_at BEFORE UPDATE ON content_embeddings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ad_embeddings_updated_at BEFORE UPDATE ON ad_embeddings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
