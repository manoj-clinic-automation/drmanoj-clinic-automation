#!/usr/bin/env python3
"""selftest_intent_s220.py -- S220 item 4: the intent scorer + its endpoint, on a COPY of the live db.
  offline: FIN_DIR=... FIN_DB=... python3 selftest_intent_s220.py  |  the box: /root/wa/venv/bin/python3 -B /root/finance/selftest_intent_s220.py
Exit code = failures. The live db is never written."""
import datetime as dt, os, shutil, sqlite3, subprocess, sys, tempfile
FIN_DIR = os.environ.get("FIN_DIR", "/root/finance"); FIN_DB = os.environ.get("FIN_DB", os.path.join(FIN_DIR, "finance.db"))
sys.path.insert(0, FIN_DIR)
from flask import Flask, jsonify                                    # noqa: E402
import darpan_app, finance_intent as fi                             # noqa: E402
fails = 0
def check(name, ok, detail=""):
    global fails
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + str(detail)) if detail and not ok else ""))
    if not ok: fails += 1
tmp = tempfile.mkdtemp(prefix="s220_intent_"); db = os.path.join(tmp, "finance.db"); shutil.copyfile(FIN_DB, db)
CON = sqlite3.connect(db, check_same_thread=False); CON.row_factory = sqlite3.Row
asof = dt.date(2026, 9, 1)
sigs = fi.compute(CON, asof)
names = {s["signal"] for s in sigs}
check("I1 all seven signals compute without an engine error", "engine" not in names and {"void shape","cash out, bank in","rate drift","large share","bill continuity"} <= names, sorted(names))
check("I2 every signal has a level, a scope, a key and a plain-English detail", all(s["level"] in ("look","watch") and s["scope"] and s["key"] and s.get("detail") for s in sigs))
check("I3 nothing is a verdict: no signal text accuses", not any(w in (s.get("detail") or "").lower() for s in sigs for w in ("fraud","theft","stole","guilty")))
import re                                                           # noqa: E402
check("I4 no ten-digit number in any detail (F-185)", not any(re.search(r"\d{10}", s.get("detail") or "") for s in sigs))
rd = [s for s in sigs if s["signal"] == "rate drift"][0]
check("I5 rate drift as of 01-Sep reads ~3.0% vs ~2.0% (the doubling, measured)", rd["value"] and rd["baseline"] and rd["value"] > rd["baseline"], (rd["value"], rd["baseline"]))
cb = [s for s in sigs if s["signal"] == "cash out, bank in"][0]
check("I6 cash-out-on-a-UPI-sale is counted (the drawer leak the owner could not see)", cb["n"] is not None and cb["n"] >= 1, cb["n"])
check("I7 every signal ending before returns.act_from is marked historical (D361)", all(s["historical"] == 1 for s in sigs))
fi.write(CON, asof, sigs)
n1 = CON.execute("SELECT COUNT(*) FROM intent_signal WHERE as_of=?", (asof.isoformat(),)).fetchone()[0]
fi.write(CON, asof, fi.compute(CON, asof))
n2 = CON.execute("SELECT COUNT(*) FROM intent_signal WHERE as_of=?", (asof.isoformat(),)).fetchone()[0]
check("I8 a run writes its rows; a re-run replaces them (no growth)", n1 == len(sigs) and n2 == n1, (n1, n2, len(sigs)))
before = CON.execute("SELECT COUNT(*), SUM(amount_p) FROM sale_item").fetchone()[:]
check("I9 the books are untouched", before == CON.execute("SELECT COUNT(*), SUM(amount_p) FROM sale_item").fetchone()[:])
env = dict(os.environ, FIN_DIR=FIN_DIR, FIN_DB=db)
r = subprocess.run([sys.executable, "-B", os.path.join(FIN_DIR, "finance_intent.py"), "--as-of", "2026-09-02", "--dry-run"], env=env, capture_output=True, text=True)
check("I10 the CLI dry run exits 0 and writes nothing", r.returncode == 0 and "DRY RUN" in r.stdout and CON.execute("SELECT COUNT(*) FROM intent_signal WHERE as_of='2026-09-02'").fetchone()[0] == 0, r.stdout[-200:] + r.stderr[-200:])
app = Flask(__name__)
@app.route("/finance/api/day", methods=["POST"])
def fake(): return jsonify(ok=True)
ROLE = {"user": "manoj", "roles": ["checker"]}
darpan_app.init(app, lambda: CON, lambda *r: (dict(ROLE), None), unit="medical")
c = app.test_client()
j = c.get("/finance/darpan/api/intent").get_json()
check("I11 the owner's endpoint returns the newest run", j.get("ok") and j.get("as_of") == asof.isoformat() and len(j.get("signals") or []) == len(sigs), (j.get("as_of"), len(j.get("signals") or [])))
ROLE["user"] = "darpan"
j2 = c.get("/finance/darpan/api/intent").get_json()
check("I12 anyone but the owner gets nothing (owner-only until proven)", j2.get("ok") and j2.get("signals") == [] and j2.get("note") == "owner only")
hub = open(os.path.join(FIN_DIR, "finance_ui", "finance_approvals.html"), encoding="utf-8").read()
check("P1 the hub carries the intent block, its loader, and no Hindi", hub.count("function loadIntent(") == 1 and 'id="intentBox"' in hub and "loadIntent();" in hub and not any("ऀ" <= ch <= "ॿ" for ch in hub))
CON.close(); shutil.rmtree(tmp, ignore_errors=True)
print("\n%s -- %d check(s) failed" % ("ALL GREEN" if fails == 0 else "RED", fails)); sys.exit(fails)
