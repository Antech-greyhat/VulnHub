#!/usr/bin/env python3
"""Fill the database with fake students, marks and payments."""
import argparse
import random
import sqlite3
import string
from pathlib import Path

from werkzeug.security import generate_password_hash

from portal import create_app
from portal.reports import render_report

DEMO_STUDENT_PASSWORD = "Student@123"
DEMO_ADMIN = ("admin", "Mfano@Admin2026")

# One student's report carries the flag revealed by the report IDOR. The flag is
# in the data, not in the fetch route, so it only appears when you pull this
# student's report instead of your own.
FLAG_REMARK_ADMISSION = "MHS1013"
FLAG_REMARK = "Excellent term. Head teacher's commendation: MFANO{1d0r_r3p0rt5_4r3_n0t_pr1v4t3}"
PLAIN_REMARK = "A steady, improving term. Keep it up."

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
    # A staff-only table the SQL-injectable search can reach with a UNION.
    conn.execute(
        "INSERT INTO staff_secrets (label, secret) VALUES (?, ?)",
        ("exams_vault_key", "MFANO{un10n_s3l3ct_th3_st4ff_v4ult}"),
    )
    names = rng.sample([f"{a} {b}" for a in FIRST_NAMES for b in LAST_NAMES], STUDENT_COUNT)
    for index, full_name in enumerate(names, start=1):
        admission = f"MHS{1000 + index}"
        user_id = conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'student')",
            (admission, student_hash),
        ).lastrowid
        paid = rng.choice([0, 10000, 20000, 30000])
        remark = FLAG_REMARK if admission == FLAG_REMARK_ADMISSION else PLAIN_REMARK
        student_id = conn.execute(
            """INSERT INTO students (user_id, admission, full_name, form, stream, fee_total, fee_balance, remark)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, admission, full_name, rng.choice(FORMS), rng.choice(STREAMS), FEE_TOTAL, FEE_TOTAL - paid, remark),
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


def write_reports(app):
    """Render every student's report to disk and leave an ops note beside them.

    The report files sit in a world-readable folder on the lab box, so exploring
    the container filesystem reveals where reports live and surfaces the same
    admin-path clue the report itself carries.
    """
    report_dir = Path(app.config["REPORT_DIR"])
    report_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    for student in conn.execute("SELECT * FROM students").fetchall():
        marks = conn.execute(
            "SELECT subject, term, score FROM marks WHERE student_id = ? ORDER BY term, subject",
            (student["id"],),
        ).fetchall()
        (report_dir / f"report_{student['id']}.html").write_text(
            render_report(student, marks), encoding="utf-8"
        )
    conn.close()
    # Planted on the box for the command-injection exercise: an injected shell
    # command (e.g. `; cat /srv/mfano/server.flag`) can read it.
    Path(app.config["MFANO_HOME"]).mkdir(parents=True, exist_ok=True)
    (Path(app.config["MFANO_HOME"]) / "server.flag").write_text(
        "MFANO{s3m1c0l0n_r34ch3d_th3_sh3ll}\n", encoding="utf-8"
    )
    (report_dir / "ADMIN_NOTES.txt").write_text(
        "Mfano reporting - internal notes\n"
        "--------------------------------\n"
        "Reports are written here, one HTML file per student id (report_<id>.html).\n"
        "TODO before term opens: put the legacy ops console at /ops/students behind\n"
        "the staff login - right now anyone who knows the path can open it.\n"
        "Housekeeping flag: MFANO{ls_c4t_gr3p_f1nd_th3_tr41l}\n",
        encoding="utf-8",
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

    write_reports(app)

    print("Demo logins (fake lab accounts):")
    print(f"  student: MHS1007 / {DEMO_STUDENT_PASSWORD}")
    print(f"  admin:   {DEMO_ADMIN[0]} / {DEMO_ADMIN[1]}")


if __name__ == "__main__":
    main()
