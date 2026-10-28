"""walk_s673.py -- kit S673_NONCASH_AT_INGEST_R2 (F-1037; S672 refused by F-1038). Runs on COPIES of the database only.
  --new DIR  the kit's files (DIR/finance/day_resync.py, finance_ingest.py) in front of --lib   (or --old: the live files alone)
  --lib ROOT the live root (its finance/ for every other module; its finance_ingest.py is the OLD one for the old = new checks)
  --db COPY  a copy of finance.db (never the live file)
  --export FILE  the real 27-Oct sale export (manojz only). WITHOUT it (the box: it deletes every raw sale export at the door,
             S186 -- F-1038) the ingest checks run on made-up bills in a made-up day, and N11 on a copy of the live 27-Oct itself.
  --scratch DIR   --fix FILE  fix_s672.py (the one-time data step) for N11
Prints one RED/green line per check and, last, '<n> of <n> green' or '<k> S673 check(s) red · <m> older red · <g> green'."""
import argparse, csv, importlib.util, io, os, shutil, sqlite3, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("--new"); ap.add_argument("--old"); ap.add_argument("--lib", required=False)
ap.add_argument("--db", required=True); ap.add_argument("--export", default=None)
ap.add_argument("--scratch", required=True); ap.add_argument("--fix", required=True)
a = ap.parse_args()
lib = a.lib or a.old
code = a.new or a.old
os.makedirs(a.scratch, exist_ok=True)
sys.path[:0] = [os.path.join(code, "finance")] + ([os.path.join(lib, "finance")] if lib != code else [])
OFF = os.path.join(a.scratch, "off_none"); os.makedirs(OFF, exist_ok=True)
os.environ["SANJEEVNI_OFF_DIR"] = OFF
import finance_ingest as FI, day_resync as DR, marg_report as MR       # noqa: E402

REAL = bool(a.export)
DAY, BILL = ("2026-10-27", "A004474") if REAL else ("2030-03-01", "WALK-P1")
res = []          # (name, ok, is_s672)


def check(name, ok, s672=True):
    res.append((name, bool(ok), s672)); print("  %-5s %s" % ("green" if ok else "RED", name))


def copy(tag):
    p = os.path.join(a.scratch, "w_%s.db" % tag)
    shutil.copyfile(a.db, p)
    c = sqlite3.connect(p, timeout=30); c.row_factory = sqlite3.Row
    return c, p


def drop(c, tag):
    try:
        c.close()
    except Exception:      # noqa: BLE001
        pass
    for x in ("", "-journal", "-wal", "-shm"):
        try:
            os.remove(os.path.join(a.scratch, "w_%s.db%s" % (tag, x)))
        except OSError:
            pass


def prep_day(c, status):
    e = c.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?", (DAY,)).fetchone()
    if e is None:
        c.execute("INSERT INTO day_entry (unit, business_date, status, source, entered_by, entered_at) "
                  "VALUES ('medical',?,?, 'app','walk','2026-10-28T08:31:00')", (DAY, status))
    else:
        c.execute("UPDATE day_entry SET status=? WHERE id=?", (status, e["id"]))
    eid = c.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?", (DAY,)).fetchone()[0]
    c.execute("DELETE FROM day_noncash_bill WHERE unit='medical' AND bill_no=? AND bill_date=?", (BILL, DAY))
    c.commit()
    return eid


if REAL:
    rep = MR.read_report(a.export)
    buf = io.StringIO(); MR.write_lines_csv(rep, buf, DAY); LINES = buf.getvalue()
else:                                   # made-up bills of our own (F-998), in the export's own column shape
    LINES = ("bill_date,bill_no,clinic_id,patient_name,phone_last4,description,amount,mode,gross,disc,mobile\n"
             "%s,WALK-P1,,PROSIJER WALKNAME,,,98.00,cash,97.56,0.00,\n"
             "%s,WALK-S1,,WALKNAME TWO,,,300.00,upi,300.00,0.00,\n"
             "%s,WALK-S2,,WALKNAME THREE,,,150.00,cash,150.00,0.00,\n") % (DAY, DAY, DAY)
EXPECT = sum(1 for r in csv.DictReader(io.StringIO(LINES)))
check("P0 the %s: %d bills, %s among them" % ("real 27-Oct export read" if REAL else "made-up day %s" % DAY, EXPECT, BILL),
      EXPECT > 0 and any(r.get("bill_no") == BILL for r in csv.DictReader(io.StringIO(LINES))), s672=False)


