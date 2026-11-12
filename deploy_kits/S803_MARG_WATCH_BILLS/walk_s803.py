#!/usr/bin/env python3
"""walk_s803.py FILES_DIR SHARED_DIR FINANCE_DIR SCHEMA [--control]
A walk on MADE-UP rows (no live data): marg_billwatch.py, sanjeevni_approvals.py and owner_notice.py from FILES_DIR (the kit's built files,
or the live ones for the control), everything else from FINANCE_DIR. SCHEMA = a finance.db opened READ ONLY (its tables' layout only, never
a row). The exports, bills and sale files are made-up rows in a scratch database; the scans sit in a made-up assets.db; the page and its
doors are driven through a Flask test client with a stand-in sign-in. Each of the five noise rules is proved twice: with the rule the noise
is silent, with the rule switched off the same rows make a finding (so the fixture really holds the noise and the rule is what stops it).
Last line: 'WALK S803 GREEN' or, with --control on the live files, 'CONTROL S803 RED as it must be'."""
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import time

FILES, SHARED, FIN, SCHEMA = sys.argv[1:5]
CONTROL = "--control" in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != HERE]   # the kit folder carries marg_billwatch.py: never imported from there
TMP = tempfile.mkdtemp(prefix="w803_")
RUN = os.path.join(TMP, "run")
os.makedirs(RUN)
for f in ("marg_billwatch.py", "sanjeevni_approvals.py", "owner_notice.py"):
    if os.path.exists(os.path.join(FILES, f)):
        shutil.copyfile(os.path.join(FILES, f), os.path.join(RUN, f))
HUB = os.path.join(FILES, "finance_approvals.html")           # the Sanjeevni Hub page as the kit builds it (the live one, for the control)
HUB_TXT = open(HUB, encoding="utf-8").read() if os.path.exists(HUB) else ""
sys.path[:0] = [RUN, FIN, SHARED]
os.environ["OWNER_NOTICE_STUB"] = os.path.join(TMP, "said.jsonl")
os.environ["OWNER_NOTICE_LOCK"] = os.path.join(TMP, "tick.lock")
os.environ["FINANCE_OFF_DIR"] = os.path.join(TMP, "_off")
RES = []


def check(name, ok):
    RES.append((name, bool(ok)))
    print(("GREEN " if ok else "RED   ") + name)


def finish():
    red = [n for n, ok in RES if not ok]
    shutil.rmtree(TMP, ignore_errors=True)
    if CONTROL:
        print("CONTROL S803 RED as it must be" if red else "CONTROL S803 NOT RED -- the control did not go red: the walk proves nothing")
    else:
        print("WALK S803 GREEN" if not red else "WALK S803 RED %d of %d" % (len(red), len(RES)))
    sys.exit(0)


DB = os.path.join(TMP, "f.db")
s = sqlite3.connect("file:%s?mode=ro" % SCHEMA, uri=True, timeout=30)
ddl = [r[0] for r in s.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'billwatch_%' "
                               "ORDER BY CASE type WHEN 'table' THEN 0 ELSE 1 END, name")]
s.close()
c0 = sqlite3.connect(DB)
for q in ddl:
    try:
        c0.execute(q)
    except sqlite3.Error:
        pass
c0.commit()

# ------------------------------------------------------------------ the made-up purchase side
IW = "ITEMWISE"
BW_MD5 = "b" * 32


def L(item, qty, free, rate, net, val=None):
    return (item, qty, free, rate, net, net if val is None else val)


def export(md5, f, t, stamp, bills):
    """bills: [(supplier, bill no, date, [L(...)])]"""
    c0.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p, superseded_by) "
               "VALUES (?,?,?,?,?,?,?,?,?,?)", (md5, IW, md5 + ".XLS", f, t, stamp, f + "T09:00:00", sum(len(b[3]) for b in bills), 0, None))
    for sup, no, d, lines in bills:
        for it, q, fr, rate, net, val in lines:
            c0.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, qty, free, rate_p, amount_p, net_amount_p, "
                       "direction, source_md5, line_type) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (sup, no, d, d[:7], it, "1*10", q, fr, int(round(rate * 100)), int(round(val * 100)), int(round(net * 100)), "PURCHASE", md5, IW))


def bill(sup, no, d, amount):
    c0.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p, bw_md5, bw_amount_p) VALUES (?,?,?,?,?,?,?,?)",
               (sup, sup, no, d, d[:7], int(round(amount * 100)), BW_MD5, int(round(amount * 100))))
    return c0.execute("SELECT last_insert_rowid()").fetchone()[0]


c0.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p, superseded_by) "
           "VALUES (?,?,?,?,?,?,?,?,?,?)", (BW_MD5, "BILLWISE", "bw.XLS", "2026-10-01", "2026-10-31", "20261110-090500", "2026-11-10T09:05:00", 0, 0, None))
