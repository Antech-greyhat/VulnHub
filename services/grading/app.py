"""Mfano internal grading service.

A tiny HTTP service that returns fake grade data. It trusts any caller on the
internal Docker network - there is no authentication at all. On its own it is
just an internal API; it becomes interesting in Phase 4, when a server-side
fetch in the main app can be pointed at it (SSRF).

It is deliberately NOT published to the host, so you cannot reach it directly
with a browser or nmap from your machine. Reaching it is the Phase 4 exercise.
"""
import os

from flask import Flask, jsonify, request

app = Flask(__name__)

# Returned to any caller that reaches this internal service. Only the server is
# supposed to be able to reach it, so pulling this out is the SSRF pay-off.
INTERNAL_TOKEN = "MFANO{internal_does_not_mean_safe}"

FAKE_GRADES = {
    "MHS1007": {"mean_grade": "B+", "position": 4},
    "MHS1013": {"mean_grade": "A-", "position": 1},
    "MHS1021": {"mean_grade": "C+", "position": 18},
}


@app.route("/")
def health():
    return jsonify(service="mfano-grading", status="ok")


@app.route("/grades")
def grades():
    admission = request.args.get("admission", "")
    return jsonify(admission=admission, result=FAKE_GRADES.get(admission, {"mean_grade": "N/A"}))


@app.route("/internal/metadata")
def metadata():
    # "Internal only" data: service identity and an access token. Anything that
    # can talk to this service can read it.
    return jsonify(
        role="grading-backend",
        network="mfano-internal",
        access_token=INTERNAL_TOKEN,
    )


@app.route("/internal/logo-config")
def logo_config():
    # The "school logo" endpoint the main app imports from. Reaching it from the
    # outside is only possible through the SSRF in the main app.
    return jsonify(
        logo_url="/static/mfano-crest.png",
        note="MFANO{ssrf_reached_the_grading_service}",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "9000")))
