"""Student dashboard."""
from flask import Blueprint, render_template

from .auth import current_user, login_required
from .db import get_db

bp = Blueprint("student", __name__, url_prefix="/student")


def own_student():
    return get_db().execute(
        "SELECT * FROM students WHERE user_id = ?", (current_user()["user_id"],)
    ).fetchone()


@bp.route("/")
@login_required("student")
def dashboard():
    student = own_student()
    marks = get_db().execute(
        "SELECT subject, term, score FROM marks WHERE student_id = ? ORDER BY term, subject",
        (student["id"],),
    ).fetchall()
    return render_template("student/dashboard.html", student=student, marks=marks)
