"""Mfano High School Portal: a fake school portal built as a learning lab."""
import os
import secrets
from pathlib import Path

from flask import Flask, redirect, session, url_for

from . import admin, auth, db, diagnostics, ops, payments, student

BASE_DIR = Path(__file__).resolve().parent.parent


def create_app(overrides=None):
    app = Flask(__name__)
    home = Path(os.environ.get("MFANO_HOME", BASE_DIR / "var"))
    app.config.update(
        SECRET_KEY=os.environ.get("MFANO_SECRET_KEY") or secrets.token_hex(32),
        MFANO_HOME=home,
        DATABASE=home / "data" / "mfano.db",
        REPORT_DIR=home / "reports",
        UPLOAD_DIR=home / "uploads",
        # Reached by rendering an uploaded template (upload -> SSTI code exec).
        SERVER_FLAG=os.environ.get("MFANO_SERVER_FLAG", "MFANO{uploaded_script_ran_on_the_server}"),
        # The internal grading service, pointed at by the SSRF "import logo" tool.
        GRADING_URL=os.environ.get("GRADING_URL", "http://grading:9000"),
        # Leaked through the interactive debugger when debug mode is left on.
        BUILD_TOKEN=os.environ.get("MFANO_BUILD_TOKEN", "MFANO{stack_trace_told_everything}"),
    )
    if overrides:
        app.config.update(overrides)

    # Debug mode is left on for the lab, so unhandled errors render a full
    # interactive traceback with source and local variables (leaky errors).
    if os.environ.get("MFANO_DEBUG") == "1":
        app.debug = True

    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(student.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(payments.bp)
    app.register_blueprint(ops.bp)
    app.register_blueprint(diagnostics.bp)

    @app.route("/")
    def index():
        role = session.get("role")
        if role == "admin":
            return redirect(url_for("admin.dashboard"))
        if role == "student":
            return redirect(url_for("student.dashboard"))
        return redirect(url_for("auth.login"))

    return app
