#!/usr/bin/env python3
"""
selftest_namecheck_s220.py -- S220 F-277: proves the four patches, LIVE-SHAPE.

Runs against a COPY of the real finance.db (never the live file), with the
four PATCHED modules on the path. Offline and on the box alike:

  offline:  FIN_DIR=/dir/with/patched/files  FIN_DB=/path/finance.db  python3 selftest_namecheck_s220.py
  the box:  /root/wa/venv/bin/python3 -B /root/finance/selftest_namecheck_s220.py
            (defaults: FIN_DIR=/root/finance, FIN_DB=/root/finance/finance.db -- COPIED to /tmp first)

Every check prints PASS/FAIL; the exit code is the number of failures.
No patient number appears in this file (F-185): names only.
"""
import os
import shutil
import sqlite3
import sys
import tempfile

FIN_DIR = os.environ.get("FIN_DIR", "/root/finance")
FIN_DB = os.environ.get("FIN_DB", os.path.join(FIN_DIR, "finance.db"))
sys.path.insert(0, FIN_DIR)

fails = 0


def check(name, ok, detail=""):
    global fails
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + str(detail)) if detail and not ok else ""))
    if not ok:
        fails += 1


# ---------------------------------------------------------------------------
# T1  the name match, calibrated on the evidence sheet (names only, no numbers)
# ---------------------------------------------------------------------------
import finance_ingest as fi                                       # noqa: E402

check("T1.0 patched ingest exposes name_agrees / resolve_patient_checked",
      hasattr(fi, "name_agrees") and hasattr(fi, "resolve_patient_checked")
      and hasattr(fi, "_note_identity_dispute"))

AGREE = [("SAHANA", "Sahana"), ("ASHOK AGARWAL", "Ashok Kumar Agarwal"),
         ("ARCHNA MITTAL", "Archana Mittal"), ("PARWATI", "Parvati"),
         ("POONAM", "Poonam"), ("BABU ANSARI", "Babu Ansari"), ("KHURSHID", "Khurshid"),
         ("GUDDI DEVI", "Guddi Devi"), ("RIFAQAT ALI", "Rifaqat Ali"), ("SONIYA", "Soniya"),
         ("MANOSHA", "Manosha"), ("MAHIMA", "Mahima"), ("KANTA PRASAD", "Kanta Parsad"),
         ("CHETNA", "Chetna"), ("ABBAS", "Abbas"), ("RAJEEV KUMAR", "Rajeev kumar"),
         ("NEHA KHAN", "Neha Khan"), ("GOVIND SINGH", "Govind Singh"), ("SALONI", "Saloni"),
         ("SWATI SINGH", "Swati Singh"), ("NEERAJ GUPTA", "Neeraj Gupta"),
         ("VIVAH SINGH", "VIVHA Singh"), ("ARCHNA", "Archana"), ("SANTOSH", "Santosh"),
         ("MEETA AGARWAL", "Meeta Agarwal"), ("SHASHI SAHU", "Shashi Sahu"),
         ("CHANDRAWATI", "Chandrwati"), ("PARAMJEET KAUR", "Paramjeet Kour")]
DIFFER = [("PARAMJEET KAUR", "Daljeet Singh"), ("SAMREEN REHMAN", "Saloni Shrivastav"),
          ("SUNITA ANAND", "Sheela Saxena"), ("PREM PAL SINGH", "Trishna"),
          ("SUNIL KUMAR", "Sunil Sharma")]
UNKNOWN = [("SMT", "Anybody"), ("", "Anybody"), ("RAJENDRA KUMAR", None), ("  ", "")]

for a, b in AGREE:
    check("T1 agree   %-16s ~ %s" % (a, b), fi.name_agrees(a, b) == "yes", fi.name_agrees(a, b))
for a, b in DIFFER:
    check("T1 differ  %-16s ~ %s" % (a, b), fi.name_agrees(a, b) == "no", fi.name_agrees(a, b))
for a, b in UNKNOWN:
    check("T1 unknown %-16r ~ %r" % (a, b), fi.name_agrees(a, b) == "unknown", fi.name_agrees(a, b))
check("T1 an ID beside the name does not matter",
      fi.name_agrees("4471 SAHANA", "Sahana") == "yes")

