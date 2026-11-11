#!/usr/bin/env python3
"""walk_s781.py FILES_DIR SHARED_DIR FINANCE_DIR SCHEMA [--control]
A walk on MADE-UP rows (no live data): purchase_app.py and provisional_s781.py from FILES_DIR (the kit's, or the live ones for the control),
the rest from FINANCE_DIR. SCHEMA = a finance.db opened read only (its tables' layout only, never a row). The bills and their item lines go
in through the real /finance/purchase/api/push door; the scans sit in a made-up assets.db; the page and the door are driven through a
Flask test client with a stand-in sign-in. Last line: 'WALK S781 GREEN' or, with --control on the live files, 'CONTROL S781 RED as it must be'."""
import datetime as dt
import hashlib
import os
import re
import shutil
import sqlite3
import sys
import tempfile

FILES, SHARED, FIN, SCHEMA = sys.argv[1:5]
CONTROL = "--control" in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != HERE]   # the kit folder carries provisional_s781.py: never imported from there
TMP = tempfile.mkdtemp(prefix="w781_")
RUN = os.path.join(TMP, "run")
os.makedirs(RUN)
for f in ("purchase_app.py", "provisional_s781.py"):
    if os.path.exists(os.path.join(FILES, f)):
        shutil.copyfile(os.path.join(FILES, f), os.path.join(RUN, f))
shutil.copyfile(os.path.join(FIN, "purchase_schema.sql"), os.path.join(RUN, "purchase_schema.sql"))
sys.path[:0] = [RUN, FIN, SHARED]

DB = os.path.join(TMP, "f.db")
if SCHEMA.endswith(".json"):                                   # the tables' layout only (schema_only.json), never a row
    import json as _json
    ddl = _json.load(open(SCHEMA, encoding="utf-8"))["ddl"]
else:
    s = sqlite3.connect("file:%s?mode=ro" % SCHEMA, uri=True, timeout=30)
    ddl = [r[0] for r in s.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' "
                                   "ORDER BY CASE type WHEN 'table' THEN 0 ELSE 1 END, name")]
    s.close()
c0 = sqlite3.connect(DB)
for q in ddl:
    try:
        c0.execute(q)
    except sqlite3.Error:
        pass
c0.commit()
c0.close()

T = dt.date.today()
M = T.strftime("%Y-%m")
PREV = (T.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
D1, D2, D3, D5, D6, D7 = ("%s-%02d" % (M, d) for d in (1, 2, 3, 5, 6, 7))
DAY = T.isoformat()
ADB = os.path.join(TMP, "assets.db")
a = sqlite3.connect(ADB)
a.execute("CREATE TABLE bills (id INTEGER PRIMARY KEY, kind TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount REAL, notes TEXT, source_stored TEXT, "
          "source_orig TEXT, created_by TEXT, created_at TEXT, stamp_no TEXT, status TEXT, submitted_by TEXT, submitted_at TEXT, approved_by TEXT, approved_at TEXT, "
          "reject_reason TEXT, vendor_phone TEXT, vendor_email TEXT, ocr_status TEXT, lane TEXT, fp TEXT, fpc TEXT, dup_of INTEGER, dup_flag TEXT, dup_cand TEXT, "
          "dup_why TEXT, late_for TEXT, bill_month TEXT, doc_kind TEXT, challan_state TEXT, challan_of INTEGER, pe_who TEXT, rescan_of INTEGER)")
a.execute("CREATE TABLE bill_items (id INTEGER PRIMARY KEY, bill_id INTEGER, item_name TEXT NOT NULL, pack_size TEXT, quantity REAL, rate REAL, amount REAL, make TEXT, "
          "model TEXT, serial_no TEXT, batch TEXT, expiry TEXT, hsn TEXT, asset_id INTEGER)")
a.execute("CREATE TABLE claude_reading (bill_id INTEGER PRIMARY KEY, at TEXT NOT NULL, model TEXT, ok INTEGER NOT NULL DEFAULT 0, doc_kind TEXT, data TEXT, error TEXT)")


def scan(i, vendor, no, d, total, items, month=M, day=DAY):
    a.execute("INSERT INTO bills (id, kind, vendor, bill_no, bill_date, total_amount, status, stamp_no, submitted_at, created_at, lane, bill_month, source_stored) "
              "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (i, "Pharmacy", vendor, no, d, total, "captured", "B-%04d" % i, day + " 10:00:00", day + " 10:00:00",
                                                    "pharmacy", month, "x.pdf"))
    for it in items:
        a.execute("INSERT INTO bill_items (bill_id, item_name, pack_size, quantity, rate, amount, batch, expiry) VALUES (?,?,?,?,?,?,?,?)", (i,) + tuple(it))


