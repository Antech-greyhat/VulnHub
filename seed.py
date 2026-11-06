#!/usr/bin/env python3
"""Fill the database with fake students, marks and payments."""
import argparse
import random
import sqlite3
import string
from pathlib import Path

from werkzeug.security import generate_password_hash

from portal import create_app

DEMO_STUDENT_PASSWORD = "Student@123"
DEMO_ADMIN = ("admin", "Mfano@Admin2026")

FIRST_NAMES = """Achieng Amani Baraka Chebet Daudi Eunice Faraja Gathoni Halima Imani Jabali Kamau
Kendi Kiprono Lulu Makena Mutua Nekesa Neema Njeri Odhiambo Otieno Pendo Rehema Salim Tumaini
Wafula Wanjiru Zawadi Zuberi""".split()
LAST_NAMES = """Mwangi Ochieng Kiptoo Mutiso Wekesa Onyango Kariuki Barasa Hamisi Nyambura Koech
Mumo""".split()
SUBJECTS = ["Mathematics", "English", "Kiswahili", "Biology", "Chemistry", "History"]
TERMS = ["2026 Term 1", "2026 Term 2"]
FORMS = ["Form 1", "Form 2", "Form 3", "Form 4"]
STREAMS = ["East", "West"]
FEE_TOTAL = 45000
STUDENT_COUNT = 30


def fake_reference(rng):
    return "QF" + "".join(rng.choices(string.ascii_uppercase + string.digits, k=8))


def seed_core(conn, rng):
    schema = Path(__file__).parent / "portal" / "schema.sql"
    conn.executescript(schema.read_text(encoding="utf-8"))
    student_hash = generate_password_hash(DEMO_STUDENT_PASSWORD)
    conn.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
        (DEMO_ADMIN[0], generate_password_hash(DEMO_ADMIN[1])),
    )
    names = rng.sample([f"{a} {b}" for a in FIRST_NAMES for b in LAST_NAMES], STUDENT_COUNT)
    for index, full_name in enumerate(names, start=1):
        admission = f"MHS{1000 + index}"
        user_id = conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'student')",
            (admission, student_hash),
        ).lastrowid
        paid = rng.choice([0, 10000, 20000, 30000])
        student_id = conn.execute(
            """INSERT INTO students (user_id, admission, full_name, form, stream, fee_total, fee_balance)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, admission, full_name, rng.choice(FORMS), rng.choice(STREAMS), FEE_TOTAL, FEE_TOTAL - paid),
        ).lastrowid
        for term in TERMS:
            for subject in SUBJECTS:
                conn.execute(
                    "INSERT INTO marks (student_id, subject, term, score) VALUES (?, ?, ?, ?)",
                    (student_id, subject, term, rng.randint(38, 92)),
                )
        if paid:
            conn.execute(
                """INSERT INTO payments (student_id, reference, amount, status, paid_at)
                   VALUES (?, ?, ?, 'COMPLETED', ?)""",
                (student_id, fake_reference(rng), paid, f"2026-0{rng.randint(1, 9)}-{rng.randint(10, 28)}"),
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--if-missing", action="store_true", help="do nothing if a database already exists")
    args = parser.parse_args()

    app = create_app()
    db_path = Path(app.config["DATABASE"])
    if args.if_missing and db_path.exists():
        return
    db_path.parent.mkdir(parents=True, exist_ok=True)
    Path(app.config["REPORT_DIR"]).mkdir(parents=True, exist_ok=True)

    rng = random.Random(2026)
    conn = sqlite3.connect(db_path)
    with conn:
        seed_core(conn, rng)
    conn.close()

    print("Demo logins (fake lab accounts):")
    print(f"  student: MHS1007 / {DEMO_STUDENT_PASSWORD}")
    print(f"  admin:   {DEMO_ADMIN[0]} / {DEMO_ADMIN[1]}")


if __name__ == "__main__":
    main()
