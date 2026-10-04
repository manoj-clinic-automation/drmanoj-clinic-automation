#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""shelf_dry_s479.py -- S479_YES_MONTHLY_READER (session 294, 04-Oct-2026; F-725). The installer's proof on the REAL shelf, and
its report afterwards. IT WRITES NOTHING: the database is opened read-only and copied into memory; every step below happens on
that copy and the copy is thrown away. It prints file ids, the slots' own labels, periods, counts and statuses -- never a file
name, an amount or a number longer than four digits.

  dry     <modules> <finance> <db>         every shelf row the net-banking reader refused ("does not print 'Period: ..'") is opened
                                          from the copy the shelf itself reads (the unlocked one when it opened a locked file):
                                           - not the monthly e-mailed layout, or not on disk  -> named, left exactly as it is
                                           - the monthly layout and the new reader REFUSES it -> RED (the reader is wrong on the
                                             bank's real page; nothing is installed)
                                           - the monthly layout and it proves                 -> the row is given back to the
                                             shelf ON THE MEMORY COPY and the shelf's own pass (packs._process_once) is run there:
                                             the slot it lands on, the period, 'read' / 'duplicate of branch copy', how many
                                             lines are new on the table and how many another file already held.
                                          Last line: DRY OK ids=<id,id,..> | DRY NONE | DRY RED <why>
  report  <modules> <finance> <db> <ids>   the same rows as they stand on the live database now, and the month's cells.
                                          Last line: REPORT OK | REPORT RED <why>
  waiting <modules> <finance> <db>         the ids of rows ON A SLOT that nobody has read yet and that are the monthly layout (given
                                          back by an earlier run that the shelf did not finish). One line: WAITING <id,id,..> | WAITING NONE
<modules> is the folder packs.py, yes_monthly.py, finance_yesbank.py and yes_branch.py are loaded from (the scratch copies before
placing, /root/finance after); all four MUST come from it or the run is RED. A row that is read but DIFFERS from a statement
already held is a RED here: the assistant reads it before anything is placed.
"""
import hashlib
import os
import re
import sqlite3
import sys

REFUSAL = "refused: this PDF does not print%"
LINE_TABLES = ("bank_statement_line", "yesbank_account_statement_line")


def mask(s):
    """No amount and no long number leaves this tool: an amount becomes <amount>, a run of five or more digits keeps its last four."""
    s = re.sub(r"-?\d[\d,]*\.\d{2}\b", "<amount>", str(s))
    return re.sub(r"\d{5,}", lambda m: "x" + m.group(0)[-4:], s)


def memory_copy(dbp):
    src = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True, timeout=60)
    mem = sqlite3.connect(":memory:")
    src.backup(mem)
    src.close()
    mem.row_factory = sqlite3.Row
    return mem


def modules(moddir, fin):
    sys.dont_write_bytecode = True
    for d in (fin, moddir):
        if d in sys.path:
            sys.path.remove(d)
        sys.path.insert(0, d)
    import packs                                          # noqa: PLC0415
    import yes_monthly                                    # noqa: PLC0415
    import finance_yesbank                                # noqa: PLC0415
    import yes_branch                                     # noqa: PLC0415
    for m in (packs, yes_monthly, finance_yesbank, yes_branch):
        if os.path.dirname(os.path.abspath(m.__file__)) != os.path.abspath(moddir):
            raise RuntimeError("%s was loaded from %s, not from %s" % (m.__name__, os.path.dirname(os.path.abspath(m.__file__)), moddir))
    return packs, yes_monthly


def has(con, t):
    return bool(con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone())


def lines_of(con, sha):
    return sum(con.execute("SELECT COUNT(*) FROM %s WHERE sha256=?" % t, (sha,)).fetchone()[0] for t in LINE_TABLES if has(con, t))


def show(con, packs, i, facts):
    """One row, as it stands on con. True when it is read (or the duplicate of a branch copy) on a slot."""
    r = con.execute("SELECT f.slot_id, f.period_from, f.period_to, f.read_status, f.matched_status, s.holder_label FROM stmt_file f "
                    "LEFT JOIN stmt_slot s ON s.id=f.slot_id WHERE f.id=?", (i,)).fetchone()
    if not r:
        print("   file %d: no longer on the shelf" % i)
        return False
    n, cash, sha = facts.get(i, (None, None, None))
    new = lines_of(con, sha) if sha else None
    ok = (bool(r["slot_id"]) and r["read_status"] in ("read", packs.DUP_OF_BRANCH)
          and not str(r["matched_status"] or "").startswith("DIFFERS"))      # a month that differs from the one held is the assistant's to read first
    print("   file %d -> %s · %s..%s%s · %s%s%s" % (
        i, r["holder_label"] or "NO SLOT", r["period_from"], r["period_to"],
        (" · %d rows, %d cash deposit(s)" % (n, cash)) if n is not None else "",
        mask(r["read_status"] or "waiting for the shelf's pass")[:90],
        (" · " + mask(r["matched_status"])[:110]) if r["matched_status"] else "",
        (" · %d line(s) of it on the table" % new) if (new is not None and r["read_status"] == "read") else ""))
    return ok


def facts_of(con, yes_monthly, ids):
    """(rows, cash deposits, sha256) of each file, read again from the copy the shelf reads."""
    out = {}
    for i in ids:
        f = con.execute("SELECT unlocked_path, local_path FROM stmt_file WHERE id=?", (i,)).fetchone()
        p = (f["unlocked_path"] or f["local_path"] or "") if f else ""
        if p and os.path.exists(p):
            with open(p, "rb") as fh:
                blob = fh.read()
            try:
                ps = yes_monthly.parse_statement(blob)
                out[i] = (len(ps["lines"]), sum(x["is_cash_deposit"] for x in ps["lines"]), hashlib.sha256(blob).hexdigest())
            except Exception:                            # noqa: BLE001
                pass
    return out


def dry(moddir, fin, dbp):
    packs, yes_monthly = modules(moddir, fin)
    mem = memory_copy(dbp)
    rows = [dict(r) for r in mem.execute("SELECT * FROM stmt_file WHERE read_status LIKE ? ORDER BY id", (REFUSAL,))]
    ids, bad = [], []
    for f in rows:
        p = f.get("unlocked_path") or f.get("local_path") or ""
        if not p or not os.path.exists(p):
            print("   file %d: its copy is not on disk -- left as it is" % f["id"])
            continue
        with open(p, "rb") as fh:
            blob = fh.read()
        if not yes_monthly.is_monthly_blob(blob):
            print("   file %d: not the monthly e-mailed layout -- left as it is" % f["id"])
            continue
        try:
            yes_monthly.parse_statement(blob)
        except Exception as ex:                          # noqa: BLE001
            print("   file %d: the monthly layout, and the new reader REFUSES it: %s" % (f["id"], mask(ex)[:220]))
            bad.append(f["id"])
            continue
        ids.append(f["id"])
    if bad:
        print("DRY RED the new reader refuses %d real statement(s) of its own layout (file %s)" % (len(bad), ", ".join(str(x) for x in bad)))
        return 1
    if not ids:
        print("DRY NONE")
        return 0
    facts = facts_of(mem, yes_monthly, ids)
    before = {i: lines_of(mem, facts[i][2]) for i in ids}
    mem.execute("UPDATE stmt_file SET read_status=NULL, matched_status=NULL WHERE id IN (%s)" % ",".join("?" * len(ids)), ids)
    packs._process_once(mem)                             # the shelf's own pass, on the memory copy
    red = [i for i in ids if not show(mem, packs, i, facts)]
    held = [i for i in ids if before[i]]
    if held:
        print("DRY RED file %s already had lines on the table before it was read" % ", ".join(str(x) for x in held))
        return 1
    if red:
        print("DRY RED on the memory copy file %s did not come out read and agreeing (see its line above: not read, on no slot, or it DIFFERS "
              "from a statement already held)" % ", ".join(str(x) for x in red))
        return 1
    print("DRY OK ids=%s" % ",".join(str(x) for x in ids))
    return 0


def waiting(moddir, fin, dbp):
    packs, yes_monthly = modules(moddir, fin)
    mem = memory_copy(dbp)
    ids = []
    for f in mem.execute("SELECT id, unlocked_path, local_path FROM stmt_file WHERE read_status IS NULL AND slot_id IS NOT NULL AND folder='bank' ORDER BY id"):
        p = f["unlocked_path"] or f["local_path"] or ""
        if p and os.path.exists(p):
            with open(p, "rb") as fh:
                if yes_monthly.is_monthly_blob(fh.read()):
                    ids.append(f["id"])
    print("WAITING %s" % (",".join(str(x) for x in ids[:20]) or "NONE"))
    return 0


def report(moddir, fin, dbp, ids):
    packs, yes_monthly = modules(moddir, fin)
    mem = memory_copy(dbp)
    facts = facts_of(mem, yes_monthly, ids)
    red = [i for i in ids if not show(mem, packs, i, facts)]
    months = sorted({r[0][:7] for r in mem.execute("SELECT period_from FROM stmt_file WHERE id IN (%s) AND period_from IS NOT NULL"
                                                   % ",".join("?" * len(ids)), ids)})
    for m in months:
        cl = packs.cells(mem, m)
        on = [c for c in cl if c["file"]]
        print("   %s: %d of %d on the shelf%s" % (m, len(on), len(cl), ("" if len(on) == len(cl) else " · still missing: "
                                                 + ", ".join(c["label"] for c in cl if not c["file"]))))
    if red:
        print("REPORT RED file %s is not read and agreeing on the live database" % ", ".join(str(x) for x in red))
        return 1
    print("REPORT OK")
    return 0


def main(argv):
    try:
        if len(argv) == 5 and argv[1] == "dry":
            return dry(argv[2], argv[3], argv[4])
        if len(argv) == 5 and argv[1] == "waiting":
            return waiting(argv[2], argv[3], argv[4])
        if len(argv) == 6 and argv[1] == "report" and re.match(r"^\d+(,\d+)*$", argv[5]):
            return report(argv[2], argv[3], argv[4], [int(x) for x in argv[5].split(",")])
    except Exception as ex:                              # noqa: BLE001
        print("%s RED %s: %s" % ({"report": "REPORT", "waiting": "WAITING"}.get(argv[1] if len(argv) > 1 else "", "DRY"), type(ex).__name__, mask(ex)[:300]))
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
