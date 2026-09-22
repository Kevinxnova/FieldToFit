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