XSS = "<SCRIPT>ALERT(1)</SCRIPT> PHARMA"
FILL = [("FILLER CO", "F%d" % i, "2026-10-%02d" % (14 + i), [L("FILLER %d" % i, 1, 0, 10, 10)]) for i in range(1, 5)]
A1 = ("ALPHA PHARMA", "A1", "2026-10-05", [L("ITEM ONE", 10, 0, 100, 1000)])
A2a = ("ALPHA PHARMA", "a 2", "2026-10-05", [L("ITEM TWO", 10, 0, 100, 1000)])
A2b = ("ALPHA PHARMA", "A2", "2026-10-05", [L("ITEM TWO", 10, 0, 100, 1000)])
B3a = ("BETA TRADERS", "B3", "2026-10-06", [L("COUGH SYRUP", 10, 2, 100, 1000)])
B3b = ("BETA TRADERS", "B3", "2026-10-06", [L("COUGH SYRUP", 8, 2, 100, 800)])
B4a = ("BETA TRADERS", "B4", "2026-10-07", [L("PAISA TAB", 10, 0, 100, 1000.00)])
B4b = ("BETA TRADERS", "B4", "2026-10-07", [L("PAISA TAB", 10, 0, 100, 1000.40)])
G5a = ("GAMMA DRUGS", "G5", "2026-10-08", [L("OLD NAME GEL", 5, 0, 50, 250)])
G5b = ("GAMMA DRUGS", "G5", "2026-10-08", [L("NEW NAME GEL", 5, 0, 50, 250)])
G6a = ("GAMMA DRUGS", "G6", "2026-10-09", [L("THIO TAB", 10, 2, 200, 2000)])
G6b = ("GAMMA DRUGS", "G6", "2026-10-09", [L("THIO", 10, 2, 200, 2000)])
D7 = ("DELTA AGENCY", "D7", "2026-10-03", [L("LATE BILL TAB", 4, 0, 25, 100)])
D8 = ("DELTA AGENCY", "D8", "2026-10-19", [L("KEYED AFTER TAB", 4, 0, 25, 100)])
E9 = ("EPSILON MEDICOS", "E9", "2026-10-10", [L("GONE BILL TAB", 6, 0, 50, 300)])
E10a = ("EPSILON MEDICOS", "E10", "2026-10-11", [L("VALUE TAB", 10, 0, 68, 680, 680)])
E10b = ("EPSILON MEDICOS", "E10", "2026-10-11", [L("VALUE TAB", 10, 0, 68, 680, 770)])
Z11a = ("ZETA PHARMA", "Z11", "2026-10-12", [L("PRICEY INJ", 10, 0, 100, 1000)])
Z11b = ("ZETA PHARMA", "Z11", "2026-10-12", [L("PRICEY INJ", 10, 0, 130, 1300)])
Z12a = ("ZETA PHARMA", "Z12", "2026-10-13", [L("DATED TAB", 2, 0, 100, 200)])
Z12b = ("ZETA PHARMA", "Z12", "2026-10-14", [L("DATED TAB", 2, 0, 100, 200)])
H13a = ("ETA SURGICALS", "H13", "2026-10-14", [L("FOUR RUPEE TAB", 10, 0, 100.0, 1000)])
H13b = ("ETA SURGICALS", "H13", "2026-10-14", [L("FOUR RUPEE TAB", 10, 0, 100.4, 1004)])
H14a = ("ETA SURGICALS", "H14", "2026-10-14", [L("ONE RUPEE OFF TAB", 10, 0, 100.0, 1000)])
H14b = ("ETA SURGICALS", "H14", "2026-10-14", [L("ONE RUPEE OFF TAB", 10, 0, 100.4, 1004)])
X15a = (XSS, "X15", "2026-10-15", [L("<B>BOLD</B> 'X'", 1, 0, 500, 500)])
X15b = (XSS, "X15", "2026-10-15", [L("<B>BOLD</B> 'X'", 2, 0, 500, 1000)])
E1 = [A1, A2a, B3a, B4a, G5a, G6a, E9, E10a, Z11a, Z12a, H13a, H14a, X15a] + FILL
E2 = [A1, A2b, B3a, B4a, G5a, G6a, D7, D8, E9, E10a, Z11a, Z12a, H13a, H14a, X15a] + FILL
E3 = [A1, A2b, B3b, B4b, G5b, G6b, D7, D8, E10b, Z11b, Z12b, H13b, H14b, X15b] + FILL
export("y1" + "0" * 30, "2025-10-01", "2025-10-31", "20251105-090000", [("ALPHA PHARMA", "A1", "2025-10-05", [L("LAST YEARS ITEM", 3, 0, 10, 30)])])   # the same number, last financial year
NOV = [("NOV HOUSE", "N%d" % i, "2026-11-%02d" % i, [L("NOV ITEM %d" % i, 1, 0, 10, 10)]) for i in range(1, 7)]
export("n1" + "0" * 30, "2026-11-01", "2026-11-10", "20261111-100000", NOV[:1])            # a filtered FIRST print of a new period: 1 of 6
export("n2" + "0" * 30, "2026-11-01", "2026-11-10", "20261114-100000", NOV)
DEC = [("DEC HOUSE", "P%d" % i, "2026-12-01", [L("DEC ITEM %d" % i, 1, 0, 10, 10)]) for i in range(1, 8)]
export("d1" + "0" * 30, "2026-12-01", "2026-12-10", "20261204-100000", DEC[:4])            # an honest early list: 4 of the 7 bills dated 1-Dec
export("d2" + "0" * 30, "2026-12-01", "2026-12-10", "20261208-100000", DEC)                # ... and 3 genuinely late ones
export("e1" + "0" * 30, "2026-10-01", "2026-10-20", "20261021-090000", E1)
export("e2" + "0" * 30, "2026-10-01", "2026-10-31", "20261105-090000", E2)
export("ep" + "0" * 30, "2026-10-01", "2026-10-31", "20261106-090000", [A1, B3a])          # a part print: 2 of the month's bills
export("e3" + "0" * 30, "2026-10-01", "2026-10-31", "20261110-090000", E3)
ID = {}
for sup, no, d, amt in (("ALPHA PHARMA", "A1", "2026-10-05", 1000), ("ALPHA PHARMA", "A2", "2026-10-05", 1000), ("BETA TRADERS", "B3", "2026-10-06", 800),
                        ("BETA TRADERS", "B4", "2026-10-07", 1000), ("GAMMA DRUGS", "G5", "2026-10-08", 250), ("GAMMA DRUGS", "G6", "2026-10-09", 2000),
                        ("DELTA AGENCY", "D7", "2026-10-03", 100), ("DELTA AGENCY", "D8", "2026-10-19", 100), ("EPSILON MEDICOS", "E10", "2026-10-11", 680),
                        ("ZETA PHARMA", "Z11", "2026-10-12", 1300), ("ZETA PHARMA", "Z12", "2026-10-14", 200), ("ETA SURGICALS", "H13", "2026-10-14", 1004),
                        ("ETA SURGICALS", "H14", "2026-10-14", 1004), (XSS, "X15", "2026-10-15", 1000)):
    ID[no] = bill(sup, no, d, amt)
