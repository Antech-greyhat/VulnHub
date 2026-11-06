-- Results-backup database for Mfano High School.
-- Loaded into Postgres on first start. The database is protected only by a
-- weak/default password set in docker-compose.yml, which is the whole point:
-- a backup service left on a default credential.

CREATE TABLE marks_backup (
    admission TEXT NOT NULL,
    full_name TEXT NOT NULL,
    subject   TEXT NOT NULL,
    term      TEXT NOT NULL,
    score     INTEGER NOT NULL
);

CREATE TABLE payments_backup (
    admission TEXT NOT NULL,
    reference TEXT NOT NULL,
    amount    INTEGER NOT NULL,
    status    TEXT NOT NULL
);

-- Operational notes copied into the backup. Reading the backup at all is the
-- exploit, so the flag travels with the data.
CREATE TABLE backup_notes (
    note TEXT NOT NULL
);

INSERT INTO marks_backup (admission, full_name, subject, term, score) VALUES
    ('MHS1007', 'Neema Kariuki', 'Mathematics', '2026 Term 1', 71),
    ('MHS1007', 'Neema Kariuki', 'English',     '2026 Term 1', 65),
    ('MHS1013', 'Baraka Onyango', 'Biology',    '2026 Term 1', 88),
    ('MHS1013', 'Baraka Onyango', 'Chemistry',  '2026 Term 1', 90),
    ('MHS1021', 'Halima Wekesa', 'History',     '2026 Term 1', 54);

INSERT INTO payments_backup (admission, reference, amount, status) VALUES
    ('MHS1007', 'QF4K2M9A1', 20000, 'COMPLETED'),
    ('MHS1013', 'QF8Z3P7Q2', 30000, 'COMPLETED');

INSERT INTO backup_notes (note) VALUES
    ('Nightly dump of marks and payments. Restore with pg_restore.'),
    ('Reminder: rotate the backup DB password off the default. Flag: MFANO{default_creds_open_the_backup}');