scan(1, "KEDAR PHARMACEUTICAL", "A000230", D5, 9120.00, [("FLUXIC P", "1*10", 30, 112.0, 3360.0, "FX1", "11/27"), ("MEG QCS", "1*10", 50, 115.2, 5760.0, "MQ1", "05/28")])
scan(2, "JANTA PHARMACEUTICALS", "21965", D2, 4450.00, [("VOLITRA APS SPRAY", "1*1", 10, 267.19, 2671.91, "V1", "01/28"),
                                                          ("POWERGESIC 200 PATCH", "1*1", 3, 177.84, 533.53, "P1", "02/28"),
                                                          ("VOLINI GEL 30G", "1*1", 10, 124.46, 1244.56, "G1", "03/28")])
scan(3, "KEDAR PHARMACEUTICAL", "226", D1, 9510.00, [("PRETOL 8", "1*10", 10, 141.12, 1411.20, "P8", "05/28"), ("C2CALZ", "1*10", 20, 121.44, 2428.80, "C2", None),
                                                      ("FLUXIC P", "1*10", 30, 112.0, 3360.0, "FX2", "11/27"), ("MEG QCS", "1*10", 20, 115.5, 2310.0, "MQ2", "05/28")])
scan(4, "DEEPAM PHARMA", "6678", D7, 8940.00, [("PANTAVIN 40", "1*15", 30, 98.2, 2946.0, "PV1", "08/28"), ("DEFVAX 6", "1*10", 20, 61.5, 1230.0, "DF1", None),
                                                ("FLUXIC P", "1*10", 30, 44.8, 1344.0, "FX3", "11/27"), ("XGESIC LA", "1*10", 25, 120.0, 3000.0, "XG", "07/28")])
scan(5, "A.A. PHARMACEUTICALS", "1", D6, 3881.00, [("PRETOL 8", "1*10", 20, 126.0, 2520.0, "PR", "05/28"), ("DOLOGESIC SP", "1*10", 10, 94.5, 945.0, "DS", "11/27")])
scan(6, "BAAS PLASMA DISTRIBUTORS", "412", "2023-05-20", 29700.00, [("Copper Wire 1.5mm", None, 200, 120.0, 24000.0, None, None), ("PVC Insulation", None, 200, 15.0, 3000.0, None, None)])
scan(7, "DEEPAM PHARMA", "6690", "2025-%s" % D6[5:], 1234.00, [("ROSIKA FORTE", "1*10", 10, 123.4, 1234.0, "RF", "01/28")])
scan(8, "DEEPAM PHARMA", "6701", D7, 2000.00, [("THIO Q", "1*10", 10, 200.0, 2000.0, "TQ", "11/27")])
scan(9, "<script>alert(1)</script>O'NEIL", "77", D6, 500.00, [("<b>BOLD</b> 'X'", None, 1, 500.0, 500.0, None, None)])
scan(10, "DEEPAM PHARMA", "6720", D7, 1500.00, [])                 # no bill_items: its lines come from the reading, which carries MRP
a.execute("INSERT INTO claude_reading (bill_id, at, ok, data) VALUES (?,?,1,?)", (10, DAY, '{"items":[{"name":"VFER 500","unit":"1*1","qty":10,"rate":150,'
          '"amount":1500,"mrp":199}]}'))
a.execute("ALTER TABLE bill_items ADD COLUMN free REAL")          # a column the scanner may read one day: shown by itself
a.execute("ALTER TABLE bill_items ADD COLUMN mrp REAL")
scan(12, "DEEPAM PHARMA", "6730", D7, 300.00, [("LIMCEE", "1*15", "LC1", "06/28", 2, 150.0, 300.0)][:0])
a.execute("INSERT INTO bill_items (bill_id, item_name, pack_size, batch, expiry, quantity, rate, amount, free, mrp) VALUES (12,'LIMCEE','1*15','LC1','06/28',2,150,300,1,199)")
scan(13, "YUVIKA SURGICALS", "YS1102", D3, 1200.00, [])          # an orthotics bill whose lines are only in the reading: the plain comparison
a.execute("INSERT INTO claude_reading (bill_id, at, ok, data) VALUES (?,?,1,?)", (13, DAY, '{"items":[{"name":"KNEE CAP TYNOR (M)","qty":1,"amount":400},'
          '{"name":"L S BELT TYNOR (L)","qty":2,"amount":800}]}'))
