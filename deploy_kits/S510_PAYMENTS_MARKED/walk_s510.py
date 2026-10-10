"""walk_s510.py -- S510_PAYMENTS_MARKED, session 304 (parent), 10-Oct-2026. The walk the installer runs BEFORE placing.

On a SCRATCH copy of finance.db, a scratch sheets folder and a scratch copy of /root/finance's programs (the kit's two over them,
unless --control):
  * the Payment Register sheet is re-made from the table itself (row numbers kept), with ONE Docterz notification row's
    description replaced by the Janitor v2.4 words and ONE ordinary receipt row marked '[NOT A PAYMENT]';
  * payments_register.py ingest reads it: the receipt row's change is recorded as before; the Docterz row's change is recorded
    WITHOUT the old words (no patient name kept as history); an older record holding such words is scrubbed;
  * the month's payment digest leaves out the marked receipt row.
The SAME walk on the live programs (--control) must end RED. Prints counts and row numbers only, never a description.
"""
import argparse
import csv
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import datetime as dt

ap = argparse.ArgumentParser()
ap.add_argument("--kit", required=True)
ap.add_argument("--fin", default="/root/finance")
ap.add_argument("--db", default="/root/finance/finance.db")
ap.add_argument("--venv", default="")
ap.add_argument("--control", action="store_true")
a = ap.parse_args()
scr = tempfile.mkdtemp(prefix="s510_walk_")
fin = os.path.join(scr, "fin")
os.makedirs(fin)
for n in os.listdir(a.fin):
    p = os.path.join(a.fin, n)
    if os.path.isfile(p) and n.endswith((".py", ".json", ".html")) and not n.startswith("."):
        shutil.copy2(p, os.path.join(fin, n))
if not a.control:
    for n in ("packs.py", "payments_register.py"):
        shutil.copy(os.path.join(a.kit, n), os.path.join(fin, n))
db = os.path.join(scr, "fin.db")
src = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True, timeout=60)
dst = sqlite3.connect(db)
src.backup(dst)
dst.close()
src.close()
red = []
GONE = "[NOT A PAYMENT] Docterz notification — patient details removed"
try:
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    rows = {r["row_no"]: r for r in con.execute("SELECT * FROM payment_register")}
    doc = next((n for n, r in sorted(rows.items()) if "docterz" in (r["vendor"] or "").lower() and not str(r["description"] or "").startswith("[")), None)
    rec = next((n for n, r in sorted(rows.items(), reverse=True) if "invoice" in str(r["description"] or "").lower() and r["amount_paise"]
                and r["date_iso"] and not str(r["description"] or "").startswith("[")), None)
    if not doc or not rec:
        raise RuntimeError("the register has no Docterz row or no invoice row to walk with")
    # an older drift record holding a Docterz row's old words (made up here, to be scrubbed)
    con.execute("INSERT INTO payment_register_drift(at,row_no,field,was,now) VALUES('2026-10-01 02:05:00',?,'description','walk: old words',?)", (doc, GONE))
    con.commit()
    sheets = os.path.join(scr, "sheets", "payment_register")
    os.makedirs(sheets)
    with open(os.path.join(sheets, "Sheet1.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Date", "Vendor", "Description", "Amount (Rs)", "Attachment in Drive", "Gmail Link"])
        for n in range(2, max(rows) + 1):
            r = rows.get(n)
            if r is None:
                w.writerow([""] * 6)
                continue
            desc = GONE if n == doc else (("[NOT A PAYMENT] " + r["description"]) if n == rec else r["description"])
            w.writerow([r["date_raw"], r["vendor"], desc, r["amount_raw"], "Yes" if r["in_drive"] else "No", r["gmail_link"]])
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30)))
    json.dump({"tabs": [{"file": "Sheet1.csv"}], "pulled_at_ist": now.strftime("%Y-%m-%d %H:%M:%S")},
              open(os.path.join(sheets, "_BOOK.json"), "w"))
    con.close()
    r = subprocess.run([sys.executable, "-B", os.path.join(fin, "payments_register.py"), "ingest", "--db", db, "--sheets-dir", os.path.join(scr, "sheets"),
                        "--ignore-stale"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
    print("  pass the ingest: exit %d" % r.returncode)
    if r.returncode != 0:
        red.append("the ingest did not run: %s" % r.stdout.decode("utf-8", "replace").strip().splitlines()[-1][:160] if r.stdout else "exit %d" % r.returncode)
    con = sqlite3.connect(db)
    d_doc = con.execute("SELECT was FROM payment_register_drift WHERE row_no=? AND field='description' ORDER BY id", (doc,)).fetchall()
    d_rec = con.execute("SELECT was FROM payment_register_drift WHERE row_no=? AND field='description' ORDER BY id DESC LIMIT 1", (rec,)).fetchone()
    leak = [w for (w,) in d_doc if w and "removed from the sheet" not in w]
    print("  pass the Docterz row %d: %d change record(s), %d still holding the old words" % (doc, len(d_doc), len(leak)))
    print("  pass the marked receipt row %d: change recorded with its old words: %s" % (rec, "yes" if d_rec and d_rec[0] else "no"))
    if leak:
        red.append("the patient's old words are still kept as history")
    if not (d_rec and d_rec[0]):
        red.append("an ordinary change is no longer recorded")
    month = con.execute("SELECT substr(date_iso,1,7) FROM payment_register WHERE row_no=?", (rec,)).fetchone()[0]
    con.close()
    sys.path.insert(0, fin)
    os.chdir(fin)
    import packs                                                   # noqa: E402
    c2 = sqlite3.connect(db)
    kept, dropped, total = packs.digest_rows(c2, month)
    c2.close()
    whys = [x.get("why") for x in dropped if "marked" in str(x.get("why") or "")]
    print("  pass the digest of %s: %d kept, %d left out (%d of them for the sheet's mark)" % (month, len(kept), len(dropped), len(whys)))
    if not whys:
        red.append("the digest still counts a row the sheet marks as not a payment")
except Exception as ex:                                            # noqa: BLE001
    red.append("%s: %s" % (type(ex).__name__, str(ex)[:200]))
finally:
    os.chdir("/")
    shutil.rmtree(scr, ignore_errors=True)
print("WALK_S510 %s%s" % ("RED: " if red else "GREEN", " | ".join(red)))
sys.exit(1 if red else 0)