c0.execute("INSERT INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES ('2026-11-10','NEW NAME GEL',5,'1*10',10,'x','walk')")
c0.execute("INSERT INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES ('2026-11-10','THIO TAB',12,'1*10',10,'x','walk')")
c0.execute("INSERT INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES ('2026-11-10','THIO',120,'1*10',10,'x','walk')")

# ------------------------------------------------------------------ the made-up scans (assets.db) and their pairs
ADB = os.path.join(TMP, "assets.db")
a = sqlite3.connect(ADB)
a.execute("CREATE TABLE bills (id INTEGER PRIMARY KEY, kind TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount REAL, notes TEXT, source_stored TEXT, "
          "source_orig TEXT, created_by TEXT, created_at TEXT, stamp_no TEXT, status TEXT, submitted_by TEXT, submitted_at TEXT, approved_by TEXT, approved_at TEXT, "
          "reject_reason TEXT, vendor_phone TEXT, vendor_email TEXT, ocr_status TEXT, lane TEXT, fp TEXT, fpc TEXT, dup_of INTEGER, dup_flag TEXT, dup_cand TEXT, "
          "dup_why TEXT, late_for TEXT, bill_month TEXT, doc_kind TEXT, challan_state TEXT, challan_of INTEGER, pe_who TEXT, rescan_of INTEGER)")
a.execute("CREATE TABLE bill_items (id INTEGER PRIMARY KEY, bill_id INTEGER, item_name TEXT NOT NULL, pack_size TEXT, quantity REAL, rate REAL, amount REAL, make TEXT, "
          "model TEXT, serial_no TEXT, batch TEXT, expiry TEXT, hsn TEXT, asset_id INTEGER)")
a.execute("CREATE TABLE claude_reading (bill_id INTEGER PRIMARY KEY, at TEXT NOT NULL, model TEXT, ok INTEGER NOT NULL DEFAULT 0, doc_kind TEXT, data TEXT, error TEXT)")


def scan(i, vendor, no, d, total, items):
    a.execute("INSERT INTO bills (id, kind, vendor, bill_no, bill_date, total_amount, status, stamp_no, submitted_at, created_at, lane, bill_month, source_stored) "
              "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (i, "Pharmacy", vendor, no, d, total, "captured", "B-%04d" % i, d + " 10:00:00", d + " 10:00:00", "pharmacy", d[:7], "x.pdf"))
    for it in items:
        a.execute("INSERT INTO bill_items (bill_id, item_name, pack_size, quantity, rate, amount) VALUES (?,?,?,?,?,?)", (i,) + tuple(it))
    c0.execute("INSERT INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)", (ID[no], i, "EXACT", "walk", "2026-11-10T10:00:00"))


scan(1, "BETA TRADERS", "B3", "2026-10-06", 800.00, [("COUGH SYRUP", "1*10", 10, 80.0, 800.0)])              # agrees with the bill as it is NOW
scan(2, "GAMMA DRUGS", "G6", "2026-10-09", 2000.00, [("THIO", "1*10", 12, 166.67, 2000.0)])                  # the total cannot tell THIO TAB from THIO
scan(3, "ZETA PHARMA", "Z11", "2026-10-12", 1000.00, [("PRICEY INJ", "1*10", 10, 100.0, 1000.0)])            # the paper says the OLD amount: Marg differs
scan(4, "ZETA PHARMA", "Z12", "2026-10-14", 200.00, [("DATED TAB", "1*10", 2, 100.0, 200.0)])               # the paper carries the NEW date
scan(5, "ETA SURGICALS", "H13", "2026-10-14", 1004.00, [("FOUR RUPEE TAB", "1*10", 10, 100.4, 1004.0)])      # a Rs 4 change, the paper agrees to the rupee
scan(6, "ETA SURGICALS", "H14", "2026-10-14", 1003.00, [("ONE RUPEE OFF TAB", "1*10", 10, 100.3, 1003.0)])   # ... and one that is a rupee off the paper
a.commit()
a.close()

# ------------------------------------------------------------------ the made-up sale side
def sfile(md5, day, stamp, bills):
    c0.execute("INSERT INTO mi_file (md5, stamp, type, variant, date_from, date_to, verdict, received_at) VALUES (?,?,?,?,?,?,?,?)",
               (md5, stamp, "SALE_BILLWISE", "DETAIL", day, day, "VERIFIED", day + "T09:00:00"))
    for no, lines in bills:
        for i, (it, pack, q, rate) in enumerate(lines):
            c0.execute("INSERT INTO mi_sale_line (md5, bill_date, bill_no, is_return, seq, item_name, pack, qty_raw, amount_p) VALUES (?,?,?,?,?,?,?,?,?)",
                       (md5, day, no, 0, i + 1, it, pack, q, int(round(rate * 100))))


S100 = ("S100", [("TAB A", "1*10", "1:0", 50)])
S101 = ("S101", [("TAB B", "1*10", "2:0", 100), ("GEL C", "1", "1.0", 300)])
S102a = ("S102", [("TAB D", "1*10", "1:0", 40)])
S102b = ("S102", [("TAB D", "1*10", "1:0", 45)])                # the same item and quantity, the money changed: not watched (D917)
S103 = ("S103", [("TAB E", "1*10", "0:5", 20)])                # 5 loose of a pack of 10 at Rs 20 a pack: Rs 10 (no sale_bill row for it)
S104a = ("S104", [("TAB F", "1*10", "5:0", 10)])
S104b = ("S104", [("TAB F", "1*10", "1:0", 10)])               # cut from 5 packs to 1: Rs 50 -> Rs 10
sfile("f1" + "0" * 30, "2026-10-20", "20261021-080000", [S100, S101, S102a, S104a])
sfile("f2" + "0" * 30, "2026-10-20", "20261022-080000", [S100, S102b, S103, S104b])
sfile("g1" + "0" * 30, "2026-10-21", "20261021-210000", [("S200", [("TAB A", "1*10", "1:0", 50)])])      # the day's own report, before the day ended
sfile("g2" + "0" * 30, "2026-10-21", "20261022-081000", [("S200", [("TAB A", "1*10", "1:0", 50)]), ("S201", [("TAB B", "1*10", "1:0", 100)])])
c0.execute("INSERT INTO sale_bill (unit, business_date, bill_no, gross_p, disc_p, tax_p, drcr_p, net_p, cash_p, noncash_p, is_credit_note, round_p, source_name, "
           "source_stamp, source_md5, written_at) VALUES ('medical','2026-10-20','S101',50000,0,0,0,50000,50000,0,0,0,'f1','20261021-080000',?, 'x')", ("f1" + "0" * 30,))
c0.commit()
c0.close()

# ------------------------------------------------------------------ the app
from flask import Flask, g, jsonify  # noqa: E402

app = Flask(__name__)
ROLE = {"user": "manoj", "roles": ["checker"]}


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB, timeout=30)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def _close(_e):
    c = g.pop("db", None)
    if c is not None:
        c.close()


