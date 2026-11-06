DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS marks;
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
    fee_balance INTEGER NOT NULL
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
