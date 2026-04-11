-- ==========================================
-- NCHU AI Counselor - Database Initialization
-- ==========================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) UNIQUE,
    name VARCHAR(100),
    department VARCHAR(100),
    email VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200),
    agent_state JSONB,
    context_window JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20),
    content TEXT,
    metadata JSONB,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Memories table (for Agent long-term memory)
CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    memory_type VARCHAR(50),
    content TEXT,
    embedding VECTOR(1536),
    importance_score FLOAT,
    last_accessed TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Documents table (RAG knowledge base metadata)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(200),
    title VARCHAR(500),
    content TEXT,
    chunk_index INTEGER,
    metadata JSONB,
    embedding VECTOR(1536),
    qdrant_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_conversations_user ON conversations(user_id, created_at);
CREATE INDEX idx_memories_user ON memories(user_id, memory_type);
CREATE INDEX idx_documents_source ON documents(source);
CREATE INDEX idx_memories_embedding ON memories USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_documents_embedding ON documents USING hnsw (embedding vector_cosine_ops);
