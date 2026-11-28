"""The yearbook proof is a public, unseeded browser challenge."""
import base64
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from threading import Thread

import pytest
from werkzeug.serving import make_server

from portal import create_app


ROOT = Path(__file__).resolve().parent.parent
PROOF = "/yearbook/proof/"


def assert_scores(stage, receipt, tmp_path):
    env = dict(os.environ, LABCTL_ROOT=str(ROOT), LABCTL_PROGRESS_FILE=str(tmp_path / "score.json"))
    result = subprocess.run(
        [str(ROOT / "labctl"), "--json", "submit", stage, "--flag-stdin", "--dry-run"],
        input=receipt + "\n", env=env, text=True, capture_output=True, check=True,
    )
    assert json.loads(result.stdout)["data"]["dry_run"]


def test_crawler_entry_leads_to_a_source_only_receipt(tmp_path):
    client = create_app({"TESTING": True}).test_client()
    rules = client.get("/robots.txt")
    assert rules.mimetype == "text/plain"
    assert f"Disallow: {PROOF}" in rules.text.splitlines()

    page = client.get(PROOF)
    assert page.status_code == 200
    comments = re.findall(r"<!--(.*?)-->", page.text, re.DOTALL)
    [receipt] = re.findall(r"MFANO\{[a-z0-9_]+\}", "\n".join(comments))
    assert "MFANO{" not in re.sub(r"<!--.*?-->", "", page.text, flags=re.DOTALL)
    assert_scores("WEB-01", receipt, tmp_path)


def test_edits_survive_reload_without_changing_the_portal_session():
    client = create_app({"TESTING": True}).test_client()
    guest = client.get(PROOF)
    cookie = client.get_cookie("yearbook_preview", path=PROOF)
    assert json.loads(base64.b64decode(cookie.value, validate=True)) == {"user": "guest", "role": "guest"}
    client.set_cookie("yearbook_preview", "unfinished-edit", path=PROOF)
    edited = client.get(PROOF)
    assert edited.data == guest.data and "Set-Cookie" not in edited.headers
    with client.session_transaction() as session:
        assert "role" not in session


def test_browser_switches_edition_on_refresh(tmp_path):
    playwright = pytest.importorskip("playwright.sync_api")
    chrome = shutil.which("chromium") or shutil.which("google-chrome")
    if not chrome:
        pytest.skip("A Chromium browser is needed for the preview check")

    with playwright.sync_playwright() as pw, make_server("127.0.0.1", 0, create_app(), threaded=True) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            browser = pw.chromium.launch(executable_path=chrome)
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{server.server_port}{PROOF}")
            edition = page.locator("#proof-edition")
            assert edition.inner_text() == "Guest preview"
            [cookie] = page.context.cookies()
            assert (cookie["name"], cookie["path"]) == ("yearbook_preview", PROOF)

            def refresh_with(value):
                page.context.add_cookies([{**cookie, "value": value}])
                page.reload()
                return edition.inner_text()

            assert refresh_with("unfinished-edit") == "Guest preview"
            for user, role in [("admin", "guest"), ("guest", "admin"), ("admin", "admin")]:
                fields = json.dumps({"role": role, "user": user}).encode()
                text = refresh_with(base64.b64encode(fields).decode("ascii"))
                if user == role == "admin":
                    assert text.startswith("Admin preview")
                    [receipt] = re.findall(r"MFANO\{[a-z0-9_]+\}", text)
                    assert_scores("WEB-02", receipt, tmp_path)
                else:
                    assert text == "Guest preview"
            assert [c["name"] for c in page.context.cookies()] == ["yearbook_preview"]
        finally:
            server.shutdown()
            thread.join()
