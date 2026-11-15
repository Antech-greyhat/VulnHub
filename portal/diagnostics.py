"""A self-test endpoint that can crash. With debug mode left on, the crash
renders a full interactive traceback that exposes source and local variables
(the leaky-error-page lesson).

It also exposes a log viewer (Phase 5d, A09): the security audit log is served
to anyone, with no login, so secrets written into it leak."""
from pathlib import Path

from flask import Blueprint, abort, current_app, jsonify, make_response, request

bp = Blueprint("diagnostics", __name__, url_prefix="/diagnostics")


@bp.route("/logs")
def logs():
    # No authentication and no restriction: any visitor can list and read the
    # server's log files. Anything sensitive that gets logged (for example a
    # cleartext password-reset code) leaks here, and nothing alerts on it.
    log_dir = Path(current_app.config["SECURITY_LOG"]).parent
    name = request.args.get("name")
    if not name:
        available = sorted(path.name for path in log_dir.glob("*.log")) if log_dir.exists() else []
        return jsonify(logs=available, note="append ?name=<file> to read one")
    path = log_dir / name
    if not path.exists():
        abort(404)
    body = path.read_text(encoding="utf-8", errors="replace")
    return make_response((body, 200, {"Content-Type": "text/plain; charset=utf-8"}))


@bp.route("/self-test")
def self_test():
    # The build token is only meant for internal logs, but it gets baked into
    # the error message below. With debug mode left on, the traceback page shows
    # that message verbatim, so the token leaks to anyone who triggers the crash.
    build_token = current_app.config["BUILD_TOKEN"]
    load = int(request.args.get("load", "0"))
    if load <= 0:
        raise RuntimeError(f"self-test aborted (build {build_token}): load must be > 0")
    return {"headroom": 100 / load}
