#!/usr/bin/env python3
"""shape_s880.py <code_dir> <db_copy> [month] -- the digest and the card sheet on a COPY of the live database, counts only.
Last line: SHAPE OK|BAD ... ."""
import io, os, sqlite3, sys
code, dbp = sys.argv[1], sys.argv[2]
sys.path.insert(0, code)
import datetime as dt
import packs as p
m = sys.argv[3] if len(sys.argv) > 3 else (dt.date.today().replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
con = sqlite3.connect(dbp); con.row_factory = sqlite3.Row
kept, dropped, total = p.digest_rows(con, m)
n0 = len(kept)
has = hasattr(p, "_s880_split")
movedl = []
if has:
    kept, dropped, movedl = p._s880_split(con, list(kept), list(dropped))
moved = len(movedl)
bank = sum(1 for r in kept if "statement," in str(r.get("debit")))      # the both-matched rows count here too
notyet = sum(1 for r in kept if "not yet read" in str(r.get("debit")))
ronly = sum(1 for r in kept if str(r.get("debit", "")).startswith("receipt only") or str(r.get("debit", "")).startswith("no card line") or str(r.get("debit", "")).startswith("no bank line"))
noamt = sum(1 for r in kept if "amount on the receipt" in str(r.get("debit")))
b, why = p.build_digest(con, m)
cb, cwhy = p.build_card_sheet(con, m)
rc = ""
if cb:
    from openpyxl import load_workbook
    ws = load_workbook(io.BytesIO(cb))["Every line"]
    rows = [[c.value for c in r] for r in ws.iter_rows()]
    rc = "card_sheet_lines=%d with_receipt=%d cols=%d" % (len(rows) - 1, sum(1 for r in rows[1:] if r[-2]), len(rows[0]))
else:
    rc = "card_sheet=not_built(%s)" % (cwhy or "")[:60]
both = sum(1 for r in kept if "a card line of the same figure too" in str(r.get("debit")))
nodebit = sum(1 for r in kept if not r.get("debit"))
okk = has and n0 > 0 and b is not None and nodebit == 0 and (moved + bank + notyet + ronly + noamt == n0) and (cb is not None or "not every card" in str(cwhy) or "no card statement" in str(cwhy))
print("SHAPE %s month=%s papers=%d moved_to_card_sheet=%d bank_line=%d (both=%d) not_yet_read=%d receipt_only=%d no_amount=%d digest_built=%s %s" % (
    "OK" if okk else "BAD", m, n0, moved, bank, both, notyet, ronly, noamt, b is not None, rc))
