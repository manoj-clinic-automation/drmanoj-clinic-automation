#!/usr/bin/env python3
"""walk_s433.py -- S433 on the box, BEFORE anything is placed: the new packs.py + yes_branch.py on a COPY of the live finance.db, reading the
live inbox's own statement files (read only). Usage: walk_s433.py <kit dir> <scratch dir> <db copy> <finance dir>. Last line 'WALK OK ...'.

It proves, on the real data: every Yes Bank branch statement in the inbox reads and proves itself; the data step reclassifies the
period-less branch files; after one identification pass the August Yes Bank rows are on the shelf; Sanjeevni's month already held in the
shared tables is checked, not written again; ...0460 is off the shelf; Amir's August pack is ready; a second pass changes nothing."""
import glob
import os
import shutil
import sys

KIT, W, DB, FIN = sys.argv[1:5]
for f in ("packs.py", "yes_branch.py"):
    shutil.copy(os.path.join(KIT, f), W)
for f in ("finance_yesbank.py", "finance_icici.py"):
    shutil.copy(os.path.join(FIN, f), W)
INBOX = os.path.join(FIN, "statements", "inbox")
os.environ.update(FINANCE_DB=DB, STMT_INBOX=INBOX, STMT_VENV_PYTHON="/nonexistent")   # the unlock step is never run from the walk
sys.path.insert(0, W)
import packs        # noqa: E402
import yes_branch   # noqa: E402

bad = []
def check(name, cond, info=""):
    print(("  PASS " if cond else "  FAIL ") + name + ("" if cond else "  -- %s" % (info,)))
    if not cond:
        bad.append(name)

# 1 · every branch statement in the inbox proves itself
nb = 0
for p in sorted(glob.glob(os.path.join(INBOX, "*.pdf"))):
    blob = open(p, "rb").read()
    txt = yes_branch.pdf_text(blob) if blob.lstrip()[:5] == b"%PDF-" else ""
    if not yes_branch.is_branch(txt):
        continue
    nb += 1
    try:
        r = yes_branch.parse_text(txt)
        print("  branch statement %s: ...%s %s..%s, %d lines, proved" % (os.path.basename(p), r["account_ref"], r["period_from"], r["period_to"], len(r["lines"])))
    except yes_branch.StatementRejected as ex:
        check("branch statement %s proves itself" % os.path.basename(p), False, ex)
check("the inbox holds branch statements (%d)" % nb, nb >= 5, nb)

con = packs._con()
packs.ensure(con)
before = con.execute("SELECT COUNT(*) FROM bank_statement_line").fetchone()[0]
beforep = con.execute("SELECT COUNT(*) FROM bank_statement_period").fetchone()[0]
# 2 · the installer's data step, on the copy
for k, v in (("packs.off_shelf_tails", "0460"), ("packs.retired_slots", "yes_cur_clinic"), ("packs.hide_locked", "1")):
    con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, packs.SETTINGS[k][1]))
n = con.execute("UPDATE stmt_file SET read_status=NULL, note=NULL WHERE folder='bank' AND COALESCE(locked,0)=0 AND period_to IS NULL "
                "AND LOWER(COALESCE(local_path,'')) LIKE '%.pdf'").rowcount
con.commit()
print("  data step: %d period-less statement file(s) given a fresh look" % n)
r1 = packs.process_inbox(con)
print("  identification pass: %s" % r1)
cl = {c["slot"]: c for c in packs.cells(con, "2026-08")}
check("the retired slot is gone from the pack", "yes_cur_clinic" not in cl)
for k in ("yes_cur_nk", "yes_cur_sanj", "yes_sav_manoj", "yes_sav_bhawna", "yes_sav_huf"):
    c = cl.get(k) or {}
    f = c.get("file") or {}
    check("%s: August on the shelf (%s)" % (k, c.get("state")), c.get("state") in ("read", "matched") and f.get("period_from") == "2026-08-01"
          and f.get("period_to") == "2026-08-31", (c.get("state"), f.get("read_status"), f.get("matched_status")))
ms = ((cl.get("yes_cur_sanj") or {}).get("file") or {}).get("matched_status") or ""
check("Sanjeevni's August checked against the statement held, not written twice", "agrees with the statement held" in ms or "ingested" in ms, ms)
check("the shared tables did not grow", con.execute("SELECT COUNT(*) FROM bank_statement_line").fetchone()[0] == before or "ingested" in ms)
check("the shared periods did not grow", con.execute("SELECT COUNT(*) FROM bank_statement_period").fetchone()[0] == beforep or "ingested" in ms)
off = con.execute("SELECT COUNT(*) FROM stmt_file WHERE tail='0460' AND slot_id IS NOT NULL").fetchone()[0]
check("...0460 is on no slot", off == 0, off)
check("...0460 is not asked about", all(u["tail"] != "0460" for u in packs.unplaced(con)))
check("Amir's August pack is ready", packs.amir_pack(con, "2026-08")["ready"])
n1 = con.execute("SELECT COUNT(*) FROM yesbank_account_statement_line").fetchone()[0]
r2 = packs.process_inbox(con)
check("a second pass changes nothing", r2["read"] == 0 and r2["placed"] == 0 and con.execute("SELECT COUNT(*) FROM yesbank_account_statement_line").fetchone()[0] == n1, r2)
rows, _ = packs.pack_rows(con, "2026-08", light=True)
yes = [r for r in rows if r["key"].startswith("stmt:yes_")]
print("  August pack, Yes Bank rows: %s" % ", ".join("%s %s" % (r["key"][5:], r["status"]) for r in yes))
con.close()
print("WALK OK -- %d branch statements proved; August's Yes Bank rows %d/%d ready; Amir's pack ready" % (nb, sum(1 for r in yes if r["status"] == "ready"), len(yes))
      if not bad else "WALK RED -- %d check(s) failed: %s" % (len(bad), "; ".join(bad)))
sys.exit(1 if bad else 0)
