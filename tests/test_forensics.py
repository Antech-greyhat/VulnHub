"""Structural checks for the forensics evidence pack.

These tests check that every evidence file is intact and parses as its own
format. They do not solve the challenges or contain any flags.
"""
import struct
import sys
import wave
import zlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "forensics" / "evidence"
sys.path.insert(0, str(ROOT))

import labctl  # noqa: E402

FILES = {
    "F-01": "01_noticeboard.png",
    "F-02": "02_staff_photo.png",
    "F-03": "03_prize_giving.png",
    "F-04": "04_school_bell.gif",
    "F-05": "05_radio_call.wav",
    "F-06": "06_assembly_recording.wav",
    "F-07": "07_corridor_cctv.avi",
}


def png_chunks(data):
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    while True:
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        crc = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])[0]
        assert zlib.crc32(kind + body) & 0xFFFFFFFF == crc, f"bad CRC in {kind!r}"
        pos += 12 + length
        yield kind, body, pos
        if kind == b"IEND":
            return


def test_every_stage_is_registered():
    stages = {stage["id"]: stage for stage in labctl.load_stages()}
    for stage_id in FILES:
        assert stage_id in stages
        assert stages[stage_id]["category"].startswith("Forensics")


def test_every_evidence_file_exists():
    assert sorted(p.name for p in EVIDENCE.iterdir()) == sorted(FILES.values())


@pytest.mark.parametrize("name", [n for n in FILES.values() if n.endswith(".png")])
def test_png_files_are_valid(name):
    chunks = list(png_chunks((EVIDENCE / name).read_bytes()))
    assert chunks[0][0] == b"IHDR" and chunks[-1][0] == b"IEND"


def test_gif_is_an_animation():
    data = (EVIDENCE / FILES["F-04"]).read_bytes()
    assert data[:6] == b"GIF89a" and data[-1:] == b"\x3b"
    assert data.count(b"\x21\xf9\x04") > 1  # more than one frame


@pytest.mark.parametrize("stage", ["F-05", "F-06"])
def test_wav_files_open(stage):
    with wave.open(str(EVIDENCE / FILES[stage])) as wf:
        assert wf.getnchannels() == 1 and wf.getsampwidth() == 2
        assert wf.getnframes() / wf.getframerate() > 5


def test_avi_is_a_riff_video():
    data = (EVIDENCE / FILES["F-07"]).read_bytes()
    assert data[:4] == b"RIFF" and data[8:12] == b"AVI "
    assert struct.unpack("<I", data[4:8])[0] == len(data) - 8
    assert b"movi" in data and b"idx1" in data


def test_only_the_easy_file_gives_a_flag_to_strings():
    # F-01 is meant to fall to `strings`; the rest need a real technique.
    for stage, name in FILES.items():
        found = b"MFANO{" in (EVIDENCE / name).read_bytes()
        assert found == (stage == "F-01"), name
