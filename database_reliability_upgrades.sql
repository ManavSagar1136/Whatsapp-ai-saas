-- Iteration 1: Reliability DB Upgrades

-- 1. Idempotency Table to prevent processing the same Meta payload twice
CREATE TABLE processed_messages (
    message_id VARCHAR PRIMARY KEY,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast idempotency lookups
CREATE INDEX idx_processed_messages_id ON processed_messages(message_id);
