#!/usr/bin/env python3
"""shelf_s734.py -- kit S734 (session 394, the parent). READ-ONLY. Need not be run by the owner; the installer runs it.

    python shelf_s734.py <packs.py under test> <live packs.py> <stmt_shelf.py> <a COPY of finance.db>

Every paper on the statement shelf whose text can be read is identified by the live file and by the new one, and placed
by each (packs.place reads only): the bank, kind, tail, period, SBI type, holder and the slot it lands in must be the same for
every paper. Prints COUNTS and shelf row numbers only -- never a name, an account, an amount or any text of a paper.
Last line SHELF OK | SHELF RED."""
import importlib.util
import os
import shutil
import sqlite3
import sys
import tempfile

src, ref, shelf, dbcopy = (os.path.abspath(a) for a in sys.argv[1:5])
T = tempfile.mkdtemp(prefix="s734s_")
os.environ.update(FINANCE_DB=os.path.join(T, "unused.db"), STMT_INBOX=os.path.join(T, "inbox"),
                  PACKS_DIR=os.path.join(T, "packs"), ASSETS_UPLOADS=os.path.join(T, "up"), PACKS_ENV=os.path.join(T, "none.env"))


def load(path, name):
    d = os.path.join(T, name)
    os.makedirs(d)
    shutil.copy(path, os.path.join(d, "packs.py"))
    shutil.copy(shelf, os.path.join(d, "stmt_shelf.py"))
    sys.path.insert(0, d)
    if os.path.dirname(shelf) not in sys.path:              # the app's own readers (yes_branch, yes_monthly), as in production
        sys.path.append(os.path.dirname(shelf))
    s = importlib.util.spec_from_file_location(name, os.path.join(d, "packs.py"))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    sys.path.remove(d)
    return m


N = load(src, "packs_new")
O = load(ref, "packs_old")
KEYS = ("bank", "kind", "tail", "period_from", "period_to", "sbi_type", "holder")
con = sqlite3.connect("file:%s?mode=ro" % dbcopy, uri=True)
con.row_factory = sqlite3.Row
files = [dict(r) for r in con.execute("SELECT * FROM stmt_file ORDER BY id")]
read = same = shorter = 0
moved, ident_diff = [], []
for f in files:
    lp = f.get("unlocked_path") or f.get("local_path") or ""
    text, _locked = O._file_text(lp)
    if not text:
        continue
    read += 1
    a, b = O.identify_text(text), N.identify_text(text)
    for m, x in ((O, a), (N, b)):
        card = m.card_read(text) if (f.get("folder") in ("cards", "decrypted") or x.get("kind") == "card") else None
        if card and card["statement_date"]:
            x.update(kind="card", tail=",".join(card["tails"]), period_from=card["period_from"], period_to=card["period_to"])
    sa, _ha = O.place(con, a)
    sb, _hb = N.place(con, b)
    ida = (sa or {}).get("id") if isinstance(sa, dict) else (sa["id"] if sa else None)
    idb = (sb or {}).get("id") if isinstance(sb, dict) else (sb["id"] if sb else None)
    if any(a.get(k) != b.get(k) for k in KEYS):
        ident_diff.append((f["id"], [k for k in KEYS if a.get(k) != b.get(k)]))
    if ida != idb:
        moved.append(f["id"])
    if ida == idb and not any(a.get(k) != b.get(k) for k in KEYS):
        same += 1
    if len(N._header(text)) < len(O._header(text)):
        shorter += 1
con.close()
shutil.rmtree(T, ignore_errors=True)
print("  shelf rows %d . readable %d . identical (bank, kind, tail, period, holder, slot) %d . heads now shorter %d" % (len(files), read, same, shorter))
for i, ks in ident_diff:
    print("  row %s: %s differ" % (i, ",".join(ks)))
for i in moved:
    print("  row %s: lands in another slot" % i)
print("SHELF OK" if (read and not moved and not ident_diff) else "SHELF RED")
sys.exit(0 if (read and not moved and not ident_diff) else 1)
