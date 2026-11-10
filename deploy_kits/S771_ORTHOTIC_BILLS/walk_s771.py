#!/usr/bin/env python3
"""walk_s771.py FILES_DIR SHARED_DIR FINANCE_DIR [--control]
A walk on MADE-UP rows (no live data): section_count.py and stock_hub.html from FILES_DIR (the kit's, or the live ones for the
control), section_map.py from FINANCE_DIR, a stand-in scan_register, a made-up assets.db. Last line: 'WALK S771 GREEN' or, with
--control on the live files, 'CONTROL S771 RED as it must be'."""
import datetime as dt
import os
import sqlite3
import sys
import tempfile
import types

FILES, SHARED, FIN = sys.argv[1], sys.argv[2], sys.argv[3]
CONTROL = "--control" in sys.argv
sys.path[:0] = [FILES, FIN, SHARED]
for m in ("section_count", "section_map", "scan_register"):
    sys.modules.pop(m, None)

from flask import Flask, g, jsonify  # noqa: E402

SR = types.ModuleType("scan_register")
SR.sup_norm = lambda s: " ".join(str(s or "").upper().replace(".", " ").split())
SR.register = lambda con, month: dict(scans=[])
sys.modules["scan_register"] = SR

TMP = tempfile.mkdtemp(prefix="w771_")
DB = os.path.join(TMP, "f.db")
ADB = os.path.join(TMP, "assets.db")
TODAY = dt.date.today()
THIS = TODAY.replace(day=1)
LAST = (THIS - dt.timedelta(days=1)).replace(day=1)
D_NOW = THIS.isoformat()                                       # a bill dated the 1st of this month
D_LAST = (LAST + dt.timedelta(days=4)).isoformat()             # the 5th of last month
DMY = lambda d: d.strftime("%d-%m-%Y")  # noqa: E731

con = sqlite3.connect(DB)
con.executescript("""
CREATE TABLE stock_snapshot (as_on TEXT, item TEXT, qty INTEGER, packing TEXT, pack_size INTEGER, loaded_at TEXT, source TEXT);
CREATE TABLE sale_line_item (id INTEGER PRIMARY KEY, day_entry_id INTEGER, ingest_batch_id INTEGER, unit TEXT, business_date TEXT, bill_no TEXT,
  is_return INTEGER, seq INTEGER, item_name TEXT, item_key TEXT, pack TEXT, qty_raw TEXT, amount_p INTEGER, expiry_ym TEXT, batch TEXT);
CREATE TABLE purchase_line (id INTEGER PRIMARY KEY, supplier_norm TEXT, bill_no TEXT, bill_date TEXT, month TEXT, item TEXT, packing TEXT, batch TEXT,
  expiry TEXT, tax TEXT, qty REAL, free REAL, rate_p INTEGER, discount_pct REAL, amount_p INTEGER, net_rate_p INTEGER, net_amount_p INTEGER,
  loose_qty REAL, purchase_rate_p INTEGER, direction TEXT, source_md5 TEXT, line_type TEXT);
CREATE TABLE purchase_bill (id INTEGER PRIMARY KEY, supplier_norm TEXT NOT NULL, supplier TEXT NOT NULL, bill_no TEXT NOT NULL, bill_date TEXT,
  month TEXT, cash_p INTEGER DEFAULT 0, credit_p INTEGER DEFAULT 0, amount_p INTEGER DEFAULT 0);
CREATE TABLE purchase_scan_link (bill_id INTEGER PRIMARY KEY, asset_bill_id INTEGER NOT NULL, grade TEXT NOT NULL, matched_on TEXT, linked_at TEXT NOT NULL);
CREATE TABLE purchase_export (md5 TEXT PRIMARY KEY, type TEXT NOT NULL, file TEXT NOT NULL, period_from TEXT NOT NULL, period_to TEXT NOT NULL,
  export_stamp TEXT NOT NULL, received_at TEXT NOT NULL, n_rows INTEGER NOT NULL DEFAULT 0, grand_amount_p INTEGER, superseded_by TEXT);
CREATE TABLE marg_hand_change (id INTEGER PRIMARY KEY, k20 TEXT, item TEXT, kind TEXT, day_from TEXT, day_to TEXT, marg_from REAL, marg_to REAL,
  system_moved REAL, shift REAL, pair_item TEXT, found_at TEXT, status TEXT, status_at TEXT, hist INTEGER);
CREATE TABLE amir_job (id INTEGER PRIMARY KEY, key TEXT NOT NULL UNIQUE, kind TEXT NOT NULL, subject TEXT NOT NULL, text_hi TEXT, sub_hi TEXT,
  created_at TEXT NOT NULL, created_by TEXT, show_from TEXT, said_at TEXT, said_by TEXT, said_what TEXT, done_at TEXT, done_how TEXT, reopened_at TEXT);
CREATE TABLE audit_log (id INTEGER PRIMARY KEY, table_name TEXT, row_id INTEGER, action TEXT, before_json TEXT, after_json TEXT, by_whom TEXT, at TEXT);
CREATE TABLE stock_count (id INTEGER PRIMARY KEY, unit TEXT, marg_as_on TEXT, status TEXT, section TEXT);
CREATE TABLE unit_role (id INTEGER PRIMARY KEY, unit TEXT, username TEXT, role TEXT, active INTEGER DEFAULT 1, note TEXT);
INSERT INTO unit_role (unit, username, role) VALUES ('medical','manoj','checker'),('medical','darpan','maker'),('stockmatch','darpan','maker'),('stockmatch','manoj','checker');
CREATE TABLE stock_item_section (item_key TEXT PRIMARY KEY, item TEXT NOT NULL, section TEXT NOT NULL, source TEXT NOT NULL, seeded_as TEXT, by_user TEXT, at TEXT NOT NULL);
""")
SNAP = [("SHOULDER IMMOB M UNISON", 3), ("SHOULDER IMMOB XL UNISON", 1), ("L S BELT L CONT GRAY UNISON", 2), ("L S BELT XL CONT GRAY UNIS", 2),
        ("TYNOR WRIST SPL RT M ELASTIC", 1), ("TYNOR WRIST SPL LF M ELAS T", 2), ("ANKLE BINDER M BAMBOO", 1), ("ANKLE BINDER M TYNOR", 3),
        ("KNEE SUPPORT L HINGED", 2), ("CAST SHOE M TYNOR", 1), ("RIB BELT UNIVERSAL UNISON", 2), ("ACILOC 300", 77)]