def require(*roles, unit="medical"):
    if not set(ROLE["roles"]) & set(roles):
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    return dict(ROLE), None


import purchase_app as PA  # noqa: E402
import section_count as SCNT  # noqa: E402
import sanjeevni_approvals as SA  # noqa: E402

SCNT.ASSETS_DB = ADB
PA.init(app, db, require, unit="medical", marg_token="walk-token", assets_db=ADB)
SA.init(app, db, require, "medical")
cl = app.test_client()
PAGE = "/finance/sanjeevni/marg-watch"

try:
    import marg_billwatch as BW
except Exception as e:                                         # noqa: BLE001 -- the control: the live box has no Marg watch
    BW = None
    check("marg_billwatch.py is there and imports (%s)" % e.__class__.__name__, False)
try:
    import owner_notice as ON
except Exception as e:                                         # noqa: BLE001
    ON = None
    check("owner_notice.py imports (%s)" % e.__class__.__name__, False)
r = cl.get(PAGE)
check("the page is mounted: GET %s answers 200 for the doctor (%d)" % (PAGE, r.status_code), r.status_code == 200)
check("owner_notice carries the bills part", ON is not None and hasattr(ON, "_part_bills"))
_live_hub = os.path.join(FIN, "finance_ui", "finance_approvals.html")
_lh = open(_live_hub, encoding="utf-8").read() if os.path.exists(_live_hub) else ""
_hub_line = '<a href="/finance/sanjeevni/marg-watch">Marg watch — bills changed after their day</a>'
check("the Sanjeevni Hub's 'Go to' has the Marg watch link, once, right under the Purchase bills link -- and nothing else in the page changed",
      HUB_TXT.count(_hub_line) == 1 and 'scanned · differences</a>\n        ' + _hub_line in HUB_TXT
      and (not _lh or _hub_line in _lh or HUB_TXT.replace("        " + _hub_line + "\n", "", 1) == _lh))
if BW is None or r.status_code != 200:
    finish()


def con():
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    return c


def snap():
    """Every table that existed before the Marg watch, hashed -- its own two tables and its three settings apart."""
    c = con()
    h = hashlib.md5()
    for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'billwatch_%' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall():
        q = "SELECT * FROM %s" % t + (" WHERE key NOT LIKE 'billchange.%'" if t == "setting" else "") + " ORDER BY 1"
        h.update(t.encode())
        for row in c.execute(q):
            h.update(repr(tuple(row)).encode("utf-8"))
    c.close()
    return h.hexdigest()


def engine(**kw):
    c = con()
    try:
        ex = [e for e in BW.purchase_exports(c) if e["stamp"] <= kw.get("upto", "9")]
        return BW.compare(ex, "purchase", kw.get("names", BW.stock_names(c)), part_rule=kw.get("part_rule", True))
    finally:
        c.close()


def got(F, no, kind=None, record=None):
    return [f for f in F if BW.billno_norm(f["no"]) == BW.billno_norm(no) and (kind is None or f["kind"] == kind) and (record is None or f["record"] == record)]


# ------------------------------------------------------------------ 1 · the five noise rules, each with its own control
F, P = engine()
check("rule 1: the part print (2 of the month's bills) is set aside whole -- 1 part list, and E9 is the only bill gone", any(p["stamp"] == "20261106-090000" for p in P) and len([f for f in F if f["kind"] == "gone"]) == 1)
F1, P1 = engine(upto="20261106-090000")
F0, P0 = engine(upto="20261106-090000", part_rule=False)
check("rule 1, the day the part print is the newest report: with the rule no bill is 'gone' (%d); its control -- with the rule off the same print makes %d bills 'gone' (10 or more)"
      % (len([f for f in F1 if f["kind"] == "gone"]), len([f for f in F0 if f["kind"] == "gone"])),
      len(P1) == 1 and not [f for f in F1 if f["kind"] == "gone"] and len([f for f in F0 if f["kind"] == "gone"]) >= 10)
