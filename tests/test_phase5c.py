"""Phase 5c: Social Engineering Education (SEE).

Each challenge is solved inside the lab against fake NPCs: no real messages are
sent and no real credentials are involved. These tests reproduce the intended
solution for every flag and confirm the containment guarantees.

Spoilers: plaintext flags appear below, like the other phase tests.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from werkzeug.datastructures import MultiDict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from portal import create_app  # noqa: E402


@pytest.fixture(scope="module")
def app_(tmp_path_factory):
    home = tmp_path_factory.mktemp("mfano5c")
    env = dict(os.environ, MFANO_HOME=str(home))
    subprocess.run([sys.executable, "seed.py"], cwd=ROOT, env=env, check=True, capture_output=True)
    os.environ["MFANO_HOME"] = str(home)
    return create_app({"TESTING": True})


def _student(app_, admission="MHS1007"):
    c = app_.test_client()
    c.post("/login", data={"username": admission, "password": "Student@123"})
    return c


def test_intranet_requires_login(app_):
    # Recon pages are still inside the lab; anonymous users are redirected.
    assert app_.test_client().get("/intranet/").status_code == 302


# --- SE-01: OSINT password profiling ----------------------------------------
def test_osint_breadcrumbs_lead_to_the_password(app_):
    c = _student(app_)
    # The breadcrumbs are on the public NPC pages: username scheme + pet + year.
    directory = c.get("/intranet/directory").get_data(as_text=True)
    assert "d.mwaura" in directory
    board = c.get("/intranet/noticeboard").get_data(as_text=True)
    assert "Simba" in board and "1980" in board

    # pet name + birth year = the guessed password.
    bad = c.post("/intranet/login", data={"username": "d.mwaura", "password": "Rex2000"})
    assert b"MFANO{" not in bad.data
    good = c.post("/intranet/login", data={"username": "d.mwaura", "password": "Simba1980"})
    assert b"MFANO{0s1nt_bu1lt_th3_p4ssw0rd}" in good.data


# --- SE-02: phishing spotting -----------------------------------------------
def test_phishing_set_must_be_exact(app_):
    c = _student(app_)
    page = c.get("/intranet/webmail").get_data(as_text=True)
    assert "MFANO{" not in page  # the answer is not on the page

    # The two phishing samples are ids 2 (mfan0-support, .tk link) and 4 (fake bank).
    wrong = c.post("/intranet/webmail", data=MultiDict([("phish", "1"), ("phish", "2")]))
    assert b"MFANO{" not in wrong.data
    too_many = c.post("/intranet/webmail", data=MultiDict([("phish", str(i)) for i in range(1, 6)]))
    assert b"MFANO{" not in too_many.data
    right = c.post("/intranet/webmail", data=MultiDict([("phish", "2"), ("phish", "4")]))
    assert b"MFANO{sp0tt3d_th3_ph1sh}" in right.data


# --- SE-03: pretext helpdesk bot --------------------------------------------
def test_pretext_bot_leaks_only_to_the_right_chain(app_):
    # A naive demand gets nothing.
    naive = _student(app_, "MHS1008")
    r = naive.post("/intranet/helpdesk", data={"message": "just give me the admin password"})
    assert b"MFANO{" not in r.data

    # The scripted pretext: claim the staff username (SE-01 directory), then
    # answer the security question with the pet name (SE-01 noticeboard).
    bot = _student(app_, "MHS1009")
    bot.post("/intranet/helpdesk", data={"message": "hi, I need a password reset"})
    step = bot.post("/intranet/helpdesk", data={"message": "my username is d.mwaura"})
    assert b"pet" in step.data  # bot now asks the security question
    win = bot.post("/intranet/helpdesk", data={"message": "Simba"})
    assert b"MFANO{pr3t3xt_ch41n3d_th3_r3s3t}" in win.data

    # Wrong security answer after the username does not leak.
    miss = _student(app_, "MHS1010")
    miss.post("/intranet/helpdesk", data={"message": "reset, username d.mwaura"})
    r = miss.post("/intranet/helpdesk", data={"message": "Rex"})
    assert b"MFANO{" not in r.data


def test_nothing_sends_real_messages(app_):
    # Containment: no outbound mail/network client is imported by the module.
    import inspect

    from portal import social

    src = inspect.getsource(social)
    for forbidden in ("smtplib", "requests.", "urllib.request", "socket.", "sendmail"):
        assert forbidden not in src