for it, q in SNAP:
    con.execute("INSERT INTO stock_snapshot VALUES (?,?,?,?,?,?,?)", (DMY(TODAY - dt.timedelta(days=1)), it, q, "1*1", 1 if it != "ACILOC 300" else 20, "x", "push_snapshot"))
    if it != "ACILOC 300":
        con.execute("INSERT INTO stock_item_section VALUES (?,?,?,?,?,?,?)", (it, it, "Orthotics", "owner", "Orthotics", "manoj", "2026-10-01T10:00:00"))
DEALER = "YUVIKA SURGICALS"
# (id, bill_no, date, amount, scan_id or None, [(marg item, qty, rate, net amount)], [(scan item, qty, rate, amount)], scan total)
BILLS = [
    (1, "901", D_NOW, 900.0, 11, [("SHOULDER IMMOB M UNISON", 1, 428.58, 450)], [("(Unison) Shoulder Immobilizer Neo-XL", 1, 450, 450)], 450),
    (2, "902", D_NOW, 1860.0, 12, [("L S BELT L CONT GRAY UNISON", 2, 442.86, 930), ("L S BELT XL CONT GRAY UNIS", 2, 442.86, 930)],
     [("(Unison) L.s Belt Cont. G-XL", 2, 442.86, 930), ("(Unison) L.s Belt Cont. G-L", 2, 442.86, 930)], 1860),
    (3, "903", D_LAST, 464.0, 13, [("TYNOR WRIST SPL LF M ELAS T", 2, 220.95, 464)], [("TY ELASTIC WRIST SPLINT RT-( M )", 2, 220.95, 464)], 464),
    (4, "904", D_LAST, 560.0, 14, [("RIB BELT UNIVERSAL UNISON", 2, 266.67, 560)], [("(Unison) Rib Belt Universal", 2, 266.67, 560)], 560),
    (5, "905", D_LAST, 189.0, 15, [("ANKLE BINDER M BAMBOO", 1, 180, 189)], [("TYNOR ANKLE BINDER (M)", 1, 180, 189)], 189),
    (6, "906", D_LAST, 450.0, 16, [("SHOULDER IMMOB XL UNISON", 1, 428.58, 450)], [("(Unison) Shoulder Immobilizer Neo-XL", 2, 225, 450)], 450),
    (7, "907", D_NOW, 1364.0, 17, [("SHOULDER IMMOB XL UNISON", 1, 428.58, 450), ("SHOULDER IMMOB M UNISON", 2, 457.14, 914)],
     [("(Unison) Shoulder Immobilizer Neo-XL", 2, 428.57, 900), ("(Unison) Shoulder Immobilizer Neo-M", 1, 457.14, 480)], 1380),
    (8, "YS0706202627", D_LAST, 574.0, 18, None, [("TYNOR CAST SHOE-( L )", 1, 546.66, 574)], 574),
    (9, "909", D_NOW, 530.0, None, [("KNEE SUPPORT L HINGED", 1, 504.76, 530)], [], None),
    (10, "910", D_LAST, 1590.0, 20, [("KNEE SUPPORT L HINGED", 2, 504.76, 1060), ("RIB BELT UNIVERSAL UNISON", 2, 265, 530)],
     [("(Unison) Knee Supp. Hinged-V", 2, 504.76, 1060)], 1590),
    (11, "911", D_LAST, 1590.0, 21, [("KNEE SUPPORT L HINGED", 2, 504.76, 1060), ("RIB BELT UNIVERSAL UNISON", 2, 265, 530)],
     [("(Unison) Knee Supp. Hinged-L", 2, 504.76, 1060)], 1060),
    (12, "912", D_LAST, 189.0, 22, [("ANKLE BINDER XL TYNOR", 1, 180, 189)], [("AKLE BNDR", 1, 180, 189)], 189),
    (13, "YS0999202627", D_LAST, 1060.0, 23, [("KNEE SUPPORT L HINGED", 1, 504.76, 530)], [("(Unison) Knee Supp. Hinged-L", 2, 504.76, 1060)], 1060),
]
a = sqlite3.connect(ADB)
a.executescript("CREATE TABLE bills(id INTEGER PRIMARY KEY, vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount REAL, source_stored TEXT, source_orig TEXT);"
                "CREATE TABLE bill_items(id INTEGER PRIMARY KEY, bill_id INTEGER, item_name TEXT, quantity REAL, rate REAL, amount REAL);")
