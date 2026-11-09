DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS marks;
DROP TABLE IF EXISTS legacy_staff;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id            INTEGER PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('student', 'admin'))
);

CREATE TABLE students (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL UNIQUE REFERENCES users (id),
    admission   TEXT NOT NULL UNIQUE,
    full_name   TEXT NOT NULL,
    form        TEXT NOT NULL,
    stream      TEXT NOT NULL,
    fee_total   INTEGER NOT NULL,
    fee_balance INTEGER NOT NULL,
    remark      TEXT NOT NULL DEFAULT '',
    about       TEXT NOT NULL DEFAULT ''
);

CREATE TABLE staff_secrets (
    id     INTEGER PRIMARY KEY,
    label  TEXT NOT NULL,
    secret TEXT NOT NULL
);

-- Legacy staff logins kept around from an old system. Passwords are stored as
-- unsalted MD5 hashes (the Phase 5b weak-hashing bug). The injectable student
-- search can UNION these rows out; the hash then cracks against a wordlist.
CREATE TABLE legacy_staff (
    id           INTEGER PRIMARY KEY,
    username     TEXT NOT NULL UNIQUE,
    md5_password TEXT NOT NULL,
    display_name TEXT NOT NULL,
    memo         TEXT NOT NULL DEFAULT ''
);

CREATE TABLE marks (
    id         INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students (id),
    subject    TEXT NOT NULL,
    term       TEXT NOT NULL,
    score      INTEGER NOT NULL
);

CREATE TABLE payments (
    id         INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students (id),
    reference  TEXT NOT NULL UNIQUE,
    amount     INTEGER NOT NULL,
    status     TEXT NOT NULL,
    paid_at    TEXT NOT NULL
);