scan(14, "YUVIKA SURGICALS", "YS1103", D3, 800.00, [("WRIST BINDER TYNOR (M)", None, 2, 400.0, 800.0, None, None)])
scan(11, "YUVIKA SURGICALS", "YS1101", D3, 1600.00, [("KNEE CAP TYNOR (L)", None, 2, 400.0, 800.0, None, None),
                                                      ("ANKLE BINDER TYNOR (M)", None, 2, 400.0, 800.0, None, None)])
a.commit()
a.close()

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

SCNT.ASSETS_DB = ADB                                            # S771's own read of the scans: the walk's made-up assets.db

PA.init(app, db, require, unit="medical", marg_token="walk-token", assets_db=ADB)
cl = app.test_client()
H = {"X-Finance-Marg": "walk-token"}
RES = []


def check(name, ok):
    RES.append((name, bool(ok)))
    print(("GREEN " if ok else "RED   ") + name)


N = {"n": 0}


def push(typ, pf, pt, rows):
    N["n"] += 1
    body = dict(type=typ, md5="%032x" % (0xabc000 + N["n"]), period_from=pf, period_to=pt, export_stamp="%s-0900%02d" % (T.strftime("%Y%m%d"), N["n"]),
                file="walk", rows=rows)
    return cl.post("/finance/purchase/api/push", json=body, headers=H)


def bill(sup, bno, d, amt):
    return dict(supplier=sup, bill_no=bno, bill_date=d, cash_p=0, credit_p=amt)


def line(sup, bno, d, item, qty, amt_p):
    return dict(supplier=sup, bill_no=bno, bill_date=d, item=item, qty=qty, rate_p=int(amt_p / qty), amount_p=amt_p, net_amount_p=amt_p, direction="PURCHASE")


P0 = "%s-01" % PREV
r1 = push("BILLWISE", P0, "%s-28" % PREV, [bill("DEEPAM PHARMA BAREILLY", "6001", "%s-10" % PREV, 100000),
                                           bill("A.A. PHARMACEUTICALS BAREILLY", "501", "%s-11" % PREV, 50000)])
r2 = push("BILLWISE", "%s-01" % M, DAY, [bill("KEDAR PHARMACEUTICAL BAREILLY", "A000230", D5, 912000),
                                        bill("YOGI MEDICALS BAREILLY", "Y-10", D5, 77700), bill("YOGI MEDICALS BAREILLY", "y-10", D5, 77700),
                                        bill("JANTA PHARMACEUTICALS BAREILLY", "21965", D2, 320544),
                                        bill("KEDAR PHARMACEUTICAL BAREILLY", "226", D3, 951000),
                                        bill("YUVIKA SURGICALS BAREILLY", "YS1101", D3, 160000),
                                        bill("YUVIKA SURGICALS BAREILLY", "YS1102", D3, 40000), bill("YUVIKA SURGICALS BAREILLY", "YS1103", D3, 40000)])
r3 = push("ITEMWISE", "%s-01" % M, DAY, [line("KEDAR PHARMACEUTICAL BAREILLY", "A000230", D5, "FLUXIC P", 30, 336000),
                                         line("KEDAR PHARMACEUTICAL BAREILLY", "A000230", D5, "MEG QCS", 50, 576000),
                                         line("JANTA PHARMACEUTICALS BAREILLY", "21965", D2, "VOLITRA APS SPRAY", 10, 267191),
                                         line("JANTA PHARMACEUTICALS BAREILLY", "21965", D2, "POWERGESIC 200 PATCH", 3, 53353),
                                         line("KEDAR PHARMACEUTICAL BAREILLY", "226", D3, "PRETOL 8", 10, 141120),
                                         line("KEDAR PHARMACEUTICAL BAREILLY", "226", D3, "C2CALZ", 20, 242880),
                                         line("KEDAR PHARMACEUTICAL BAREILLY", "226", D3, "FLUXIC P", 30, 336000),
                                         line("KEDAR PHARMACEUTICAL BAREILLY", "226", D3, "MEG QCS", 20, 231000),
                                         line("YUVIKA SURGICALS BAREILLY", "YS1101", D3, "KNEE CAP TYNOR (M)", 2, 80000),
                                         line("YUVIKA SURGICALS BAREILLY", "YS1101", D3, "ANKLE BINDER TYNOR (M)", 2, 80000),
                                         line("YUVIKA SURGICALS BAREILLY", "YS1102", D3, "KNEE CAP TYNOR (M)", 1, 40000),
                                         line("YUVIKA SURGICALS BAREILLY", "YS1103", D3, "WRIST BINDER TYNOR (M)", 1, 40000)])
