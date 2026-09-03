#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walk_amir_access_s221.py -- THE LIVE-SHAPE WALK for S221_AMIR_ACCESS.

It mounts the REAL patched blueprints on a COPY of the live finance.db and then
asks the only question that matters: **as Amir, what opens and what refuses?**

Both halves are checked, and the second half is the important one. A permission
change is easy to prove permissive and easy to leave too wide; every route this
kit did NOT relax is exercised AS AMIR and must come back 403.

IT NEVER TOUCHES THE LIVE DATABASE. The first thing it does is copy it.

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/walk_amir_access_s221.py
Offline:         FIN_DB=/path/to/finance.db python3 -B walk_amir_access_s221.py
"""

import os
import shutil
import sqlite3
import sys
import tempfile

SRC_DB = os.environ.get("FIN_DB", "/root/finance/finance.db")
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

FAILED, PASSED = [], []
WHO = {"role": "viewer", "user": "amir"}


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("   [%s]" % detail) if detail and not cond else ""))


def main():
    if not os.path.exists(SRC_DB):
        print("no database at %s -- set FIN_DB" % SRC_DB)
        return 2
    tmp = tempfile.mkdtemp(prefix="walk_amir_")
    db = os.path.join(tmp, "finance.db")
    shutil.copyfile(SRC_DB, db)
    print("walking on a COPY: %s\n" % db)

    import stock_app as SA
    src = open(SA.__file__, encoding="utf-8").read()
    ck("the patched stock app is under test", "S221 COUNTER VIEWER" in src)

    from flask import Flask, jsonify
    app = Flask(__name__)

    def _db():
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        return c

    def _require(*roles):
        if WHO["role"] not in roles:
            return None, (jsonify(ok=False, error="forbidden"), 403)
        return dict(WHO), None

    SA.init(app, _db, _require, unit="medical", url_prefix="/finance/stock",
            marg_token="t")

    # the desk, so the walk covers every surface his card offers
    try:
        import returns_desk as RD
        RD.init(app, _db, _require, unit="medical",
                url_prefix="/finance/returns/desk")
        have_desk = True
    except Exception:
        have_desk = False
    ck("the Vaapsi desk is mounted for this walk", have_desk)

    cl = app.test_client()

    def code(path, post=None):
        r = cl.post(path, json=(post or {})) if post is not None else cl.get(path)
        return r.status_code

    # ------------------------------------------------- WHAT MUST OPEN FOR HIM
    OPEN = [("the stock count screen", "/finance/stock/page/count", None),
            ("the stock differences list", "/finance/stock/page/diffs", None),
            ("the open-differences data", "/finance/stock/api/open", None),
            ("the audit finding index", "/finance/stock/api/findings", None),
            ("the audit finding page", "/finance/stock/page/finding", None)]
    for label, path, body in OPEN:
        ck("AMIR CAN OPEN: %s" % label, code(path, body) == 200, str(code(path, body)))

    if have_desk:
        ck("AMIR CAN OPEN: the Vaapsi desk",
           code("/finance/returns/desk/") == 200)

    # submitting a count must be allowed -- a counter who cannot submit is no use
    r = cl.post("/finance/stock/api/count", json=dict(
        marg_as_on="09-09-2027", bill_no="AMIRWALK", bill_date="09-09-2027",
        items_total=1, items=[dict(item="ZZAMIR ONE", marg_qty=10, counted_qty=9,
                                   pack_size=1, counted_by="amir",
                                   entered_by="shivani")]))
    ck("AMIR CAN SUBMIT a finished count", r.status_code == 200
       and (r.get_json() or {}).get("ok"), r.get_data(as_text=True)[:120])
    cid = (r.get_json() or {}).get("count_id")

    # ---------------------------------------------- WHAT MUST STILL REFUSE HIM
    did = None
    con = sqlite3.connect(db)
    row = con.execute("SELECT id FROM stock_diff WHERE count_id=?", (cid,)).fetchone()
    con.close()
    did = row[0] if row else 1

    SHUT = [("name the cause of a difference",
             "/finance/stock/api/diff/%d/cause" % did, {"cause": "THEFT"}),
            ("rule on a difference (write off / recover)",
             "/finance/stock/api/diff/%d/decision" % did, {"decision": "WRITE_OFF"}),
            ("set a price",
             "/finance/stock/api/rate", {"item": "ZZAMIR ONE", "rate_p": 100}),
            ("record a Marg voucher",
             "/finance/stock/api/voucher",
             {"count_id": cid, "voucher_no": "X", "voucher_date": "2027-09-09"}),
            ("see the drift page", "/finance/stock/page/drift", None),
            ("see the drift data", "/finance/stock/api/drift", None),
            ("see the losses report", "/finance/stock/api/losses", None)]
    for label, path, body in SHUT:
        ck("AMIR IS REFUSED: %s" % label, code(path, body) == 403,
           "got %s" % code(path, body))

    # ...but he MAY answer a line, because that is evidence, not a ruling
    ck("AMIR CAN answer a difference line (evidence, never a verdict)",
       code("/finance/stock/api/diff/%d/answer" % did,
            {"reason": "count_error"}) == 200)

    # ------------------------------------------------ and the owner still can
    WHO.update(role="checker", user="manoj")
    for label, path, body in SHUT:
        ck("the owner can still: %s" % label, code(path, body) in (200, 400),
           "got %s" % code(path, body))

    # ------------------------------------------- a stranger gets nothing at all
    WHO.update(role="nobody", user="stranger")
    for label, path, body in OPEN:
        ck("a stranger is refused: %s" % label, code(path, body) == 403,
           "got %s" % code(path, body))

    print("\n%s -- %d passed, %d failed" %
          ("WALK GREEN" if not FAILED else "WALK RED", len(PASSED), len(FAILED)))
    for f in FAILED:
        print("   FAILED: %s" % f)
    return 0 if not FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
