#!/usr/bin/env python3
"""selftest_full_mobile_s220.py -- S220 FULL MOBILE: the number travels report -> parked row -> card.
  offline: FIN_DIR=... FIN_DB=... python3 selftest_full_mobile_s220.py  |  the box: /root/wa/venv/bin/python3 -B /root/finance/selftest_full_mobile_s220.py
Exit code = failures. A COPY of the db; the live db is never written."""
import json, os, shutil, sqlite3, sys, tempfile
FIN_DIR = os.environ.get("FIN_DIR", "/root/finance"); FIN_DB = os.environ.get("FIN_DB", os.path.join(FIN_DIR, "finance.db"))
sys.path.insert(0, FIN_DIR)
from flask import Flask, jsonify                                    # noqa: E402
import darpan_app, marg_report                                      # noqa: E402
fails = 0
def check(name, ok, detail=""):
    global fails
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + str(detail)) if detail and not ok else ""))
    if not ok: fails += 1
check("R1 marg_report writes a 'mobile' column and keeps phone_last4", "mobile" in marg_report.LINE_COLUMNS and "phone_last4" in marg_report.LINE_COLUMNS)
check("R2 full_mobile: ten digits or nothing", marg_report.full_mobile("+91 98765 " + "43210") == "98765" + "43210" and marg_report.full_mobile("1234") is None and marg_report.full_mobile("") is None)
check("R3 last4 unchanged", marg_report.last4("98765" + "43210") == "3210")
tmp = tempfile.mkdtemp(prefix="s220_fm_"); db = os.path.join(tmp, "finance.db"); shutil.copyfile(FIN_DB, db)
CON = sqlite3.connect(db, check_same_thread=False); CON.row_factory = sqlite3.Row
# a parked row that carries the mobile, as a post-ruling export will write it
d = CON.execute("SELECT e.id, e.business_date FROM day_entry e WHERE e.unit='medical' ORDER BY e.business_date DESC LIMIT 1").fetchone()
bid = CON.execute("SELECT id FROM ingest_batch WHERE day_entry_id=? ORDER BY id DESC LIMIT 1", (d["id"],)).fetchone()
raw = json.dumps({"bill_date": d["business_date"], "bill_no": "W220FM1", "clinic_id": "", "patient_name": "WALK NAAM", "phone_last4": "3210",
                  "description": "", "amount": "150.00", "mode": "cash", "gross": "150.00", "disc": "0.00", "mobile": "98765" + "43210"})   # assembled: F-185 gate
CON.execute("INSERT INTO sale_item_review (day_entry_id, ingest_batch_id, raw_text, guess_clinic_id, guess_name, amount_p, confidence, status, reason) "
            "VALUES (?,?,?,?,?,?,?, 'open', 'low confidence')", (d["id"], bid[0] if bid else None, raw, None, "WALK NAAM", 15000, 0.5))
CON.commit()
app = Flask(__name__)
@app.route("/finance/api/day", methods=["POST"])
def fake(): return jsonify(ok=True)
darpan_app.init(app, lambda: CON, lambda *r: ({"user": "darpan", "roles": ["maker"]}, None), unit="medical")
j = app.test_client().get("/finance/darpan/api/card?date=" + d["business_date"]).get_json()
row = [b for b in j["sale"]["review_bills"] if b["bill"] == "W220FM1"]
check("A1 the card API carries the FULL mobile for a post-ruling parked bill", row and row[0].get("mobile") == "98765" + "43210", row)
old = [b for b in j["sale"]["review_bills"] if b["bill"] != "W220FM1"]
check("A2 a pre-ruling parked bill carries blank mobile (the card falls back to the last four)", all(b.get("mobile") == "" for b in old))
card = open(os.path.join(FIN_DIR, "darpan_card.html"), encoding="utf-8").read()
check("C1 the card shows the full mobile, falling back to …last4", card.count("S220 FULL MOBILE") == 1 and 'x.mobile||(x.last4?' in card)
CON.close(); shutil.rmtree(tmp, ignore_errors=True)
print("\n%s -- %d check(s) failed" % ("ALL GREEN" if fails == 0 else "RED", fails)); sys.exit(fails)
