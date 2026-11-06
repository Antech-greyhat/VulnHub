"""Student dashboard and report download."""
from pathlib import Path

from flask import Blueprint, abort, current_app, render_template, request, send_file

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


@bp.route("/report")
@login_required("student")
def report():
    # The report is fetched by a student id from the query string. There is no
    # check that the id belongs to the logged-in student, so changing it returns
    # someone else's report (IDOR).
    sid = request.args.get("sid", default=own_student()["id"], type=int)
    path = Path(current_app.config["REPORT_DIR"]) / f"report_{sid}.html"
    if not path.exists():
        abort(404)
    return send_file(path, mimetype="text/html", as_attachment=True, download_name=f"report_{sid}.html")