for bid, bno, d, amt, sid, ml, sl, st in BILLS:
    con.execute("INSERT INTO purchase_bill (id, supplier_norm, supplier, bill_no, bill_date, month, amount_p) VALUES (?,?,?,?,?,?,?)",
                (bid, DEALER, "Yuvika Surgicals", bno, d, d[:7], int(round(amt * 100))))
    if ml is not None:
        for it, q, r, net in ml:
            con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, item, qty, free, rate_p, net_amount_p, direction, source_md5, line_type) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (DEALER, bno, d, it, q, 0, int(round(r * 100)), int(round(net * 100)), "PURCHASE", "p0" if bid == 13 else "e1", "ITEMWISE"))
    if sid:
        con.execute("INSERT INTO purchase_scan_link VALUES (?,?,?,?,?)", (bid, sid, "EXACT", "x", "2026-11-01T10:00:00"))
        a.execute("INSERT INTO bills VALUES (?,?,?,?,?,?,?)", (sid, DEALER, "YS/" + bno, d, st, "s%d" % sid, "b%d.%s" % (sid, "pdf" if sid == 12 else "jpg")))
        for it, q, r, am in sl:
            a.execute("INSERT INTO bill_items (bill_id, item_name, quantity, rate, amount) VALUES (?,?,?,?,?)", (sid, it, q, r, am))
