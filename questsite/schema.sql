DROP TABLE IF EXISTS general;
DROP TABLE IF EXISTS edits;
DROP TABLE IF EXISTS paragraphs;

CREATE TABLE general (
    name TEXT PRIMARY KEY,
    value BLOB
);

INSERT INTO general VALUES ('maxparagr', 1000);
INSERT INTO general VALUES ('size', 0);

CREATE TABLE edits (
    id INTEGER PRIMARY KEY,
    paragraph INTEGER NOT NULL,
    lang TEXT NOT NULL,
    type TEXT DEFAULT "new",
    previous INTEGER,
    stamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT,
    story TEXT
);

CREATE TABLE paragraphs (
    id INTEGER PRIMARY KEY,
    protected BOOLEAN CHECK (protected IN (TRUE, FALSE)) DEFAULT FALSE,
    current_ru INTEGER,
    current_en INTEGER
);
