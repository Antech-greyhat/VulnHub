"""Login, logout and role checks."""
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from .db import get_db

bp = Blueprint("auth", __name__)


def current_user():
    """Return {"user_id", "role"} for the signed-in user, or None."""
    if "user_id" not in session:
        return None
    return {"user_id": session["user_id"], "role": session["role"]}


def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if user is None:
                return redirect(url_for("auth.login"))
            if role and user["role"] != role:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def start_session(user):
    session.clear()
    session["user_id"] = user["id"]
    session["role"] = user["role"]


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = get_db().execute(
            "SELECT * FROM users WHERE username = ?",
            (request.form.get("username", "").strip(),),
        ).fetchone()
        if user and check_password_hash(user["password_hash"], request.form.get("password", "")):
            start_session(user)
            return redirect(url_for("index"))
        flash("Wrong username or password.")
    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