def nc(c, eid, bill=None):
    q = "SELECT head, bill_no, amount_p, note FROM day_noncash_bill WHERE day_entry_id=?"
    args = [eid]
    if bill:
        q += " AND bill_no=?"; args.append(bill)
    return [dict(r) for r in c.execute(q, args)]


def ingest_rows(c, eid):
    out = []
    for t, q in (("sale_item", "SELECT source_ref, amount_p, mode, patient_ref_id, home_med FROM sale_item WHERE day_entry_id=? ORDER BY source_ref, amount_p"),
                 ("review", "SELECT guess_name, amount_p, status, reason FROM sale_item_review WHERE day_entry_id=? ORDER BY guess_name, amount_p"),
                 ("resolution", "SELECT bill_no, rung, clinic_id FROM identity_resolution WHERE unit='medical' AND business_date=? ORDER BY bill_no")):
        out.append((t, [tuple(r) for r in c.execute(q, (DAY if t == "resolution" else eid,))]))
    return out


# N1 -- the live shape: the real 27-Oct bills, an unapproved day, the ingest as the push path calls it (commit=False, then commit)
c, _ = copy("n1"); eid = prep_day(c, "submitted")
r = FI.ingest_day(c, "medical", DAY, "marg_export", LINES, run_by="walk", source_ref="push:walk", commit=False); c.commit()
got = nc(c, eid, BILL)
check("N1 the ingest deducts %s as procedure medicine at once (%s)" % (BILL, got and got[0]["amount_p"]),
      r.get("rows_read") == EXPECT and len(got) == 1 and got[0]["head"] == "procedure_medicine" and got[0]["amount_p"] in (9756, 9800)
      and "S672" in (got[0]["note"] or ""))
n1_rows = ingest_rows(c, eid)
n1_audit = c.execute("SELECT COUNT(*) FROM audit_log WHERE table_name='day_entry' AND row_id=? AND action='noncash_sync' "
                     "AND after_json LIKE '%S672 at ingest%'", (eid,)).fetchone()[0]
check("N1b one audit row 'noncash_sync' from the ingest", n1_audit == 1)

# N5 -- day_resync pass 2 after it: PRESENT, no second row
p5 = os.path.join(a.scratch, "w_n1.db"); c.close()
out5 = subprocess.run([sys.executable, "-B", os.path.join(code, "finance", "day_resync.py"), "--db", p5, "--since", DAY, "--no-reconcile"],
                      capture_output=True, text=True, env=dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path[:2])), timeout=300).stdout
c5 = sqlite3.connect(p5); c5.row_factory = sqlite3.Row
check("N5 the half-hour job afterwards finds it already there -- one row, not two",
      len(nc(c5, eid, BILL)) == 1 and ("already: " in out5 or "PRESENT" in out5) and "WOULD_ADD" not in out5)
drop(c5, "n1")

# N2 -- old = new: the ingest's own rows (sale_item, review queue, ladder notes) identical under the live finance_ingest.py
spec = importlib.util.spec_from_file_location("fi_old_s672", os.path.join(lib, "finance", "finance_ingest.py"))
FO = importlib.util.module_from_spec(spec); spec.loader.exec_module(FO)
c2, _ = copy("n2"); eid2 = prep_day(c2, "submitted")
FO.ingest_day(c2, "medical", DAY, "marg_export", LINES, run_by="walk", source_ref="push:walk", commit=False); c2.commit()
check("N2 old = new: sale_item, the review queue and the ladder's notes are the live file's, row for row", ingest_rows(c2, eid2) == n1_rows, s672=False)
drop(c2, "n2")

# N3 -- the caller's rollback takes the deduction with it (S474: one transaction)
c3, _ = copy("n3"); eid3 = prep_day(c3, "submitted")
FI.ingest_day(c3, "medical", DAY, "marg_export", LINES, run_by="walk", commit=False); c3.rollback()
check("N3 a rolled-back ingest leaves no deduction and no audit row",
      nc(c3, eid3, BILL) == [] and c3.execute("SELECT COUNT(*) FROM audit_log WHERE after_json LIKE '%S672 at ingest%'").fetchone()[0] == 0)
drop(c3, "n3")

