#!/usr/bin/env python3
"""proof_s781.py FILES_DIR SHARED_DIR FINANCE_DIR DB_COPY ASSETS_DB LABEL
On a COPY of this box's finance.db (never the live one) and the live assets.db opened READ ONLY: the Purchase bills page of the newest
month as the doctor sees it, what S781 would show there, and one door pressed and undone on the copy. Last line:
'PROOF S781 <LABEL>: in Marg N · provisional N (N read right) · differs N · GREEN' or '... RED <why>'."""
import os
import re
import shutil
import sqlite3
import sys
import tempfile

FILES, SHARED, FIN, DBC, ADB, LABEL = sys.argv[1:7]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != HERE]
TMP = tempfile.mkdtemp(prefix="p781_")
RUN = os.path.join(TMP, "run")
os.makedirs(RUN)
for f in ("purchase_app.py", "provisional_s781.py"):
    shutil.copyfile(os.path.join(FILES, f), os.path.join(RUN, f))
shutil.copyfile(os.path.join(FIN, "purchase_schema.sql"), os.path.join(RUN, "purchase_schema.sql"))
sys.path[:0] = [RUN, FIN, SHARED]
AC = os.path.join(TMP, "assets_ro.db")                         # a copy of assets.db: the page never touches the live one
if os.path.exists(ADB):
    s = sqlite3.connect("file:%s?mode=ro" % ADB, uri=True, timeout=30)
    d = sqlite3.connect(AC)
    s.backup(d)
    d.close()
    s.close()
from flask import Flask, g, jsonify  # noqa: E402

app = Flask(__name__)


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DBC, timeout=30)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def _close(_e):
    c = g.pop("db", None)
    if c is not None:
        c.close()


def require(*roles, unit="medical"):
    return dict(user="manoj", roles=["checker"]), None


import purchase_app as PA  # noqa: E402

PA.init(app, db, require, unit="medical", marg_token="proof", assets_db=AC if os.path.exists(AC) else os.path.join(TMP, "none.db"))
import provisional_s781 as PS  # noqa: E402

cl = app.test_client()
bad = []
import time  # noqa: E402
t0 = time.time()
r = cl.get("/finance/purchase/page/scans")
took = time.time() - t0
h = r.get_data(as_text=True)
if r.status_code != 200 or 'id="s781"' not in h:
    bad.append("the page %s, S781 section %s" % (r.status_code, 'id="s781"' in h))
mo = re.search(r"\?month=(\d{4}-\d\d)\">[^<]*</a>", h[h.find('class="s749m on"') - 5:]) if 'class="s749m on"' in h else None
month = mo.group(1) if mo else None
c = sqlite3.connect(DBC, timeout=30)
c.row_factory = sqlite3.Row
if not month:
    month = PA._s454_sr().months_with_bills(c)[0]
with app.test_request_context():
    scans = PA._s454_sr().asset_scans(c) or {}
    prov = PS.provisional(c, month, scans)
    diffs = PS.differences(c, month, scans)
    rel = PS.reliability(c, [m for m in sorted({str(x[0]) for x in c.execute("SELECT DISTINCT month FROM purchase_sarvam_check")})][-3:])
bills = PS.month_bills(c, month)
print("month %s · the scans reachable: %d · the page took %.1f s (with the matcher's first run)" % (month, len(scans), took))
print("in Marg: %d bills, %s" % (len(bills), PA._s454_sr().rs(sum(int(b["amount_p"] or 0) for b in bills))))
for x in prov:
    print("provisional scan %s · %s · no. %s · %s · %s · %d line(s) · %s" % (x["stamp"], x["dealer"][:28], x["bill_no"][-4:], x["date"], PA._s454_sr().rs(x["total_p"])
                                                                        if x["total_p"] else "no total", len(x["lines"]), "READS RIGHT" if not x["why"] else "check: " + x["why"][0]))
for x in diffs:
    print("differs: %s %s · %s · %s" % (PA.supplier_key(x["bill"]["supplier"])[:24], x["bill"]["bill_no"], PS.chip(x), "; ".join(PS.diff_words(x))[:160]))
for m, n, st, ru in rel:
    print("reliability %s: %d of %d by the rules (strict %d)" % (m, ru, n, st))
free = [x for x in diffs if not x["mark"] and not x["cleared"]]
if free:
    b0 = int(free[0]["bill"]["id"])
    r1 = cl.post("/finance/purchase/api/s781/mark", json=dict(bill=b0, action="clear"))
    gone = 'id="s781C%d"' % b0 not in cl.get("/finance/purchase/page/scans?month=%s" % month).get_data(as_text=True)
    r2 = cl.post("/finance/purchase/api/s781/mark", json=dict(bill=b0, action="undo"))
    left = c.execute("SELECT COUNT(*) FROM purchase_s781_mark WHERE bill_id=?", (b0,)).fetchone()[0]
    print("door on the copy: Marg is right %s (the row left: %s) · undo %s · marks left %d" % (r1.status_code, gone, r2.status_code, left))
    if r1.status_code != 200 or r2.status_code != 200 or left or not gone:
        bad.append("the door")
c.close()
print("PROOF S781 %s: in Marg %d · provisional %d (%d read right) · differs %d · %s" % (LABEL, len(bills), len(prov), sum(1 for x in prov if not x["why"]),
                                                                                    len(diffs), "GREEN" if not bad else "RED " + "; ".join(bad)))