F0, P0 = engine(part_rule=False)
check("a bill gone in one report and back unchanged in the next is no finding (the second net under rule 1)", len([f for f in F0 if f["kind"] == "gone"]) == 1)
check("rule 2: D8, dated 2 days before the earlier report was taken, is no finding; D7, dated 18 days before, is 'added late'", not got(F, "D8") and len(got(F, "D7", "late", False)) == 1)
keep = BW.LATE_DAYS
BW.LATE_DAYS = 0
F0, _ = engine()
BW.LATE_DAYS = keep
check("rule 2's control: with the 3-day rule off, D8 becomes 'added late'", len(got(F0, "D8", "late")) == 1)
check("rule 3: B4 differs by 40 paise -- for the record, not counted", len(got(F, "B4", "changed", True)) == 1 and got(F, "B4")[0]["changes"][0]["kind"] == "paise")
keep = BW.PAISE_ABS
BW.PAISE_ABS = 0
F0, _ = engine()
BW.PAISE_ABS = keep
check("rule 3's control: with the paise rule off, B4 is counted", len(got(F0, "B4", "changed", False)) == 1)
check("rule 4: G5's item was renamed (only the new name holds stock) -- for the record; G6's item changed and BOTH names hold stock -- counted",
      len(got(F, "G5", "changed", True)) == 1 and len(got(F, "G6", "changed", False)) == 1 and got(F, "G6")[0]["changes"][0]["kind"] == "item")
F0, _ = engine(names={"OLD NAME GEL", "NEW NAME GEL", "THIO"})
check("rule 4's control: when the old name holds stock too, G5 is counted; when THIO TAB holds none, G6 is a rename",
      len(got(F0, "G5", "changed", False)) == 1 and len(got(F0, "G6", "changed", True)) == 1)
check("rule 5: 'a 2' and 'A2' are one bill -- no finding", not got(F, "A2"))
keep = BW.billno_norm
BW.billno_norm = lambda s: str(s or "")
F0, _ = engine()
BW.billno_norm = keep
check("rule 5's control: without the rule 'a 2' is gone and 'A2' is added late", any(f["no"] == "a 2" and f["kind"] == "gone" for f in F0) and any(f["no"] == "A2" and f["kind"] == "late" for f in F0))
check("Marg's own purchase rate re-set (E10: the value column moved, the bill's money did not) is for the record",
      len(got(F, "E10", "changed", True)) == 1 and got(F, "E10")[0]["changes"][0]["kind"] == "value")
check("D935: a Rs 4 change of a bill's money is a finding like any other (H13, H14 counted, +Rs 4 each)",
      len(got(F, "H13", "changed", False)) == 1 and got(F, "H13")[0]["rupee_p"] == 400 and len(got(F, "H14", "changed", False)) == 1)
check("a quantity change (B3 10+2 -> 8+2), a removed bill (E9), a re-dated bill (Z12) and a money change (Z11) are each found once",
      len(got(F, "B3", "changed", False)) == 1 and len(got(F, "E9", "gone", False)) == 1 and len(got(F, "Z12", "redated", False)) == 1 and len(got(F, "Z11", "changed", False)) == 1)
check("unchanged bills make no finding (A1 and the fillers) -- and A1 of LAST financial year is another bill, not a change of this one", not got(F, "A1") and not any(f["sup"] == "FILLER CO" for f in F))
keep = BW._fy
BW._fy = lambda d: ""
F0, _ = engine()
BW._fy = keep
check("the financial-year rule's control: without it last year's A1 makes this year's A1 look changed", len(got(F0, "A1")) >= 1)
check("rule 1, looking forward: a filtered FIRST print of a new period (1 of 6 bills) is no baseline -- none of the 5 others is 'added late', and the print is listed as a part",
      not any(f["sup"] == "NOV HOUSE" for f in F) and any(p["stamp"] == "20261111-100000" for p in P))
F0, P0 = engine(part_rule=False)
check("... its control: with the rule off the same print makes 5 bills 'added late'", len([f for f in F0 if f["sup"] == "NOV HOUSE" and f["kind"] == "late"]) == 5)
check("... and it does not swallow real ones: an honest early list (4 of 7 bills) keeps its 3 genuinely late bills as findings, and is not called a part",
      len([f for f in F if f["sup"] == "DEC HOUSE" and f["kind"] == "late"]) == 3 and not any(p["stamp"] == "20261204-100000" for p in P))
check("D935: the paise rule has no percentage arm -- a line of Rs 50,000 that moves by Rs 40 is counted", BW._paise(5000000, 5004000) is False and BW._paise(5000000, 5000099) is True)

# ------------------------------------------------------------------ 2 · the sale side
c = con()
SF, _ = BW.compare(BW.sale_exports(c), "sale", None, part_rule=False, record_kinds=BW.RECORD_KINDS + ("amount",))
c.close()
check("sale: S101 is gone, S103 was added after the day's report, S104's quantity was cut (counted), S102's money-only change is for the record (D917)",
      len(got(SF, "S101", "gone", False)) == 1 and len(got(SF, "S103", "late", False)) == 1 and len(got(SF, "S104", "changed", False)) == 1
      and len(got(SF, "S102", "changed", True)) == 1)
check("sale: S201, made after the day's own evening report, is no finding; S100 and S200 unchanged", not got(SF, "S201") and not got(SF, "S100") and not got(SF, "S200"))

