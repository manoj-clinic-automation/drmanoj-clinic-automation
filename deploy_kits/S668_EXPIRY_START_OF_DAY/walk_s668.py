"""walk_s668.py -- kit S668_EXPIRY_START_OF_DAY (Sanjeevni session S359, 27-Oct-2026). Writes nothing outside --scratch.
  python walk_s668.py --new <root holding finance/expiry_watch.py as built> --lib <root of the unchanged modules> --db <COPY of finance.db>
                      --scratch <dir> [--spine <spine.db> --archive <marg_ingest/archive>]     (--old <live root>: the control)
A: the cut-off day on the estate's capture-hour rule. B: compute() uses it. C (on the box, --spine): the whole list made on copies -- no batch
whose own sales since its Batch Stock's start reach its printed stock is still listed."""
import argparse, os, shutil, sqlite3, sys, warnings, datetime as dt
warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
for x in ("--new", "--old", "--lib", "--db", "--scratch", "--spine", "--archive"):
    ap.add_argument(x)
a = ap.parse_args()
a.db = os.path.abspath(a.db)
ROOT = os.path.abspath(a.old or a.new)
LIB = os.path.abspath(a.lib or a.old or a.new)
a.scratch = os.path.abspath(a.scratch); os.makedirs(a.scratch, exist_ok=True)
FIN = os.path.join(a.scratch, "overlay", "finance"); os.makedirs(FIN)
for e in os.listdir(os.path.join(LIB, "finance")):
    if e not in ("expiry_watch.py", "finance.db"):
        os.symlink(os.path.join(LIB, "finance", e), os.path.join(FIN, e))
shutil.copyfile(os.path.join(ROOT, "finance", "expiry_watch.py"), os.path.join(FIN, "expiry_watch.py"))
sys.path[:0] = [FIN]
os.chdir(a.scratch)
res = []


def check(name, ok, s668=True, note=""):
    res.append((name, bool(ok), s668, str(note)[:300]))


import expiry_watch, stock_figure                                  # noqa: E402
assert os.path.dirname(os.path.abspath(expiry_watch.__file__)) == FIN
cut = getattr(expiry_watch, "_sales_after", lambda R: R.get("as_on"))   # the live file: the printed day, always


def R(as_on, stamp):
    return dict(as_on=as_on, name="BATCH_STOCK_BATCHWISE__%s__%s__9ac300a6.xls" % (as_on, stamp) if stamp else "BATCH_STOCK_BATCHWISE__%s.xls" % as_on)


check("A1 a Batch Stock taken at 05:38 on its own day (26-Oct) stands for the end of 25-Oct: 26-Oct's sales come off", cut(R("2026-10-26", "20261026-053818")) == "2026-10-25",
      note=cut(R("2026-10-26", "20261026-053818")))
check("A2 taken at 22:30 on its own day: its own day (unchanged)", cut(R("2026-10-26", "20261026-223000")) == "2026-10-26", s668=False)
check("A3 taken in shop hours on its own day: its own day (unchanged -- the rule cannot tell)", cut(R("2026-10-26", "20261026-120000")) == "2026-10-26", s668=False)
check("A4 printed for an earlier day (22-Oct, taken 24-Oct): the printed day (unchanged)", cut(R("2026-10-22", "20261024-225914")) == "2026-10-22", s668=False)
check("A5 no stamp in the name: the printed day (unchanged)", cut(R("2026-10-26", None)) == "2026-10-26", s668=False)
src = open(os.path.join(FIN, "expiry_watch.py"), encoding="utf-8").read()
check("B1 the list takes off the sales, the purchases since and the written-off check from that day",
      'ORDER BY l.date", (sales_after,)' in src and "date > ?\", (sales_after,))}" in src and "gone = written_off(sp, sales_after)" in src)

if a.spine:                                                        # ---- C: the live shape (the box)
    SPC = os.path.join(a.scratch, "spine_copy.db")
    s0 = sqlite3.connect("file:%s?mode=ro" % a.spine, uri=True); d0 = sqlite3.connect(SPC); s0.backup(d0); d0.close(); s0.close()
    sp, alias = expiry_watch._spine(SPC)
    con = sqlite3.connect(a.db)
    today = expiry_watch.now_ist().date()
    run_, lines = expiry_watch.compute(con, sp, alias, a.archive, today)
    check("C1 on copies of the live database and spine: the whole list is made from a whole-shop Batch Stock", run_.get("whole") == 1 and run_.get("export_name"),
          s668=False, note=(run_.get("export_name"), run_.get("note", "")[:120]))
    path = [p for p in expiry_watch.batch_exports(a.archive) if os.path.basename(p) == run_.get("export_name")]
    gone, listed = [], {(x.get("k20"), expiry_watch.nbatch(x.get("batch"))) for x in lines if x["section"] in ("near", "expired")}
    if path:
        RR = expiry_watch.read_batch_stock(path[0])
        start = stock_figure.end_day(RR["as_on"], stock_figure.stamp_iso(os.path.basename(path[0]).split("__")[2])) or RR["as_on"]
        printed = {}
        for b in RR["batches"]:
            kk = (alias.get(expiry_watch.K(b["item"]), expiry_watch.K(b["item"])), b["batch"])
            printed[kk] = printed.get(kk, 0) + b["units"]
        sold = {}
        for r in sp.execute("SELECT l.k20, l.batch, l.units, COALESCE(b.credit_note,0) cn FROM sp_sale_line l LEFT JOIN sp_sale_bill b ON b.date=l.date AND b.bill=l.bill WHERE l.date > ?", (start,)):
            kk = (alias.get(r["k20"], r["k20"]), expiry_watch.nbatch(r["batch"]))
            sold[kk] = sold.get(kk, 0) + int(round(r["units"] or 0)) * (-1 if r["cn"] else 1)
        gone = [kk for kk, u in printed.items() if u > 0 and sold.get(kk, 0) >= u]
    bad = [kk for kk in gone if kk in listed]
    check("C2 no batch whose own sales since its Batch Stock's start reach its printed stock is still on the near or expired list (%d such batch(es))" % len(gone),
          path and not bad, note=bad[:6])
    sp.close(); con.close()

for n, ok, s, note in res:
    print("%s  %s%s" % ("green" if ok else "RED  ", n, "" if ok else "   -- " + note))
g = sum(1 for _n, ok, _s, _x in res if ok)
if a.old:
    r6 = sum(1 for _n, ok, s, _x in res if s and not ok); ro = sum(1 for _n, ok, s, _x in res if not s and not ok)
    print("%d S668 check(s) red · %d older red · %d green" % (r6, ro, g))
else:
    print("%d of %d green" % (g, len(res)))
