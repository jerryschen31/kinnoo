-- Initial auth schema migration.

CREATE TABLE IF NOT EXISTS users (
	id TEXT PRIMARY KEY,
	email TEXT NOT NULL UNIQUE,
	password_hash TEXT NOT NULL,
	role TEXT NOT NULL,
	force_password_change INTEGER NOT NULL DEFAULT 0,
	created_at TEXT NOT NULL,
	updated_at TEXT NOT NULL,
	locked_until TEXT,
	failed_login_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tenants (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	tenant_slug TEXT NOT NULL UNIQUE,
	owner_user_id TEXT NOT NULL,
	visibility TEXT NOT NULL DEFAULT 'private',
	created_at_epoch INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS identities (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	user_id TEXT NOT NULL,
	provider TEXT NOT NULL,
	provider_user_id TEXT NOT NULL,
	provider_email TEXT,
	created_at_epoch INTEGER NOT NULL,
	updated_at_epoch INTEGER,
	UNIQUE(provider, provider_user_id)
);

CREATE TABLE IF NOT EXISTS sessions (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	session_id TEXT NOT NULL UNIQUE,
	user_id TEXT NOT NULL,
	csrf_token TEXT NOT NULL,
	created_at_epoch INTEGER NOT NULL,
	expires_at_epoch INTEGER NOT NULL,
	invalidated_at_epoch INTEGER
);

CREATE TABLE IF NOT EXISTS one_time_tokens (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	token_type TEXT NOT NULL,
	subject_user_id TEXT,
	subject_email TEXT,
	token_hash TEXT NOT NULL UNIQUE,
	expires_at_epoch INTEGER,
	consumed_at_epoch INTEGER,
	created_at_epoch INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS password_history (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	user_id TEXT NOT NULL,
	password_hash TEXT NOT NULL,
	created_at_epoch INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_one_time_tokens_token_hash ON one_time_tokens(token_hash);
