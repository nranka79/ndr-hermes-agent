-- gws_oauth_tokens: per-user Google OAuth credential store
-- Keyed by telegram_id. One row per DRAAS employee.
-- Access tokens are transient (refreshed on demand by n8n; never sent to Hermes).
-- Run once on the VPS PostgreSQL instance that n8n uses.

CREATE TABLE IF NOT EXISTS gws_oauth_tokens (
    telegram_id         TEXT        PRIMARY KEY,
    telegram_username   TEXT,
    display_name        TEXT,
    email               TEXT,
    refresh_token       TEXT        NOT NULL,
    access_token        TEXT,
    token_expiry        TIMESTAMPTZ,
    scope               TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast name/username lookups (used by hermes-user-lookup workflow)
CREATE INDEX IF NOT EXISTS idx_gws_oauth_email         ON gws_oauth_tokens (LOWER(email));
CREATE INDEX IF NOT EXISTS idx_gws_oauth_username      ON gws_oauth_tokens (LOWER(telegram_username));
CREATE INDEX IF NOT EXISTS idx_gws_oauth_display_name  ON gws_oauth_tokens (LOWER(display_name));