# ------------------------------------------------------------------ 3 · the paper: the Purchase bills page's judgement, read
c = con()
B = BW.build(c, paper=True)
c.close()
by = {BW.billno_norm(f["no"]): f for f in B["findings"]}
st = {k: (f["paper"] or {}).get("state") for k, f in by.items()}
check("the scans were read", B["paper_ok"])
check("D926: B3 now agrees with its paper to the rupee, and the money moved -- Settled by the scanned bill", st.get("B3") == "settled" and by["B3"]["status"] == "settled")
check("D926: Z12's new date is the paper's -- settled; H13 (+Rs 4) agrees with its paper to the rupee -- settled", st.get("Z12") == "settled" and st.get("H13") == "settled")
check("D935: H14 is one rupee off its paper -- NOT settled, open (%s)" % st.get("H14"), st.get("H14") == "differs" and by["H14"]["status"] == "open")
check("D926: G6's money did not change, so the paper's total cannot settle it -- open (%s)" % st.get("G6"), st.get("G6") == "agrees" and by["G6"]["status"] == "open")
check("Z11: the paper says the old amount -- Marg differs from the paper, open, with that page's own row", st.get("Z11") == "differs" and by["Z11"]["paper"].get("dx") is not None)
check("D7 and A-less bills: no paper on file -- open (%s); a removed bill has no bill to check (%s)" % (st.get("D7"), st.get("E9")), st.get("D7") == "no_paper" and st.get("E9") == "no_bill")
check("the removed sale bill carries its own total and how it was paid (Rs 500, cash)", by["S101"]["rupee_p"] == -50000 and by["S101"]["pay"] == "cash")
check("a sale line's money is Marg's rate per pack x the quantity: S103 (5 loose of 10 at Rs 20) is +Rs 10, not Rs 20; S104 cut from 5 packs to 1 is -Rs 40, not Rs 0 (%s, %s)"
      % (by["S103"]["rupee_p"], by["S104"]["rupee_p"]), by["S103"]["rupee_p"] == 1000 and by["S104"]["rupee_p"] == -4000 and "₹10" in BW.notice_line(by["S103"]))
N_COUNTED = len(B["findings"])
check("counted findings: 15 (%d) · for the record: 4 (%d) · part lists: 2 (%d)" % (N_COUNTED, len(B["record"]), len(B["parts"])), N_COUNTED == 15 and len(B["record"]) == 4 and len(B["parts"]) == 2)
rec102 = next(f for f in B["record"] if f["no"] == "S102")
check("a sale line's rate is called a rate, never an amount ('%s')" % rec102["what"], "rate per pack ₹40 → ₹45" in rec102["what"] and "amount" not in rec102["what"])

# ------------------------------------------------------------------ 4 · the page reads only
h0 = snap()
r = cl.get(PAGE)
html = r.get_data(as_text=True)
check("the page opens and names its parts", r.status_code == 200 and all(x in html for x in ("Marg watch", "Today&#39;s inputs" if "Today&#39;s inputs" in html else "Today's inputs", "Since the page began", "Before this page", "Settled by the scanned bill", "For the record")))
check("before the fill the page has not begun: nothing is new, everything is 'before'", "has not begun" in html and 'class="badge">NEW' not in html)
check("a made-up supplier and item with markup are escaped on the page", "<SCRIPT>ALERT(1)" not in html and "<B>BOLD</B>" not in html and "&lt;B&gt;BOLD&lt;/B&gt;" in html)
check("the removed sale bill says 'Yours to close' and shows its two choices", "Yours to close" in html and "The sale stands" in html and "The sale was cancelled" in html)
check("the inputs strip: a full list came after the part print, so the purchase list reads 'Complete'", "Complete ✓" in html and "Purchase list — part" not in html)
rp = cl.get(PAGE + "/api/panel?f=" + by["B3"]["fkey"])
t = rp.get_data(as_text=True)
check("D936: View on B3 gives the Purchase bills page's parts in the row -- its verdict, the paper's lines beside Marg's, its scan viewer on its own scan route",
      rp.status_code == 200 and "Paper matches" in t and 'id="s781"' in t and "/finance/purchase/api/s738/scan/1" in t and "s738open(this)" in t and "Scan qty" in t)
rp = cl.get(PAGE + "/api/panel?f=" + by["Z11"]["fkey"])
t = rp.get_data(as_text=True)
check("D927: where Marg differs (Z11) the row opens that page's OWN panel -- 'The difference', its taps (Amir fixes Marg), its scan",
      rp.status_code == 200 and "The difference:" in t and "Amir fixes Marg" in t and "/finance/purchase/api/s738/scan/3" in t)
rp = cl.get(PAGE + "/api/panel?f=" + by["D7"]["fkey"])
check("a bill with no scan says so in the row", rp.status_code == 200 and "No scanned bill on file" in rp.get_data(as_text=True))
check("a malformed row key is refused (400), an unknown one is 404", cl.get(PAGE + "/api/panel?f=zz").status_code == 400 and cl.get(PAGE + "/api/panel?f=" + "0" * 16).status_code == 404)
check("READ ONLY: the page and three opened rows changed no table that existed before (only billwatch_* may differ)", snap() == h0)
ROLE["roles"] = ["maker"]
codes = [cl.get(PAGE).status_code, cl.get(PAGE + "/api/panel?f=" + by["B3"]["fkey"]).status_code,
         cl.post(PAGE + "/api/close", json={"f": by["S101"]["fkey"], "decision": "stands"}).status_code, cl.post(PAGE + "/api/oklot", json={"n": 1}).status_code]
ROLE["roles"] = ["checker"]
check("only the doctor: another login is refused on the page and every door %r" % (codes,), codes == [403, 403, 403, 403])

# ------------------------------------------------------------------ 5 · the fill, and what is new after it
c = con()
check("before the fill nothing is noted and nothing can be told", BW.refresh(c) == (0, 0) and BW.judge(c) == 0 and BW.tellable(c) == [])
c.close()
rc = BW.main([DB, "--fill"])
c = con()
n_seen = c.execute("SELECT COUNT(*), SUM(before) FROM billwatch_seen").fetchone()
since = BW.setting(c, "billchange.since", "")
check("the fill notes every finding as 'before this page' (%s of %s) and the page begins" % (n_seen[1], n_seen[0]), rc == 0 and n_seen[0] == 19 and n_seen[1] == 19 and bool(since))
html = cl.get(PAGE).get_data(as_text=True)
check("the phone notice ships OFF: the setting, and the page says so with its 'Turn on'", BW.setting(c, "billchange.on", "?") == "off" and "<b>Off</b>" in html and "Turn on" in html)
r_bad = cl.post(PAGE + "/api/notice", json={"on": "yes"})
r_on = cl.post(PAGE + "/api/notice", json={"on": True})
c.commit()
time.sleep(1.2)                                                # the notice tells what is found AFTER the second it was turned on
check("he turns it on, on the page (a malformed tap is refused); from that moment only", r_bad.status_code == 400 and r_on.status_code == 200 and BW.setting(c, "billchange.on", "?") == "on"
      and bool(BW.setting(c, "billchange.tell_from", "")) and "Turn off" in cl.get(PAGE).get_data(as_text=True))
