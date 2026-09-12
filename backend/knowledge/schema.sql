CREATE TABLE IF NOT EXISTS knowledge_records (
 id TEXT PRIMARY KEY,
 kind TEXT NOT NULL CHECK(kind IN ('event','paper','resource')),
 canonical_url TEXT NOT NULL,
 title TEXT NOT NULL,
 title_zh TEXT NOT NULL DEFAULT '',
 summary TEXT NOT NULL DEFAULT '',
 summary_zh TEXT NOT NULL DEFAULT '',
 object_type TEXT NOT NULL DEFAULT 'tool',
 topics TEXT NOT NULL DEFAULT '[]',
 source_id TEXT NOT NULL,
 published_at TEXT,
 collected_at TEXT NOT NULL,
 checked_at TEXT,
 updated_at TEXT NOT NULL,
 version TEXT NOT NULL DEFAULT '',
 completeness TEXT NOT NULL DEFAULT 'basic',
 status TEXT NOT NULL DEFAULT 'published',
 facts TEXT NOT NULL DEFAULT '{}',
 metadata TEXT NOT NULL DEFAULT '{}',
 UNIQUE(kind, canonical_url)
);
CREATE INDEX IF NOT EXISTS knowledge_kind_date ON knowledge_records(kind, published_at);
CREATE INDEX IF NOT EXISTS knowledge_updated ON knowledge_records(updated_at, id);
CREATE TABLE IF NOT EXISTS knowledge_evidence (
 id TEXT PRIMARY KEY,
 record_id TEXT NOT NULL REFERENCES knowledge_records(id),
 url TEXT NOT NULL,
 title TEXT NOT NULL,
 body TEXT NOT NULL DEFAULT '',
 locator TEXT NOT NULL DEFAULT '',
 version TEXT NOT NULL DEFAULT '',
 evidence_type TEXT NOT NULL DEFAULT 'source',
 coverage TEXT NOT NULL DEFAULT 'excerpt',
 retrieved_at TEXT NOT NULL,
 content_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_relations (
 id TEXT PRIMARY KEY,
 from_id TEXT NOT NULL REFERENCES knowledge_records(id),
 to_id TEXT NOT NULL REFERENCES knowledge_records(id),
 relation TEXT NOT NULL,
 evidence_url TEXT NOT NULL,
 note TEXT NOT NULL DEFAULT '',
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_changes (
 seq INTEGER PRIMARY KEY AUTOINCREMENT,
 record_id TEXT NOT NULL,
 action TEXT NOT NULL,
 snapshot TEXT NOT NULL,
 reason TEXT NOT NULL DEFAULT '',
 changed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS knowledge_changes_record ON knowledge_changes(record_id, seq);
CREATE TABLE IF NOT EXISTS knowledge_sources (
 id TEXT PRIMARY KEY,
 name TEXT NOT NULL,
 category TEXT NOT NULL,
 url TEXT NOT NULL,
 adapter TEXT NOT NULL,
 config TEXT NOT NULL DEFAULT '{}',
 enabled INTEGER NOT NULL DEFAULT 1,
 interval_days INTEGER NOT NULL DEFAULT 1 CHECK(interval_days = 1),
 last_attempt_at TEXT,
 last_success_at TEXT,
 status TEXT NOT NULL DEFAULT 'pending',
 error TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS knowledge_runs (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 source_id TEXT NOT NULL,
 started_at TEXT NOT NULL,
 finished_at TEXT,
 status TEXT NOT NULL,
 found INTEGER NOT NULL DEFAULT 0,
 changed INTEGER NOT NULL DEFAULT 0,
 error TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS knowledge_verifications (
 id TEXT PRIMARY KEY,
 record_id TEXT NOT NULL REFERENCES knowledge_records(id),
 title TEXT NOT NULL,
 method TEXT NOT NULL,
 version TEXT NOT NULL DEFAULT '',
 environment TEXT NOT NULL,
 steps TEXT NOT NULL,
 expected TEXT NOT NULL,
 result TEXT NOT NULL CHECK(result IN ('passed','failed','not_run')),
 output TEXT NOT NULL,
 limitations TEXT NOT NULL,
 checked_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_feedback (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 record_id TEXT,
 category TEXT NOT NULL,
 content TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_users (
 id TEXT PRIMARY KEY,
 username TEXT UNIQUE NOT NULL,
 password_hash TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_sessions (
 token_hash TEXT PRIMARY KEY,
 user_id TEXT NOT NULL REFERENCES knowledge_users(id),
 expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_collections (
 user_id TEXT NOT NULL REFERENCES knowledge_users(id),
 record_id TEXT NOT NULL,
 action TEXT NOT NULL CHECK(action IN ('save','follow')),
 created_at TEXT NOT NULL,
 PRIMARY KEY(user_id, record_id, action)
);
CREATE TABLE IF NOT EXISTS knowledge_subscriptions (
 user_id TEXT PRIMARY KEY REFERENCES knowledge_users(id),
 email TEXT NOT NULL,
 enabled INTEGER NOT NULL DEFAULT 0,
 unsubscribe_hash TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_jobs (
 record_id TEXT NOT NULL REFERENCES knowledge_records(id),
 stage TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending',
 input_hash TEXT NOT NULL DEFAULT '',
 attempts INTEGER NOT NULL DEFAULT 0,
 started_at TEXT,
 finished_at TEXT,
 error TEXT NOT NULL DEFAULT '',
 PRIMARY KEY(record_id,stage)
);
CREATE TABLE IF NOT EXISTS knowledge_settings (
 key TEXT PRIMARY KEY,
 value TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_source_progress (
 source_id TEXT PRIMARY KEY REFERENCES knowledge_sources(id),
 state TEXT NOT NULL DEFAULT '{}',
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_conflicts (
 id TEXT PRIMARY KEY,
 record_id TEXT NOT NULL REFERENCES knowledge_records(id),
 field TEXT NOT NULL,
 alternatives TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'open',
 resolution TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL,
 resolved_at TEXT
);
CREATE TABLE IF NOT EXISTS knowledge_editorial_actions (
 id TEXT PRIMARY KEY,
 action TEXT NOT NULL,
 payload TEXT NOT NULL,
 reason TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'applied',
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_briefs (
 date TEXT PRIMARY KEY,
 items TEXT NOT NULL,
 generated_at TEXT NOT NULL,
 scope TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_feedback_actions (
 feedback_id INTEGER PRIMARY KEY REFERENCES knowledge_feedback(id),
 status TEXT NOT NULL,
 resolution TEXT NOT NULL DEFAULT '',
 record_id TEXT,
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_task_materials (
 id TEXT PRIMARY KEY,
 title TEXT NOT NULL,
 persona TEXT NOT NULL,
 goal TEXT NOT NULL,
 content TEXT NOT NULL,
 record_ids TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'draft',
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_workflow_runs (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 kind TEXT NOT NULL,
 started_at TEXT NOT NULL,
 finished_at TEXT,
 status TEXT NOT NULL DEFAULT 'running',
 summary TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS knowledge_platform_profiles (
 record_id TEXT PRIMARY KEY REFERENCES knowledge_records(id),
 revision INTEGER NOT NULL,
 data TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_selections (
 record_id TEXT PRIMARY KEY REFERENCES knowledge_records(id),
 state TEXT NOT NULL CHECK(state IN ('candidate','review','published','needs_review','withdrawn')),
 revision INTEGER,
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_publications (
 seq INTEGER PRIMARY KEY AUTOINCREMENT,
 record_id TEXT NOT NULL REFERENCES knowledge_records(id),
 state TEXT NOT NULL,
 snapshot TEXT NOT NULL,
 reason TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS knowledge_publications_record ON knowledge_publications(record_id,seq);
CREATE TABLE IF NOT EXISTS knowledge_read_snapshots (
 id TEXT PRIMARY KEY,
 kind TEXT NOT NULL,
 query TEXT NOT NULL,
 data TEXT NOT NULL,
 created_at TEXT NOT NULL,
 expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_editions (
 id TEXT PRIMARY KEY,
 revision INTEGER NOT NULL,
 data TEXT NOT NULL,
 published_revision INTEGER,
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_edition_publications (
 seq INTEGER PRIMARY KEY AUTOINCREMENT,
 edition_id TEXT NOT NULL REFERENCES knowledge_editions(id),
 state TEXT NOT NULL,
 data TEXT NOT NULL,
 reason TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS knowledge_edition_history ON knowledge_edition_publications(edition_id,seq);
CREATE TABLE IF NOT EXISTS knowledge_platform_intake (
 id TEXT PRIMARY KEY,
 source_id TEXT NOT NULL REFERENCES knowledge_sources(id),
 record_id TEXT NOT NULL,
 fingerprint TEXT NOT NULL,
 data TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('pending','superseded','applied')),
 created_at TEXT NOT NULL,
 reviewed_at TEXT,
 editor TEXT
);
CREATE INDEX IF NOT EXISTS platform_intake_pending ON knowledge_platform_intake(state,created_at);
CREATE TABLE IF NOT EXISTS knowledge_platform_material_checks (
 source_id TEXT NOT NULL REFERENCES knowledge_sources(id),
 material_key TEXT NOT NULL,
 url TEXT NOT NULL,
 content_hash TEXT NOT NULL,
 checked_at TEXT NOT NULL,
 PRIMARY KEY(source_id,material_key)
);

-- Unified management: publication snapshots are separate from editable drafts.
CREATE TABLE IF NOT EXISTS fieldtofit_content_sets (
 kind TEXT PRIMARY KEY,
 published_json TEXT NOT NULL,
 revision INTEGER NOT NULL DEFAULT 1,
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fieldtofit_content_items (
 kind TEXT NOT NULL,
 id TEXT NOT NULL,
 draft_json TEXT NOT NULL,
 draft_version INTEGER NOT NULL DEFAULT 1,
 published_json TEXT,
 source_ref TEXT NOT NULL DEFAULT '',
 updated_at TEXT NOT NULL,
 PRIMARY KEY(kind,id)
);
CREATE TABLE IF NOT EXISTS fieldtofit_content_history (
 seq INTEGER PRIMARY KEY AUTOINCREMENT,
 kind TEXT NOT NULL,
 item_id TEXT NOT NULL,
 action TEXT NOT NULL,
 reason TEXT NOT NULL,
 snapshot TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fieldtofit_inbox (
 ref TEXT PRIMARY KEY,
 status TEXT NOT NULL CHECK(status IN ('pending','selected','deferred','ignored','completed')),
 kind TEXT NOT NULL DEFAULT '',
 item_id TEXT NOT NULL DEFAULT '',
 note TEXT NOT NULL DEFAULT '',
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fieldtofit_manual_candidates (
 ref TEXT PRIMARY KEY,
 title TEXT NOT NULL,
 summary TEXT NOT NULL,
 url TEXT NOT NULL,
 source TEXT NOT NULL,
 item_type TEXT NOT NULL,
 created_at TEXT NOT NULL,
 feedback_id INTEGER
);
CREATE TABLE IF NOT EXISTS fieldtofit_item_sources (
 kind TEXT NOT NULL,
 item_id TEXT NOT NULL,
 ref TEXT NOT NULL,
 PRIMARY KEY(kind,item_id,ref)
);
