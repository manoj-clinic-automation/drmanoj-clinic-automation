#!/usr/bin/env python3
"""
REHEARSAL_patientjoin.py -- the LIVE-SHAPE walk for S211_PATIENTJOIN.

Runs the WHOLE loop against the real follow-up tracker data on the clinic PC:
build the workbooks exactly as the PC would, then fold them into a throwaway
finance.db carrying the real patient_ref schema, exactly as the VPS would.

It writes NOTHING into the tracker folder and NOTHING into any live database.
Everything lands in a temporary directory that is reported at the end.

Run it from inside this kit folder:
    python REHEARSAL_patientjoin.py  --tracker <path to the followup_tracker folder>
"""
import csv
import os
import re
import sqlite3
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import push_patient_join as J                                 # noqa: E402
import finance_patient_sync as S                              # noqa: E402

SALT = "rehearsal-salt-not-the-live-one"
OK = BAD = 0


def check(name, cond, detail=""):
    global OK, BAD
    if cond:
        OK += 1
    else:
        BAD += 1
    print(("  ok   " if cond else "  FAIL ") + name + (("   " + detail) if detail else ""))


def main(argv):
    tracker = None
    if "--tracker" in argv:
        tracker = argv[argv.index("--tracker") + 1]
    for guess in (tracker, os.path.join(HERE, "..", "..", "followup_tracker")):
        if guess and os.path.isdir(os.path.join(guess, "data")):
            tracker = guess
            break
    if not tracker:
        print("!! give me the tracker folder:  --tracker <path>")
        return 2
    D = os.path.join(tracker, "data")
    tmp = tempfile.mkdtemp(prefix="pjoin_walk_")
    print("tracker: %s\nscratch: %s\n" % (tracker, tmp))

    # ---- 1. the PC half, on the real files -------------------------------
    master, mc = J.build_master(SALT, os.path.join(D, "patient_master.csv"))
    visits, vc = J.build_visits(SALT, os.path.join(D, "visit_ledger.csv"))
    print("PC HALF   patients %s\n          visits   %s\n" % (mc, vc))
    check("the real master produced rows", mc["written"] > 1000, "%d" % mc["written"])
    check("the real visit ledger produced rows", vc["written"] > 100, "%d" % vc["written"])

    mp = J.write_workbook(os.path.join(tmp, S.MASTER_XLSX), J.MASTER_COLS, master)
    vp = J.write_workbook(os.path.join(tmp, S.VISITS_XLSX), J.VISIT_COLS, visits)

    # ---- 2. THE PRIVACY ASSERTION ----------------------------------------
    # Not "no ten-digit run" -- a 32-character hex fingerprint throws those up by
    # chance, so that check would be red forever and would teach everyone to
    # ignore it. The real question is whether any run IS one of the real numbers.
    real = set()
    with open(os.path.join(D, "patient_master.csv"), encoding="utf-8-sig",
              errors="replace") as f:
        for r in csv.DictReader(f):
            m = J.normalise_mobile(r.get("Mobile_Clean") or r.get("Mobile_Raw") or "")
            if m:
                real.add(m)
    rx = re.compile(r"[6-9]\d{9}")
    leaked = 0
    for p in (mp, vp):
        with zipfile.ZipFile(p) as z:
            for n in z.namelist():
                found = set(rx.findall(z.read(n).decode("utf-8", "replace")))
                leaked += len(found & real)
    check("NO REAL MOBILE NUMBER travels to the VPS", leaked == 0,
          "checked against all %d real numbers" % len(real))

    # ---- 3. the VPS half, on a throwaway db with the real schema ---------
    db = os.path.join(tmp, "finance.db")
    con = sqlite3.connect(db)
    con.executescript(S.SCHEMA)
    con.commit()
    con.close()
    rc = S.run(db, tmp)
    check("the VPS sync runs clean", rc == 0)

    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    n_pat = con.execute("SELECT COUNT(*) c FROM patient_ref").fetchone()["c"]
    n_vis = con.execute("SELECT COUNT(*) c FROM patient_visit").fetchone()["c"]
    n_col = con.execute("SELECT COUNT(*) c FROM patient_id_collision").fetchone()["c"]
    check("every usable patient is ACCOUNTED FOR -- landed, or recorded as a collision",
          n_pat + n_col == mc["written"],
          "%d landed + %d colliding = %d" % (n_pat, n_col, mc["written"]))
    check("clinic-ID collisions are RECORDED, never dropped in silence", n_col > 0,
          "%d clinic IDs name more than one patient" % n_col)
    check("every visit landed", n_vis == vc["written"], "%d" % n_vis)

    # ---- 4. the ambiguity must SURVIVE the round trip ---------------------
    # In the source, this many mobiles belong to more than one patient. If the
    # fingerprint lost that, the system would confidently name the wrong family
    # member -- which is exactly F-34, and exactly what the AMBIGUOUS verdict is
    # for. So the count has to come through unchanged.
    src = {}
    with open(os.path.join(D, "patient_master.csv"), encoding="utf-8-sig",
              errors="replace") as f:
        for r in csv.DictReader(f):
            cid = (r.get("Clinic_Specific_Id") or "").strip()
            m = J.normalise_mobile(r.get("Mobile_Clean") or r.get("Mobile_Raw") or "")
            if cid and m:
                src.setdefault(m, set()).add(cid)
    src_shared = sum(1 for v in src.values() if len(v) > 1)
    db_shared = con.execute(
        "SELECT COUNT(*) c FROM (SELECT mobile_fp FROM patient_ref "
        "WHERE mobile_fp<>'' GROUP BY mobile_fp HAVING COUNT(DISTINCT clinic_id)>1)"
    ).fetchone()["c"]
    check("shared-mobile ambiguity survives the fingerprint",
          src_shared == db_shared, "source %d = database %d" % (src_shared, db_shared))

    biggest = con.execute(
        "SELECT COUNT(DISTINCT clinic_id) n FROM patient_ref WHERE mobile_fp<>'' "
        "GROUP BY mobile_fp ORDER BY n DESC LIMIT 1").fetchone()["n"]
    check("the largest family group is preserved, not collapsed", biggest > 1,
          "%d patients on one number" % biggest)

    short = con.execute("SELECT COUNT(*) c FROM patient_ref "
                        "WHERE LENGTH(clinic_id)=1").fetchone()["c"]
    check("single-digit clinic IDs survive (the old regex could never match them)",
          short > 0, "%d of them" % short)

    con.close()

    # ---- 5. idempotency on the real volume -------------------------------
    rc2 = S.run(db, tmp)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    check("a second run changes nothing",
          rc2 == 0
          and con.execute("SELECT COUNT(*) c FROM patient_ref").fetchone()["c"] == n_pat
          and con.execute("SELECT COUNT(*) c FROM patient_visit").fetchone()["c"] == n_vis)
    con.close()

    print("\nREHEARSAL: %d/%d %s" % (OK, OK + BAD, "ALL PASS" if BAD == 0 else "-- FAILED"))
    print("scratch (delete when you like): %s" % tmp)
    return 0 if BAD == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
