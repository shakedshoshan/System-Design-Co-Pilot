-- System Design Co-Pilot — core PostgreSQL DDL (human-readable reference).
-- Mirrors Alembic revision: 20260405_0001_initial_core_schema
-- Source of truth for *applied* schema: apps/api/migrations/versions/
-- UUID primary keys are generated in the application (no DB default here).

CREATE TABLE sessions (
    id UUID NOT NULL,
    title VARCHAR(512),
    phase VARCHAR(32) NOT NULL DEFAULT 'product',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT sessions_pkey PRIMARY KEY (id)
);

CREATE TABLE messages (
    id UUID NOT NULL,
    session_id UUID NOT NULL,
    role VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    extra JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT messages_pkey PRIMARY KEY (id),
    CONSTRAINT messages_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
);

CREATE INDEX ix_messages_session_id ON messages (session_id);

CREATE TABLE artifacts (
    id UUID NOT NULL,
    session_id UUID NOT NULL,
    artifact_type VARCHAR(64) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT artifacts_pkey PRIMARY KEY (id),
    CONSTRAINT artifacts_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE,
    CONSTRAINT uq_artifact_session_type_version
        UNIQUE (session_id, artifact_type, version)
);

CREATE INDEX ix_artifacts_session_id ON artifacts (session_id);
CREATE INDEX ix_artifacts_artifact_type ON artifacts (artifact_type);

CREATE TABLE event_logs (
    id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    level VARCHAR(16) NOT NULL,
    kind VARCHAR(128) NOT NULL,
    message TEXT NOT NULL,
    payload JSONB,
    session_id UUID,
    CONSTRAINT event_logs_pkey PRIMARY KEY (id),
    CONSTRAINT event_logs_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE SET NULL
);

CREATE INDEX ix_event_logs_created_at ON event_logs (created_at);
CREATE INDEX ix_event_logs_level ON event_logs (level);
CREATE INDEX ix_event_logs_kind ON event_logs (kind);
CREATE INDEX ix_event_logs_session_id ON event_logs (session_id);
