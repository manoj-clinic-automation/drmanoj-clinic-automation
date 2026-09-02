#!/usr/bin/env python3
"""
selftest_rejoin_s220.py -- proves rejoin_returns_s220.py on a COPY of the live db.

  offline:  FIN_DIR=/dir/with/live/modules  FIN_DB=/path/finance.db  python3 selftest_rejoin_s220.py
  the box:  /root/wa/venv/bin/python3 -B /root/finance/selftest_rejoin_s220.py
The live database is never opened for writing. Exit code = failures.
"""
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

FIN_DIR = os.environ.get("FIN_DIR", "/root/finance")
FIN_DB = os.environ.get("FIN_DB", os.path.join(FIN_DIR, "finance.db"))
TOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rejoin_returns_s220.py")
SINCE = "2026-06-18"
fails = 0


def check(name, ok, detail=""):
    global fails
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + str(detail)) if detail and not ok else ""))
    if not ok:
        fails += 1


def run(db, *args):
    env = dict(os.environ, FIN_DIR=FIN_DIR, FIN_DB=db)
    r = subprocess.run([sys.executable, "-B", TOOL] + list(args), env=env, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


tmp = tempfile.mkdtemp(prefix="s220_rejoin_")
db = os.path.join(tmp, "finance.db")
shutil.copyfile(FIN_DB, db)
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
sys.path.insert(0, FIN_DIR)
import finance_returns_audit as fra                                # noqa: E402

def synth():
    return con.execute("SELECT COUNT(*) FROM sale_item s JOIN day_entry d ON d.id=s.day_entry_id "
                       "WHERE s.service LIKE '%return%' AND s.source_ref LIKE 'S186-F104-%' AND d.business_date>=?",
                       (SINCE,)).fetchone()[0]

def orphans():
    return con.execute("SELECT COUNT(DISTINCT bill_no) FROM sale_line_item l WHERE l.is_return=1 AND l.business_date>=? "
                       "AND NOT EXISTS (SELECT 1 FROM sale_item s WHERE s.source_ref=l.bill_no)", (SINCE,)).fetchone()[0]

def money():
    return con.execute("SELECT COUNT(*), SUM(amount_p), SUM(patient_ref_id) FROM sale_item WHERE service LIKE '%return%'").fetchone()[:]

def audit_rows(days):
    n = 0
    for d in days:
        n += len(fra.returns_for_day(con, d, "medical")[0])
    return n

s0, o0, m0 = synth(), orphans(), money()
days = [r[0] for r in con.execute("SELECT DISTINCT d.business_date FROM sale_item s JOIN day_entry d ON d.id=s.day_entry_id "
                                   "WHERE s.source_ref LIKE 'S186-F104-%' AND d.business_date>=?", (SINCE,))]
a0 = audit_rows(days)
check("R0 the defect is present on this database (synthetic rows == orphan credit notes since 18-Jun)", s0 == o0 and s0 > 0, (s0, o0))

rc, out = run(db)
check("R1 dry run exits 0 and changes nothing", rc == 0 and "nothing changed" in out and synth() == s0, out[-300:])
check("R2 dry run pairs every synthetic row uniquely (0 unpaired, 0 ambiguous)",
      ("pairs: %d unique   unpaired: 0   ambiguous: 0" % s0) in out, [l for l in out.splitlines() if l.startswith("pairs")])

rc, out = run(db, "--apply")
check("R3 apply exits 0 and took a backup beside the db", rc == 0 and "backup   " in out and
      any(f.startswith("finance.db.bak_S220_rejoin_") for f in os.listdir(tmp)), out[-300:])
con.close(); con = sqlite3.connect(db); con.row_factory = sqlite3.Row
check("R4 no synthetic return refs remain since 18-Jun", synth() == 0, synth())
check("R5 no orphan credit notes remain since 18-Jun", orphans() == 0, orphans())
m1 = money()
check("R6 the money is untouched: same row count, same rupees, same patients", m1 == m0, (m0, m1))
a1 = audit_rows(days)
check("R7 the audit now counts each return ONCE (rows fell by exactly the pair count)", a0 - a1 == s0, (a0, a1, s0))
import json                                                        # noqa: E402
rekeyed = {json.loads(x[0])["source_ref"] for x in con.execute("SELECT after_json FROM audit_log WHERE action='rekey_return_S220'")}
one = [r for d in days for r in fra.returns_for_day(con, d, "medical")[0] if r["bill"] in rekeyed]
check("R7b the re-keyed credit notes are all visible to the audit", len(one) == s0, (len(one), s0))
check("R8 every re-keyed credit note is valued from its bill row and shows its lines",
      one and all(r["n_lines"] > 0 and "bill row" in (r.get("money_from") or "") for r in one),
      [(r["bill"], r["n_lines"], r.get("money_from", "")[:14]) for r in one if not (r["n_lines"] > 0 and "bill row" in (r.get("money_from") or ""))][:3])
check("R9 identity is untouched: the re-keyed rows still read 'identity needed' (WALK-IN) -- Darpan's sheet, not this tool",
      one and all(r["verdict"] in ("identity needed", "DISCOUNTED RETURN") for r in one),
      sorted({r["verdict"] for r in one}))
rc, out = run(db)
check("R10 a second run finds nothing to do (idempotent)", rc == 0 and "pairs: 0 unique" in out)
check("R11 every re-key is in audit_log", con.execute("SELECT COUNT(*) FROM audit_log WHERE action='rekey_return_S220'").fetchone()[0] == s0)

con.close()
shutil.rmtree(tmp, ignore_errors=True)
print("\n%s -- %d check(s) failed" % ("ALL GREEN" if fails == 0 else "RED", fails))
sys.exit(fails)