check("history is never told: after the fill nothing waits to be judged or told", BW.judge(c) == 0 and BW.tellable(c) == [])
# a report of an OLDER day that arrives after the page began brings history: noted, shown under 'Before this page', never told
c0 = c
E0 = [(b[0], b[1], b[2], [L(b[3][0][0], 3, 0, 10, 30)]) if b[1] in ("F3", "F4") else b for b in E1]
export("e0" + "0" * 30, "2026-10-01", "2026-10-20", "20261102-090000", E0)
c.commit()
n_new, _tot = BW.refresh(c)
late_hist = c.execute("SELECT COUNT(*), SUM(before) FROM billwatch_seen").fetchone()
check("a late-arriving report of an older day makes %d more finding(s) -- all 'before this page', none to judge, none to tell" % n_new,
      n_new >= 2 and late_hist[0] == 19 + n_new and late_hist[1] == late_hist[0] and BW.judge(c) == 0 and BW.tellable(c) == [])
A1b = ("ALPHA PHARMA", "A1", "2026-10-05", [L("ITEM ONE", 12, 0, 100, 1200)])
c0 = c
FUT1 = (BW.now_ist() + dt.timedelta(hours=1)).strftime("%Y%m%d-%H%M%S")        # a report taken AFTER the page began
FUT2 = (BW.now_ist() + dt.timedelta(hours=2)).strftime("%Y%m%d-%H%M%S")
export("e4" + "0" * 30, "2026-10-01", "2026-10-31", FUT1, [A1b if b is A1 else b for b in E3])
c.commit()
c.close()
html = cl.get(PAGE).get_data(as_text=True)
c = con()
fa1 = next(f for f in BW.build(c, paper=True)["findings"] if f["no"] == "A1")
check("a change that arrives after the page began is NEW: noted when found, shown first, with its badge", fa1["before"] == 0 and bool(fa1["found_at"]) and 'class="badge">NEW' in html and "1 new" in html)
nj = BW.judge(c)
check("... it is judged once, and it alone is to be told", nj == 1 and BW.judge(c) == 0 and [r["fkey"] for r in BW.tellable(c)] == [fa1["fkey"]])
c.close()

# ------------------------------------------------------------------ 6 · the notice (owner_notice's part) -- nothing can reach a phone: the stub
c = con()
ON.ensure(c)
NOON = dt.datetime(2026, 11, 12, 12, 0, tzinfo=ON.IST)
m = ON._part_bills(c, NOON)
check("the notice: one message for the new finding, in his words, opening the Marg watch",
      len(m) == 1 and m[0]["key"] == "bill:" + fa1["fkey"] and "Alpha Pharma bill A1" in m[0]["body"] and ON._payload(m[0]["key"], "t", "b")["url"] == PAGE)
check("the notice keeps the hours: nothing at 23:00", ON._part_bills(c, NOON.replace(hour=23)) == [])
msgs, errs = ON.collect(c, NOON)
check("collect carries it (and a fault elsewhere never stops it)", any(x["key"] == "bill:" + fa1["fkey"] for x in msgs))
c.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('billchange.on','off')")
c.commit()
check("the switch: billchange.on = off silences it", ON._part_bills(c, NOON) == [])
c.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('billchange.on','on')")
c.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('owner_notice.on','on')")
c.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('owner_notice.since',?)", (since,))
c.commit()
res = ON.tick(c, NOON)
said = open(os.environ["OWNER_NOTICE_STUB"], encoding="utf-8").read() if os.path.exists(os.environ["OWNER_NOTICE_STUB"]) else ""
check("the tick makes the message once and hands it to the road (the walk's stub): %s" % (res.get("error") or "ok"), ("bill:" + fa1["fkey"]) in said)
check("told once: the part has nothing more to say", ON._part_bills(c, NOON) == [])
four = [("ALPHA PHARMA", "A2", "2026-10-05", [L("ITEM TWO", 11, 0, 100, 1100)]), ("DELTA AGENCY", "D8", "2026-10-19", [L("KEYED AFTER TAB", 5, 0, 25, 125)]),
        ("FILLER CO", "F1", "2026-10-15", [L("FILLER 1", 2, 0, 10, 20)]), ("FILLER CO", "F2", "2026-10-16", [L("FILLER 2", 2, 0, 10, 20)])]
nos = {b[1]: b for b in four}
c0 = c
export("e5" + "0" * 30, "2026-10-01", "2026-10-31", FUT2, [nos.get(b[1], A1b if b is A1 else b) for b in E3])
c.commit()
ON.tick(c, NOON)                                               # the tick notes them (refresh) and says them
m_rows = [r[0] for r in c.execute("SELECT key FROM owner_notice WHERE kind='bill' ORDER BY id")]
check("four at once come as ONE message (%r)" % (m_rows,), len(m_rows) == 2 and m_rows[1].startswith("bill:batch:"))
check("... and are not told again", ON._part_bills(c, NOON) == [])
# the same bill changed AGAIN (or the same change re-read from another report) within the week is the same news: shown NEW, not pushed
FUT3 = (BW.now_ist() + dt.timedelta(hours=3)).strftime("%Y%m%d-%H%M%S")
A1c = ("ALPHA PHARMA", "A1", "2026-10-05", [L("ITEM ONE", 13, 0, 100, 1300)])
c0 = c
export("e6" + "0" * 30, "2026-10-01", "2026-10-31", FUT3, [nos.get(b[1], A1c if b is A1 else b) for b in E3])
c.commit()
before_rows = c.execute("SELECT COUNT(*) FROM owner_notice WHERE kind='bill'").fetchone()[0]
ON.tick(c, NOON)
a1_rows = sorted((tuple(r) for r in c.execute("SELECT tell FROM billwatch_seen WHERE sup='ALPHA PHARMA' AND bill_no='A1' AND before=0")), reverse=True)
check("one bill is told at most once a week: A1 changed again -- noted, judged quiet, nothing pushed (%r)" % (a1_rows,),
      a1_rows == [(1,), (0,)] and c.execute("SELECT COUNT(*) FROM owner_notice WHERE kind='bill'").fetchone()[0] == before_rows)