check("1 the made-up bills and lines go in through the real push door", all(r.status_code == 200 for r in (r1, r2, r3)))
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row
bid = {r["bill_no"]: r["id"] for r in c.execute("SELECT id, bill_no FROM purchase_bill")}
for no, sid in (("A000230", 1), ("21965", 2), ("226", 3), ("YS1101", 11), ("YS1102", 13), ("YS1103", 14)):                   # the three pairs as reception / the matcher would hold them
    c.execute("INSERT OR REPLACE INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)",
              (bid[no], sid, "EXACT", "walk", DAY + "T09:00:00"))
c.commit()


def snap(con):
    out = {}
    for t in ("purchase_bill", "purchase_line", "purchase_scan_link"):
        rows = con.execute("SELECT * FROM %s ORDER BY 1" % t).fetchall()
        out[t] = hashlib.md5(repr([tuple(r) for r in rows]).encode()).hexdigest()
    return out


def page(month=M, extra=""):
    return cl.get("/finance/purchase/page/scans?month=%s%s" % (month, extra))


def mark(b, action, flag="", note=""):
    return cl.post("/finance/purchase/api/s781/mark", json=dict(bill=b, action=action, flag=flag, note=note))


r = page()
h = r.get_data(as_text=True)
if CONTROL:
    print("CONTROL S781 RED as it must be" if r.status_code == 200 and 'id="s781"' not in h and "Purchase bills" in h
          else "CONTROL S781 NOT RED (%s, %s)" % (r.status_code, 'id="s781"' in h))
    sys.exit(0)
check("2 the Purchase bills page opens (200) with the S781 section above the register's chips", r.status_code == 200 and h.find('id="s781"') > 0
      and h.find('id="s781"') < h.find('id="s454heads"'))
inm = c.execute("SELECT COUNT(*), SUM(amount_p) FROM purchase_bill WHERE month=?", (M,)).fetchone()
import provisional_s781 as PS  # noqa: E402
check("3 the In-Marg tile: the month's bills and their sum (the double entry once)", PA._s454_sr().rs(inm[1] - 77700) in h)
sec = h[h.find('id="s781prov"'):h.find('id="s781diff"')]
rows = {int(x): sec[sec.find('data-scan="%s"' % x):][:1500] for x in re.findall(r'data-scan="(\d+)"', sec)}
check("4 the provisional list holds the waiting scans 4-10 and 12, none of the linked ones", sorted(rows) == [4, 5, 6, 7, 8, 9, 10, 12])
l12 = sec[sec.find('id="s781L12"'):][:3000]
check("4e free goods and MRP read into bill_items columns show in their places (Free after Qty, MRP after Rate)",
      re.search(r"<th class=\"n\">Qty</th><th class=\"n\">Free</th><th class=\"n\">Rate</th><th class=\"n\">MRP</th>", l12) is not None
      and "₹199" in l12 and "Not read on this scan: discount, GST" in l12)
l10 = sec[sec.find('id="s781L10"'):][:3000]
check("4d a column the scanner reads only sometimes (MRP) shows by itself when the scan carries it; the others are named as not read",
      "<th class=\"n\">MRP</th>" in l10 and "₹199" in l10 and "Not read on this scan: free goods, discount, GST" in l10
      and "<th class=\"n\">MRP</th>" not in sec[sec.find('id="s781L4"'):sec.find('id="s781L4"') + 3000])
chipn = re.search(r'<span class="chipn">(\d+) bills in Marg</span>', h)
check("4b the In-Marg tile counts a Marg double entry once, as the register's own chip does", chipn and ("%s bills</span>" % chipn.group(1)) in h
      and inm[0] == int(chipn.group(1)) + 1)
check("4c a scan-read name is escaped everywhere (no raw <script>, no raw <b> from a scan)", "<script>alert(1)" not in h and "<b>BOLD</b>" not in h
      and "&lt;script&gt;alert(1)" in h)
