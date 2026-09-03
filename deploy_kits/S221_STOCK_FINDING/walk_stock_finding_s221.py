#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walk_stock_finding_s221.py -- THE LIVE-SHAPE WALK for S221_STOCK_FINDING.

It mounts the REAL patched stock_app blueprint on a COPY of the live
finance.db, pushes a real-shaped Marg snapshot, submits a real count through
the REAL /api/count, and then works the finding the way the three people will:
the staff answer, the owner rules, a rate is typed in, a voucher is recorded.

It measures the two properties the owner's rulings actually are:

  * D-c LOG ONLY -- every table in the database is fingerprinted before and
    after the owner marks a recovery, and NO ledger, advance, salary or cash
    table is allowed to differ. "Nothing is deducted" is a measurement here,
    not a promise in a README.

  * THE SEAL -- the finding's md5 is recomputed on every read, and the walk
    proves it both agrees with a clean finding and DETECTS a tampered row.

IT NEVER TOUCHES THE LIVE DATABASE. The first thing it does is copy it.

Fixtures are assembled at run time; no patient data and no real item is
written into this file.

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/walk_stock_finding_s221.py
Offline:         FIN_DB=/path/to/finance.db python3 -B walk_stock_finding_s221.py
"""

import datetime as dt
import hashlib
import json
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


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("   [%s]" % detail) if detail and not cond else ""))


def fingerprint(db):
    con = sqlite3.connect(db)
    out = {}
    for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' "
                               "ORDER BY name").fetchall():
        try:
            h = hashlib.md5()
            for row in con.execute('SELECT * FROM "%s"' % name):
                h.update(repr(row).encode("utf-8", "replace"))
            out[name] = h.hexdigest()
        except Exception as ex:                               # pragma: no cover
            out[name] = "unreadable:%s" % ex
    con.close()
    return out


ROLE = {"role": "checker", "user": "manoj"}


def main():
    if not os.path.exists(SRC_DB):
        print("no database at %s -- set FIN_DB" % SRC_DB)
        return 2
    tmp = tempfile.mkdtemp(prefix="walk_sf_")
    db = os.path.join(tmp, "finance.db")
    shutil.copyfile(SRC_DB, db)
    print("walking on a COPY: %s\n" % db)

    import stock_app as SA
    ck("the patched stock app is the one under test",
       "S221 FINDING" in open(SA.__file__, encoding="utf-8").read())

    from flask import Flask
    app = Flask(__name__)

    def _db():
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        return c

    def _require(*roles):
        if ROLE["role"] not in roles:
            from flask import jsonify
            return None, (jsonify(ok=False, error="forbidden"), 403)
        return dict(ROLE), None

    SA.init(app, _db, _require, unit="medical", url_prefix="/finance/stock",
            marg_token="walk-token")
    cl = app.test_client()
    AS_ON = "01-01-2027"                       # a date the live data cannot hold

    # ---------------------------------------------------- a real-shaped export
    # three items with a rate, one deliberately WITHOUT -- the 189-item problem,
    # reproduced rather than described.
    items = [dict(item="ZZWALK ALPHA", qty=100, packing="10x10", pack_size=10, rate_p=250),
             dict(item="ZZWALK BETA", qty=40, packing="1x10", pack_size=10, rate_p=1200),
             dict(item="ZZWALK GAMMA", qty=25, packing="1x5", pack_size=5, rate_p=600),
             dict(item="ZZWALK NORATE", qty=30, packing="1x10", pack_size=10)]
    r = cl.post("/finance/stock/api/snapshot",
                json=dict(as_on=AS_ON, source="walk", items=items))
    ck("the export loads", r.status_code == 200 and r.get_json().get("ok"),
       r.get_data(as_text=True)[:200])

    # ------------------------------------------------------------- the count
    counted = [dict(item="ZZWALK ALPHA", marg_qty=100, counted_qty=92, pack_size=10,
                    counted_by="alisha", entered_by="shivani"),
               dict(item="ZZWALK BETA", marg_qty=40, counted_qty=40, pack_size=10,
                    counted_by="alisha", entered_by="shivani"),
               dict(item="ZZWALK GAMMA", marg_qty=25, counted_qty=22, pack_size=5,
                    counted_by="shavez", entered_by="shivani"),
               dict(item="ZZWALK NORATE", marg_qty=30, counted_qty=26, pack_size=10,
                    counted_by="alisha", entered_by="shivani")]
    r = cl.post("/finance/stock/api/count",
                json=dict(marg_as_on=AS_ON, bill_no="A009999", bill_date="01-01-2027",
                          items_total=4, items=counted))
    j = r.get_json()
    ck("the count submits", r.status_code == 200 and j.get("ok"),
       r.get_data(as_text=True)[:200])
    cid = j.get("count_id")
    ck("three differences were raised, the agreeing item raised none",
       j.get("differences") == 3, str(j))
    ck("THE FINDING IS SEALED AT SUBMIT, and numbered", bool(j.get("finding_no")),
       str(j.get("finding_no")))

    # -------------------------------------------------------- the document
    d = cl.get("/finance/stock/api/finding/%d" % cid).get_json()
    ck("the document composes", bool(d and d.get("ok")), json.dumps(d)[:200] if d else "")
    F = d["finding"]
    ck("the seal verifies against the rows as they stand", F["seal_ok"] is True)
    ck("it names the Marg export it was counted against", F["marg_as_on"] == AS_ON)
    ck("it names BOTH the counters and the writer",
       sorted(F["counted_by"]) == ["alisha", "shavez"] and F["entered_by"] == ["shivani"],
       str(F))
    ck("it carries the date and time it was sealed", bool(F["sealed_at"]))
    ck("the basis is stated as MRP (the owner's D-a)", F["basis"] == "MRP")
    ck("the VALUED differences are the two with a rate", len(d["lines"]) == 2,
       str([l["item"] for l in d["lines"]]))
    ck("the UNVALUED one is listed separately, not dropped",
       len(d["unvalued"]) == 1 and d["unvalued"][0]["item"] == "ZZWALK NORATE",
       str(d["unvalued"]))
    # 8 units x Rs 2.50 = Rs 20.00 ; 3 x Rs 6.00 = Rs 18.00 -> Rs 38.00 short
    ck("the shortage totals correctly at MRP (Rs 38.00)",
       d["totals"]["short_p"] == 3800, str(d["totals"]))
    ck("the unvalued line is NOT inside that total",
       d["totals"]["short_p"] == 3800 and d["totals"]["undecided_lines"] == 3,
       str(d["totals"]))
    ck("the cost column is present and honestly empty (M3 backfills it)",
       all(l["cost_p"] is None for l in d["lines"]))

    # --------------------------------------------------------- the staff layer
    ROLE.update(role="maker", user="darpan")
    line = [l for l in d["lines"] if l["item"] == "ZZWALK ALPHA"][0]
    a = cl.post("/finance/stock/api/diff/%d/answer" % line["id"],
                json=dict(reason="not_billed", note="bill nahin bana"))
    ck("a staff answer is accepted", a.status_code == 200 and a.get_json().get("ok"))
    bad = cl.post("/finance/stock/api/diff/%d/answer" % line["id"],
                  json=dict(reason="whatever"))
    ck("an invented reason is REFUSED", bad.status_code == 400)
    forb = cl.post("/finance/stock/api/diff/%d/decision" % line["id"],
                   json=dict(decision="WRITE_OFF"))
    ck("STAFF CANNOT RULE ON A LINE -- the decision is the checker's alone",
       forb.status_code == 403, str(forb.status_code))

    d2 = cl.get("/finance/stock/api/finding/%d" % cid).get_json()
    l2 = [l for l in d2["lines"] if l["id"] == line["id"]][0]
    ck("his answer shows on the line, with his name",
       l2["answer"] and l2["answer"]["reason"] == "not_billed"
       and l2["answer"]["answered_by"] == "darpan")
    ck("and it changed no number", l2["value_p"] == line["value_p"]
       and l2["marg_qty"] == line["marg_qty"])
    ck("the seal still verifies after the staff have worked it",
       d2["finding"]["seal_ok"] is True)

    # ------------------------------------ THE RULING, MEASURED: log only (D-c)
    ROLE.update(role="checker", user="manoj")
    before = fingerprint(db)
    dec = cl.post("/finance/stock/api/diff/%d/decision" % line["id"],
                  json=dict(decision="RECOVER", recover_from="darpan"))
    ck("the owner can mark a recovery", dec.status_code == 200 and dec.get_json().get("ok"),
       dec.get_data(as_text=True)[:200])
    after = fingerprint(db)
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    ck("marking a recovery changed ONLY the decision table and the line's status",
       changed == ["stock_diff", "stock_diff_decision"], "changed: %s" % changed)
    money = [k for k in changed if any(w in k.lower() for w in
             ("ledger", "advance", "salary", "cash", "staff", "payout", "hold"))]
    ck("NO ledger, advance, salary, staff or cash table was touched -- nothing is "
       "deducted by this code", not money, str(money))

    d3 = cl.get("/finance/stock/api/finding/%d" % cid).get_json()
    l3 = [l for l in d3["lines"] if l["id"] == line["id"]][0]
    ck("the amount defaults to the MRP value of the shortage (Rs 20.00)",
       l3["decision"]["recover_p"] == 2000, str(l3["decision"]))
    ck("D-d: the LINE is closed", l3["line_state"] == "closed" and l3["status"] == "closed")
    ck("D-d: the recovery AMOUNT stays open", l3["decision"]["recovery_state"] == "open")
    ck("it appears on the recovery list, against the person named",
       any(x["person"] == "darpan" and x["amount_p"] == 2000 for x in d3["recovery"]),
       str(d3["recovery"]))
    ck("and in the total marked for recovery", d3["totals"]["to_recover_p"] == 2000,
       str(d3["totals"]))

    other = [l for l in d3["lines"] if l["item"] == "ZZWALK GAMMA"][0]
    cl.post("/finance/stock/api/diff/%d/decision" % other["id"],
            json=dict(decision="WRITE_OFF"))
    d4 = cl.get("/finance/stock/api/finding/%d" % cid).get_json()
    ck("a write-off lands in its own total (Rs 18.00)",
       d4["totals"]["written_off_p"] == 1800, str(d4["totals"]))
    ck("and on its own list", any(w["item"] == "ZZWALK GAMMA" for w in d4["writeoffs"]))
    ck("nothing is left undecided among the valued lines",
       d4["totals"]["undecided_lines"] == 1, str(d4["totals"]))   # the unvalued one

    # ---------------------------------------- a recovery with no value is refused
    uv = d4["unvalued"][0]
    no = cl.post("/finance/stock/api/diff/%d/decision" % uv["id"],
                 json=dict(decision="RECOVER", recover_from="darpan"))
    ck("a recovery on a line with NO RATE is REFUSED, not guessed at",
       no.status_code == 400, no.get_data(as_text=True)[:160])

    # ------------------------------------------- D-b: type a rate, it re-values
    rr = cl.post("/finance/stock/api/rate", json=dict(item="ZZWALK NORATE", rate_p=500))
    ck("a rate can be typed in", rr.status_code == 200 and rr.get_json().get("ok"))
    ck("and it re-valued the waiting line", rr.get_json().get("revalued") == 1,
       str(rr.get_json()))
    d5 = cl.get("/finance/stock/api/finding/%d" % cid).get_json()
    ck("the line has moved out of the unvalued block", not d5["unvalued"])
    ck("its value is right (4 x Rs 5.00 = Rs 20.00)",
       any(l["item"] == "ZZWALK NORATE" and l["value_p"] == -2000 for l in d5["lines"]),
       str([(l["item"], l["value_p"]) for l in d5["lines"]]))
    ck("THE SEAL STILL HOLDS after a late re-valuation -- it covers the counted "
       "quantities, not the price, which may legitimately be filled in later",
       d5["finding"]["seal_ok"] is True, str(d5["finding"]))

    # ...but a changed QUANTITY must break it. Nothing in the app can do this;
    # the walk reaches into the database exactly as a tamperer would.
    _tc = sqlite3.connect(db)
    _tc.execute("UPDATE stock_diff SET counted_qty=counted_qty-1 WHERE item='ZZWALK BETA' "
                "OR item='ZZWALK ALPHA'")
    _tc.commit(); _tc.close()
    dT = cl.get("/finance/stock/api/finding/%d" % cid).get_json()
    ck("but a COUNTED QUANTITY altered behind the app's back IS detected",
       dT["finding"]["seal_ok"] is False, str(dT["finding"]))
    _tc = sqlite3.connect(db)
    _tc.execute("UPDATE stock_diff SET counted_qty=counted_qty+1 WHERE item='ZZWALK BETA' "
                "OR item='ZZWALK ALPHA'")
    _tc.commit(); _tc.close()
    ck("and the seal comes back when the tampering is undone",
       cl.get("/finance/stock/api/finding/%d" % cid).get_json()["finding"]["seal_ok"] is True)

    # ------------------------------------------- the export re-values too (D-b)
    con = sqlite3.connect(db)
    con.execute("UPDATE stock_diff SET value_p=NULL WHERE item='ZZWALK NORATE'")
    con.execute("DELETE FROM stock_rate WHERE item='ZZWALK NORATE'")
    con.commit()
    con.close()
    r2 = cl.post("/finance/stock/api/snapshot",
                 json=dict(as_on=AS_ON, source="walk2",
                           items=[dict(item="ZZWALK NORATE", qty=30, pack_size=10,
                                       rate_p=500)]))
    ck("a later export with the missing rate re-values it by itself",
       r2.get_json().get("revalued") == 1, str(r2.get_json()))

    # ------------------------------------------------------------ the voucher
    v = cl.post("/finance/stock/api/voucher",
                json=dict(count_id=cid, voucher_no="SA-001", voucher_date="2027-01-02",
                          note="walk", scan_ref="scans/2027-01/SA-001.jpg"))
    ck("the Marg correction voucher is recorded, with its date",
       v.status_code == 200 and v.get_json().get("ok"))
    d6 = cl.get("/finance/stock/api/finding/%d" % cid).get_json()
    ck("it appears on the document", any(x["voucher_no"] == "SA-001"
                                         for x in d6["vouchers"]))
    ck("with the place the scan is kept",
       d6["vouchers"][0]["scan_ref"] == "scans/2027-01/SA-001.jpg")

    # ------------------------------------------------------------- the pages
    p = cl.get("/finance/stock/page/finding")
    ck("the document page serves", p.status_code == 200, str(p.status_code))
    html = p.get_data(as_text=True)
    ck("it is printable", "@media print" in html)
    ck("it says in words that recovery is logged only",
       "not deducted" in html.lower())
    ck("the older screens still serve",
       cl.get("/finance/stock/page/diffs").status_code == 200
       and cl.get("/finance/stock/api/open").status_code == 200)
    ck("the losses report is untouched and still answers",
       cl.get("/finance/stock/api/losses").status_code == 200)

    # ------------------------------------------------- re-sealing is impossible
    r3 = cl.post("/finance/stock/api/count",
                 json=dict(marg_as_on=AS_ON, bill_no="A009999", bill_date="01-01-2027",
                           items_total=4, items=counted))
    ck("a re-count makes a NEW finding, it does not overwrite the old one",
       r3.get_json().get("count_id") != cid and bool(r3.get_json().get("finding_no")),
       str(r3.get_json()))
    d7 = cl.get("/finance/stock/api/finding/%d" % cid).get_json()
    ck("the first finding still says exactly what it said",
       d7["finding"]["no"] == F["no"] and d7["finding"]["sealed_at"] == F["sealed_at"])

    print("\n%s -- %d passed, %d failed" %
          ("WALK GREEN" if not FAILED else "WALK RED", len(PASSED), len(FAILED)))
    for f in FAILED:
        print("   FAILED: %s" % f)
    return 0 if not FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
