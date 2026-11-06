"""A self-test endpoint that can crash. With debug mode left on, the crash
renders a full interactive traceback that exposes source and local variables
(the leaky-error-page lesson)."""
from flask import Blueprint, current_app, request

bp = Blueprint("diagnostics", __name__, url_prefix="/diagnostics")


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
