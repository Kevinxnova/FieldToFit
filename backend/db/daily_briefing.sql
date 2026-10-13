CREATE TABLE IF NOT EXISTS fieldtofit_daily_issues (
 day TEXT PRIMARY KEY, draft_json TEXT NOT NULL, draft_version INTEGER NOT NULL,
 review_hash TEXT, review_json TEXT, published_revision INTEGER,
 state TEXT NOT NULL DEFAULT 'draft', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fieldtofit_daily_publications (
 day TEXT NOT NULL, revision INTEGER NOT NULL, snapshot_json TEXT NOT NULL,
 content_hash TEXT NOT NULL, published_at TEXT NOT NULL, reason_json TEXT NOT NULL,
 PRIMARY KEY(day, revision)
);
CREATE TABLE IF NOT EXISTS fieldtofit_daily_pdfs (
 day TEXT NOT NULL, revision INTEGER NOT NULL, lang TEXT NOT NULL,
 data_base64 TEXT NOT NULL, sha256 TEXT NOT NULL, pages INTEGER NOT NULL,
 PRIMARY KEY(day, revision, lang)
);
CREATE TABLE IF NOT EXISTS fieldtofit_daily_runs (
 day TEXT NOT NULL, phase TEXT NOT NULL, token TEXT NOT NULL, state TEXT NOT NULL,
 started_at TEXT NOT NULL, finished_at TEXT, lease_until TEXT NOT NULL,
 attempts INTEGER NOT NULL DEFAULT 1, result_json TEXT NOT NULL DEFAULT '{}',
 PRIMARY KEY(day, phase)
);
CREATE TABLE IF NOT EXISTS fieldtofit_daily_evidence (
 day TEXT PRIMARY KEY, payload_json TEXT NOT NULL, collected_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fieldtofit_daily_prepared (
 day TEXT NOT NULL, content_hash TEXT NOT NULL, lang TEXT NOT NULL,
 data_base64 TEXT NOT NULL, sha256 TEXT NOT NULL, pages INTEGER NOT NULL,
 PRIMARY KEY(day, content_hash, lang)
);
