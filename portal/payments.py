"""Fee payments page. All payments are fake; there is no payment API."""
from flask import Blueprint, render_template

from .auth import login_required
from .db import get_db
from .student import own_student

bp = Blueprint("payments", __name__, url_prefix="/payments")


@bp.route("/")
@login_required("student")
def history():
    student = own_student()
    rows = get_db().execute(
        "SELECT reference, amount, status, paid_at FROM payments WHERE student_id = ? ORDER BY paid_at DESC",
        (student["id"],),
    ).fetchall()
    return render_template("student/payments.html", student=student, rows=rows)
