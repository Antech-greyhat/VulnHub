"""The yearbook proof is a public, unseeded browser challenge."""
import hashlib
import re
from pathlib import Path

from portal import create_app


ROOT = Path(__file__).resolve().parent.parent
PROOF = "/yearbook/proof/"


def test_crawler_entry_leads_to_a_source_only_receipt():
    client = create_app({"TESTING": True}).test_client()
    rules = client.get("/robots.txt")
    assert rules.mimetype == "text/plain"
    assert f"Disallow: {PROOF}" in rules.text.splitlines()

    page = client.get(PROOF)
    assert page.status_code == 200
    comments = re.findall(r"<!--(.*?)-->", page.text, re.DOTALL)
    [receipt] = re.findall(r"MFANO\{[a-z0-9_]+\}", "\n".join(comments))
    assert receipt not in re.sub(r"<!--.*?-->", "", page.text, flags=re.DOTALL)
    digest = hashlib.sha256(receipt.encode()).hexdigest()
    assert f"WEB-01:{digest}:" in (ROOT / "flags.sha256").read_text()
