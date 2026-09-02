#!/usr/bin/env python3
"""selftest_english_s220.py -- S220 item 3: the owner's endpoints answer in English.
  offline: FIN_DIR=... FIN_DB=... python3 selftest_english_s220.py   |  the box: /root/wa/venv/bin/python3 -B /root/finance/selftest_english_s220.py
Runs the real blueprint on a COPY of the db. Exit code = failures."""
import os, re, shutil, sqlite3, sys, tempfile
FIN_DIR = os.environ.get("FIN_DIR", "/root/finance")
FIN_DB = os.environ.get("FIN_DB", os.path.join(FIN_DIR, "finance.db"))
sys.path.insert(0, FIN_DIR)
from flask import Flask, jsonify                                    # noqa: E402
import darpan_app                                                   # noqa: E402
fails = 0
def check(name, ok, detail=""):
    global fails
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + str(detail)) if detail and not ok else ""))
    if not ok: fails += 1
tmp = tempfile.mkdtemp(prefix="s220_en_"); db = os.path.join(tmp, "finance.db"); shutil.copyfile(FIN_DB, db)
CON = sqlite3.connect(db, check_same_thread=False); CON.row_factory = sqlite3.Row
app = Flask(__name__)
@app.route("/finance/api/day", methods=["POST"])
def fake(): return jsonify(ok=True)
darpan_app.init(app, lambda: CON, lambda *r: ({"user": "manoj", "roles": ["checker", "maker"]}, None), unit="medical")
c = app.test_client()
HINDI = re.compile(r"\b(hai|nahin|nahi|bhara|aayi|gaya|lagani|kijiye|karo|dekho|din|par)\b", re.I)
src = open(os.path.join(FIN_DIR, "darpan_app.py"), encoding="utf-8").read()
check("E0 patched darpan_app carries the mark once", src.count("S220 OWNER ENGLISH") == 2)
for s in ("sab aa gaya", "report aayi hai, workbench", "din bhara hai par Marg", "report hai par din nahin", "na din bhara na report"):
    check("E1 old coverage string gone: %r" % s, s not in src)
j = c.get("/finance/darpan/api/coverage?since=2026-08-01").get_json()
check("E2 coverage answers ok", j.get("ok") is True, j)
bad = [r for r in (j.get("rows") or []) if HINDI.search(r.get("hindi") or "")]
check("E3 no coverage row explains itself in Hindi (%d rows checked)" % len(j.get("rows") or []), not bad, [b.get("hindi") for b in bad[:2]])
check("E4 every verdict still has an explanation", all((r.get("hindi") or "").strip() for r in (j.get("rows") or [])))
k = c.get("/finance/darpan/api/corrections").get_json()
check("E5 corrections answers ok", k.get("ok") is True, k)
ins = [r.get("instruction") or "" for r in (k.get("rows") or [])]
check("E6 every correction instruction leads in English and keeps the Hindi for the relay (%d)" % len(ins),
      all(i.startswith("Marg: change bill ") and "kijiye" in i for i in ins))
CON.close(); shutil.rmtree(tmp, ignore_errors=True)
print("\n%s -- %d check(s) failed" % ("ALL GREEN" if fails == 0 else "RED", fails)); sys.exit(fails)
