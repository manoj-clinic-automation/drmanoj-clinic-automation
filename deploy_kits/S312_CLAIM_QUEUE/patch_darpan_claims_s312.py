#!/usr/bin/env python
"""S312_CLAIM_QUEUE -- the darpan_app.py half.  Anchored, idempotent, refuses on
drift.  Adds two doors and nothing else:
  GET  /finance/darpan/api/claims              -- his open claims, aged to the top
  POST /finance/darpan/api/claim/<id>/answer   -- his answer: open -> contacted
He can never settle a claim; that door is the owner's, in stock_app (S312).
"""
import argparse
import hashlib
import os
import shutil
import sys

MARK = "S312_CLAIM_QUEUE"

IMP_OLD = '''ANSWERS = ("was_upi", "not_upi", "attach_bill", "advance", "dont_know")
'''
IMP_NEW = '''ANSWERS = ("was_upi", "not_upi", "attach_bill", "advance", "dont_know")

# --- S312_CLAIM_QUEUE begin (D471) ---------------------------------------
# Darpan's stock claim queue lives beside this file.  Defensive: his day card
# must never fail to load because the queue could not be imported.
try:
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import claim_queue as _cq                                      # noqa: PLC0415
    CLAIM_QUEUE_OK = True
except Exception:                                                  # pragma: no cover
    _cq = None
    CLAIM_QUEUE_OK = False
# --- S312_CLAIM_QUEUE end ------------------------------------------------
'''

ROUTE_OLD = '''@bp.route("/finance/darpan/corrections")
def page_corrections():
'''
ROUTE_NEW = '''@bp.route("/finance/darpan/api/claims")
def api_claims():
    """S312 (D471).  WHAT DARPAN IS BEING ASKED, and why he is being asked it.

    A line reaches this list only because the owner marked it "to pursue" on
    the stock check hub, and it arrives with the evidence the server already
    holds (S308): how much of it sold in the thirty days before the count, or
    the plain fact that it did not sell once.  He is asked with the evidence in
    hand; he is never asked to remember.

    D471: a claim older than fourteen days sorts to the TOP, so nothing sinks
    quietly to the bottom of the list by being ignored.
    """
    u, err = _require("maker", "checker")
    if err:
        return err
    if not CLAIM_QUEUE_OK:
        return jsonify(ok=True, claims=[], answers=[], available=False)
    con = _db()
    ensure_schema(con)
    _cq.ensure(con)
    try:
        _cq.sweep(con)
        con.commit()
    except Exception:                                              # noqa: BLE001
        pass
    rows = _cq.queue(con, limit=50)
    return jsonify(ok=True, available=True, claims=rows,
                   answers=[dict(key=k, label=v) for k, v in _cq.ANSWERS.items()],
                   aged_days=_cq.AGE_TO_TOP_DAYS,
                   open=sum(1 for r in rows if r["state"] == "open"),
                   answered=sum(1 for r in rows if r["state"] == "contacted"))


@bp.route("/finance/darpan/api/claim/<int:claim_id>/answer", methods=["POST"])
def api_claim_answer(claim_id):
    """S312 (D471).  His tap: open -> contacted, with his answer recorded as
    HIS.  He may change it while it is still contacted.  He cannot settle -- the
    owner's rule on the hub is "His answer is evidence; your tap decides", and
    this door stops exactly where that sentence does."""
    u, err = _require("maker", "checker")
    if err:
        return err
    if not CLAIM_QUEUE_OK:
        return jsonify(ok=False, error="unavailable",
                       message="abhi yeh list nahin khul rahi"), 503
    b = request.get_json(silent=True) or {}
    ans = str(b.get("answer") or "").strip()
    note = str(b.get("note") or "").strip()[:300]
    con = _db()
    ensure_schema(con)
    ok, msg = _cq.answer(con, int(claim_id), ans, note, u["user"])
    if not ok:
        return jsonify(ok=False, error="bad_request", message=msg), 400
    _audit(con, u["user"], "claim_answered",
           {"id": int(claim_id), "answer": ans})
    con.commit()
    return jsonify(ok=True, id=int(claim_id), answer=ans,
                   label=_cq.ANSWERS.get(ans, ans), message=msg)


@bp.route("/finance/darpan/corrections")
def page_corrections():
'''

EDITS = [("the claim_queue import", IMP_OLD, IMP_NEW),
         ("Darpan's two claim doors", ROUTE_OLD, ROUTE_NEW)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--from", dest="frm", default="")
    ap.add_argument("--expect", default="")
    a = ap.parse_args()
    p = a.file
    if not os.path.exists(p):
        print("MISSING %s" % p); return 2
    src = open(p, encoding="utf-8").read()
    cur = hashlib.md5(src.encode("utf-8")).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED -- %s" % cur); return 0
    if a.frm and cur != a.frm:
        print("REFUSED -- live md5 %s, expected %s" % (cur, a.frm)); return 3
    for name, old, new in EDITS:
        n = src.count(old)
        if n != 1:
            print("REFUSED -- anchor '%s' occurs %d times, expected 1" % (name, n)); return 4
        src = src.replace(old, new)
    shutil.copyfile(p, p + ".bak_S312_" + cur[:8])
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    new_md5 = hashlib.md5(src.encode("utf-8")).hexdigest()
    if a.expect and new_md5 != a.expect:
        print("REFUSED AFTER WRITE -- got %s, expected %s" % (new_md5, a.expect)); return 5
    print("PATCHED %s -> %s" % (cur, new_md5))
    return 0


if __name__ == "__main__":
    sys.exit(main())
