"""walk_s511.py -- S511_RECEPTION_MATCH, session 304 (parent), 10-Oct-2026. The walk the installer runs BEFORE placing.

On a SCRATCH copy of finance.db and scratch copies of the programs (the kit's over them, unless --control):
  * the shared 'reception' login is granted Docterz daily collection, Morning match and Check karein (tile_grants.json v34);
  * Morning match, opened as 'reception', lists every October working day still waiting for a first pass, OLDEST FIRST (one
    day goes straight to it; none goes to yesterday) -- read from the copy of the real books, days and counts only;
  * no day's verdict says the bank agrees while the bank's part has not answered (F-796), over every October day.
The SAME walk on the live programs (--control) must end RED. Prints dates and counts only.
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

ap = argparse.ArgumentParser()
ap.add_argument("--kit", required=True)
ap.add_argument("--fin", default="/root/finance")
ap.add_argument("--portal", default="/root/portal")
ap.add_argument("--db", default="/root/finance/finance.db")
ap.add_argument("--venv", default="")
ap.add_argument("--control", action="store_true")
a = ap.parse_args()
scr = tempfile.mkdtemp(prefix="s511_walk_")
fin = os.path.join(scr, "fin")
os.makedirs(fin)
for n in os.listdir(a.fin):
    p = os.path.join(a.fin, n)
    if os.path.isfile(p) and n.endswith((".py", ".json", ".html")) and not n.startswith("."):
        shutil.copy2(p, os.path.join(fin, n))
grants = os.path.join(a.kit if not a.control else a.portal, "tile_grants.json")
if not a.control:
    shutil.copy(os.path.join(a.kit, "clinic_money.py"), os.path.join(fin, "clinic_money.py"))
db = os.path.join(scr, "fin.db")
src = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True, timeout=60)
dst = sqlite3.connect(db)
src.backup(dst)
dst.close()
src.close()
sys.path.insert(0, fin)
os.chdir(fin)
red = []
try:
    g = json.load(open(grants))
    got = set((g["users"].get("reception") or {}).get("extra") or [])
    need = {"Docterz daily collection", "Morning match", "Check karein"}
    print("  pass the reception login's tiles (v%s): %s" % (g.get("version"), ", ".join(sorted(need & got)) or "none of the three"))
    if not need <= got:
        red.append("the reception login still lacks %s" % ", ".join(sorted(need - got)))
    import clinic_money as CM                                      # noqa: E402
    from flask import Flask                                        # noqa: E402

    def _g():
        c = sqlite3.connect(db, timeout=60)
        c.row_factory = sqlite3.Row
        return c
    app = Flask("walk_s511")
    CM.init(app, _g, lambda *r, **k: (dict(user="reception", role="staff", roles=["maker"]), None))
    cl = app.test_client()
    r = cl.get("/finance/clinic/match")
    con = _g()
    st = {x["business_date"]: x["status"] for x in con.execute("SELECT business_date, status FROM clinic_money_day")}
    if r.status_code == 200:
        days = re.findall(r"/finance/clinic/match/(\d{4}-\d{2}-\d{2})", r.get_data(as_text=True))
        print("  pass Morning match as 'reception': a list of %d day(s) still waiting, oldest %s, newest %s" % (len(days), days[0], days[-1]))
        if days != sorted(days) or any(st.get(d, "open") != "open" for d in days) or any(d < "2026-10-01" for d in days):
            red.append("the list is not October's waiting days oldest first")
    elif r.status_code in (301, 302):
        print("  pass Morning match as 'reception': straight to %s (one day or none waiting)" % r.headers.get("Location", "")[-10:])
    else:
        red.append("Morning match answered %d" % r.status_code)
    if not hasattr(CM, "waiting_days"):
        red.append("no list of the days still waiting")
    bad, n = [], 0
    today = dt.date.today()
    d = dt.date(2026, 10, 1)
    while d < today:
        if d.weekday() != 6:
            m = CM.match_day(con, d.isoformat())
            n += 1
            if not m.get("bank_known") and any("and the bank agree" in ln for ln in (m.get("lines") or [])):
                bad.append(d.isoformat())
        d += dt.timedelta(days=1)
    print("  pass the verdicts of %d October day(s): %d say the bank agrees while it has not answered" % (n, len(bad)))
    if bad:
        red.append("the verdict says the bank agrees on %s while the bank has not answered" % ", ".join(bad))
    con.close()
except Exception as ex:                                            # noqa: BLE001
    red.append("%s: %s" % (type(ex).__name__, str(ex)[:200]))
finally:
    os.chdir("/")
    shutil.rmtree(scr, ignore_errors=True)
print("WALK_S511 %s%s" % ("RED: " if red else "GREEN", " | ".join(red)))
sys.exit(1 if red else 0)
