"""Admin dashboard, student review (stored-XSS sink) and a weakly-gated console."""
from flask import Blueprint, abort, jsonify, render_template, request

from .auth import login_required
from .db import get_db

bp = Blueprint("admin", __name__, url_prefix="/admin")

# Only an admin session can read this. A stored script running in an admin's
# browser can fetch it, which is the point of the stored-XSS exercise.
REVIEW_TOKEN = "MFANO{stored_script_stole_the_review_token}"

# Shown by the console that is gated on a forgeable cookie instead of the session.
CONSOLE_FLAG = "MFANO{unsigned_cookie_made_me_admin}"


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
