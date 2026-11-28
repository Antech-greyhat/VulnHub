"""Public discovery pages and four retired practice logins."""
import base64
import hashlib

from flask import Blueprint, Response, make_response, render_template, request, url_for

bp = Blueprint("bruteforce", __name__)

# These fake accounts belong only to the retired consoles, not the main portal.
CHALLENGES = {
    "BF-01": {
        "area": "archive", "title": "Archive administration",
        "username": "a.njeri", "password": "sunshine", "order": "generic",
        "flag": "MFANO{f13ld_n4m3s_m4tt3r}",
        "lesson": "The form showed Username, but JavaScript sent username. The source hid an account in Base64: encoding is reversible. A generic error did not stop guesses against a weak password.",
    },
    "BF-02": {
        "area": "office", "title": "Office administration",
        "username": "registrar", "password": "welcome1", "order": "username",
        "flag": "MFANO{3rr0rs_l34k_us3rs}",
        "lesson": "This login checked the username first. Incorrect password confirmed an existing username. Incorrect username did not prove the password was correct: the password had not been checked.",
    },
    "BF-03": {
        "area": "backup", "title": "Backup administration",
        "username": "archivist", "password": "football", "order": "password",
        "flag": "MFANO{p4ssw0rd_ch3ck3d_f1rst}",
        "lesson": "This gate checked one shared password before the username. With an invalid username, incorrect username proved the shared password had passed. That conclusion depends on the check order; the message alone is not enough.",
    },
    "BF-04": {
        "area": "management", "title": "Management administration",
        "username": "examadmin", "password": "dragon", "order": "generic",
        "flag": "MFANO{h4sh_th3n_gu3ss}",
        "lesson": "MD5 cannot be decoded. Hashing candidate usernames until one matched recovered the account offline. The weak password still needed a separate dictionary attack. Robots.txt had not listed this console.",
    },
}


@bp.get("/robots.txt")
def robots():
    # The fourth console must be discovered independently, e.g. with Gobuster.
    return Response(
        "User-agent: *\nDisallow: /archive/\nDisallow: /office/\nDisallow: /backup/\n"
        f"Disallow: {url_for('.yearbook_proof')}\n",
        mimetype="text/plain",
    )


@bp.get("/yearbook/proof/")
def yearbook_proof():
    receipt = base64.b64decode("TUZBTk97cHIwMGZfMW5fdGgzX200cmcxbn0=").decode("ascii")
    page = make_response(render_template("yearbook_proof.html", receipt=receipt))
    if "yearbook_preview" not in request.cookies:
        guest = base64.b64encode(b'{"user":"guest","role":"guest"}').decode("ascii")
        page.set_cookie("yearbook_preview", guest, path=url_for(".yearbook_proof"), samesite="Lax")
    return page


def directory(challenge_id):
    challenge = CHALLENGES[challenge_id]
    return render_template(
        "bruteforce.html", title=challenge["title"], directory=True,
        login_url=url_for(f"bruteforce.{challenge_id}_login"),
    )


def login(challenge_id):
    challenge = CHALLENGES[challenge_id]
    error = None
    if request.method == "POST":
        # Field names are case-sensitive. An uppercase Username is ignored.
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if challenge["order"] == "password":
            if password != challenge["password"]:
                error = "incorrect password"
            elif username != challenge["username"]:
                error = "incorrect username"
        elif challenge["order"] == "username":
            if username != challenge["username"]:
                error = "incorrect username"
            elif password != challenge["password"]:
                error = "incorrect password"
        elif username != challenge["username"] or password != challenge["password"]:
            error = "incorrect username or password"
        if error is None:
            return render_template("bruteforce.html", title=challenge["title"], stage_id=challenge_id, flag=challenge["flag"], lesson=challenge["lesson"])

    clue = ""
    if challenge_id == "BF-01":
        clue = "username_b64=" + base64.b64encode(challenge["username"].encode()).decode()
    elif challenge_id == "BF-03":
        clue = "check_order=password,username; password_scope=shared"
    elif challenge_id == "BF-04":
        clue = "username_md5=" + hashlib.md5(challenge["username"].encode()).hexdigest()
    # Failures deliberately share HTTP 200; tools must inspect the response body.
    return render_template(
        "bruteforce.html", title=challenge["title"], error=error, clue=clue,
        legacy_field=challenge_id == "BF-01", shared_password=challenge_id == "BF-03",
    )


for challenge_id, challenge in CHALLENGES.items():
    bp.add_url_rule(f"/{challenge['area']}/", endpoint=f"{challenge_id}_directory", view_func=directory, defaults={"challenge_id": challenge_id})
    bp.add_url_rule(f"/{challenge['area']}/login", endpoint=f"{challenge_id}_login", view_func=login, defaults={"challenge_id": challenge_id}, methods=["GET", "POST"])