con.execute("INSERT INTO purchase_export VALUES (?,?,?,?,?,?,?,?,?,?)", ("p0", "ITEMWISE", "x", LAST.isoformat(), (THIS - dt.timedelta(days=1)).isoformat(), "20261005-090000", "x", 1, 0, None))
# bill 8: the number spilled into the item column in two exports; the newer one is read; another bill's spill is never taken
for md5, stamp, q in (("o1", "20261008-090000", 3), ("o2", "20261029-090000", 1)):
    con.execute("INSERT INTO purchase_export VALUES (?,?,?,?,?,?,?,?,?,?)", (md5, "ITEMWISE", "x", LAST.isoformat(), (THIS - dt.timedelta(days=1)).isoformat(), stamp, "x", 1, 0, None))
    con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, item, qty, free, rate_p, net_amount_p, direction, source_md5, line_type) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (DEALER, None, None, "06202627CAST SHOE M TYNOR", q, 0, 54666, 57400 * q, "PURCHASE", md5, "ITEMWISE"))
    con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, item, qty, free, rate_p, net_amount_p, direction, source_md5, line_type) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (DEALER, None, None, "11112222RIB BELT UNIVERSAL UNISON", 9, 0, 26667, 1, "PURCHASE", md5, "ITEMWISE"))
    con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, item, qty, free, rate_p, net_amount_p, direction, source_md5, line_type) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (DEALER, None, None, "2627RIB BELT UNIVERSAL UNISON", 9, 0, 26667, 1, "PURCHASE", md5, "ITEMWISE"))
con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, item, qty, free, rate_p, net_amount_p, direction, source_md5, line_type) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (DEALER, None, None, "99202627KNEE SUPPORT L HINGED", 2, 0, 50476, 106000, "PURCHASE", "o2", "ITEMWISE"))
con.commit()
con.close()
a.commit()
a.close()

app = Flask(__name__)


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


ROLES = {"darpan": ["maker"], "manoj": ["checker"]}
CUR = {"u": "manoj"}


def require(*roles, unit="medical"):
    have = ROLES.get(CUR["u"], []) if unit == "stockmatch" else []
    if not set(have) & set(roles):
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    return dict(user=CUR["u"], role="staff", roles=have), None


import section_count as S  # noqa: E402

S.init(app, db, require)
cl = app.test_client()
RES = []


def check(name, ok):
    RES.append((name, bool(ok)))
    print(("GREEN " if ok else "RED   ") + name)


def J(r):
    try:
        return r.get_json() or {}
    except Exception:  # noqa: BLE001
        return {}


P = "/finance/stockmatch/count"
hub = open(os.path.join(FILES, "stock_hub.html"), encoding="utf-8").read()
if CONTROL:
    r = cl.get(P + "/api/bills?section=Orthotics")
    s771 = [r.status_code == 200, hasattr(S, "bills_card"), 'id="s771"' in hub, getattr(S, "KIT", "") == "S771_ORTHOTIC_BILLS"]
    old = cl.get(P + "/api/healthz").status_code == 200
    print("CONTROL S771 RED as it must be" if old and not any(s771) else "CONTROL S771 NOT RED (%s)" % s771)
    sys.exit(0)

S.ASSETS_DB = ADB
r = cl.get(P + "/api/healthz")
check("1 healthz names S771 (v1.2)", r.status_code == 200 and J(r).get("kit") == "S771_ORTHOTIC_BILLS" and J(r).get("version") == "1.2")
CUR["u"] = "darpan"
check("2 the card is the doctor's: Darpan gets 403 on the list and on a mark",
      cl.get(P + "/api/bills?section=Orthotics").status_code == 403 and cl.post(P + "/api/bills/mark", json=dict(bill=1, key="x", action="clear")).status_code == 403)
CUR["u"] = "manoj"
r = cl.get(P + "/api/bills?section=Orthotics")
C = J(r)
check("3 the doctor's list answers 200 with the dealer found by the section's names", r.status_code == 200 and C.get("dealers") == [DEALER] and C.get("scans_ok") is True)
NOW = {x["no"]: x for x in C.get("now", [])}
OPEN = {x["no"]: x for x in C.get("open", [])}
SET = {x["no"] for x in C.get("settled", [])}


def kinds(x):
    return [l["kind"] for l in x["lines"] if l["kind"]]


check("4 this month: bills 901, 902, 907, 909; earlier differing: 903, 905, YS0706202627, 911; settled: 904, 906, 910, 912, YS0999202627",
      set(NOW) == {"901", "902", "907", "909"} and set(OPEN) == {"903", "905", "YS0706202627", "911"} and SET == {"904", "906", "910", "912", "YS0999202627"})
