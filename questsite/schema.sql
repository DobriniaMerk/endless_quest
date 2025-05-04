PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS general (
    name TEXT PRIMARY KEY,
    value BLOB
);

INSERT INTO general VALUES ('maxparagr', 1000);
INSERT INTO general VALUES ('size', 0);

CREATE TABLE IF NOT EXISTS variables (
    name TEXT NOT NULL,
    user_id INTEGER,
    visible INTEGER NOT NULL DEFAULT 0 CHECK (is_moderator IN (0,1)),
    value TEXT NOT NULL,
    PRIMARY KEY (name, user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS edits (
    id INTEGER PRIMARY KEY,
    paragraph INTEGER NOT NULL,
    lang TEXT NOT NULL,
    type TEXT DEFAULT "new",
    previous INTEGER,
    stamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT,
    story TEXT
);

CREATE TABLE IF NOT EXISTS paragraphs (
    id INTEGER PRIMARY KEY,
    protected BOOLEAN CHECK (protected IN (TRUE, FALSE)) DEFAULT FALSE,
    current_ru INTEGER,
    current_en INTEGER
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    is_moderator INTEGER NOT NULL DEFAULT 0 CHECK (is_moderator IN (0,1)),
    created_at TIMESTAMP NOT NULL DEFAULT (datetime('now')),
    last_login TEXT
)

CREATE TRIGGER IF NOT EXISTS users_set_created_at
    AFTER INSERT ON users
    FOR EACH ROW
    BEGIN
        UPDATE users
            SET created_at = datetime('now')
        WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS users_update_last_login
    BEFORE UPDATE ON users
    FOR EACH ROW
    WHEN NEW.username = OLD.username
        AND NEW.password_hash = OLD.password_hash
        AND NEW.email = OLD.email
    BEGIN
        UPDATE users SET last_login = datetime('now') WHERE id = OLD.id;
    END;

COMMIT
PRAGMA foreign_keys = ON;
