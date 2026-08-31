#!/usr/bin/env python3
"""
REHEARSAL_match.py -- the LIVE-SHAPE walk for the D355 matcher.

Builds a throwaway finance.db from the REAL patient master and visit ledger,
then asks the matcher the questions the counter actually creates: a full bill, a
partial one, a family mobile, a colliding clinic ID, a misspelling, a wrong name,
and a bill with nothing on it at all.

Writes nothing anywhere except a temp folder. Prints counts and verdicts only --
never a patient name, never a number.
"""
import os
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "S211_PATIENTJOIN"))
import push_patient_join as J                                 # noqa: E402
import finance_patient_sync as S                              # noqa: E402
import finance_patient_match as M                             # noqa: E402

SALT = "rehearsal-salt-not-the-live-one"
ENV = {M.SALT_ENV: SALT}
OK = BAD = 0


def check(name, cond, detail=""):
    global OK, BAD
    if cond: OK += 1
    else: BAD += 1
    print(("  ok   " if cond else "  FAIL ") + name + (("   " + detail) if detail else ""))


def main(argv):
    tracker = argv[argv.index("--tracker") + 1] if "--tracker" in argv else None
    if not tracker or not os.path.isdir(os.path.join(tracker, "data")):
        print("!! give me the tracker folder:  --tracker <path>")
        return 2
    D = os.path.join(tracker, "data")
    tmp = tempfile.mkdtemp(prefix="match_walk_")

    master, mc = J.build_master(SALT, os.path.join(D, "patient_master.csv"))
    visits, _ = J.build_visits(SALT, os.path.join(D, "visit_ledger.csv"))
    J.write_workbook(os.path.join(tmp, S.MASTER_XLSX), J.MASTER_COLS, master)
    J.write_workbook(os.path.join(tmp, S.VISITS_XLSX), J.VISIT_COLS, visits)
    db = os.path.join(tmp, "finance.db")
    con = sqlite3.connect(db); con.executescript(S.SCHEMA); con.commit(); con.close()
    S.run(db, tmp)

    con = sqlite3.connect(db); con.row_factory = sqlite3.Row
    n = con.execute("SELECT COUNT(*) c FROM patient_ref").fetchone()["c"]
    print("\nreal patients loaded: %d\n" % n)

    # index the source rows so we can build realistic bill text (never printed)
    by_cid = {r[0]: r for r in master if r[0]}
    fp_groups = {}
    for r in master:
        if r[3]:
            fp_groups.setdefault(r[3], []).append(r)
    shared = [g for g in fp_groups.values() if len({x[0] for x in g}) > 1]
    solo = [g[0] for g in fp_groups.values() if len(g) == 1 and g[0][2]]

    # we need the real mobile back to build the bill text; take it from source
    import csv as _csv
    mob_by_cid = {}
    with open(os.path.join(D, "patient_master.csv"), encoding="utf-8-sig",
              errors="replace") as f:
        for r in _csv.DictReader(f):
            cid = (r.get("Clinic_Specific_Id") or "").strip()
            m = J.normalise_mobile(r.get("Mobile_Clean") or r.get("Mobile_Raw") or "")
            if cid and m: mob_by_cid[cid] = m

    def V(text, date=None):
        return M.match_bill(con, text, date, ENV)["verdict"]

    # --- 1. a complete bill, the way the counter is meant to write it
    hit = 0; tried = 0
    for row in solo[:400]:
        cid, _, name = row[0], row[1], row[2]
        mob = mob_by_cid.get(cid)
        if not mob or not name: continue
        tried += 1
        if V("%s %s %s" % (mob, name, cid)) == "matched_clinic_id": hit += 1
    check("a COMPLETE bill matches on the clinic ID", tried and hit == tried,
          "%d/%d" % (hit, tried))

    # --- 2. mobile + name, no clinic id  -> partial
    hit = tried = 0
    for row in solo[:400]:
        cid, name = row[0], row[2]
        mob = mob_by_cid.get(cid)
        if not mob or not name: continue
        tried += 1
        if V("%s %s" % (mob, name)) == "matched_partial": hit += 1
    check("mobile + name, no clinic ID, resolves as PARTIAL", tried and hit == tried,
          "%d/%d" % (hit, tried))

    # --- 3. clinic id alone -> still a clean match (the name comes from the master)
    hit = tried = 0
    for row in solo[:400]:
        tried += 1
        if V(row[0]) == "matched_clinic_id": hit += 1
    check("a clinic ID ALONE is a clean match, never parked", tried and hit == tried,
          "%d/%d" % (hit, tried))

    # --- 4. a family mobile with no name -> ambiguous, never a pick
    hit = tried = 0
    for g in shared[:200]:
        mob = mob_by_cid.get(g[0][0])
        if not mob: continue
        tried += 1
        if V(mob) == "ambiguous": hit += 1
    check("a FAMILY mobile with no name is AMBIGUOUS, never a pick",
          tried and hit == tried, "%d/%d" % (hit, tried))

    # --- 5. a family mobile WITH the right name -> separated to one
    hit = tried = 0
    for g in shared[:200]:
        mob = mob_by_cid.get(g[0][0]); name = g[0][2]
        if not mob or not name: continue
        tried += 1
        if V("%s %s" % (mob, name)) in ("matched_partial", "matched_clinic_id"): hit += 1
    # Not a fitted threshold. The SAFETY property is what matters: when the name
    # cannot separate relatives, the answer must be AMBIGUOUS -- never a pick.
    # The separation rate is reported as a measurement, not asserted.
    wrong = 0
    for g in shared[:200]:
        mob = mob_by_cid.get(g[0][0]); name = g[0][2]
        if not mob or not name: continue
        r = M.match_bill(con, "%s %s" % (mob, name), None, ENV)
        if r["verdict"].startswith("matched") and r["patient"] \
           and r["patient"]["clinic_id"] != g[0][0]:
            wrong += 1
    check("a family mobile NEVER resolves to the wrong relative", wrong == 0,
          "%d wrong out of %d" % (wrong, tried))
    print("       (measurement, not a gate: the name separates %d of %d family "
          "mobiles; the rest stay ambiguous for a human to pick)" % (hit, tried))

    # --- 6. a colliding clinic id -> ambiguous
    col = [r["clinic_id"] for r in con.execute(
        "SELECT clinic_id FROM patient_id_collision").fetchall()]
    hit = sum(1 for c in col if V(c) == "ambiguous")
    check("a COLLIDING clinic ID is AMBIGUOUS, not a clean match",
          col and hit == len(col), "%d/%d" % (hit, len(col)))

    # --- 7. a misspelling still matches when the ID is right
    hit = tried = 0
    for row in solo[:300]:
        cid, name = row[0], row[2]
        if not name or len(name) < 6: continue
        wrong = name[:-1]                      # one letter dropped
        tried += 1
        if V("%s %s" % (cid, wrong)) == "matched_clinic_id": hit += 1
    check("a MISSPELLED name still matches when the clinic ID is right",
          tried and hit >= tried * 0.95, "%d/%d" % (hit, tried))

    # --- 8. a clearly WRONG name against a right ID -> ambiguous, not a match
    names = [r[2] for r in solo if r[2]]
    hit = tried = 0
    for i, row in enumerate(solo[:300]):
        cid = row[0]
        other = names[(i + 5000) % len(names)]
        if M.names_agree(other, row[2]): continue
        tried += 1
        if V("%s %s" % (cid, other)) == "ambiguous": hit += 1
    check("a WRONG name against a right ID is AMBIGUOUS, never a silent match",
          tried and hit == tried, "%d/%d" % (hit, tried))

    # --- 9. nothing usable -> unmatched, the counter gap
    for junk in ("PROSIJER", "WR", "BPJ", "", "   ", "CASH SALE"):
        if V(junk) != "unmatched":
            check("a bill with nothing usable is the counter gap", False, repr(junk))
            break
    else:
        check("a bill with nothing usable is the COUNTER GAP", True, "6 shapes")

    # --- 10. no salt -> mobile matching REFUSED, never silently skipped
    r = M.match_bill(con, "9999999999 SOMEBODY", None, {})
    check("with NO SALT the mobile rung refuses rather than silently skipping",
          any("REFUSED" in str(s.get("detail")) for s in r["steps"]))

    con.close()
    print("\nREHEARSAL: %d/%d %s" % (OK, OK + BAD, "ALL PASS" if BAD == 0 else "-- FAILED"))
    return 0 if BAD == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
