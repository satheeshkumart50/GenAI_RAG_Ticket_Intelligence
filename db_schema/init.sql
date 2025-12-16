-- ============================================================
-- Enable pgvector extension
-- ============================================================
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- Main Ticket Table: tickets
-- ============================================================
CREATE TABLE IF NOT EXISTS tickets (
    IncId TEXT PRIMARY KEY,
    Description TEXT,
    Submitter TEXT,
    CreateDate BIGINT,       -- epoch seconds
    IncidentStatus TEXT,
    AssignedGroup TEXT,
    Region TEXT,
    City TEXT,
    Category TEXT,
    WorkLog JSONB,
    Hub TEXT,
    Node TEXT,
    Agent TEXT,
    AlertDetails TEXT,
    AlertProcessId BIGINT,
    AlertKey TEXT,
    Related_Tickets TEXT,
    Related_CR TEXT,
    CR_Description TEXT,
    CR_StartTime BIGINT,
    CR_EndTime BIGINT,
    CR_Region TEXT
);

-- ============================================================
-- Recommended Indexes for Faster Filtering
-- ============================================================

-- Status-based queries
CREATE INDEX IF NOT EXISTS idx_tickets_status
    ON tickets (IncidentStatus);

-- Region filtering
CREATE INDEX IF NOT EXISTS idx_tickets_region
    ON tickets (Region);

-- Timestamp filtering (epoch)
CREATE INDEX IF NOT EXISTS idx_tickets_createdate
    ON tickets (CreateDate);

-- Category filtering
CREATE INDEX IF NOT EXISTS idx_tickets_category
    ON tickets (Category);

-- Assigned group filtering
CREATE INDEX IF NOT EXISTS idx_tickets_group
    ON tickets (AssignedGroup);

-- City filtering
CREATE INDEX IF NOT EXISTS idx_tickets_city
    ON tickets (City);

-- Hub filtering
CREATE INDEX IF NOT EXISTS idx_tickets_hub
    ON tickets (Hub);

-- Node filtering
CREATE INDEX IF NOT EXISTS idx_tickets_node
    ON tickets (Node);

-- Agent filtering
CREATE INDEX IF NOT EXISTS idx_tickets_agent
    ON tickets (Agent);

-- Alert Key filtering
CREATE INDEX IF NOT EXISTS idx_tickets_alertkey
    ON tickets (AlertKey);

-- CR Region filtering
CREATE INDEX IF NOT EXISTS idx_tickets_cr_region
    ON tickets (CR_Region);

-- CR time filtering
CREATE INDEX IF NOT EXISTS idx_tickets_cr_time
    ON tickets (CR_StartTime, CR_EndTime);

-- Related Ticket filtering
CREATE INDEX IF NOT EXISTS idx_tickets_related
    ON tickets (Related_Tickets);

-- ============================================================
-- Embedding Table for RAG: ticket_chunks
-- ============================================================
CREATE TABLE IF NOT EXISTS ticket_chunks (
    chunk_id BIGSERIAL PRIMARY KEY,
    IncId TEXT REFERENCES tickets(IncId) ON DELETE CASCADE,
    chunk_type TEXT,
    chunk_no INT,
    text_chunk TEXT,
    embedding VECTOR(384),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- HNSW Vector Index for Semantic Search
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_ticket_chunks_embedding
    ON ticket_chunks
    USING hnsw (embedding vector_l2_ops)
    WITH (m = 16, ef_construction = 200);