check("5 scan 4 reads right (known dealer, number, date, lines add up)", "Reads right" in rows.get(4, ""))
check('6 scan 5: "Check the paper — bill number "1""', 'bill number &quot;1&quot;' in rows.get(5, "") or 'bill number "1"' in rows.get(5, ""))
check("7 scan 6 (an unknown dealer, a 2023 paper): Check the paper -- the supplier is not known", "the supplier is not known" in rows.get(6, ""))
check("8 scan 7: the misread year is named", "the year reads 2025" in rows.get(7, ""))
check("9 the provisional tile counts only the scans that read right (4, 8, 10, 12: Rs 12,740) and names the rest as not counted",
      PA._s454_sr().rs(1274000) in h and "4 more to check, not counted" in h and "4 bills · from the scans" in h)
check("9b a paper of another year shows its year in the date column", "20-May-2023" in rows.get(6, ""))
check("10 scan 4's read lines fold under '4 lines' and a field not read says so", 'aria-controls="s781L4"' in h and "4 lines" in rows.get(4, "")
      and "not read" in sec[sec.find('id="s781L4"'):sec.find('id="s781L4"') + 3000])
dsec = h[h.find('id="s781diff"'):]
def _upto_next(t):
    j = t.find('<tr data-bill="', 10)
    return t[:j] if j > 0 else t


dr = {int(x): _upto_next(dsec[dsec.find('<tr data-bill="%s"' % x):]) for x in re.findall(r'<tr data-bill="(\d+)"', dsec)}
check("11 'Where Marg differs': Janta 21965 (the total, a line not in Marg), Kedar 226 (the date), Yuvika YS1101 (an orthotics size) -- "
      "the agreeing bill A000230 not listed", sorted(dr) == sorted([bid["21965"], bid["226"], bid["YS1101"], bid["YS1102"], bid["YS1103"]]))
y = dr.get(bid["YS1101"], "")
check("11b the orthotics bill shows S771's line check: the size difference named, its own per-line taps; the agreeing line says so",
      "Size: the bill says L, Marg has M" in y and "1 line differs" in y and 'data-a="amir" onclick="s781l(this)"' in y
      and 'table class="items s771"' in y and ">agrees<" in y and "line buttons above send each line to Amir" in y and "Whole bill: Marg is right" not in y)
y2 = dr.get(bid["YS1102"], "")
check("11d an orthotics bill with lines only in the reading: the plain comparison (L S BELT not in Marg), not an empty S771 table",
      "not in Marg" in y2 and 'table class="items s771"' not in y2 and "L S BELT TYNOR (L)" in y2)
y3 = dr.get(bid["YS1103"], "")
check("11e an orthotics quantity line + its total: the bill-level 'Amir fixes Marg' is withheld (one job, from the line), the line's own button offered",
      "Quantity: the bill says 2, Marg has 1" in y3 and "line buttons above send each line to Amir" in y3 and 'data-a="amir" onclick="s781l(this)"' in y3
      and mark(bid["YS1103"], "amir").status_code == 409)
j = dr.get(bid["21965"], "")
check("12 Janta: Marg differs by Rs 1,245; VOLINI GEL 30G marked not in Marg; the scan loads inline from the s738 door",
      "Marg differs by" in j and "1,245" in j and "not in Marg" in j and "/api/s738/scan/2" in j)
k = dr.get(bid["226"], "")
check("13 Kedar 226: Marg's date is not the paper's; the difference named with both dates", "Marg&#x27;s date is not the paper&#x27;s" in k
      or "Marg's date is not the paper's" in k)
check("14 the four taps on a differing bill for the doctor", all(x in j for x in ("Amir fixes Marg", "Marg is right", "Raise a purchase return", "Flag something else")))
before = snap(c)
rel = PS.reliability(c, [PREV, M])
check("15 how reliable: the month's linked bills counted strict and by the rules", 'How reliable the scans are' in h and rel and rel[-1][0] == M and rel[-1][1] >= 1)


