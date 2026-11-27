"""Recover the beginner investigation flags from the learner evidence (spoilers)."""
import csv
import json
import os
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "osint" / "sources"
VISITOR_MAP = SOURCES / "visitor-map.md"


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def submit_finding(stage, code, tmp_path):
    progress = tmp_path / "progress.json"
    result = subprocess.run(
        [str(ROOT / "labctl"), "--json", "submit", stage, "--flag-stdin"],
        input=f"MFANO{{{code}}}\n", text=True, capture_output=True, check=True,
        env=dict(os.environ, LABCTL_ROOT=str(ROOT), LABCTL_PROGRESS_FILE=str(progress)),
    )
    assert json.loads(result.stdout)["data"]["recorded"] is True
    assert json.loads(progress.read_text())["solved"] == [stage]


def test_confirmed_swap_venue(tmp_path):
    updates = [row for row in read_rows(SOURCES / "notices.csv")
               if row["activity"] == "Book swap" and row["publisher"] == "Fair Committee"]
    venue = max(updates, key=lambda row: row["published_eat"])["location"]
    code, = re.findall(rf"^\| {re.escape(venue)} \| (\w+) \|$", VISITOR_MAP.read_text(), re.M)
    submit_finding("OSINT-01", code, tmp_path)


def test_original_photo_credit(tmp_path):
    clips = [row for row in read_rows(SOURCES / "press-index.csv") if row["caption"] == "The first crate"]
    original, *reprints = sorted(clips, key=lambda row: row["published_eat"])
    assert reprints and all(original["outlet"] in copy["credit"] for copy in reprints)
    submit_finding("OSINT-02", original["edition_code"], tmp_path)


def test_returns_desk_between_landmarks(tmp_path):
    notice, = [row for row in read_rows(SOURCES / "notices.csv")
               if row["activity"] == "Book returns" and row["publisher"] == "Library Volunteers"]
    assert "both the bell tower and the fountain" in notice["notice"]
    desk, = re.findall(r"\| Bell tower \| (\w+_d3sk) \| Fountain \|", VISITOR_MAP.read_text())
    submit_finding("OSINT-03", desk, tmp_path)