# N4 -- an approved day is never touched by the ingest
c4, _ = copy("n4"); eid4 = prep_day(c4, "approved"); before4 = len(nc(c4, eid4))
FI.ingest_day(c4, "medical", DAY, "marg_export", LINES, run_by="walk")
check("N4 an approved day: nothing added", len(nc(c4, eid4)) == before4 and nc(c4, eid4, BILL) == [])
drop(c4, "n4")


# N6 -- the Sanjeevni switch OFF: the ingest adds nothing
c6, _ = copy("n6"); eid6 = prep_day(c6, "submitted")
OFF6 = os.path.join(a.scratch, "off_all"); os.makedirs(OFF6, exist_ok=True); open(os.path.join(OFF6, "ALL_OFF"), "w").close()
_keep = DR.OFF_DIR; DR.OFF_DIR = OFF6
try:
    FI.ingest_day(c6, "medical", DAY, "marg_export", LINES, run_by="walk")
finally:
    DR.OFF_DIR = _keep
check("N6 with the Sanjeevni switch OFF the ingest adds nothing", nc(c6, eid6, BILL) == [])
drop(c6, "n6")

# N7 -- fail-soft: the door raising leaves the ingest exactly as the live file makes it, and the transaction usable
c7, _ = copy("n7"); eid7 = prep_day(c7, "submitted")
_real = getattr(DR, "at_ingest", None)
def _boom(*_x, **_y):
    c7.execute("INSERT INTO day_noncash_bill (day_entry_id, unit, bill_date, head, bill_no, amount_p) VALUES (?,?,?,?,?,?)",
               (eid7, "medical", DAY, "home_medicine", "WALK-BOOM", 1))
    raise RuntimeError("walk: the door fails")
DR.at_ingest = _boom
try:
    r7 = FI.ingest_day(c7, "medical", DAY, "marg_export", LINES, run_by="walk", commit=False)
    c7.execute("INSERT INTO audit_log (table_name, row_id, action, after_json, by_whom, at) VALUES ('walk',0,'walk','{}','walk','x')")
    c7.commit(); ok7 = True
except Exception as ex:      # noqa: BLE001
    ok7 = False; print("    ", ex)
finally:
    if _real is not None:
        DR.at_ingest = _real
    else:
        del DR.at_ingest
check("N7 a failing door: the ingest stands, its half-write rolled back, the caller's next write commits",
      ok7 and r7.get("rows_read") == EXPECT and nc(c7, eid7, "WALK-BOOM") == [] and nc(c7, eid7, BILL) == []
      and ingest_rows(c7, eid7) == n1_rows and hasattr(DR, "at_ingest"))
drop(c7, "n7")

# N8 -- the door's own limits
c8, _ = copy("n8")
check("N8 the door looks at nothing for the clinic, before 1-Sep, or a day not filed",
      hasattr(DR, "at_ingest") and DR.at_ingest(c8, "clinic", DAY) is None and DR.at_ingest(c8, "medical", "2026-08-15") is None
      and DR.at_ingest(c8, "medical", "2031-01-01") is None and c8.row_factory is sqlite3.Row)
drop(c8, "n8")

# N9/N10 -- made-up rows of our own (F-998): a procedure bill and a home bill on a made-up unapproved day
c9, _ = copy("n9")
c9.execute("INSERT INTO day_entry (unit, business_date, status, source, entered_by, entered_at) VALUES ('medical','2030-02-01','submitted','app','walk','2030-02-01T09:00:00')")
e9 = c9.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date='2030-02-01'").fetchone()[0]; c9.commit()
L9 = "bill_date,bill_no,clinic_id,patient_name,phone_last4,description,amount,mode,gross,disc,mobile\n" \
     "2030-02-01,WALK-P1,,PROSEJAR WALKNAME,,,195.00,cash,195.00,0.00,\n" \
     "2030-02-01,WALK-H1,,HOME MEDISUN,,,250.00,cash,250.00,0.00,\n" \
     "2030-02-01,WALK-S1,,WALKNAME TWO,,,300.00,cash,300.00,0.00,\n"
FI.ingest_day(c9, "medical", "2030-02-01", "marg_export", L9, run_by="walk")
g9 = sorted((x["bill_no"], x["head"], x["amount_p"]) for x in nc(c9, e9))
check("N9 made-up day: the procedure bill and the home bill deducted at ingest, the ordinary bill not (%s)" % g9,
      g9 == [("WALK-H1", "home_medicine", 25000), ("WALK-P1", "procedure_medicine", 19500)])
