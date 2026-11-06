"""Mfano High School Portal: a fake school portal built as a learning lab."""
import os
import secrets
from pathlib import Path

from flask import Flask, redirect, session, url_for

from . import admin, auth, db, payments, student

BASE_DIR = Path(__file__).resolve().parent.parent


def create_app(overrides=None):
    app = Flask(__name__)
    home = Path(os.environ.get("MFANO_HOME", BASE_DIR / "var"))
    app.config.update(
        SECRET_KEY=os.environ.get("MFANO_SECRET_KEY") or secrets.token_hex(32),
        MFANO_HOME=home,
        DATABASE=home / "data" / "mfano.db",
        REPORT_DIR=home / "reports",
    )
    if overrides:
        app.config.update(overrides)

    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(student.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(payments.bp)

    @app.route("/")
    def index():
        role = session.get("role")
        if role == "admin":
            return redirect(url_for("admin.dashboard"))
        if role == "student":
            return redirect(url_for("student.dashboard"))
        return redirect(url_for("auth.login"))

    return app