c.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('billchange.on','off')")
c.commit()
FUT4 = (BW.now_ist() + dt.timedelta(hours=4)).strftime("%Y%m%d-%H%M%S")
export("e7" + "0" * 30, "2026-10-01", "2026-10-31", FUT4, [nos.get(b[1], A1c if b is A1 else ((b[0], b[1], b[2], [L("FILLER 3", 5, 0, 10, 50)]) if b[1] == "F3" else b)) for b in E3])
c.commit()
ON.tick(c, NOON)
f3 = c.execute("SELECT tell FROM billwatch_seen WHERE bill_no='F3' AND before=0").fetchall()
time.sleep(1.2)
cl.post(PAGE + "/api/notice", json={"on": True})
c.commit()
ON.tick(c, NOON)
f3b = c.execute("SELECT tell FROM billwatch_seen WHERE bill_no='F3' AND before=0").fetchall()
check("while the notice is off a new finding is noted and not judged; turning it on later does NOT send that backlog (%r, %r)" % ([tuple(r) for r in f3], [tuple(r) for r in f3b]),
      [tuple(r) for r in f3] == [(None,)] and [tuple(r) for r in f3b] == [(None,)] and c.execute("SELECT COUNT(*) FROM owner_notice WHERE kind='bill'").fetchone()[0] == before_rows)
c.close()

# ------------------------------------------------------------------ 7 · his decisions, on the row
fk = by["S101"]["fkey"]
r1 = cl.post(PAGE + "/api/close", json={"f": fk, "decision": ""})
r2 = cl.post(PAGE + "/api/close", json={"f": fk, "decision": "ok"})
check("a removed sale bill needs one of its two choices (no choice 400, 'OK' 400)", r1.status_code == 400 and r2.status_code == 400)
r3 = cl.post(PAGE + "/api/close", json={"f": fk, "decision": "stands", "reason": "  the goods   left <b>x</b> "})
c = con()
row = c.execute("SELECT action, decision, reason, by_user FROM billwatch_act WHERE fkey=? ORDER BY id DESC LIMIT 1", (fk,)).fetchone()
aud = c.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='billwatch_close' AND ref=?", (fk,)).fetchone()[0]
c.close()
html = cl.get(PAGE).get_data(as_text=True)
check("D923: 'The sale stands' with a reason closes the row, by him, audited; the reason is shown escaped",
      r3.status_code == 200 and tuple(row) == ("close", "stands", "the goods left <b>x</b>", "manoj") and aud == 1 and "the goods left &lt;b&gt;x&lt;/b&gt;" in html)
check("a closed row cannot be closed twice (409); Reopen puts it back", cl.post(PAGE + "/api/close", json={"f": fk, "decision": "stands"}).status_code == 409
      and cl.post(PAGE + "/api/reopen", json={"f": fk}).status_code == 200 and cl.post(PAGE + "/api/reopen", json={"f": fk}).status_code == 409)
fk6 = by["G6"]["fkey"]
r = cl.post(PAGE + "/api/close", json={"f": fk6, "decision": "notok", "reason": "the paper says THIO TAB"})
c = con()
g6 = next(f for f in BW.build(c, paper=True)["findings"] if f["fkey"] == fk6)
c.close()
check("'Not OK' keeps the row open and marked", r.status_code == 200 and g6["status"] == "open" and g6["act"]["action"] == "notok" and "Marked Not OK by you" in cl.get(PAGE).get_data(as_text=True))
fkb = by["B3"]["fkey"]
r = cl.post(PAGE + "/api/reopen", json={"f": fkb})
c = con()
b3 = next(f for f in BW.build(c, paper=True)["findings"] if f["fkey"] == fkb)
c.close()
check("D926: a row the paper settled can be reopened by him -- then it is open", r.status_code == 200 and b3["status"] == "open")
c = con()
lot = [f for f in BW.build(c, paper=True)["findings"] if f["before"] and f["status"] == "open" and not (f["side"] == "sale" and f["kind"] == "gone")]
c.close()
r1 = cl.post(PAGE + "/api/oklot", json={"n": len(lot) + 1})
r2 = cl.post(PAGE + "/api/oklot", json={"n": len(lot)})
c = con()
after = BW.build(c, paper=True)["findings"]
c.close()
still = [f for f in after if f["before"] and f["status"] == "open"]
check("OK the lot: refused when the count he saw is not the count now (409); with the right count it closes %d -- and leaves the removed sale bill for its own choice" % len(lot),
      r1.status_code == 409 and r2.status_code == 200 and [f["no"] for f in still] == ["S101"])
check("what is new is never swept into the lot", any(f["no"] == "A1" and f["status"] == "open" for f in after))
z = by["Z11"]
r = cl.post("/finance/purchase/api/s781/mark", json={"bill": ID["Z11"], "action": "clear"})
check("the tap inside an opened panel is the Purchase bills page's own door and still works (%d)" % r.status_code, r.status_code == 200)
c = con()
ok_tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'billwatch_%'")}
c.close()
check("its own tables are the two it names", ok_tables == {"billwatch_seen", "billwatch_act"})
finish()