FI.ingest_day(c9, "medical", "2030-02-01", "marg_export", L9, run_by="walk")
check("N10 the same export again: still two rows", len(nc(c9, e9)) == 2)
drop(c9, "n9")

# N11 -- the one-time data step: on the box on a copy of the LIVE 27-Oct (approved, A004474 undeducted); with --export on a 27-Oct
#        staged from the real export and approved, as the server holds it
c11, p11 = copy("n11")
if REAL:
    e11 = prep_day(c11, "submitted")
    _had11 = getattr(DR, "at_ingest", None)          # stage the day as the server holds it: ingested WITHOUT the door
    if _had11 is not None:
        DR.at_ingest = lambda *_x, **_y: None
    try:
        FO.ingest_day(c11, "medical", DAY, "marg_export", LINES, run_by="walk")
    finally:
        if _had11 is not None:
            DR.at_ingest = _had11
    c11.execute("UPDATE day_entry SET status='approved' WHERE id=?", (e11,)); c11.commit(); c11.close()
    fx = [sys.executable, "-B", a.fix, "--db", p11, "--lib", os.path.join(code, "finance")]
    o1 = subprocess.run(fx + ["--apply"], capture_output=True, text=True, timeout=300); o2 = subprocess.run(fx + ["--apply"], capture_output=True, text=True, timeout=300)
    c11 = sqlite3.connect(p11); c11.row_factory = sqlite3.Row
    g11 = nc(c11, e11, BILL)
    check("N11 the one-time step adds %s to the approved 27-Oct once; a second run adds nothing" % BILL,
          o1.returncode == 0 and "ADDED" in o1.stdout and len(g11) == 1 and g11[0]["head"] == "procedure_medicine"
          and o2.returncode == 0 and "ALREADY" in o2.stdout)
else:
    c11.close()
    fx = [sys.executable, "-B", a.fix, "--db", p11, "--lib", os.path.join(code, "finance")]
    o1 = subprocess.run(fx + ["--apply"], capture_output=True, text=True, timeout=300); o2 = subprocess.run(fx + ["--apply"], capture_output=True, text=True, timeout=300)
    c11 = sqlite3.connect(p11); c11.row_factory = sqlite3.Row
    g11 = [dict(x) for x in c11.execute("SELECT head FROM day_noncash_bill WHERE unit='medical' AND bill_no='A004474' AND bill_date='2026-10-27'")]
    check("N11 the one-time step on a copy of the live 27-Oct adds A004474 once; a second run adds nothing (%s)" % o1.stdout.strip()[-90:],
          o1.returncode == 0 and "ADDED" in o1.stdout and len(g11) == 1 and g11[0]["head"] == "procedure_medicine"
          and o2.returncode == 0 and "ALREADY" in o2.stdout)
drop(c11, "n11")

# S -- finance_ingest's own selftest, on a throwaway copy: it ends EXACTLY as the live file's does (on today's data the live file's
#      selftest stops at its "unidentified return goes to review" step -- a stale check, older than this kit, named in the close)
def selftest_end(fi_path):
    tmp = os.path.join(a.scratch, "st"); os.makedirs(tmp, exist_ok=True)
    o = subprocess.run([sys.executable, "-B", fi_path, a.db], capture_output=True, text=True, timeout=600, cwd=tmp,
                       env=dict(os.environ, TMPDIR=tmp, PYTHONPATH=os.pathsep.join(sys.path[:2])))
    for f in os.listdir(tmp):
        if f.startswith("finance_ingest_smoke_"):
            os.remove(os.path.join(tmp, f))
    lines = [x for x in (o.stdout + o.stderr).strip().splitlines() if x.strip()]
    return o.returncode, (lines[-1].strip() if lines else ""), sum(1 for x in lines if x.strip().startswith("FAIL:"))
sn, so = selftest_end(os.path.join(code, "finance", "finance_ingest.py")), selftest_end(os.path.join(lib, "finance", "finance_ingest.py"))
check("S finance_ingest's own selftest ends as the live file's (%s)" % sn[1][:70], sn == so)


red_new = sum(1 for _, ok, s in res if not ok and s); red_old = sum(1 for _, ok, s in res if not ok and not s)
green = sum(1 for _, ok, _s in res if ok)
print("%d of %d green" % (green, len(res)) if not red_new and not red_old else
      "%d S673 check(s) red · %d older red · %d green" % (red_new, red_old, green))
