#!/usr/bin/env python3
"""
selftest_metrics_s220.py -- S220 item 2: the two lines, proved on a COPY of the live
db through the real darpan blueprint (the selftest_darpan pattern), on a real month.

  offline:  FIN_DIR=/dir/with/patched/files  FIN_DB=/path/finance.db  python3 selftest_metrics_s220.py
  the box:  /root/wa/venv/bin/python3 -B /root/finance/selftest_metrics_s220.py
Exit code = failures. Nothing is written to the live db.
"""
import os
import shutil
import sqlite3
import sys
import tempfile

FIN_DIR = os.environ.get("FIN_DIR", "/root/finance")
FIN_DB = os.environ.get("FIN_DB", os.path.join(FIN_DIR, "finance.db"))
sys.path.insert(0, FIN_DIR)
from flask import Flask, jsonify                                    # noqa: E402
import darpan_app                                                   # noqa: E402
import finance_returns_audit as fra                                 # noqa: E402

fails = 0


def check(name, ok, detail=""):
    global fails
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + str(detail)) if detail and not ok else ""))
    if not ok:
        fails += 1


tmp = tempfile.mkdtemp(prefix="s220_metrics_")
db = os.path.join(tmp, "finance.db")
shutil.copyfile(FIN_DB, db)
CON = sqlite3.connect(db, check_same_thread=False)
CON.row_factory = sqlite3.Row
ROLE = {"user": "manoj", "roles": ["checker", "maker"]}
app = Flask(__name__)


@app.route("/finance/api/day", methods=["POST"])
def fake_filing():
    return jsonify(ok=True)


def require(*roles):
    have = set(ROLE.get("roles") or [])
    if not have.intersection(roles):
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    return dict(ROLE), None


darpan_app.init(app, lambda: CON, require, unit="medical")
c = app.test_client()
check("M0 patched darpan_app exposes _month_metrics", hasattr(darpan_app, "_month_metrics"))

month = "2026-08"
j = c.get("/finance/darpan/api/cn-detail?month=" + month).get_json()
M = j.get("metrics") or {}
check("M1 cn-detail carries metrics with every key", j.get("ok") and all(k in M for k in (
    "examinable_p", "flagged_p", "examinable_pct", "flagged_pct", "sales_p", "rate_pct", "prev_month", "prev_rate_pct")), sorted(M))

# recompute independently from the audit's own rows
CANT = ("not examinable", "identity needed", "identity disputed", "no patient attributed")
MONEY = ("NEVER BOUGHT", "REFUNDED MORE THAN PAID", "RETURNED MORE THAN SOLD", "DISCOUNTED RETURN")
days = [r[0] for r in CON.execute("SELECT DISTINCT business_date FROM day_entry WHERE unit='medical' AND business_date LIKE ? ORDER BY 1", (month + "%",))]
tot = ex = fl = 0
for d in days:
    for r in fra.returns_for_day(CON, d, "medical")[0]:
        tot += r["amount_p"]
        if r["verdict"] not in CANT:
            ex += r["amount_p"]
        if r["verdict"] in MONEY:
            fl += r["amount_p"]
check("M2 examinable rupees == the audit's own rows, recomputed", M["examinable_p"] == ex, (M["examinable_p"], ex))
check("M3 flagged rupees == the audit's own rows, recomputed", M["flagged_p"] == fl, (M["flagged_p"], fl))
check("M4 the shares are of the month's total and add up sensibly",
      M["examinable_pct"] == round(100.0 * ex / tot, 1) and M["flagged_pct"] == round(100.0 * fl / tot, 1) and fl <= ex <= tot,
      (M["examinable_pct"], M["flagged_pct"], tot))
sp = CON.execute("SELECT COALESCE(SUM(CASE WHEN s.service LIKE '%!_return' ESCAPE '!' THEN s.amount_p END),0),"
                 " COALESCE(SUM(CASE WHEN s.service NOT LIKE '%!_return' ESCAPE '!' THEN s.amount_p END),0)"
                 " FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id WHERE e.unit='medical' AND substr(e.business_date,1,7)=?", (month,)).fetchone()
check("M5 the rate is returns / sales on the bill spine, to 0.1%", M["sales_p"] == sp[1] and M["rate_pct"] == round(100.0 * sp[0] / sp[1], 1), (M["rate_pct"], sp))
check("M6 the previous month is named and rated (Jul for Aug)", M["prev_month"] == "2026-07" and M["prev_rate_pct"] is not None, (M["prev_month"], M["prev_rate_pct"]))
check("M7 August's rate is above July's (the doubling the owner saw)", M["rate_pct"] > M["prev_rate_pct"], (M["rate_pct"], M["prev_rate_pct"]))
j2 = c.get("/finance/darpan/api/cn-detail?month=2026-01").get_json()
M2 = j2.get("metrics") or {}
check("M8 a month with no data is fail-soft: None, not a crash", j2.get("ok") and M2.get("rate_pct") is None and M2.get("examinable_pct") is None)
check("M9 January's previous month wraps to December of the year before", M2.get("prev_month") == "2025-12")
hub = open(os.path.join(FIN_DIR, "finance_ui", "finance_approvals.html"), encoding="utf-8").read()
check("P1 the hub carries the gist line once, English only", hub.count("S220 METRICS") == 1 and "to look at" in hub and not any("ऀ" <= ch <= "ॿ" for ch in hub))
CON.close()
shutil.rmtree(tmp, ignore_errors=True)
print("\n%s -- %d check(s) failed" % ("ALL GREEN" if fails == 0 else "RED", fails))
sys.exit(fails)