SCNT.ensure_s771(c)
_ac = SCNT._acon()
yl = [l for l in SCNT.one_bill(c, _ac, dict(c.execute("SELECT * FROM purchase_bill WHERE id=?", (bid["YS1101"],)).fetchone()))["lines"] if l["kind"]]
_ac.close()
import html as _html  # noqa: E402
ks = [_html.unescape(k) for k in re.findall(r'data-b="%d" data-k="([^"]*)" data-a="amir"' % bid["YS1101"], y)]
check("11c0 the key the page's line button carries is S771's own key for that line", ks == [yl[0]["key"]])
ok_, res_, code_ = SCNT.mark(c, bid["YS1101"], ks[0] if ks else "", "amir", "manoj")
hy = page().get_data(as_text=True)
yy = _upto_next(hy[hy.find('<tr data-bill="%d"' % bid["YS1101"]):])
n771 = c.execute("SELECT COUNT(*) FROM amir_job WHERE created_by='S771'").fetchone()[0]
check("11c the line tap (S771's door, the page's key): exactly one S771 job; the line shows 'with Amir' and its Undo; the bill reads 'Lines with Amir'",
      ok_ and n771 == 1 and "with Amir" in yy and 'data-a="undo"' in yy and "Lines with Amir" in yy)
SCNT.mark(c, bid["YS1101"], yl[0]["key"], "undo", "manoj")
SCNT.mark(c, bid["YS1101"], yl[0]["key"], "clear", "manoj")
hc = page().get_data(as_text=True)
dc = hc[hc.find('id="s781diff"'):]
check("11f a bill whose S771 lines are all cleared leaves the list for 'Cleared by you', its line Undo still there",
      '<tr data-bill="%d"' % bid["YS1101"] not in dc and "its lines, each cleared by you" in dc and 'data-b="%d"' % bid["YS1101"] in dc)
SCNT.mark(c, bid["YS1101"], yl[0]["key"], "undo", "manoj")
r = mark(bid["226"], "amir")
jb = c.execute("SELECT key, text_hi, sub_hi, created_by, done_at FROM amir_job WHERE created_by='S781'").fetchall()
check("16 Amir fixes Marg (Kedar 226): one job on Amir's card, in Hindi, naming both dates", r.status_code == 200 and len(jb) == 1
      and "tareekh" in jb[0]["text_hi"] and "Marg ki entry theek kijiye" in jb[0]["text_hi"] and "Dr sahab ne scan se milaya" in jb[0]["sub_hi"])
check("17 a second answer on the same bill is refused (409) and adds no job", mark(bid["226"], "clear").status_code == 409
      and c.execute("SELECT COUNT(*) FROM amir_job WHERE created_by='S781'").fetchone()[0] == 1)
h2 = page().get_data(as_text=True)
check("18 the page shows the answer on the row ('with Amir') and an Undo", "with Amir" in h2 and "s781(%d,'undo')" % bid["226"] in h2)
r = mark(bid["226"], "undo")
check("19 Undo: the mark and the job not yet done both leave", r.status_code == 200 and not c.execute("SELECT 1 FROM purchase_s781_mark").fetchone()
      and not c.execute("SELECT 1 FROM amir_job WHERE created_by='S781'").fetchone())
check("20 Flag 'Other' with no note is refused (400)", mark(bid["21965"], "flag", "other", "").status_code == 400)
r = mark(bid["21965"], "flag", "short", "")
check("21 Flag 'Short supply' is kept and shown on the row", r.status_code == 200 and "flagged: Short supply" in page().get_data(as_text=True))
mark(bid["21965"], "undo")
check("22a the page's 'Raise a purchase return' sends the note box's text (the JS reads it for every action)",
      "var i=document.getElementById('s781n'+id);var note=i?i.value:''" in h and "s781(%d,'return')" % bid["21965"] in h)
r = mark(bid["21965"], "return", "", "3 tubes leaking")
jr = c.execute("SELECT text_hi FROM amir_job WHERE created_by='S781'").fetchone()
check("22 Raise a purchase return: one job on Amir's card with the note", r.status_code == 200 and jr and "PURCHASE RETURN" in jr[0] and "3 tubes leaking" in jr[0])
mark(bid["21965"], "undo")
r = mark(bid["21965"], "clear")
h3 = page().get_data(as_text=True)
d3 = h3[h3.find('id="s781diff"'):]
check("23 Marg is right -- clear: the bill leaves 'Where Marg differs'", r.status_code == 200 and '<tr data-bill="%d"' % bid["21965"] not in d3
      and '<tr data-bill="%d"' % bid["226"] in d3)
