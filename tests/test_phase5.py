import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from portal import create_app  # noqa: E402


@pytest.fixture(scope="module")
def seeded_home(tmp_path_factory):
    home = tmp_path_factory.mktemp("mfano5")
    env = dict(os.environ, MFANO_HOME=str(home))
    subprocess.run([sys.executable, "seed.py"], cwd=ROOT, env=env, check=True, capture_output=True)
    os.environ["MFANO_HOME"] = str(home)
    return home


def test_frontend_secret_is_served_to_the_browser(seeded_home):
    app = create_app({"TESTING": True})
    body = app.test_client().get("/static/payment.js").data
    # The "secret" key is shipped to any visitor in client-side JS.
    assert b"MFANO{frontend_key_opened_the_till}" in body


def test_secret_is_recoverable_from_git_history():
    # The secret was removed from the tree but remains in git history.
    tree = subprocess.run(
        ["git", "grep", "-I", "git_history_never_forgets"], cwd=ROOT, capture_output=True, text=True
    )
    assert tree.returncode != 0  # not in the current tree

    history = subprocess.run(
        ["git", "log", "-p", "-S", "git_history_never_forgets"], cwd=ROOT, capture_output=True, text=True
    )
    assert "MFANO{git_history_never_forgets}" in history.stdout


def test_requirements_pins_outdated_dependency():
    reqs = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "requests==2.19.1" in reqs


def test_leaky_debugger_exposes_build_token(seeded_home):
    # Emulates the running server: debug on, WSGI app wrapped by the interactive
    # debugger, which renders the traceback (including the exception message).
    from werkzeug.debug import DebuggedApplication
    from werkzeug.test import Client

    app = create_app({"BUILD_TOKEN": "MFANO{stack_trace_told_everything}"})
    app.debug = True
    client = Client(DebuggedApplication(app.wsgi_app, evalex=False))
    resp = client.get("/diagnostics/self-test?load=0")
    html = resp.get_data(as_text=True)
    assert resp.status_code == 500
    assert "Traceback" in html
    assert "MFANO{stack_trace_told_everything}" in html


def test_no_leak_when_debug_off(seeded_home):
    app = create_app({"BUILD_TOKEN": "MFANO{stack_trace_told_everything}"})
    resp = app.test_client().get("/diagnostics/self-test?load=0")
    assert resp.status_code == 500
    assert b"MFANO{" not in resp.data
