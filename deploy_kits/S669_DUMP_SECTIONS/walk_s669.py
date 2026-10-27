"""walk_s669.py -- kit S669_DUMP_SECTIONS (Sanjeevni session S359, 28-Oct-2026). Writes nothing outside --scratch.
  python walk_s669.py --new <root holding finance/expiry_watch.py as built> --lib <root of the unchanged modules> --db <COPY of finance.db>
                      --batch <the newest whole-shop Batch Stock .XLS> --scratch <dir> [--after-data] (--old <live root>: the control)
--after-data: the database copy has had the kit's data step (the two cast shoes -> Orthotics): checks C are then expected green."""
import argparse, os, re, shutil, sqlite3, sys, warnings
warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
for x in ("--new", "--old", "--lib", "--db", "--batch", "--scratch"):
    ap.add_argument(x)
ap.add_argument("--after-data", action="store_true")
a = ap.parse_args()
a.db, a.batch = os.path.abspath(a.db), os.path.abspath(a.batch)
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


def check(name, ok, s669=True, note=""):
    res.append((name, bool(ok), s669, str(note)[:300]))


import expiry_watch as ew                                          # noqa: E402
assert os.path.dirname(os.path.abspath(ew.__file__)) == FIN
DB = os.path.join(a.scratch, "walk.db"); shutil.copyfile(a.db, DB)
con = sqlite3.connect(DB)
is_o = ew.ortho_of(con)

# ---- A: the owner's word survives Marg's widths (his own rows, read from the copy) --------------------------------------------------
check("A1 BLING ELASTIC SHOULDER IMMOB S (the Batch Stock's spelling) is an orthotic by his ruling of 18-Sep on ... IMMOB", is_o("BLING ELASTIC SHOULDER IMMOB S", "1*1"))
check("A2 the same name as the closing stock prints it (exact key) is an orthotic (unchanged)", is_o("BLING ELASTIC SHOULDER IMMOB", "1*1"), s669=False)
check("A3 L S BELT XL CONT GRAY UNIS (26 letters) is an orthotic (its table twin ... UNISON; the word BELT carried it before)", is_o("L S BELT XL CONT GRAY UNIS", "1*1"), s669=False)
check("A4 a short name never borrows a twin (too short to be sure): 'HADJOD' alone is not an orthotic", not is_o("HADJOD", "1*1"), s669=False)
# own rows: two table keys sharing a prefix -> no twin (ambiguous)
c2 = sqlite3.connect(DB)
c2.execute("INSERT OR IGNORE INTO stock_item_section (item_key, item, section, source, at) VALUES ('WALK S669 TWIN AAA ORTHO','WALK S669 TWIN AAA ORTHO','Orthotics','walk','2099-01-01')")
c2.execute("INSERT OR IGNORE INTO stock_item_section (item_key, item, section, source, at) VALUES ('WALK S669 TWIN AAA MEDIC','WALK S669 TWIN AAA MEDIC','Medicines','walk','2099-01-01')")
c2.execute("INSERT OR IGNORE INTO stock_item_section (item_key, item, section, source, at) VALUES ('WALK S669 ONLY ONE ROW HERE','WALK S669 ONLY ONE ROW HERE','Orthotics','walk','2099-01-01')")
c2.commit(); c2.close()
is_o2 = ew.ortho_of(sqlite3.connect(DB))
check("A5 two table rows that could both be the twin: neither is taken (the word list decides, as before)", not is_o2("WALK S669 TWIN AAA", "1*1"), note="ambiguous prefix")
check("A6 one table row as the twin of a longer Marg name: taken", is_o2("WALK S669 ONLY ONE ROW HERE XL", "1*1"))
check("A7 a medicine with a twin ruling stays a medicine (the twin's section is used, not 'orthotic' blindly)", not is_o2("WALK S669 TWIN AAA MEDIC XL", "1*1"))

# ---- B: every item on the newest Batch Stock -- its section before and after, only width twins change ------------------------------
R = ew.read_batch_stock(a.batch)
names = sorted({b["item"] for b in R["batches"]})
tab = {ew.nkey(k or it): s for k, it, s in sqlite3.connect(DB).execute("SELECT item_key, item, section FROM stock_item_section WHERE source<>'walk'")}
exact = lambda n: tab.get(ew.nkey(n))                                 # noqa: E731
moved = [n for n in names if exact(n) is None and getattr(ew, "_twin", lambda s, k: None)(tab, ew.nkey(n)) is not None]
check("B1 over the %d names of the Batch Stock, a twin ruling is used only where the exact key misses (%d names), never over an exact row" % (len(names), len(moved)),
      all(exact(n) is None for n in moved), note=moved[:8])
check("B2 ... and every one of those %d twins is a longer-or-shorter spelling of the SAME item (first 12 letters agree)" % len(moved),
      all(any(ew.nkey(n)[:12] == t[:12] for t in tab if t != ew.nkey(n) and (ew.nkey(n).startswith(t) or t.startswith(ew.nkey(n)))) for n in moved), note=moved[:8])

# ---- C: the two cast shoes (the data step) --------------------------------------------------------------------------------------------
rows = {r[0]: (r[1], r[2]) for r in sqlite3.connect(DB).execute("SELECT item, section, source FROM stock_item_section WHERE item IN ('CAST SHOE S TYNOR','PRIME CAST SHOE S')")}
if a.after_data:
    check("C1 after the data step: CAST SHOE S TYNOR and PRIME CAST SHOE S are Orthotics by the owner's word", rows.get("CAST SHOE S TYNOR") == ("Orthotics", "owner") and rows.get("PRIME CAST SHOE S") == ("Orthotics", "owner"), note=rows)
    check("C2 ... and the watch puts them with the orthotics", is_o("CAST SHOE S TYNOR", "1*1") and is_o("PRIME CAST SHOE S", "1*1"))
else:
    check("C0 before the data step: the two cast shoes are still the seed's Consumables (the installer changes them)", rows.get("CAST SHOE S TYNOR") == ("Consumables", "seed") and rows.get("PRIME CAST SHOE S") == ("Consumables", "seed"), s669=False, note=rows)
n_owner = sqlite3.connect(DB).execute("SELECT COUNT(*) FROM stock_item_section WHERE source='owner'").fetchone()[0]
check("C3 the owner's other rulings are untouched (%d owner rows%s)" % (n_owner, ", 7 before the step" if not a.after_data else ", 9 after the step"),
      n_owner == (9 if a.after_data else 7), s669=False, note=n_owner)

for n, ok, s, note in res:
    print("%s  %s%s" % ("green" if ok else "RED  ", n, "" if ok else "   -- " + note))
g = sum(1 for _n, ok, _s, _x in res if ok)
if a.old:
    r6 = sum(1 for _n, ok, s, _x in res if s and not ok); ro = sum(1 for _n, ok, s, _x in res if not s and not ok)
    print("%d S669 check(s) red · %d older red · %d green" % (r6, ro, g))
else:
    print("%d of %d green" % (g, len(res)))
