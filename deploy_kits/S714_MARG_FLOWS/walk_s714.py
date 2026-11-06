#!/usr/bin/env python3
"""walk_s714.py -- S714 on a MADE-UP root: the real finance_app (its own gate, every module it mounts) on a made-up finance.db, no data.
    python3 -B walk_s714.py <finance code dir to test>
Signed-in requests use the app's own offline switch (FINANCE_ALLOW_HEADER_AUTH, a temporary database); anonymous requests carry nothing.
CONTROL: run it on the code before S714 (finance_app 00cc4935, reports_tile 0598072c, no marg_flows.py) -- the S714 checks go red."""
import os
import re
import sqlite3
import sys
import tempfile

CODE = os.path.abspath(sys.argv[1])
tmp = tempfile.mkdtemp(prefix="s714walk_")
os.environ.update(FINANCE_DB=os.path.join(tmp, "finance.db"), FINANCE_SSO_DIR=os.path.join(tmp, "nosso"), FINANCE_ALLOW_HEADER_AUTH="1",
                  FINANCE_SCAN_DIR=os.path.join(tmp, "scans"))
sys.path.insert(0, CODE)
sys.path.insert(0, os.path.join(os.path.dirname(CODE), "shared"))
ok = bad = 0


def check(name, cond):
    global ok, bad
    print(("  ok   " if cond else "  RED  ") + name)
    ok += bool(cond)
    bad += (not cond)


import finance_app as F                                      # noqa: E402

cl = F.app.test_client()
con = sqlite3.connect(os.environ["FINANCE_DB"])
con.executescript(open(os.path.join(CODE, "finance_schema.sql")).read())     # the app's own schema (unit_role and the rest)
con.execute("CREATE TABLE IF NOT EXISTS mi_file (md5 TEXT, drive_id TEXT, drive_name TEXT, drive_folder TEXT, drive_mtime TEXT, size INTEGER, stamp TEXT, "
            "type TEXT, variant TEXT, date_from TEXT, date_to TEXT, verdict TEXT, reason TEXT, server_name TEXT, kept INTEGER, lines INTEGER, pc_type TEXT, "
            "pc_verdict TEXT, agree INTEGER, received_at TEXT, source TEXT)")                     # the live box's columns (S388 read)
con.execute("INSERT INTO mi_file (md5, type, verdict, reason, server_name, received_at, source) VALUES ('a','BATCH_STOCK','VERIFIED','','x','2026-11-04T10:33:00','push')")
con.execute("INSERT INTO mi_file (md5, type, verdict, reason, server_name, received_at, source) VALUES ('b','STOCK_VALUATION','REFUSED','not whole stores','y',"
            "'2026-11-04T10:14:00','push')")
con.commit()
ANON = {}
SHIVANI = {"X-Clinic-User": "shivani", "X-Clinic-Role": "viewer"}
OWNER = {"X-Clinic-User": "manoj", "X-Clinic-Role": "checker"}


def get(path, h=None):
    r = cl.get(path, headers=h or ANON)
    return r


print("S714 walk on %s" % CODE)
r = get("/finance/flows")
h = r.get_data(as_text=True)
check("1.1 the index opens WITHOUT a login (200)", r.status_code == 200 and "Marg report kaise banayein" in h)
check("1.2 ... it lists all ten flows", all(("/finance/flows/%s" % f) in h for f in ("valuation", "batch", "salt", "items", "purchase-bill", "purchase-item",
                                                                                      "order-sheet", "category", "sale", "stock")))
check("1.3 ... kept out of search engines (header and page)", r.headers.get("X-Robots-Tag") == "noindex, nofollow" and "noindex" in h)
r = get("/finance/flows/batch")
h = r.get_data(as_text=True)
check("2.1 one flow (Batch Stock) opens WITHOUT a login, in Roman Hindi, with its steps and pictures", r.status_code == 200 and "Batch Stock" in h
      and "Alt + P" in h and h.count("/finance/flows/pic/") >= 8 and "Narangi ghera" in h)
check("2.2 ... 'WhatsApp par bhejiye' carries this page's own address only", "WhatsApp par bhejiye" in h
      and "https://wa.me/?text=" in h and "followup.dr-manoj.in%2Ffinance%2Fflows%2Fbatch" in h)
r = get("/finance/flows/sale")
h = r.get_data(as_text=True)
check("2.3 the morning sale report's flow (the in-app guide's own steps) opens without a login", r.status_code == 200 and "DAILY SALES" in h
      and "/finance/flows/pic/menu_sales.jpg" in h)
check("2.4 no figure, no name, no database word on a public page", not re.search(r"\b\d{10}\b", h) and "mi_file" not in h and "Signed in" not in h)
r = get("/finance/flows/pic/b1.jpg")
check("3.1 a flow's picture opens without a login (a JPEG)", r.status_code == 200 and r.mimetype == "image/jpeg" and r.data[:2] == b"\xff\xd8")
check("3.2 a picture no flow shows (the guide's stock result) is refused", get("/finance/flows/pic/stock_view.jpg").status_code == 404)
check("3.3 an unknown flow goes back to the index", get("/finance/flows/nope").status_code == 302)
check("4.1 everything else still needs a login: the in-app list, Aaj ki reports, an address that only begins alike",
      all(get(p).status_code == 302 for p in ("/finance/reports/flows", "/finance/reports/aaj", "/finance/flowsx")))
check("4.2 a POST to the flows is not let through", cl.post("/finance/flows").status_code in (302, 401, 403, 405))
r = get("/finance/reports/aaj", SHIVANI)
h = r.get_data(as_text=True)
check("5.1 Shivani's Aaj ki reports carries 'Marg reports: har report ke steps'", r.status_code == 200 and "Marg reports: har report ke steps" in h
      and "/finance/reports/flows" in h)
r = get("/finance/reports/flows", SHIVANI)
h = r.get_data(as_text=True)
check("5.2 her in-app list: every flow, its page, its WhatsApp share, in Roman Hindi", r.status_code == 200 and h.count("WhatsApp par bhejiye") == 10
      and "Pichhli report" in h)
check("5.3 ... with the server's word: Batch Stock received 04-11 10:33, Stock Valuation refused", "Pichhli report aa gayi 04-11 10:33" in h
      and "Pichhli report manzoor nahi hui 04-11 10:14" in h)
r = get("/finance/reports/flows", OWNER)
h = r.get_data(as_text=True)
check("5.4 the owner's list in English", r.status_code == 200 and "Last report received 04-11 10:33" in h and "Last report refused" in h)
print("WALK S714: %d ok, %d red" % (ok, bad))
