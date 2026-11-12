#!/usr/bin/env python3
"""proof_s803.py FILES_DIR SHARED_DIR FINANCE_DIR DB_COPY [ASSETS_DB]
The kit's marg_billwatch.py (FILES_DIR) run on a COPY of finance.db -- the live shape, read only in effect (the copy is thrown away):
the compare on the real line tables, the paper side against the real scans (assets.db, opened READ ONLY -- the box's own unless one is
named), the history fill, and the page made whole. Prints counts and bill numbers only (no item line, no patient's name: the tables it
reads hold none). Last line: 'PROOF S803: counted N (...) · settled n · no paper n · for the record n · part lists n · paper side read
· fill N · page N bytes'."""
import os
import sqlite3
import sys

FILES, SHARED, FIN, DBC = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != HERE]
sys.path[:0] = [FILES, FIN, SHARED]
import purchase_app as PA  # noqa: E402

if len(sys.argv) > 5:
    PA._assets_db = sys.argv[5]
    try:
        import section_count as SCNT  # noqa: E402
        SCNT.ASSETS_DB = sys.argv[5]
    except Exception:                                          # noqa: BLE001
        pass
import marg_billwatch as BW  # noqa: E402

con = sqlite3.connect(DBC, timeout=30)
con.row_factory = sqlite3.Row
B = BW.build(con, paper=True)
fs = B["findings"]
for f in fs:
    print("   %-10s %-7s %-24s %-14s %-8s %10s  %s" % (f["date"], f["side"], " ".join(f["sup"].split())[:24], f["no"][:14], f["kind"], BW.rs(f["rupee_p"], sign=True),
                                                     (f["paper"] or {}).get("state", "")))
n, tot = BW.refresh(con, fill=True)
page = BW.page_html(con)
kinds = {}
for f in fs:
    kinds[f["kind"]] = kinds.get(f["kind"], 0) + 1
ok_page = all(x in page for x in ("Marg watch", "Before this page", "For the record")) and page.count('data-f="') >= len(fs)
print("PROOF S803: counted %d (%s) · settled %d · no paper %d · for the record %d · part lists %d · paper side %s · fill %d · page %s"
      % (len(fs), ", ".join("%s %d" % kv for kv in sorted(kinds.items())) or "none", sum(1 for f in fs if f["status"] == "settled"),
         sum(1 for f in fs if (f.get("paper") or {}).get("state") == "no_paper"), len(B["record"]), len(B["parts"]),
         "read" if B["paper_ok"] else "NOT READ", n, ("%d bytes" % len(page.encode("utf-8"))) if ok_page else "NOT MADE"))
con.close()