# ---------------------------------------------------------------------------
# T2  the dispute record, on a COPY of the real database
# ---------------------------------------------------------------------------
tmp = tempfile.mkdtemp(prefix="s220_selftest_")
db = os.path.join(tmp, "finance.db")
shutil.copyfile(FIN_DB, db)
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
NOW = "2026-09-02T20:00:00"
TID = "ZZ-S220-TEST"                      # a clinic ID that cannot exist in the master
con.execute("INSERT INTO patient_ref (clinic_id, name, first_seen) VALUES (?,?,?)",
            (TID, "Ramesh Kumar", "2026-09-02"))
before = con.execute("SELECT COUNT(*) FROM sale_item").fetchone()[0]

pid, agree, master = fi.resolve_patient_checked(con, TID, "Suresh Verma")
check("T2.1 checked resolver attaches BY ID (same pid as resolve_patient)",
      pid == fi.resolve_patient(con, TID, "Suresh Verma"))
check("T2.2 ... and reports the disagreement", agree == "no" and master == "Ramesh Kumar", (agree, master))
fi._note_identity_dispute(con, "medical", "2026-09-02", "A9999901", TID, "Suresh Verma", master,
                          pid, agree, "sale", NOW)
d = con.execute("SELECT * FROM identity_dispute WHERE bill_no='A9999901'").fetchall()
check("T2.3 one open dispute row written", len(d) == 1 and d[0]["status"] == "open", len(d))
fi._note_identity_dispute(con, "medical", "2026-09-02", "A9999901", TID, "Suresh Verma", master,
                          pid, agree, "sale", NOW)
check("T2.4 re-ingest of the same bill does NOT duplicate it",
      con.execute("SELECT COUNT(*) FROM identity_dispute WHERE bill_no='A9999901'").fetchone()[0] == 1)
pid2, agree2, _ = fi.resolve_patient_checked(con, TID, "Ramesh Kumar")
check("T2.5 the same ID with the master's name agrees", agree2 == "yes" and pid2 == pid)
fi._note_identity_dispute(con, "medical", "2026-09-02", "A9999901", TID, "Ramesh Kumar", master,
                          pid, agree2, "sale", NOW)
check("T2.6 ... and CLOSES the open dispute on that bill, resolution recorded",
      con.execute("SELECT status, resolved_by FROM identity_dispute WHERE bill_no='A9999901'")
      .fetchone()[:] == ("resolved", "ingest"))
check("T2.7 no ID -> unknown, no dispute, still WALK-IN",
      fi.resolve_patient_checked(con, None, "Anyone")[1] == "unknown"
      and con.execute("SELECT COUNT(*) FROM identity_dispute").fetchone()[0] == 1)
check("T2.8 the money path wrote nothing extra (sale_item count unchanged)",
      con.execute("SELECT COUNT(*) FROM sale_item").fetchone()[0] == before)

# ---------------------------------------------------------------------------
# T3  the verdict, on a REAL August return day, with a dispute injected
# ---------------------------------------------------------------------------
import finance_returns_audit as fra                                # noqa: E402
import finance_returns_escalate as fre                             # noqa: E402

check("T3.0 patched audit exposes _identity_dispute", hasattr(fra, "_identity_dispute"))
# pick a real return bill on a real day (the newest one) -- names never printed
# The sample must be a CLEAN return ("ok"): a return refunded short keeps its
# DISCOUNTED RETURN verdict even when disputed, by S219's own rule (one bill's
# arithmetic needs no patient), and that is checked separately in T3.9.
r = base = None
for cand in con.execute("SELECT s.source_ref bill, d.business_date d, s.patient_ref_id pid, s.unit unit "
                        "FROM sale_item s JOIN day_entry d ON d.id=s.day_entry_id "
                        "WHERE s.service='pharmacy_return' AND s.patient_ref_id<>1 AND s.source_ref IS NOT NULL "
                        "ORDER BY d.business_date DESC LIMIT 40").fetchall():
    rows0 = [x for x in fra.returns_for_day(con, cand["d"], cand["unit"])[0] if x["bill"] == cand["bill"]]
    if rows0 and rows0[0]["verdict"] == "ok":
        r, base = cand, rows0
        break