check("5 size: the bill XL, Marg M -> one differing line, its why says so", kinds(NOW["901"]) == ["size"] and "the bill says XL, Marg has M" in NOW["901"]["lines"][0]["why"])
check("6 two lines of one product, L and XL, pair by their sizes -> agrees", NOW["902"]["state"] == "agrees" and not kinds(NOW["902"]))
check("7 side: Right on the bill, Left in Marg", kinds(OPEN["903"]) == ["side"] and "Right" in OPEN["903"]["lines"][0]["why"])
check("8 brand: Tynor on the bill, Bamboo in Marg", kinds(OPEN["905"]) == ["brand"] and "Tynor" in OPEN["905"]["lines"][0]["why"])
l6 = [l for l in C["settled"] if l["no"] == "906"]
c6 = sqlite3.connect(DB)
c6.row_factory = sqlite3.Row
c6a = sqlite3.connect(ADB)
c6a.row_factory = sqlite3.Row
x6 = S.one_bill(c6, c6a, c6.execute("SELECT * FROM purchase_bill WHERE id=6").fetchone())
check("9 a quantity read wrong while the line's amount is the same on both sides is a grey note, not a difference",
      x6["state"] == "agrees" and "one piece" in x6["lines"][0]["note"])
check("10 quantities swapped (the amounts differ too) -> two quantity lines", sorted(kinds(NOW["907"])) == ["qty", "qty"])
x8 = OPEN["YS0706202627"]
check("11 the bill number spilled into the item column: read for this bill, the number cut off, the NEWER export (qty 1), never another bill's spill; its size judged",
      x8["overflow"] is True and [(l["marg"], l["mq"]) for l in x8["lines"]] == [("CAST SHOE M TYNOR", 1)] and kinds(x8) == ["size"])
check("12 a bill with no scan: 'no_scan', its Marg lines shown", NOW["909"]["state"] == "no_scan" and NOW["909"]["lines"][0]["marg"] == "KNEE SUPPORT L HINGED")
x10 = S.one_bill(c6, c6a, c6.execute("SELECT * FROM purchase_bill WHERE id=10").fetchone())
check("13 'Hinged-V' is the reader's misread of L (a note); a Marg line the reader missed while the totals agree is a note, not a difference",
      x10["state"] == "agrees" and any('"V" is the reader' in l["note"] for l in x10["lines"]) and any("missed" in l["note"] for l in x10["lines"]))
check("14 the same Marg line missing from the scan while the totals DIFFER is a difference ('Not on the bill')", kinds(OPEN["911"]) == ["missing_bill"])
check("15 every bill names its scan for the fold: /scanapp/bills/<id>/file; a .pdf scan is kind pdf, a .jpg image",
      NOW["901"]["scan_url"] == "/scanapp/bills/11/file" and NOW["902"]["scan_kind"] == "pdf" and NOW["901"]["scan_kind"] == "image" and NOW["909"]["scan_url"] == "")
c6.close()
c6a.close()

k1 = NOW["901"]["lines"][0]["key"]
r = cl.post(P + "/api/bills/mark", json=dict(bill=1, key=k1, action="amir"))
c7 = sqlite3.connect(DB)
job = c7.execute("SELECT key, kind, subject, text_hi, sub_hi, created_by FROM amir_job").fetchall()
check("16 'Amir fixes Marg' puts ONE tap job on Amir's card, in his words",
      r.status_code == 200 and len(job) == 1 and job[0][1] == "tap" and job[0][0].startswith("S771:b1:") and "Marg ki entry theek kijiye" in job[0][3]
      and "size XL" in job[0][3] and "bill 901" in job[0][4] and job[0][5] == "S771")
check("17 a second tap on the same line is refused (409), still one job", cl.post(P + "/api/bills/mark", json=dict(bill=1, key=k1, action="amir")).status_code == 409
      and c7.execute("SELECT COUNT(*) FROM amir_job").fetchone()[0] == 1)
