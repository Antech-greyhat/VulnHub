"""Phase 5c: Social Engineering Education (SEE).

A fully contained training module. Everything here is fake and local:

* Every "person" is an invented NPC. No real names, companies or branding.
* Nothing sends a message. The webmail items are static samples; the helpdesk
  "bot" is a rule-based echo that talks to nothing outside this process.
* There is no working phishing page and no credential capture. The intranet
  login only compares against a hardcoded NPC password and stores nothing.

Three challenges:
  SE-01  OSINT      - public NPC breadcrumbs reveal a guessable password.
  SE-02  Phishing   - pick the phishing samples out of a static inbox.
  SE-03  Pretext    - a scripted helpdesk bot leaks a code only to the right
                      pretext, which chains the staff id + answer from SE-01.
"""
from flask import Blueprint, render_template, request, session

from .auth import login_required

bp = Blueprint("social", __name__, url_prefix="/intranet")

# --- SE-01: OSINT password profiling ----------------------------------------
# The target NPC and the breadcrumbs that give away the password. The password
# itself is derived by the learner from the public posts, not handed over.
OSINT_USERNAME = "d.mwaura"
OSINT_PASSWORD = "Simba1980"  # pet name (noticeboard) + birth year (noticeboard)
OSINT_FLAG = "MFANO{0s1nt_bu1lt_th3_p4ssw0rd}"

STAFF_DIRECTORY = [
    {
        "name": "Daniel Mwaura", "username": "d.mwaura", "role": "ICT Administrator",
        "bio": "Keeper of the server room and the new printer. Dog person.",
    },
    {
        "name": "Grace Achieng", "username": "g.achieng", "role": "Deputy Principal",
        "bio": "Timetables, discipline, and far too many meetings.",
    },
    {
        "name": "Peter Kimani", "username": "p.kimani", "role": "Bursar",
        "bio": "Fees, procurement, and the tuck-shop accounts.",
    },
]

# Static fake "social wall" posts. The OSINT trail lives here in plain sight.
NOTICEBOARD_POSTS = [
    {"who": "Daniel Mwaura", "when": "2 days ago",
     "text": "Caught Simba chewing my good shoes again. Worst guard dog, best boy."},
    {"who": "Daniel Mwaura", "when": "1 week ago",
     "text": "Turning the big 4-5 this year and still fixing printers. Born in 1980, "
             "feeling every bit of it."},
    {"who": "Daniel Mwaura", "when": "3 weeks ago",
     "text": "Note to self taped to the monitor again: 'usual password - the dog + "
             "the year'. One day IT will catch me. (I am IT.)"},
    {"who": "Grace Achieng", "when": "4 days ago",
     "text": "Reminder: staff usernames are first-initial dot surname. Mine is g.achieng."},
]


# --- SE-02: phishing spotting -----------------------------------------------
# Five static sample emails. Two are phishing. The learner submits their picks;
# scoring is server-side so the answer is not readable from the page.
INBOX = [
    {"id": 1, "from": "exams@mfano.sch.ke", "subject": "Term 2 timetable attached",
     "link": "https://portal.mfano.sch.ke/timetable",
     "body": "Hi all, the Term 2 timetable is on the portal. No action needed.",
     "phish": False},
    {"id": 2, "from": "IT-Helpdesk <admin@mfan0-support.com>",
     "subject": "URGENT: your mailbox will be CLOSED in 24 hours",
     "link": "http://mfano-support.com.verify-login.tk/reset",
     "body": "Your account exceeded its quota. Verify your password NOW or lose access.",
     "phish": True},
    {"id": 3, "from": "library@mfano.sch.ke", "subject": "Overdue book reminder",
     "link": "https://portal.mfano.sch.ke/library",
     "body": "Our records show one overdue title. Please return it at your convenience.",
     "phish": False},
    {"id": 4, "from": "Mfano Bank <payroll@mfano-bank-secure.co>",
     "subject": "Salary payment on hold - action required",
     "link": "http://secure-mfano-bank.tk/login",
     "body": "We could not process your salary. Confirm your bank login within 2 hours "
             "to release the funds.",
     "phish": True},
    {"id": 5, "from": "principal@mfano.sch.ke", "subject": "Staff briefing, Friday 8am",
     "link": "https://portal.mfano.sch.ke/notices",
     "body": "Short briefing in the staff room on Friday. Agenda on the portal.",
     "phish": False},
]
PHISH_IDS = {item["id"] for item in INBOX if item["phish"]}
PHISH_FLAG = "MFANO{sp0tt3d_th3_ph1sh}"


