#!/usr/bin/env python3
"""selftest_parked_bills_s220.py -- S220 F-282b: the parked bills reach Darpan's card, expandable.
  offline: FIN_DIR=... FIN_DB=... python3 selftest_parked_bills_s220.py  |  the box: /root/wa/venv/bin/python3 -B /root/finance/selftest_parked_bills_s220.py
Exit code = failures. Nothing is written to the live db."""
import os, re, shutil, sqlite3, sys, tempfile
FIN_DIR = os.environ.get("FIN_DIR", "/root/finance"); FIN_DB = os.environ.get("FIN_DB", os.path.join(FIN_DIR, "finance.db"))
sys.path.insert(0, FIN_DIR)
from flask import Flask, jsonify                                    # noqa: E402
import darpan_app                                                   # noqa: E402
fails = 0
def check(name, ok, detail=""):
    global fails
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + str(detail)) if detail and not ok else ""))
    if not ok: fails += 1
tmp = tempfile.mkdtemp(prefix="s220_pb_"); db = os.path.join(tmp, "finance.db"); shutil.copyfile(FIN_DB, db)
CON = sqlite3.connect(db, check_same_thread=False); CON.row_factory = sqlite3.Row
app = Flask(__name__)
@app.route("/finance/api/day", methods=["POST"])
def fake(): return jsonify(ok=True)
darpan_app.init(app, lambda: CON, lambda *r: ({"user": "darpan", "roles": ["maker"]}, None), unit="medical")
c = app.test_client()
d = CON.execute("SELECT business_date, in_review_count, in_review_p FROM v_day_attribution WHERE unit='medical' AND in_review_count>0 ORDER BY business_date DESC LIMIT 1").fetchone()
check("B0 a day with parked bills exists", d is not None)
j = c.get("/finance/darpan/api/card?date=" + d["business_date"]).get_json(); s = j["sale"]
check("B1 the card lists the parked bills", isinstance(s.get("review_bills"), list) and len(s["review_bills"]) == d["in_review_count"], (len(s.get("review_bills") or []), d["in_review_count"]))
check("B2 each carries bill, rupees, name, last4 -- and the rupees add up to the parked total", all(set(("bill","amount_p","name","clinic_id","last4")) <= set(b) for b in s["review_bills"]) and sum(b["amount_p"] for b in s["review_bills"]) == d["in_review_p"])
check("B3 no whole phone number leaves the API (F-185)", not re.search(r"\d{10}", str(s["review_bills"])))
check("B4 a day without parked bills lists none", c.get("/finance/darpan/api/card?date=2026-04-02").get_json()["sale"].get("review_bills") == [])
card = open(os.path.join(FIN_DIR, "darpan_card.html"), encoding="utf-8").read()
check("C1 the card row is now a <details> with the bills table", card.count("S220 F-282b") == 1 and "tbl(j.sale.review_bills||[]" in card)
CON.close(); shutil.rmtree(tmp, ignore_errors=True)
print("\n%s -- %d check(s) failed" % ("ALL GREEN" if fails == 0 else "RED", fails)); sys.exit(fails)
