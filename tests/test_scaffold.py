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
    home = tmp_path_factory.mktemp("mfano")
    env = dict(os.environ, MFANO_HOME=str(home))
    subprocess.run([sys.executable, "seed.py"], cwd=ROOT, env=env, check=True, capture_output=True)
    os.environ["MFANO_HOME"] = str(home)
    return create_app({"TESTING": True})


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password}, follow_redirects=True)


def test_seed_counts(app):
    conn = sqlite3.connect(app.config["DATABASE"])
    assert conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 30
    assert conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0] > 0
    conn.close()


def test_login_required(app):
    response = app.test_client().get("/student/")
    assert response.status_code == 302 and "/login" in response.location
    assert app.test_client().get("/admin/").status_code == 302


def test_wrong_password_rejected(app):
    assert b"Wrong username or password" in login(app.test_client(), "MHS1007", "nope").data


def test_student_dashboard(app):
    client = app.test_client()
    page = login(client, "MHS1007", "Student@123")
    assert b"My marks" in page.data and b"Fee balance" in page.data
    assert client.get("/payments/").status_code == 200


def test_admin_dashboard(app):
    client = app.test_client()
    page = login(client, "admin", "Mfano@Admin2026")
    assert b"MHS1001" in page.data
    assert client.get("/admin/marks").status_code == 200
    assert client.get("/admin/payments").status_code == 200
