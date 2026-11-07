"""Fee payments page. All payments are fake; there is no payment API."""
import datetime

from flask import Blueprint, render_template, request

from .auth import login_required
from .db import get_db
from .student import own_student

bp = Blueprint("payments", __name__, url_prefix="/payments")

# Revealed when a client-driven "payment" clears the balance with no real money.
CLEARED_FLAG = "MFANO{p41d_n0th1ng_f33s_cl34r3d}"


@bp.route("/")
@login_required("student")
def history():
    student = own_student()
    rows = get_db().execute(
        "SELECT reference, amount, status, paid_at FROM payments WHERE student_id = ? ORDER BY paid_at DESC",
        (student["id"],),
    ).fetchall()
    return render_template("student/payments.html", student=student, rows=rows)


@bp.route("/pay", methods=["POST"])
@login_required("student")
def pay():
    student = own_student()
    # The amount and status both come from the client and are trusted as-is.
    # There is no real payment: whatever amount is posted is applied to the
    # balance, so fees can be cleared without paying.
    amount = request.form.get("amount", type=int) or 0
    status = request.form.get("status", "COMPLETED")
    reference = request.form.get("reference", "SELF" + datetime.datetime.now().strftime("%H%M%S"))
    db = get_db()
    db.execute(
        "INSERT INTO payments (student_id, reference, amount, status, paid_at) VALUES (?, ?, ?, ?, ?)",
        (student["id"], reference, amount, status, datetime.date.today().isoformat()),
    )
    new_balance = max(student["fee_balance"] - amount, 0)
    db.execute("UPDATE students SET fee_balance = ? WHERE id = ?", (new_balance, student["id"]))
    db.commit()
    payload = {"ok": True, "balance": new_balance}
    if new_balance == 0 and status == "COMPLETED":
        payload["flag"] = CLEARED_FLAG
    return payload
