"""Phase 5b: weak-cryptography challenges.

Each route here misuses a crypto primitive on purpose:

* /staff/login     - verifies passwords stored as unsalted MD5 (C1).
* cookies issued to students carry a base64 "locker" value sold as encrypted (C2),
  and a JWT signed with a weak, guessable secret (C3).
* /api/exam-key    - trusts that JWT; forge role=admin to read the flag (C3).
* /api/seal        - an AES-ECB oracle; byte-at-a-time recovery leaks a flag (C5).

The hardcoded-key challenge (C4) needs no route: the key and the ciphertext are
shipped together in portal/static/app.config.js, so the browser can decrypt them.

Nothing here should ever be copied into real code.
"""
import base64
import hashlib
import os

from flask import Blueprint, abort, jsonify, make_response, render_template, request

from .auth import login_required
from .cryptolib import aes_ecb_encrypt, jwt_decode, jwt_encode
from .db import get_db

bp = Blueprint("crypto", __name__)

# C1 pay-off: shown only after a successful legacy staff login, which requires
# cracking the unsalted MD5 hash first. It lives here, not in the database, so
# the SQL-injection that leaks the hash cannot also leak the flag.
STAFF_FLAG = "MFANO{md5_cr4ck3d_th3_st4ff_h4sh}"

# C3: the session/API JWT is signed with this weak, guessable secret. Cracking
# it (hashcat -m 16500, jwt_tool, or a tiny wordlist) lets anyone forge tokens.
JWT_SECRET = "mfano123"

# C2: a value handed to the browser in a cookie and labelled "encrypted". It is
# only base64 - encoding, not encryption - so decoding it hands over the flag.
VAULT_COOKIE_B64 = "TUZBTk97YjRzM19zMXh0eWYwdXJfMXNfbjB0X2NyeXB0MH0="

# C3 pay-off: only returned to a token whose role is "admin". A staff token can
# be *re-signed* to admin once the weak secret above is cracked.
EXAM_KEY_FLAG = "MFANO{w34k_jwt_s3cr3t_f0rg3d_4dm1n}"

# C5: the secret appended by the ECB oracle. The key is random per process (the
# attacker never needs it); ECB's blockwise determinism is what leaks the flag.
_ECB_KEY = os.urandom(16)
_ECB_SECRET = b"MFANO{3cb_r3p34ts_g1v3_1t_4w4y}"


def issue_student_cookies(response, admission):
    """Attach the Phase 5b student cookies to an outgoing response.

    mfano_vault - C2 fake "encrypted" locker token (actually base64).
    mfano_api   - C3 JWT signed with the weak JWT_SECRET, role "student".
    """
    response.set_cookie("mfano_vault", VAULT_COOKIE_B64)
    token = jwt_encode({"sub": admission, "role": "student"}, JWT_SECRET)
    response.set_cookie("mfano_api", token)
    return response


# --- C1: legacy staff login verifying unsalted MD5 ---------------------------
@bp.route("/staff/login", methods=["GET", "POST"])
def staff_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        row = get_db().execute(
            "SELECT username, md5_password, display_name, memo FROM legacy_staff WHERE username = ?",
            (username,),
        ).fetchone()
        # The stored hash is unsalted MD5. A wordlist (e.g. rockyou) cracks it,
        # and this check accepts the cracked password straight away.
        if row and hashlib.md5(password.encode()).hexdigest() == row["md5_password"]:
            return render_template("staff/dashboard.html", staff=row, flag=STAFF_FLAG)
        error = "Invalid staff credentials."
    return render_template("staff/login.html", error=error)


# --- C3: an API that trusts a JWT signed with a weak secret ------------------
@bp.route("/api/exam-key")
def exam_key():
    token = request.cookies.get("mfano_api", "")
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer "):]
    try:
        claims = jwt_decode(token, JWT_SECRET)
    except ValueError:
        abort(401, "missing or invalid token")
    # The only check is the role claim inside the (weakly signed) token.
    if claims.get("role") != "admin":
        return jsonify(error="exam key is restricted to admin tokens"), 403
    return jsonify(flag=EXAM_KEY_FLAG, note="forged admin token accepted")


# --- C5: an AES-ECB encryption oracle ----------------------------------------
@bp.route("/api/seal")
@login_required()
def seal():
    raw = request.args.get("q", "")
    try:
        prefix = base64.b64decode(raw, validate=True) if raw else b""
    except Exception:  # noqa: BLE001 - lab tolerates junk input
        prefix = raw.encode()
    # ECB encrypts (attacker_prefix || secret). Because equal 16-byte plaintext
    # blocks map to equal ciphertext blocks, the appended secret can be peeled
    # off one byte at a time. The response is ciphertext only.
    ciphertext = aes_ecb_encrypt(_ECB_KEY, prefix + _ECB_SECRET)
    resp = make_response(ciphertext.hex())
    resp.mimetype = "text/plain"
    return resp