check("T3.1 a real, clean, named return exists to test on", r is not None)
if r:
    check("T3.2 before the dispute, the audit says ok", base[0]["verdict"] == "ok")
    con.execute("INSERT INTO identity_dispute (unit, business_date, bill_no, clinic_id, bill_name, "
                "master_name, patient_ref_id, kind, status, noted_at) VALUES (?,?,?,?,?,?,?,?,'open',?)",
                (r["unit"], r["d"], r["bill"], "X", "Bill Name", "Master Name", r["pid"], "return", NOW))
    con.commit()
    after = [x for x in fra.returns_for_day(con, r["d"], r["unit"])[0] if x["bill"] == r["bill"]]
    check("T3.3 with an OPEN dispute the verdict is 'identity disputed'",
          after and after[0]["verdict"] == "identity disputed", after and after[0]["verdict"])
    check("T3.4 ... no purchase-matching lines, and the note names both names",
          after and after[0]["lines"] == [] and "Bill Name" in after[0]["note"] and "Master Name" in after[0]["note"])
    check("T3.5 ... THE MONEY IS UNCHANGED (amount identical to before)",
          after and base and after[0]["amount_p"] == base[0]["amount_p"])
    check("T3.6 the escalation spine does NOT treat it as a money finding",
          fre.flagged_rows(after) == [])
    con.execute("UPDATE identity_dispute SET status='resolved' WHERE bill_no=?", (r["bill"],))
    con.commit()
    closed = [x for x in fra.returns_for_day(con, r["d"], r["unit"])[0] if x["bill"] == r["bill"]]
    check("T3.7 a RESOLVED dispute no longer changes the verdict",
          closed and closed[0]["verdict"] == base[0]["verdict"])
    # T3.9  a return refunded SHORT keeps DISCOUNTED RETURN even when disputed
    short = None
    for cand in con.execute("SELECT s.source_ref bill, d.business_date d, s.patient_ref_id pid, s.unit unit "
                            "FROM sale_item s JOIN day_entry d ON d.id=s.day_entry_id "
                            "WHERE s.service='pharmacy_return' AND s.patient_ref_id<>1 AND s.source_ref IS NOT NULL "
                            "ORDER BY d.business_date DESC LIMIT 80").fetchall():
        rows0 = [x for x in fra.returns_for_day(con, cand["d"], cand["unit"])[0] if x["bill"] == cand["bill"]]
        if rows0 and rows0[0]["verdict"] == "DISCOUNTED RETURN":
            short = cand
            break
    if short:
        con.execute("INSERT INTO identity_dispute (unit, business_date, bill_no, clinic_id, bill_name, "
                    "master_name, patient_ref_id, kind, status, noted_at) VALUES (?,?,?,?,?,?,?,?,'open',?)",
                    (short["unit"], short["d"], short["bill"], "X", "B", "M", short["pid"], "return", NOW))
        con.commit()
        v = [x for x in fra.returns_for_day(con, short["d"], short["unit"])[0] if x["bill"] == short["bill"]][0]["verdict"]
        check("T3.9 a short-refunded return stays DISCOUNTED RETURN when disputed (S219 rule)",
              v == "DISCOUNTED RETURN", v)
    else:
        print("skip  T3.9 no short-refunded named return in the last 80 to test on")
con.execute("DROP TABLE identity_dispute")
con.commit()
check("T3.8 without the table at all, the audit is fail-soft (S219 behaviour)",
      r is not None and [x for x in fra.returns_for_day(con, r["d"], r["unit"])[0]
                         if x["bill"] == r["bill"]][0]["verdict"] == base[0]["verdict"])

# ---------------------------------------------------------------------------
# T4  the consumers: darpan count + hub colour carry the new verdict
# ---------------------------------------------------------------------------
dsrc = open(os.path.join(FIN_DIR, "darpan_app.py"), encoding="utf-8").read()
check("T4.1 darpan_app excludes 'identity disputed' from the flagged count",
      '"identity needed", "identity disputed"):' in dsrc)
hub = os.path.join(FIN_DIR, "finance_ui", "finance_approvals.html")
hsrc = open(hub, encoding="utf-8").read() if os.path.exists(hub) else ""
check("T4.2 the hub paints 'identity disputed' AMBER", 'n.verdict==="identity disputed"' in hsrc)
check("T4.3 the escalation module's MONEY_FLAGS is an allow-list without it",
      "identity disputed" not in fre.MONEY_FLAGS and "identity needed" not in fre.MONEY_FLAGS)

con.close()
shutil.rmtree(tmp, ignore_errors=True)
print("\n%s -- %d check(s) failed" % ("ALL GREEN" if fails == 0 else "RED", fails))
sys.exit(fails)
