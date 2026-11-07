"""Student dashboard, report download, classmate search and profile."""
from pathlib import Path

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_file, url_for

from .auth import current_user, login_required
from .db import get_db

bp = Blueprint("student", __name__, url_prefix="/student")

# Revealed when a mark change actually goes through on a client-supplied
# authorization field, which the server should never trust.
TAMPER_FLAG = "MFANO{cl13nt_s41d_4dm1n_s0_m4rks_ch4ng3d}"


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


@bp.route("/search")
@login_required("student")
def search():
    query = request.args.get("q", "")
    results, error = [], None
    if query:
        # The search term is concatenated straight into the SQL string with no
        # parameters, so the query is injectable.
        sql = (
            "SELECT admission, full_name FROM students "
            "WHERE full_name LIKE '%" + query + "%' ORDER BY full_name"
        )
        try:
            results = get_db().execute(sql).fetchall()
        except Exception as exc:  # noqa: BLE001 - verbose on purpose for the lab
            error = str(exc)
    return render_template("student/search.html", query=query, results=results, error=error)


@bp.route("/profile", methods=["GET", "POST"])
@login_required("student")
def profile():
    student = own_student()
    if request.method == "POST":
        # Stored as-is. It is shown later to staff without escaping (stored XSS).
        get_db().execute(
            "UPDATE students SET about = ? WHERE id = ?",
            (request.form.get("about", ""), student["id"]),
        )
        get_db().commit()
        flash("Profile saved.")
        return redirect(url_for("student.profile"))
    return render_template("student/profile.html", student=student)


@bp.route("/marks/update", methods=["POST"])
@login_required("student")
def update_marks():
    # Whether this privileged edit is allowed is decided by a "role" field sent
    # by the client, with no server-side check of the real session role.
    if request.form.get("role") != "admin":
        abort(403)
    student = own_student()
    get_db().execute(
        "UPDATE marks SET score = ? WHERE student_id = ? AND subject = ? AND term = ?",
        (request.form.get("score", type=int), student["id"],
         request.form.get("subject"), request.form.get("term")),
    )
    get_db().commit()
    return {"ok": True, "message": "Marks updated.", "flag": TAMPER_FLAG}