# --- SE-03: pretext helpdesk bot --------------------------------------------
# Rule-based, offline. It releases a "reset code" only after the caller presents
# the staff username (from SE-01's directory) AND the verification answer (the
# pet name from the noticeboard). That info-chain is the whole lesson.
PRETEXT_FLAG = "MFANO{pr3t3xt_ch41n3d_th3_r3s3t}"


def _helpdesk_reply(message):
    """Return (bot_text, leaked_flag_or_None). Pure function of message + session."""
    text = message.lower().strip()
    stage = session.get("hd_verified_user", False)

    reset_intent = any(w in text for w in ("reset", "password", "locked", "access", "code"))
    has_username = OSINT_USERNAME in text
    has_answer = "simba" in text

    # All-in-one pretext: identify as the staff member and answer the question.
    if has_username and has_answer:
        session["hd_verified_user"] = False
        return (
            "Identity confirmed for d.mwaura, security answer accepted. "
            "Here is your one-time reset code: " + PRETEXT_FLAG,
            PRETEXT_FLAG,
        )

    if not text:
        return ("Mfano Helpdesk here. How can I help? (I can only reset accounts "
                "for verified staff.)", None)

    if reset_intent and not has_username:
        return ("I can help reset a staff account. First, what is your staff "
                "username? (format: first-initial dot surname)", None)

    if has_username and not stage:
        session["hd_verified_user"] = True
        return ("Thanks. To verify it's really you, security question: what is "
                "the name of your pet?", None)

    if stage and has_answer:
        session["hd_verified_user"] = False
        return ("Verified. Here is your one-time reset code: " + PRETEXT_FLAG, PRETEXT_FLAG)

    if stage:
        return ("That doesn't match the security answer on file. Try again, or "
                "contact your administrator.", None)

    return ("I can only share account details with verified staff. Tell me your "
            "staff username to begin.", None)


# --- routes -----------------------------------------------------------------
@bp.route("/")
@login_required()
def home():
    return render_template("intranet/home.html")


@bp.route("/directory")
@login_required()
def directory():
    return render_template("intranet/directory.html", staff=STAFF_DIRECTORY)


@bp.route("/noticeboard")
@login_required()
def noticeboard():
    return render_template("intranet/noticeboard.html", posts=NOTICEBOARD_POSTS)


@bp.route("/login", methods=["GET", "POST"])
@login_required()
def staff_login():
    result = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == OSINT_USERNAME and password == OSINT_PASSWORD:
            result = {"ok": True, "flag": OSINT_FLAG}
        else:
            result = {"ok": False}
    return render_template("intranet/login.html", result=result)


@bp.route("/webmail", methods=["GET", "POST"])
@login_required()
def webmail():
    result = None
    if request.method == "POST":
        picked = {int(v) for v in request.form.getlist("phish") if v.isdigit()}
        if picked == PHISH_IDS:
            result = {"ok": True, "flag": PHISH_FLAG}
        else:
            result = {"ok": False, "picked": picked}
    return render_template("intranet/webmail.html", inbox=INBOX, result=result)


@bp.route("/helpdesk", methods=["GET", "POST"])
@login_required()
def helpdesk():
    reply = None
    if request.method == "POST":
        message = request.form.get("message", "")
        text, flag = _helpdesk_reply(message)
        reply = {"you": message, "bot": text, "flag": flag}
    return render_template("intranet/helpdesk.html", reply=reply)
