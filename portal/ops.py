"""A legacy "ops" console that was never put behind the login.

It is deliberately not linked anywhere and not protected: anyone who learns
the path reaches it. This is the "forced browsing / missing access control"
lesson for Phase 1.
"""
from flask import Blueprint, render_template

from .db import get_db

bp = Blueprint("ops", __name__, url_prefix="/ops")

# Shown on the unprotected page. Reaching this page at all is the exploit.
CONSOLE_TOKEN = "MFANO{unlinked_is_not_protected}"


@bp.route("/students")
def students():
    rows = get_db().execute(
        "SELECT admission, full_name, form, stream, fee_balance FROM students ORDER BY admission"
    ).fetchall()
    return render_template("ops_students.html", rows=rows, token=CONSOLE_TOKEN)
