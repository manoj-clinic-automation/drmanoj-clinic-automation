#!/usr/bin/env python
"""S312_CLAIM_QUEUE -- the stock_app.py half.  Anchored, idempotent, refuses on
any drift.  Adds:
  * a defensive import of claim_queue (beside this file on the box);
  * _pursue_block(), which keeps the queue in step with the owner's own words,
    runs the sweep, and gives step 8 a state that can reach DONE (D544);
  * /api/claim/<id>/settle -- the owner's tap, the only door that settles.
It changes nothing else: no existing route, no existing query, no schema of
another module.  claim_line is created by claim_queue.ensure(), additively.
"""
import argparse
import hashlib
import os
import shutil
import sys

MARK = "S312_CLAIM_QUEUE"

IMPORT_OLD = '''PAGE_COUNT = os.path.join(HERE, "stock_check_live.html")
PAGE_DIFFS = os.path.join(HERE, "stock_diffs.html")

bp = Blueprint("stock", __name__)
'''
IMPORT_NEW = '''PAGE_COUNT = os.path.join(HERE, "stock_check_live.html")
PAGE_DIFFS = os.path.join(HERE, "stock_diffs.html")

# --- S312_CLAIM_QUEUE begin (D471 / D544) --------------------------------
# Darpan's claim queue lives beside this file.  The import is defensive on
# purpose: the walk runs this module from inside a kit folder, and a stock page
# must never fail to render because a queue could not be imported.  When it is
# not there the hub behaves exactly as it did before S312.
try:
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import claim_queue as _cq                              # noqa: PLC0415
    CLAIM_QUEUE_OK = True
except Exception:                                          # pragma: no cover
    _cq = None
    CLAIM_QUEUE_OK = False
# --- S312_CLAIM_QUEUE end ------------------------------------------------

bp = Blueprint("stock", __name__)
'''

BLOCK_OLD = '''                pursue=dict(lines=tot["pursue"], cards=_pursue_cards(con, d),   # S308: the evidence rides with the question
                            state=("wait" if not tot["pursue"] else "now")),
'''
BLOCK_NEW = '''                pursue=_pursue_block(con, d, tot),   # S308 evidence + S312 the claim queue
'''

FUNC_OLD = '''def _hub_data(con, cid):
    d = _pad_report_data(con, cid)
'''
FUNC_NEW = '''def _pursue_block(con, d, tot):
    """S312 (D471, D544).  Step 8 of the hub, with its missing half.

    Before S312 this step could show only 'waiting' and 'now': the evidence was
    gathered (S308) and the question was asked, but there was nowhere to record
    an answer, so the hub's last step stayed amber for ever and the count never
    visibly finished.  The claim queue is that door.

    Three things happen here, in this order, and all three are derived -- none
    of them invents anything the owner did not say:

      1. the queue is brought into step with his words.  Every line whose word
         is RECOVER has a live claim; every live claim whose line no longer
         carries that word is withdrawn, not deleted.  Idempotent, so reading
         the page twice changes nothing.
      2. the sweep runs (claim_queue.sweep): a later count that finds the item
         agreeing settles the claim by itself; a credit note is recorded as a
         candidate and closes nothing; the purchase-return rule is written and
         asleep until a return is actually stored on this box.
      3. step 8 gets a state that can reach DONE -- when every pursued line has
         a claim in a terminal state (D544).

    It writes on a read, which is deliberate and narrow: everything written is a
    function of the owner's own decisions, the page is his alone, and a failure
    here must never take the hub down -- hence the single guard around the lot.
    """
    cards = _pursue_cards(con, d)
    out = dict(lines=tot["pursue"], cards=cards,
               state=("wait" if not tot["pursue"] else "now"),
               claims=[], summary=None, queue_ok=bool(CLAIM_QUEUE_OK),
               returns_stored=False,
               note=("" if CLAIM_QUEUE_OK else "The claim queue is not loaded on this box."))
    if not CLAIM_QUEUE_OK:
        return out
    try:
        root = int(d.get("count_id") or 0) or int(d.get("root") or 0)
        if not root:
            return out
        pursued = [dict(item=x["item"],
                        short_qty=(-int(x["diff"]) if (x.get("diff") or 0) < 0 else None),
                        value_p=(-int(x["mrp_p"]) if (x.get("mrp_p") is not None and x["mrp_p"] < 0) else None),
                        word_at=(x.get("word") or {}).get("at"))
                   for x in d["differences"] if (x.get("word") or {}).get("action") == "RECOVER"]
        who = "hub"
        _cq.sync_from_words(con, root, pursued, who)
        _cq.sweep(con)
        con.commit()
        out["claims"] = _cq.lines(con, root)
        out["summary"] = _cq.summary(con, root)
        out["returns_stored"] = bool(_cq._returns_available(con))
        out["state"] = _cq.step8_state(con, root, tot["pursue"])
    except Exception:
        # the hub renders with S308's behaviour and says so, rather than 500
        out["note"] = "The claim queue could not be read; the evidence below is unchanged."
    return out


def _hub_data(con, cid):
    d = _pad_report_data(con, cid)
'''

ROUTE_OLD = '''def _xlsx_rows(title, note, heads, rows, widths):
    """A one-sheet workbook through padwriter's stdlib writer."""
'''
ROUTE_NEW = '''@bp.route("/api/claim/<int:claim_id>/settle", methods=["POST"])
def api_claim_settle(claim_id):
    """S312 (D471).  THE OWNER SETTLES A CLAIM -- and only he does.

    His own rule on the hub: "His answer is evidence; your tap decides."  So
    Darpan's door can carry a claim from open to contacted and no further, and
    this one is the only door that reaches 'settled'.  Body: {outcome, note}.
    """
    u, err = _require("checker")
    if err:
        return err
    if not _may_decide(u):
        return jsonify(ok=False, error="forbidden", message="Only the doctor settles a claim."), 403
    if not CLAIM_QUEUE_OK:
        return jsonify(ok=False, error="unavailable", message="The claim queue is not loaded."), 503
    b = request.get_json(silent=True) or {}
    outcome = str(b.get("outcome") or "").strip()
    note = str(b.get("note") or "").strip()[:300]
    con = _db()
    ensure_schema(con)
    ok, msg = _cq.settle(con, int(claim_id), outcome, note, (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="bad_request", message=msg), 400
    con.commit()
    return jsonify(ok=True, id=int(claim_id), outcome=outcome,
                   label=_cq.OUTCOMES.get(outcome, outcome), message="Settled.")


def _xlsx_rows(title, note, heads, rows, widths):
    """A one-sheet workbook through padwriter's stdlib writer."""
'''

EDITS = [("the claim_queue import", IMPORT_OLD, IMPORT_NEW),
         ("_pursue_block", FUNC_OLD, FUNC_NEW),
         ("hub step 8 wiring", BLOCK_OLD, BLOCK_NEW),
         ("the settle door", ROUTE_OLD, ROUTE_NEW)]


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
