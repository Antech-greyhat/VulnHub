"""Admin dashboard."""
from flask import Blueprint, render_template

from .auth import login_required
from .db import get_db

bp = Blueprint("admin", __name__, url_prefix="/admin")


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