C2 = J(cl.get(P + "/api/bills?section=Orthotics"))
x1 = [x for x in C2["now"] if x["no"] == "901"][0]
check("18 the line shows it is with Amir and stays open (highlighted) until Marg is fixed", x1["lines"][0]["mark"]["action"] == "amir" and x1["open"] == 1 and x1["with_amir"] == 1)
k3 = OPEN["903"]["lines"][0]["key"]
r = cl.post(P + "/api/bills/mark", json=dict(bill=3, key=k3, action="clear"))
C3 = J(cl.get(P + "/api/bills?section=Orthotics"))
check("19 'Marg is right' clears the line: the bill leaves 'still open' and reads settled", r.status_code == 200 and "903" not in {x["no"] for x in C3["open"]}
      and "903" in {x["no"] for x in C3["settled"]})
r = cl.post(P + "/api/bills/mark", json=dict(bill=3, key=k3, action="undo"))
C4 = J(cl.get(P + "/api/bills?section=Orthotics"))
check("20 Undo puts it back as it was", r.status_code == 200 and "903" in {x["no"] for x in C4["open"]})
check("21 a key that does not differ is refused (409); an unknown bill 404; an unknown action 400",
      cl.post(P + "/api/bills/mark", json=dict(bill=2, key="size|A|B", action="clear")).status_code == 409
      and cl.post(P + "/api/bills/mark", json=dict(bill=99, key="x", action="clear")).status_code == 404
      and cl.post(P + "/api/bills/mark", json=dict(bill=5, key=OPEN["905"]["lines"][0]["key"], action="explode")).status_code == 400)
check("22 every mark is audited", c7.execute("SELECT COUNT(*) FROM audit_log WHERE action LIKE 'bill_%'").fetchone()[0] == 3)
# Marg fixed: a newer export of bill 901 carries the right size -> the line no longer differs and the mark is left inert
c7.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, item, qty, free, rate_p, net_amount_p, direction, source_md5, line_type) "
           "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (DEALER, "901", D_NOW, "SHOULDER IMMOB XL UNISON", 1, 0, 42858, 45000, "PURCHASE", "e2", "ITEMWISE"))
c7.commit()
C5 = J(cl.get(P + "/api/bills?section=Orthotics"))
x1 = [x for x in C5["now"] if x["no"] == "901"][0]
check("23 the next export shows Marg fixed: bill 901 agrees by itself", x1["state"] == "agrees" and x1["open"] == 0)
# the star at the next count: bill 905's Bamboo line (open) and its Tynor item; 903's Left item
r = cl.post(P + "/api/start", json=dict(section="Orthotics"))
cid = J(r).get("count")
fl = {row[0]: (row[1], row[2]) for row in c7.execute("SELECT item, flag, flag_why FROM section_count_line WHERE count_id=?", (cid,))}
check("24 the next Orthotics count stars the items named on open differing lines (both sides), with the bill in the reason",
      r.status_code == 200 and fl.get("ANKLE BINDER M BAMBOO", (0,))[0] >= 1 and "Bill 905" in fl["ANKLE BINDER M BAMBOO"][1]
      and fl.get("ANKLE BINDER M TYNOR", (0,))[0] >= 1 and fl.get("TYNOR WRIST SPL LF M ELAS T", (0,))[0] >= 1
      and fl.get("TYNOR WRIST SPL RT M ELASTIC", (0,))[0] >= 1 and fl.get("CAST SHOE M TYNOR", (0,))[0] >= 1
      and "Bill 911" in fl.get("RIB BELT UNIVERSAL UNISON", (0, ""))[1] and fl.get("KNEE SUPPORT L HINGED", (9,))[0] == 0)
c7.close()
S.ASSETS_DB = os.path.join(TMP, "nowhere.db")
r = cl.get(P + "/api/bills?section=Orthotics")
check("25 assets.db unreadable: the card still answers and says the scans could not be read", r.status_code == 200 and J(r)["scans_ok"] is False)
S.ASSETS_DB = ADB
P1 = S.parse_name("(Unisex) L.S. Belt Const. G-MN")
P2 = S.parse_name("L S BELT XXL CONT GRAY UNI")
P3 = S.parse_name("TY ELASTIC WRIST SPLINT RT-( M )")
check("26 the name reader: 'L.S.' is never a size; MN unreadable; UNI is Unison; TY is Tynor, RT is Right; S/L two sizes; univ. no size",
      P1["size"] == "?" and P1["size_raw"] == "MN" and P2["size"] == "XXL" and P2["brand"] == "Unison" and P3["brand"] == "Tynor" and P3["side"] == "Right"
      and P3["size"] == "M" and S.parse_name("(Unison) Clavical Brace- S/L")["size"] == "?" and S.parse_name("(Unison) Tennis Elbow-univ.")["size"] == "")
