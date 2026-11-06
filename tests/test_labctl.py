import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import labctl  # noqa: E402

FLAG = "MFANO{sample}"
LINE = f"S1:{hashlib.sha256(FLAG.encode()).hexdigest()}:A01 Broken Access Control:Easy\n"


@pytest.fixture
def lab(tmp_path, monkeypatch):
    flags = tmp_path / "flags.sha256"
    flags.write_text("# header\n" + LINE, encoding="utf-8")
    monkeypatch.setattr(labctl, "FLAGS_FILE", flags)
    monkeypatch.setattr(labctl, "PROGRESS_FILE", tmp_path / ".labprogress.json")
    return flags


def test_wrong_flag(lab, capsys):
    assert labctl.main(["submit", "MFANO{nope}"]) == 1
    assert "wrong flag" in capsys.readouterr().out


def test_right_flag_then_repeat(lab, capsys):
    assert labctl.main(["submit", FLAG]) == 0
    assert "Correct! Stage S1 solved" in capsys.readouterr().out
    assert labctl.main(["submit", FLAG]) == 0
    assert "already solved" in capsys.readouterr().out


def test_status_hides_hash(lab, capsys):
    labctl.main(["status"])
    output = capsys.readouterr().out
    assert "0 / 1 solved" in output and "Next stage: S1" in output
    assert hashlib.sha256(FLAG.encode()).hexdigest() not in output


def test_empty_flag_file(lab, capsys):
    lab.write_text("# only a header\n", encoding="utf-8")
    assert labctl.main(["status"]) == 0
    assert "0 / 0 solved" in capsys.readouterr().out
    assert labctl.main(["submit", FLAG]) == 1
