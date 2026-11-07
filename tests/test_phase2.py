import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "services" / "grading"))

import app as grading  # noqa: E402


def test_grading_health():
    client = grading.app.test_client()
    assert client.get("/").get_json()["status"] == "ok"


def test_grading_returns_fake_grades():
    client = grading.app.test_client()
    data = client.get("/grades?admission=MHS1013").get_json()
    assert data["result"]["mean_grade"] == "A-"


def test_grading_metadata_exposes_token_to_any_caller():
    # No auth header, no session - the internal service trusts everyone.
    data = grading.app.test_client().get("/internal/metadata").get_json()
    assert data["access_token"] == "MFANO{1nt3rn4l_d03s_n0t_m34n_s4f3}"
