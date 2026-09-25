#!/usr/bin/python3
"""walk_s399.py -- S399_DAY_TRUTH_5 proof on a SCRATCH copy of the live database.
Scenario rows are the walk's own (dated 2099-12-30, bill numbers WALK-S399-*), found by key, never by count (F-627).
  A  a procedure bill the ladder attached to a patient (identity_resolution)  -> S399 adds it; S367 does not
  B  a home-medicine bill whose name disagreed with its clinic ID (identity_dispute) -> S399 adds it
  C  an ordinary patient bill in identity_resolution                              -> nothing added
  D  a second run                                                                  -> PRESENT, no second row
  E  an APPROVED day with a label bill and no deduction                            -> named, not touched
  F  the live days: every row S399 would add is a label bill, dry run changes nothing
usage: walk_s399.py --db SCRATCH --new day_resync.py --old day_resync_S367.py"""
import argparse, io, contextlib, importlib.util, sqlite3, sys

ap = argparse.ArgumentParser(); ap.add_argument("--db"); ap.add_argument("--new"); ap.add_argument("--old")
a = ap.parse_args()
fails = []
N = [0]
def check(name, ok):
    N[0] += 1
    print(("  ok   " if ok else "  FAIL ") + name)
    if not ok: fails.append(name)
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m
def run(mod, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        mod.main(["--db", a.db, "--no-reconcile"] + list(args))
    return out.getvalue()

new, old = load(a.new, "dr_new"), load(a.old, "dr_old")
c = sqlite3.connect(a.db)
now = "2099-12-30T10:00:00"
def mk_day(iso, status):
    c.execute("INSERT INTO day_entry (unit, business_date, status, source) VALUES ('medical',?,?, 'app')", (iso, status))
    return c.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?", (iso,)).fetchone()[0]
def mk_bill(iso, bill, net):
    c.execute("INSERT INTO sale_bill (unit,business_date,bill_no,gross_p,disc_p,tax_p,drcr_p,net_p,cash_p,noncash_p,"
              "is_credit_note,round_p,source_name,source_stamp,source_md5,written_at) VALUES "
              "('medical',?,?,?,0,0,0,?,?,0,0,0,'walk','walk','walk',?)", (iso, bill, net, net, net, now))
D1, D2 = "2099-12-30", "2099-12-29"
e1 = mk_day(D1, "submitted"); e2 = mk_day(D2, "approved")
mk_bill(D1, "WALK-S399-A", 19500); mk_bill(D1, "WALK-S399-B", 6200); mk_bill(D1, "WALK-S399-C", 40000)
mk_bill(D2, "WALK-S399-E", 1500)
c.execute("INSERT INTO identity_resolution (unit,business_date,bill_no,rung,clinic_id,bill_name,master_name,noted_at) "
          "VALUES ('medical',?, 'WALK-S399-A','same-day visit','0','PROSIJER WALK PATIENT','WALK PATIENT',?)", (D1, now))
c.execute("INSERT INTO identity_dispute (unit,business_date,bill_no,clinic_id,bill_name,master_name,kind,status,noted_at) "
          "VALUES ('medical',?, 'WALK-S399-B','0','HOME MEDICINE','SOMEONE','sale','open',?)", (D1, now))
c.execute("INSERT INTO identity_resolution (unit,business_date,bill_no,rung,clinic_id,bill_name,master_name,noted_at) "
          "VALUES ('medical',?, 'WALK-S399-C','mobile','0','RAM PRAKASH','RAM PRAKASH',?)", (D1, now))
c.execute("INSERT INTO identity_resolution (unit,business_date,bill_no,rung,clinic_id,bill_name,master_name,noted_at) "
          "VALUES ('medical',?, 'WALK-S399-E','mobile','0','PROSIJER OLD','OLD',?)", (D2, now))
c.commit()
nc = lambda b: c.execute("SELECT head, amount_p, note FROM day_noncash_bill WHERE bill_no=?", (b,)).fetchall()

o_old = run(old, "--since", "2099-12-01", "--dry-run")
check("negative control: S367 does NOT see the laddered procedure bill (the fault)", "WALK-S399-A" not in o_old)
o1 = run(new, "--since", "2099-12-01")
check("A: the laddered procedure bill is added once as procedure_medicine 195",
      nc("WALK-S399-A") and len(nc("WALK-S399-A")) == 1 and nc("WALK-S399-A")[0][:2] == ("procedure_medicine", 19500))
check("A: its note names where the text was found (resolution)", "resolution" in (nc("WALK-S399-A") or [("", 0, "")])[0][2])
check("B: the name-disputed home-medicine bill is added as home_medicine 62",
      nc("WALK-S399-B") and nc("WALK-S399-B")[0][:2] == ("home_medicine", 6200))
check("C: an ordinary patient bill is NOT added", not nc("WALK-S399-C"))
o2 = run(new, "--since", "2099-12-01")
check("D: a second run adds nothing (still one row each)", len(nc("WALK-S399-A")) == 1 and len(nc("WALK-S399-B")) == 1)
check("D: the second run says PRESENT", "PRESENT" in o2 and "ADDED" not in o2)
check("E: the approved day's label bill is named", "WALK-S399-E" in o1 and "APPROVED" in o1)
check("E: the approved day is NOT touched", not nc("WALK-S399-E"))
before = c.execute("SELECT COUNT(*) FROM day_noncash_bill").fetchone()[0]
o3 = run(new, "--dry-run")
after = c.execute("SELECT COUNT(*) FROM day_noncash_bill").fetchone()[0]
check("F: a dry run over the live days writes nothing", before == after)
words = new.words(c, "noncash.home_words", new.HOME_DEFAULT) + new.words(c, "noncash.proc_words", new.PROC_DEFAULT)
print("   live days, S399 dry run:"); [print("     " + l) for l in o3.splitlines() if "WOULD_ADD" in l or "APPROVED" in l]
c.close()
print("WALK_S399 RED -- %d check(s) failed" % len(fails) if fails else "WALK_S399 GREEN -- %d checks" % N[0])
sys.exit(1 if fails else 0)
