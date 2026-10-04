-- Public cumulative visits. Short-lived identifiers are separate from the total.
CREATE TABLE IF NOT EXISTS fieldtofit_visit_total (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    visits INTEGER NOT NULL CHECK (visits >= 0),
    started_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS fieldtofit_visit_sessions (
    browser_id TEXT PRIMARY KEY,
    last_seen INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_visit_sessions_expiry ON fieldtofit_visit_sessions(last_seen);
CREATE TABLE IF NOT EXISTS fieldtofit_visit_events (
    event_id TEXT PRIMARY KEY,
    received_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_visit_events_expiry ON fieldtofit_visit_events(received_at);
CREATE TABLE IF NOT EXISTS fieldtofit_visit_limits (
    scope TEXT NOT NULL,
    bucket INTEGER NOT NULL,
    hits INTEGER NOT NULL,
    PRIMARY KEY(scope,bucket)
);
-- v1.6 detailed analytics. Only digests, canonical paths and allowlisted labels.
CREATE TABLE IF NOT EXISTS fieldtofit_analytics_visitors(browser_id TEXT PRIMARY KEY, first_seen INTEGER NOT NULL, last_seen INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS fieldtofit_analytics_sessions(session_id TEXT PRIMARY KEY, browser_id TEXT NOT NULL, started_at INTEGER NOT NULL, last_seen INTEGER NOT NULL, entry TEXT NOT NULL, source TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_analytics_sessions_browser ON fieldtofit_analytics_sessions(browser_id,last_seen);
CREATE TABLE IF NOT EXISTS fieldtofit_analytics_events(event_id TEXT PRIMARY KEY, received_at INTEGER NOT NULL, day TEXT NOT NULL, browser_id TEXT, session_id TEXT, kind TEXT NOT NULL, path TEXT NOT NULL, content_id TEXT, source TEXT NOT NULL, is_returning INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS idx_analytics_events_time ON fieldtofit_analytics_events(received_at);
CREATE TABLE IF NOT EXISTS fieldtofit_analytics_daily(day TEXT PRIMARY KEY, pv INTEGER NOT NULL DEFAULT 0, uv INTEGER NOT NULL DEFAULT 0, sessions INTEGER NOT NULL DEFAULT 0, anonymous_pv INTEGER NOT NULL DEFAULT 0, content_views INTEGER NOT NULL DEFAULT 0, exports INTEGER NOT NULL DEFAULT 0, material_reads INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS fieldtofit_analytics_state(id INTEGER PRIMARY KEY CHECK(id=1), started_at INTEGER NOT NULL, updated_at INTEGER NOT NULL);