check("27 the hub page carries the card, its fold for the scan (loaded on a tap) and its calls",
      'id="s771"' in hub and "s771load();" in hub and "/api/bills/mark" in hub and "data-s771scan" in hub and "Show the scanned bill" in hub
      and "Amir fixes Marg" in hub and "Marg is right" in hub and "s769top();" in hub)
check("28 the card's style is scoped to it (#s771) and the page's own steps are untouched", "#s771 details.s771b" in hub and 'id="s769fold"' in hub)

c9 = sqlite3.connect(DB)
c9.row_factory = sqlite3.Row
c9a = sqlite3.connect(ADB)
c9a.row_factory = sqlite3.Row
x12 = S.one_bill(c9, c9a, c9.execute("SELECT * FROM purchase_bill WHERE id=12").fetchone())
check("29 a scan name read too badly to pair by its words pairs by its amount; it is not called 'Not in Marg'", x12["state"] == "agrees"
      and x12["lines"][0]["marg"] == "ANKLE BINDER XL TYNOR")
x13 = S.one_bill(c9, c9a, c9.execute("SELECT * FROM purchase_bill WHERE id=13").fetchone())
check("30 a bill printed properly in an older export and spilled in a newer one is read from the NEWER (by its stamp)",
      x13["overflow"] is True and x13["lines"][0]["mq"] == 2 and x13["state"] == "agrees")
check("31 an empty key is never a line to mark (409), even on a bill whose lines agree",
      cl.post(P + "/api/bills/mark", json=dict(bill=2, key="", action="clear")).status_code == 409)
x7 = S.one_bill(c9, c9a, c9.execute("SELECT * FROM purchase_bill WHERE id=7").fetchone())
k7 = [l["key"] for l in x7["lines"] if l["kind"] == "qty"][0]
cl.post(P + "/api/bills/mark", json=dict(bill=7, key=k7, action="clear"))
x7b = S.one_bill(c9, c9a, c9.execute("SELECT * FROM purchase_bill WHERE id=7").fetchone())
c9.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, item, qty, free, rate_p, net_amount_p, direction, source_md5, line_type) VALUES "
           "(?,?,?,?,?,?,?,?,?,?,?),(?,?,?,?,?,?,?,?,?,?,?)", (DEALER, "907", D_NOW, "SHOULDER IMMOB XL UNISON", 3, 0, 42858, 135000, "PURCHASE", "e9", "ITEMWISE",
                                                                 DEALER, "907", D_NOW, "SHOULDER IMMOB M UNISON", 2, 0, 45714, 91400, "PURCHASE", "e9", "ITEMWISE"))
c9.commit()
x7c = S.one_bill(c9, c9a, c9.execute("SELECT * FROM purchase_bill WHERE id=7").fetchone())
check("32 a cleared quantity line comes back when Marg's figure changes to another wrong one (the figures are in its key)",
      x7b["open"] == 1 and x7c["open"] == 2)
x5 = [l for l in S.one_bill(c9, c9a, c9.execute("SELECT * FROM purchase_bill WHERE id=5").fetchone())["lines"] if l["kind"]][0]
cl.post(P + "/api/bills/mark", json=dict(bill=5, key=x5["key"], action="amir"))
n1 = c9.execute("SELECT COUNT(*) FROM amir_job WHERE key LIKE 'S771:b5:%'").fetchone()[0]
cl.post(P + "/api/bills/mark", json=dict(bill=5, key=x5["key"], action="undo"))
n2 = c9.execute("SELECT COUNT(*) FROM amir_job WHERE key LIKE 'S771:b5:%'").fetchone()[0]
check("33 Undo of 'Amir fixes Marg' takes the job off Amir's card while he has not done it", n1 == 1 and n2 == 0)
c9.close()
c9a.close()

bad = [n for n, ok in RES if not ok]
print("WALK S771 GREEN" if not bad else "WALK S771 RED (%d): %s" % (len(bad), "; ".join(bad)[:300]))