check("23b ...and stays reachable under 'Cleared by you' with its Undo", "Cleared by you (Marg is right): 1" in d3 and "s781(%d,'undo')" % bid["21965"] in d3)
r = mark(bid["21965"], "undo")
check("23c Undo after clear brings the bill back", r.status_code == 200 and '<tr data-bill="%d"' % bid["21965"] in page().get_data(as_text=True))
mark(bid["21965"], "clear")
check("24 a tap on a bill that does not differ is refused (409)", mark(bid["A000230"], "amir").status_code == 409)
check("25 an unknown action is refused (400); no bill (400)", mark(bid["226"], "stock").status_code == 400 and mark(0, "amir").status_code == 400)
after = snap(c)
check("26 NEVER into stock: purchase_bill, purchase_line and the scan links are byte-for-byte as before the taps", before == after)
check("27 nothing written to a stock table by S781 (no table with 'stock' in its name changed)",
      all(c.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0] == 0 for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%stock%'")))
ROLE.update(user="shavez", roles=["maker"])
hv = page().get_data(as_text=True)
check("28 a non-doctor sees the tiles and the provisional list, not 'Where Marg differs' nor the paper links",
      'id="s781prov"' in hv and 'id="s781diff"' not in hv and "Open the paper" not in hv)
check("29 the door refuses a non-doctor (403)", mark(bid["226"], "amir").status_code == 403)
ROLE.update(user="manoj", roles=["checker"])
hl = page(extra="&legacy=1").get_data(as_text=True)
check("30 the old tables (?legacy=1) are untouched by S781", 'id="s781"' not in hl)
push("BILLWISE", "%s-01" % M, DAY, [bill("KEDAR PHARMACEUTICAL BAREILLY", "A000230", D5, 912000),   # Marg's next export: the month again, + 6678
                                    bill("YUVIKA SURGICALS BAREILLY", "YS1101", D3, 160000),
                                    bill("YOGI MEDICALS BAREILLY", "Y-10", D5, 77700), bill("YOGI MEDICALS BAREILLY", "y-10", D5, 77700),
                                    bill("JANTA PHARMACEUTICALS BAREILLY", "21965", D2, 320544), bill("KEDAR PHARMACEUTICAL BAREILLY", "226", D3, 951000),
                                    bill("DEEPAM PHARMA BAREILLY", "6678", D7, 894000)])
b4 = c.execute("SELECT id FROM purchase_bill WHERE bill_no='6678'").fetchone()
c.execute("INSERT OR REPLACE INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)", (b4[0], 4, "EXACT", "walk", DAY))
c.commit()
h4 = page().get_data(as_text=True)
s4 = h4[h4.find('id="s781prov"'):h4.find('id="s781diff"')]
check("31 Marg's bill arrives for scan 4: it leaves the provisional list by itself", 'data-scan="4"' not in s4 and 'data-scan="8"' in s4)
real = PS.summary_html
PS.summary_html = lambda *a_, **k_: 1 / 0
hb = page().get_data(as_text=True)
PS.summary_html = real
check("32 fail-soft: with S781 failing the page is 200 and as before S781", 'id="s781"' not in hb and 'id="s454heads"' in hb)
mark(bid["226"], "amir")
n = PS.lift_all(c)
check("33 the undo's lift: the open S781 job leaves Amir's card", n == 1 and not c.execute("SELECT 1 FROM amir_job WHERE created_by='S781' AND done_at IS NULL").fetchone())
with app.test_request_context():
    pick = PS.dealer_of(c, PA._s454_sr().Ctx(c), dict(id=999, vendor="SHREE BALAJI MEDICOS AGENCY"), known=["BALAJI", "SHREE BALAJI MEDICOS"])
check("35 the dealer shown is the longest matching known name, never the first", pick == ("SHREE BALAJI MEDICOS", True))
fake = dict(supplier_ok=1, billno_ok=1, date_ok=0, total_ok=1, bill_id=bid["A000230"],
            detail='{"scan":{"vendor":"KEDAR PHARMACEUTICAL","bill_no":"A000230","date":"2025-%s","total_p":912000},'
                   '"marg":{"supplier":"KEDAR PHARMACEUTICAL","bill_no":"A000230","date":"%s","total_p":912000}}' % (D5[5:], D5))
st, ru = PS.rules_row(c, PA._s454_sr().Ctx(c), fake)
check("34 the rules: a misread year is right by the rules, not by the strict count", st is False and ru is True)
c.close()
red = [n_ for n_, ok in RES if not ok]
print("WALK S781 GREEN" if not red else "WALK S781 RED (%d of %d): %s" % (len(red), len(RES), "; ".join(red)))
