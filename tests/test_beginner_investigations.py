"""Recover the beginner investigation flags from the learner evidence (spoilers)."""
import csv
from email import policy
from email.parser import BytesParser
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "osint" / "sources"
VISITOR_MAP = SOURCES / "visitor-map.md"
PRINT_ROOM = ROOT / "forensics" / "starter"


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


def test_first_completed_hall_print_job(tmp_path):
    finished = [row for row in read_rows(PRINT_ROOM / "print-queue.csv")
                if row["printer"] == "hall" and row["document"] == "programme.pdf"
                and row["event"] == "printed"]
    first = min(finished, key=lambda row: row["time_eat"])
    submit_finding("F-08", first["job_id"], tmp_path)


def test_direct_parent_of_saved_email(tmp_path):
    message = BytesParser(policy=policy.default).parsebytes((PRINT_ROOM / "print-room.eml").read_bytes())
    parent = message["In-Reply-To"]
    assert parent != message["Message-ID"] and parent in message["References"].split()
    code, = re.findall(r"^<(\w+)@mfano\.example>$", parent)
    submit_finding("F-09", code, tmp_path)


def test_copy_matches_recorded_digest(tmp_path):
    note = (PRINT_ROOM / "handover.txt").read_text()
    digest, = re.findall(r"^SHA-256 +([a-f0-9]{64})$", note, re.M)
    copies = list((PRINT_ROOM / "copies").glob("*.txt"))
    assert len(copies) == 3
    match, = [path for path in copies if hashlib.sha256(path.read_bytes()).hexdigest() == digest]
    submit_finding("F-10", match.stem, tmp_path)
