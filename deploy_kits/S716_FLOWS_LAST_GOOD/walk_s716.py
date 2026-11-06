#!/usr/bin/env python3
"""walk_s716.py -- S716 on a MADE-UP root: the real finance_app (its own gate) on a made-up finance.db; then S714's walk on the same code.
    python3 -B walk_s716.py <finance code dir to test>
CONTROL: on the code before S716 (reports_tile cb0d5e0c, marg_flows 7af3f3ec) the S716 checks go red."""
import os, sqlite3, subprocess, sys, tempfile
CODE = os.path.abspath(sys.argv[1]); tmp = tempfile.mkdtemp(prefix="s716walk_")
os.environ.update(FINANCE_DB=os.path.join(tmp, "finance.db"), FINANCE_SSO_DIR=os.path.join(tmp, "nosso"), FINANCE_ALLOW_HEADER_AUTH="1",
                  FINANCE_SCAN_DIR=os.path.join(tmp, "scans"))
sys.path.insert(0, CODE); sys.path.insert(0, os.path.join(os.path.dirname(CODE), "shared"))
ok = bad = 0
def check(name, cond):
    global ok, bad
    print(("  ok   " if cond else "  RED  ") + name); ok += bool(cond); bad += (not cond)
import finance_app as F, reports_tile as RT
con = sqlite3.connect(os.environ["FINANCE_DB"])
con.executescript(open(os.path.join(CODE, "finance_schema.sql")).read())
con.execute("CREATE TABLE IF NOT EXISTS mi_file (md5 TEXT, drive_id TEXT, drive_name TEXT, drive_folder TEXT, drive_mtime TEXT, size INTEGER, stamp TEXT, "
            "type TEXT, variant TEXT, date_from TEXT, date_to TEXT, verdict TEXT, reason TEXT, server_name TEXT, kept INTEGER, lines INTEGER, pc_type TEXT, "
            "pc_verdict TEXT, agree INTEGER, received_at TEXT, source TEXT)")
for md5, typ, v, at in (("a", "SALE_BILLWISE", "VERIFIED", "2026-11-05T10:32:40"), ("b", "SALE_BILLWISE", "REFUSED", "2026-11-05T14:46:00"),
                        ("c", "STOCK_VALUATION", "REFUSED", "2026-11-04T10:14:00"), ("d", "BATCH_STOCK", "VERIFIED", "2026-11-05T04:46:00"),
                        ("e", "STOCK_CLOSING", "REFUSED", "2026-11-05 08:00:00"), ("f", "STOCK_CLOSING", "VERIFIED", "2026-11-05T09:46:00")):
    con.execute("INSERT INTO mi_file (md5, type, verdict, reason, server_name, received_at, source) VALUES (?,?,?,?,?,?,'push')",
                (md5, typ, v, "" if v == "VERIFIED" else "the medical PC refused it: the reader refused it (line 12)", md5, at))
con.commit()
cl = F.app.test_client()
OWNER = {"X-Clinic-User": "manoj", "X-Clinic-Role": "checker"}; SHIVANI = {"X-Clinic-User": "shivani", "X-Clinic-Role": "viewer"}
print("S716 walk on %s" % CODE)
h = cl.get("/finance/reports/flows", headers=OWNER).get_data(as_text=True)
check("1.1 the sale line shows the last GOOD report (05-11 10:32), not the later refused file", "Last report received 05-11 10:32" in h
      and "Last report refused 05-11 14:46" not in h)
check("1.2 ... and says underneath that a later file was refused (05-11 14:46)", "A later file was refused 05-11 14:46" in h)
check("1.3 a report with only refused files still says refused (Stock Valuation 04-11 10:14)", "Last report refused 04-11 10:14" in h)
check("1.4 an older refused file before a good one is not mentioned (closing stock: received 05-11 09:46 only)", "Last report received 05-11 09:46" in h
      and h.count("A later file was refused") == 1)
hs = cl.get("/finance/reports/flows", headers=SHIVANI).get_data(as_text=True)
check("1.5 Shivani's list in Roman Hindi", "Pichhli report aa gayi 05-11 10:32" in hs and "Uske baad ek file manzoor nahi hui 05-11 14:46" in hs)
row = RT._row_html(dict(key="PURCHASE_BILLWISE", label="Purchase bill-wise report", state="ok", at="10:13"))
check("2.1 a report line on Aaj ki reports carries 'Steps dekhiye' to its own flow page", "href='/finance/flows/purchase-bill'" in row and "Steps dekhiye" in row)
row2 = RT._row_html(dict(key="SOMETHING_ELSE", label="x", state="ok", at="10:13"))
check("2.2 a line with no flow carries no link", "Steps dekhiye" not in row2)
check("2.3 Aaj ki reports still draws for Shivani", cl.get("/finance/reports/aaj", headers=SHIVANI).status_code == 200)
here = os.path.dirname(os.path.abspath(__file__))
r = subprocess.run([sys.executable, "-W", "ignore", "-B", os.path.join(here, "walk_s714.py"), CODE], capture_output=True, text=True, timeout=600, cwd="/tmp")
last = (r.stdout.strip().splitlines() or [""])[-1]
check("3.1 S714's walk on the same code: %s" % last, last == "WALK S714: 16 ok, 0 red")
print("WALK S716: %d ok, %d red" % (ok, bad))
