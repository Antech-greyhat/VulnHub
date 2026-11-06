import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from portal import create_app  # noqa: E402


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    home = tmp_path_factory.mktemp("mfano1")
    env = dict(os.environ, MFANO_HOME=str(home))
    subprocess.run([sys.executable, "seed.py"], cwd=ROOT, env=env, check=True, capture_output=True)
    os.environ["MFANO_HOME"] = str(home)
    return create_app({"TESTING": True})


def login(client, username, password="Student@123"):
    return client.post("/login", data={"username": username, "password": password}, follow_redirects=True)


def student_id(app, admission):
    conn = sqlite3.connect(app.config["DATABASE"])
    row = conn.execute("SELECT id FROM students WHERE admission = ?", (admission,)).fetchone()
    conn.close()
    return row[0]


def test_report_idor_exposes_other_student(app):
    client = app.test_client()
    login(client, "MHS1007")
    victim = student_id(app, "MHS1013")
    body = client.get(f"/student/report?sid={victim}").data
    # Pulling another student's report (not our own) reveals the flag in it.
    assert b"MFANO{idor_reports_are_not_private}" in body


def test_own_report_has_no_flag(app):
    client = app.test_client()
    login(client, "MHS1007")
    assert b"MFANO{" not in client.get("/student/report").data


def test_report_requires_login(app):
    assert app.test_client().get("/student/report").status_code == 302


def test_ops_console_is_unprotected(app):
    # No login at all, yet the page opens and shows its token.
    body = app.test_client().get("/ops/students").data
    assert b"MFANO{unlinked_is_not_protected}" in body


def test_report_points_at_ops_console(app):
    client = app.test_client()
    login(client, "MHS1007")
    assert b"/ops/students" in client.get("/student/report").data


def test_report_files_and_notes_on_disk(app):
    report_dir = Path(app.config["REPORT_DIR"])
    assert (report_dir / "report_1.html").exists()
    notes = (report_dir / "ADMIN_NOTES.txt").read_text(encoding="utf-8")
    assert "MFANO{ls_cat_grep_find_the_trail}" in notes and "/ops/students" in notes
