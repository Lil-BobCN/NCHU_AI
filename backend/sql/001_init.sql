CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS admins (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  username varchar(64) NOT NULL UNIQUE,
  password_hash varchar(255) NOT NULL,
  display_name varchar(64) NOT NULL,
  is_active boolean NOT NULL DEFAULT true,
  last_login_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS documents (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  title varchar(255) NOT NULL,
  file_name varchar(255) NOT NULL,
  file_ext varchar(32) NOT NULL,
  mime_type varchar(128) NULL,
  file_size bigint NOT NULL,
  file_hash varchar(128) NOT NULL,
  storage_bucket varchar(128) NOT NULL,
  storage_object_key varchar(512) NOT NULL,
  knowledge_base varchar(64) NOT NULL DEFAULT 'default',
  source_url text NULL,
  preview_url text NULL,
  download_url text NULL,
  status varchar(32) NOT NULL DEFAULT 'uploaded',
  parse_quality_score numeric(5,2) NULL,
  error_message text NULL,
  created_by uuid NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz NULL
);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_active_file_name_ci
ON documents (lower(btrim(file_name)))
WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS knowledge_base_versions (
  scope varchar(64) PRIMARY KEY DEFAULT 'default',
  version bigint NOT NULL DEFAULT 1,
  changed_at timestamptz NOT NULL DEFAULT now(),
  reason varchar(128) NULL,
  document_id uuid NULL REFERENCES documents(id) ON DELETE SET NULL
);
INSERT INTO knowledge_base_versions(scope, version, changed_at, reason)
VALUES ('default', 1, now(), 'initial')
ON CONFLICT (scope) DO NOTHING;

CREATE TABLE IF NOT EXISTS document_jobs (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  job_type varchar(32) NOT NULL,
  status varchar(32) NOT NULL DEFAULT 'pending',
  progress integer NOT NULL DEFAULT 0,
  message text NULL,
  error_message text NULL,
  retry_count integer NOT NULL DEFAULT 0,
  params jsonb NOT NULL DEFAULT '{}',
  result jsonb NOT NULL DEFAULT '{}',
  started_at timestamptz NULL,
  finished_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_document_jobs_document_id ON document_jobs(document_id);
CREATE INDEX IF NOT EXISTS idx_document_jobs_status ON document_jobs(status);
CREATE INDEX IF NOT EXISTS idx_document_jobs_type_status ON document_jobs(job_type, status);

CREATE TABLE IF NOT EXISTS document_parse_results (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id uuid NOT NULL UNIQUE REFERENCES documents(id) ON DELETE CASCADE,
  parser_name varchar(64) NOT NULL,
  parser_version varchar(64) NULL,
  content_text text NOT NULL,
  content_md text NULL,
  content_object_key varchar(512) NULL,
  page_count integer NULL,
  quality_score numeric(5,2) NULL,
  parse_meta jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_chunks (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  parent_chunk_id uuid NULL REFERENCES document_chunks(id) ON DELETE SET NULL,
  chunk_no integer NOT NULL,
  chunk_type varchar(32) NOT NULL DEFAULT 'text',
  content text NOT NULL,
  content_hash varchar(128) NOT NULL,
  token_count integer NULL,
  char_count integer NOT NULL,
  page_start integer NULL,
  page_end integer NULL,
  section_path text NULL,
  metadata jsonb NOT NULL DEFAULT '{}',
  search_vector tsvector NULL,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_content_hash ON document_chunks(content_hash);
CREATE INDEX IF NOT EXISTS idx_chunks_active ON document_chunks(is_active);
CREATE INDEX IF NOT EXISTS idx_chunks_search_vector ON document_chunks USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON document_chunks USING GIN(metadata);

CREATE TABLE IF NOT EXISTS chunk_embeddings (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  chunk_id uuid NOT NULL UNIQUE REFERENCES document_chunks(id) ON DELETE CASCADE,
  document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  embedding vector(1024) NOT NULL,
  embedding_model varchar(128) NOT NULL,
  embedding_provider varchar(64) NOT NULL,
  content_hash varchar(128) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_document_id ON chunk_embeddings(document_id);
CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_content_hash ON chunk_embeddings(content_hash);
CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_vector_hnsw
ON chunk_embeddings USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS qa_pairs (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  question text NOT NULL,
  answer text NOT NULL,
  status varchar(32) NOT NULL DEFAULT 'enabled',
  source_document_id uuid NULL REFERENCES documents(id) ON DELETE SET NULL,
  source_chunk_ids uuid[] NULL,
  source_url text NULL,
  tags text[] NULL,
  version integer NOT NULL DEFAULT 1,
  created_by uuid NULL,
  updated_by uuid NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz NULL
);
CREATE INDEX IF NOT EXISTS idx_qa_pairs_status ON qa_pairs(status);
CREATE INDEX IF NOT EXISTS idx_qa_pairs_source_document_id ON qa_pairs(source_document_id);
CREATE INDEX IF NOT EXISTS idx_qa_pairs_question_trgm ON qa_pairs USING GIN(question gin_trgm_ops);

CREATE TABLE IF NOT EXISTS qa_pair_embeddings (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  qa_pair_id uuid NOT NULL UNIQUE REFERENCES qa_pairs(id) ON DELETE CASCADE,
  embedding vector(1024) NOT NULL,
  embedding_model varchar(128) NOT NULL,
  content_hash varchar(128) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_qa_pair_embeddings_vector_hnsw
ON qa_pair_embeddings USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS conversations (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  title varchar(255) NOT NULL,
  created_by uuid NULL,
  summary text NOT NULL DEFAULT '',
  context_state jsonb NOT NULL DEFAULT '{}',
  message_count integer NOT NULL DEFAULT 0,
  last_message_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz NULL
);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);

CREATE TABLE IF NOT EXISTS conversation_messages (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role varchar(32) NOT NULL,
  content text NOT NULL,
  rewritten_query text NULL,
  retrieval_trace jsonb NOT NULL DEFAULT '{}',
  citations jsonb NOT NULL DEFAULT '[]',
  suggested_questions jsonb NOT NULL DEFAULT '[]',
  latency_ms integer NULL,
  model_name varchar(128) NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON conversation_messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON conversation_messages(created_at DESC);

CREATE TABLE IF NOT EXISTS retrieval_logs (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id uuid NULL REFERENCES conversations(id) ON DELETE SET NULL,
  message_id uuid NULL REFERENCES conversation_messages(id) ON DELETE SET NULL,
  raw_query text NOT NULL,
  rewritten_query text NULL,
  recall_results jsonb NOT NULL DEFAULT '[]',
  rerank_results jsonb NOT NULL DEFAULT '[]',
  final_context jsonb NOT NULL DEFAULT '[]',
  citations jsonb NOT NULL DEFAULT '[]',
  suggested_questions jsonb NOT NULL DEFAULT '[]',
  answer text NULL,
  answer_quality jsonb NOT NULL DEFAULT '{}',
  model_name varchar(128) NULL,
  embedding_model varchar(128) NULL,
  rerank_model varchar(128) NULL,
  latency_ms integer NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_retrieval_logs_created_at ON retrieval_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_retrieval_logs_conversation_id ON retrieval_logs(conversation_id);

CREATE TABLE IF NOT EXISTS answer_feedbacks (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  user_message_id uuid NULL REFERENCES conversation_messages(id) ON DELETE SET NULL,
  assistant_message_id uuid NOT NULL REFERENCES conversation_messages(id) ON DELETE CASCADE,
  retrieval_log_id uuid NULL REFERENCES retrieval_logs(id) ON DELETE SET NULL,
  error_type varchar(32) NOT NULL,
  description text NOT NULL DEFAULT '',
  question_snapshot text NOT NULL DEFAULT '',
  answer_snapshot text NOT NULL DEFAULT '',
  citations_snapshot jsonb NOT NULL DEFAULT '[]',
  status varchar(32) NOT NULL DEFAULT 'open',
  created_by uuid NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_answer_feedbacks_conversation_status ON answer_feedbacks(conversation_id, status);
CREATE INDEX IF NOT EXISTS idx_answer_feedbacks_assistant_message ON answer_feedbacks(assistant_message_id);
CREATE INDEX IF NOT EXISTS idx_answer_feedbacks_created_at ON answer_feedbacks(created_at DESC);

CREATE TABLE IF NOT EXISTS evaluation_cases (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  question text NOT NULL,
  expected_answer text NULL,
  expected_document_ids uuid[] NULL,
  expected_chunk_ids uuid[] NULL,
  tags text[] NULL,
  difficulty varchar(32) NULL,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_eval_cases_active ON evaluation_cases(is_active);
CREATE INDEX IF NOT EXISTS idx_eval_cases_tags ON evaluation_cases USING GIN(tags);

CREATE TABLE IF NOT EXISTS evaluation_runs (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name varchar(255) NOT NULL,
  config jsonb NOT NULL DEFAULT '{}',
  metrics jsonb NOT NULL DEFAULT '{}',
  status varchar(32) NOT NULL DEFAULT 'running',
  started_at timestamptz NULL,
  finished_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evaluation_results (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  run_id uuid NOT NULL REFERENCES evaluation_runs(id) ON DELETE CASCADE,
  case_id uuid NOT NULL REFERENCES evaluation_cases(id) ON DELETE CASCADE,
  answer text NULL,
  hit_top3 boolean NULL,
  hit_top5 boolean NULL,
  answer_score numeric(5,2) NULL,
  citation_score numeric(5,2) NULL,
  suggested_question_score numeric(5,2) NULL,
  failure_reason varchar(64) NULL,
  trace jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_eval_results_run_id ON evaluation_results(run_id);
CREATE INDEX IF NOT EXISTS idx_eval_results_case_id ON evaluation_results(case_id);
