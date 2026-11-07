"""Admin dashboard, student review, weak console, and server-side tools.

The tools in this module (diagnostics, upload, logo import) are the Phase 4
"reach the server" bugs. They are admin-gated, but Phase 3 shows how a normal
user becomes admin, which is the intended chain.
"""
import subprocess
import urllib.request
from pathlib import Path

from flask import (
    Blueprint, abort, current_app, jsonify, render_template, render_template_string, request,
)

from .auth import login_required
from .db import get_db

bp = Blueprint("admin", __name__, url_prefix="/admin")

# Only an admin session can read this. A stored script running in an admin's
# browser can fetch it, which is the point of the stored-XSS exercise.
REVIEW_TOKEN = "MFANO{st0r3d_scr1pt_st0l3_th3_r3v13w_t0k3n}"

# Shown by the console that is gated on a forgeable cookie instead of the session.
CONSOLE_FLAG = "MFANO{uns1gn3d_c00k13_m4d3_m3_4dm1n}"


@bp.route("/")
@login_required("admin")
def dashboard():
    db = get_db()
    return render_template(
        "admin/dashboard.html",
        students=db.execute("SELECT * FROM students ORDER BY form, full_name").fetchall(),
        payment_count=db.execute("SELECT COUNT(*) FROM payments").fetchone()[0],
    )


@bp.route("/marks")
@login_required("admin")
def marks():
    rows = get_db().execute(
        """SELECT s.admission, s.full_name, m.subject, m.term, m.score
           FROM marks m JOIN students s ON s.id = m.student_id
           ORDER BY s.full_name, m.subject"""
    ).fetchall()
    return render_template("admin/marks.html", rows=rows)


@bp.route("/payments")
@login_required("admin")
def payments():
    rows = get_db().execute(
        """SELECT s.admission, s.full_name, p.reference, p.amount, p.status, p.paid_at
           FROM payments p JOIN students s ON s.id = p.student_id
           ORDER BY p.paid_at DESC"""
    ).fetchall()
    return render_template("admin/payments.html", rows=rows)


@bp.route("/student/<int:sid>")
@login_required("admin")
def student_review(sid):
    row = get_db().execute("SELECT * FROM students WHERE id = ?", (sid,)).fetchone()
    if row is None:
        abort(404)
    # The "about" text is rendered without escaping on this staff page, so a
    # script a student stored there runs in the admin's browser (stored XSS).
    return render_template("admin/student_review.html", student=row)


@bp.route("/review-token")
@login_required("admin")
def review_token():
    return jsonify(review_token=REVIEW_TOKEN)


@bp.route("/console")
def console():
    # Privilege here is decided by a plaintext, unsigned "mfano_role" cookie the
    # client can edit, not by the server-side session. Set it to "admin" and the
    # console opens.
    if request.cookies.get("mfano_role") != "admin":
        abort(403)
    return render_template("admin/console.html", flag=CONSOLE_FLAG)


@bp.route("/tools")
@login_required("admin")
def tools():
    return render_template("admin/tools.html")


@bp.route("/tools/ping", methods=["POST"])
@login_required("admin")
def ping():
    host = request.form.get("host", "")
    # The host goes straight into a shell command. A ';' or '&' lets you run
    # your own OS commands on the lab box (command injection).
    command = "ping -c 1 " + host
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
    return "<pre>" + (result.stdout + result.stderr) + "</pre>"


@bp.route("/tools/upload", methods=["POST"])
@login_required("admin")
def upload():
    uploaded = request.files.get("file")
    if uploaded is None or uploaded.filename == "":
        abort(400)
    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    # No type or content check, and the original name is kept as-is.
    dest = upload_dir / uploaded.filename
    uploaded.save(dest)
    return jsonify(saved=uploaded.filename)


@bp.route("/tools/preview")
@login_required("admin")
def preview():
    name = request.args.get("name", "")
    path = Path(current_app.config["UPLOAD_DIR"]) / name
    if not path.exists():
        abort(404)
    # An uploaded file is rendered as a template, so its contents run on the
    # server. Upload a template payload and it executes (SSTI / code exec).
    return render_template_string(path.read_text(encoding="utf-8", errors="replace"))


@bp.route("/tools/import-logo", methods=["POST"])
@login_required("admin")
def import_logo():
    url = request.form.get("url", "")
    # The URL is fetched with no restriction on where it points, so it can be
    # aimed at internal-only services (SSRF).
    with urllib.request.urlopen(url, timeout=10) as response:  # noqa: S310
        body = response.read(65536).decode("utf-8", errors="replace")
    return "<pre>" + body + "</pre>"
