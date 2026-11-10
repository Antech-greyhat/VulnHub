"""Phase 5d: integrity and insecure-design flaws (student "account" area).

Three deliberate bugs live here, each solved by *exploiting* it, not by reading
this file:

* /account/prefs    - deserialises a user-controlled cookie with ``pickle``.
  Unpickling attacker bytes runs attacker-chosen callables, i.e. arbitrary code
  execution (A08 Software and Data Integrity Failures). The flag is placed in
  the process environment so a gadget that reads it proves code ran.
* /account/settings - a profile update that writes *every* submitted field whose
  name matches a real column (mass assignment / A06 Insecure Design). The form
  only offers "about" and the display name, but ``is_rep`` and ``fee_balance``
  go through just the same. Setting ``is_rep=1`` opens the rep room.
* /account/forgot   - a self-service password reset that logs the generated
  recovery code in cleartext to a security log, which ``/diagnostics/logs``
  then serves to anyone (A09 Security Logging and Monitoring Failures). Request
  a reset for ``admin`` and read the log to recover the flag.

None of this should ever be copied into real code.
"""
import base64
import hashlib
import os
import pickle  # noqa: S403 - the insecure use is the lesson
from datetime import datetime, timezone
from pathlib import Path

from flask import (
    Blueprint, abort, current_app, flash, jsonify, make_response, redirect,
    render_template, request, url_for,
)

from .auth import current_user, login_required
from .db import get_db

bp = Blueprint("integrity", __name__, url_prefix="/account")

# --- P5D-01: insecure deserialization --------------------------------------
# The flag is exported into the process environment, not shipped in any repo
# file. A `pickle` payload that runs `os.getenv("MFANO_INTEGRITY_FLAG")` (or any
# command, e.g. a subprocess gadget running `printenv`) recovers it - which only
# works because the server executed attacker-chosen code while unpickling.
INTEGRITY_FLAG = "MFANO{p1ckl3_l04ds_r4n_my_c0d3}"
os.environ.setdefault("MFANO_INTEGRITY_FLAG", INTEGRITY_FLAG)

DEFAULT_PREFS = {"theme": "light", "lang": "en", "rows": 25}

# --- P5D-02: mass assignment -----------------------------------------------
# Every real column of the students table. The settings handler writes any
# submitted field whose name is in here, so a student can set privileged
# columns the form never exposes.
STUDENT_COLUMNS = {
    "full_name", "form", "stream", "fee_total", "fee_balance", "remark",
    "about", "is_rep",
}
# Shown only to a student whose is_rep column is set - which the mass-assignment
# bug lets them do to their own row.
REP_FLAG = "MFANO{m4ss_4ss1gn_m4d3_m3_r3p}"

# --- P5D-03: secrets in an exposed log -------------------------------------
# Logged in cleartext as the "recovery code" when a reset is requested for the
# admin account, then leaked by the unprotected /diagnostics/logs viewer.
RESET_FLAG = "MFANO{l0gs_l34k3d_th3_r3s3t_c0d3}"


def own_student():
    return get_db().execute(
        "SELECT * FROM students WHERE user_id = ?", (current_user()["user_id"],)
    ).fetchone()


def _reset_code(username):
    """A deterministic, non-flag recovery code for ordinary accounts."""
    digest = hashlib.sha256(f"mfano-reset:{username}".encode()).hexdigest()
    return digest[:8].upper()


def _audit(line):
    """Append a security-audit line to the (over-shared) security log."""
    log_path = Path(current_app.config["SECURITY_LOG"])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{stamp} AUDIT {line}\n")


# --- P5D-01 route ----------------------------------------------------------
@bp.route("/prefs")
@login_required("student")
def prefs():
    raw = request.cookies.get("mfano_prefs")
    if not raw:
        # First visit: hand the browser a pickled-then-base64 cookie. Decoding
        # it reveals a pickle stream (\x80...), which invites tampering.
        blob = base64.b64encode(pickle.dumps(DEFAULT_PREFS)).decode()
        response = make_response(jsonify(prefs=str(DEFAULT_PREFS), note="defaults applied"))
        response.set_cookie("mfano_prefs", blob)
        return response
    # The cookie is trusted and unpickled. pickle.loads on attacker-controlled
    # bytes executes callables the attacker chose: arbitrary code execution.
    loaded = pickle.loads(base64.b64decode(raw))  # noqa: S301
    return jsonify(prefs=str(loaded))


# --- P5D-02 routes ---------------------------------------------------------
@bp.route("/settings", methods=["GET", "POST"])
@login_required("student")
def settings():
    me = own_student()
    if request.method == "POST":
        # Intended: edit the display name and the "about" blurb. In practice,
        # any submitted field that names a real column is written straight to
        # the student's row - including is_rep and fee_balance.
        updates = {key: value for key, value in request.form.items() if key in STUDENT_COLUMNS}
        if updates:
            assignments = ", ".join(f"{column} = ?" for column in updates)
            get_db().execute(
                f"UPDATE students SET {assignments} WHERE id = ?",
                (*updates.values(), me["id"]),
            )
            get_db().commit()
        flash("Settings saved.")
        return redirect(url_for("integrity.settings"))
    return render_template("account/settings.html", student=me)


@bp.route("/rep-room")
@login_required("student")
def rep_room():
    me = own_student()
    # Gate is the is_rep column on the student's own row.
    if not me["is_rep"]:
        abort(403)
    return render_template("account/rep_room.html", student=me, flag=REP_FLAG)


# --- P5D-03 route ----------------------------------------------------------
@bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        # The "recovery code" is written to the audit log in cleartext. For the
        # admin account that code is the flag; for anyone else it is a dummy.
        code = RESET_FLAG if username == "admin" else _reset_code(username)
        _audit(f"password-reset requested user={username or '(blank)'} recovery_code={code}")
        return render_template(
            "account/forgot.html",
            submitted=True,
            username=username,
            log_hint="logs/portal-security.log (viewer: /diagnostics/logs)",
        )
    return render_template("account/forgot.html", submitted=False)
