#!/usr/bin/env python3
"""selftest_daytotal_s220.py -- S220 F-281/F-282: the day's Marg money, told once, on both screens.
  offline: FIN_DIR=... FIN_DB=... python3 selftest_daytotal_s220.py  |  the box: /root/wa/venv/bin/python3 -B /root/finance/selftest_daytotal_s220.py
Runs Darpan's card API on a COPY of the db and reads finance_app's patched helper by text (the app is not importable
outside its service). Exit code = failures."""
import os, re, shutil, sqlite3, sys, tempfile
FIN_DIR = os.environ.get("FIN_DIR", "/root/finance"); FIN_DB = os.environ.get("FIN_DB", os.path.join(FIN_DIR, "finance.db"))
FA = os.environ.get("FA_PATH", os.path.join(FIN_DIR, "finance_app.py"))
sys.path.insert(0, FIN_DIR)
from flask import Flask, jsonify                                    # noqa: E402
import darpan_app                                                   # noqa: E402
fails = 0
def check(name, ok, detail=""):
    global fails
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + str(detail)) if detail and not ok else ""))
    if not ok: fails += 1
tmp = tempfile.mkdtemp(prefix="s220_dt_"); db = os.path.join(tmp, "finance.db"); shutil.copyfile(FIN_DB, db)
CON = sqlite3.connect(db, check_same_thread=False); CON.row_factory = sqlite3.Row
app = Flask(__name__)
@app.route("/finance/api/day", methods=["POST"])
def fake(): return jsonify(ok=True)
darpan_app.init(app, lambda: CON, lambda *r: ({"user": "darpan", "roles": ["maker"]}, None), unit="medical")
c = app.test_client()
# a day with bills parked for review, and a day with a return
d_rev = CON.execute("SELECT business_date, day_total_p, attributed_p, in_review_p, in_review_count FROM v_day_attribution WHERE unit='medical' AND in_review_count>0 ORDER BY business_date DESC LIMIT 1").fetchone()
d_ret = CON.execute("SELECT e.business_date FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id WHERE s.service LIKE '%return%' AND e.unit='medical' ORDER BY e.business_date DESC LIMIT 1").fetchone()
check("D0 a day with parked bills exists to test on", d_rev is not None, d_rev)
if d_rev:
    j = c.get("/finance/darpan/api/card?date=" + d_rev["business_date"]).get_json()
    s = j.get("sale") or {}
    check("D1 the card now carries review_p / review_n", "review_p" in s and "review_n" in s, sorted(s))
    check("D2 the card's day sale = sold - returned + parked (signed)", s.get("day_sale_p") == s.get("sold_p") - s.get("returned_p") + s.get("review_p"), s)
    check("D3 ... and the parked figures equal v_day_attribution's", s.get("review_p") == d_rev["in_review_p"] and s.get("review_n") == d_rev["in_review_count"], (s.get("review_p"), d_rev["in_review_p"]))
    check("D4 ... so the card equals the day's attributed + parked money (the view)", s.get("day_sale_p") == d_rev["attributed_p"] + d_rev["in_review_p"], (s.get("day_sale_p"), d_rev["attributed_p"], d_rev["in_review_p"]))
if d_ret:
    j2 = c.get("/finance/darpan/api/card?date=" + d_ret[0]).get_json()
    s2 = j2.get("sale") or {}
    check("D5 a return still SUBTRACTS on the card", s2.get("returned_p", 0) > 0 and s2.get("day_sale_p") < s2.get("sold_p") + s2.get("review_p", 0), s2)
src = open(FA, encoding="utf-8").read()
check("F1 finance_app's Marg total now reads v_day_attribution (attributed + parked, returns subtracted)",
      src.count("S220 F-281") == 1 and "marg_total_p = int(_va[\"attributed_p\"] or 0) + int(_va[\"in_review_p\"] or 0)" in src)
check("F2 the old unsigned sum is gone", 'for b_r in con.execute(\n            "SELECT s.amount_p, s.service FROM sale_item s JOIN day_entry e "\n            "ON e.id=s.day_entry_id WHERE e.unit=? AND e.business_date=?",\n            (UNIT, iso))) if st.get("exists") else 0' not in src)
card = open(os.path.join(FIN_DIR, "darpan_card.html"), encoding="utf-8").read()
check("C1 Darpan's card names the parked bills (Hindi, staff page)", card.count("S220 F-282") == 1 and "bina pehchaan ke bill" in card)
CON.close(); shutil.rmtree(tmp, ignore_errors=True)
print("\n%s -- %d check(s) failed" % ("ALL GREEN" if fails == 0 else "RED", fails)); sys.exit(fails)
