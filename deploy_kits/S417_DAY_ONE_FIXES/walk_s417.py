#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s417.py -- kit S417_DAY_ONE_FIXES (F-636). THE REAL finance_app.py (a copy of /root/finance carrying the kit's seven files) over
SCRATCH COPIES of finance.db, never the live one. Own rows by key (W417 …), never by count. Every part runs the same probe on the box as
it is (--old) as its negative control.

  1  the stock in the order's own unit: crafted items (a 10-strip with 124 units, a syrup, a '1*1' item of unknown pack, an orthotic)
     on /page/orders, /page/staff, the Purchase orders screen (the engine's plan, the day's proposal, the orthotic line) and the
     owner's section; the WhatsApp text byte-identical.
  2  the card shelf: a fixture Drive (two months of decrypted card statements in HDFC's two layouts and ICICI's, a re-issued ICICI
     card, the locked originals, one locked original with no decrypted twin, All_Transactions.xlsx in the cards root) -- the cells,
     the tails, pack row 4, 'duplicate of decrypted', 'decrypted copy not yet made', the Excel never unplaced.
  3  the Yes Bank tile: no event -> the answer byte-identical; a crafted provisional NEFT -> the line and the headline; a crafted
     confirming statement -> the line gone and nothing counted twice; an unconfirmed SMS event, a rejected one, one carrying
     S407's bank line -> never on the tile.
  4  the name search: crafted JIARDIANCE / GRDIANS names found with their fields, a GUARDIAN decoy not.
  5  the real shelf (a scratch copy as the box is): seed_s417 re-reads the real card files -- every decrypted statement dated, the
     three card slots learn their numbers, the months' cells and pack row 4 fill, the Excel leaves 'which account?'; the bank rows
     and the bank tables unchanged.

  --app NEW --old OLD --db PATH
"""
import argparse
import datetime as dt
import json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
for k in ("--app", "--old", "--db"):
    ap.add_argument(k, required=True)
a = ap.parse_args()
assert "walk" in a.db or "scratch" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
n, fails = 0, []
W = os.path.dirname(os.path.abspath(a.db))
KIT = os.path.dirname(os.path.abspath(__file__))
TODAY = dt.date.today()
ORDER_DAY = "2099-03-02"
STUB = os.path.join(W, "stub417")


def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:700] + "]") if got is not None else ""))
    if not cond:
        fails.append(label)


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def text_pdf(path, lines):
    """A minimal text PDF (Courier) -- pdftotext -layout reads it back line for line (S408's fixture writer)."""
    pages = [lines[i:i + 55] for i in range(0, len(lines), 55)] or [[]]
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", None, b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>"]
    kids = []
    for pg in pages:
        content = b"BT /F1 10 Tf 12 TL 40 800 Td " + b" ".join(b"(" + ln.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").encode("latin-1", "replace") + b") Tj T*" for ln in pg) + b" ET"
        objs.append(b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")
        c = len(objs)
        objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>" % c)
        kids.append(len(objs))
    objs[1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (b" ".join(b"%d 0 R" % k for k in kids), len(kids))
    out = bytearray(b"%PDF-1.4\n")
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    x = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offs)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)
    with open(path, "wb") as fh:
        fh.write(bytes(out))


def locked_pdf(path, lines):
    """The same, password-locked with a random password made now (pypdf, the venv) -- pdftotext refuses it as it refuses the bank's."""
    from pypdf import PdfReader, PdfWriter           # noqa: PLC0415
    tmp = path + ".plain"
    text_pdf(tmp, lines)
    w = PdfWriter(clone_from=PdfReader(tmp))
    w.encrypt(secrets.token_hex(8), algorithm="AES-256")
    with open(path, "wb") as fh:
        w.write(fh)
    os.remove(tmp)


# ============================================================================ the fixtures
REAL = a.db + ".real"
copydb(a.db, REAL)                                   # 5: the real shelf, as the box is, before any fixture
db = sqlite3.connect(a.db)
db.row_factory = sqlite3.Row
D = lambda k: (TODAY - dt.timedelta(days=k)).isoformat()      # noqa: E731
NOW = dt.datetime.now().replace(microsecond=0).isoformat()
for t, col in (("purchase_bill", "bill_no"), ("purchase_line", "bill_no"), ("sale_line_item", "bill_no")):
    db.execute("DELETE FROM %s WHERE %s LIKE 'W417%%'" % (t, col))
db.execute("DELETE FROM stock_snapshot WHERE item LIKE 'W417%'")
db.execute("DELETE FROM purchase_export WHERE md5 LIKE 'w417%'")
db.execute("DELETE FROM stock_item_section WHERE item LIKE 'W417%'")
db.execute("DELETE FROM stock_count_item WHERE item LIKE 'W417%'")
db.execute("DELETE FROM porder_keep WHERE item LIKE 'W417%'")
db.execute("DELETE FROM order_proposal WHERE supplier_norm LIKE 'W417%'")
db.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES ('w417exp','ITEMWISE','w417','2026-01-01','2099-12-31','w417',?,0,0)", (NOW,))
db.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES ('w417bw','BILLWISE','w417','2026-01-01','2099-12-31','w417',?,0,0)", (NOW,))
SUP = "W417 STRIP CO"
for i, k in enumerate((40, 25, 10), 1):
    db.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, cash_p, credit_p, amount_p, bw_md5, date_src) VALUES (?,?,?,?,?,0,0,?,?,?)",
               (SUP, SUP, "W417B%02d" % i, D(k), D(k)[:7], 900000, "w417bw", "BILLWISE"))
db.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, cash_p, credit_p, amount_p, bw_md5, date_src) VALUES (?,?,?,?,?,0,0,?,?,?)",
           ("W417 PHARMA", "W417 PHARMA", "W417N1", D(3), D(3)[:7], 50000, "w417bw", "BILLWISE"))
ITEMS = [  # item, packing, pack size, stock units, rate_p per pack, sale qty_raw per day
    ("W417 STRIP TEN", "1*10", 10, 124, 30000, "5:0"),
    ("W417 SYRUP", "100ML", 1, 3, 25000, "1"),
    ("W417 PLAIN", "1*1", 1, 5, 30000, "2"),
]
AS_ON = max({r[0] for r in db.execute("SELECT DISTINCT as_on FROM stock_snapshot")}, key=lambda s: (s[6:], s[3:5], s[:2]))
eid = db.execute("SELECT id FROM day_entry WHERE unit='medical' ORDER BY business_date DESC LIMIT 1").fetchone()[0]
sn = 0
for j, (item, packing, size, qty, rate, raw) in enumerate(ITEMS, 1):
    db.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, qty, free, rate_p, amount_p, net_rate_p, net_amount_p, loose_qty, purchase_rate_p, direction, source_md5, line_type) "
               "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (SUP, "W417L%02d" % j, D(10), D(10)[:7], item, packing, 10, 0, rate, 10 * rate, rate // size, 10 * rate, 10 * size, rate, "PURCHASE", "w417exp", "ITEMWISE"))
    db.execute("INSERT INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES (?,?,?,?,?,?,?)", (AS_ON, item, qty, packing, size, NOW, "walk"))
    for k in range(1, 28):
        sn += 1
        db.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, pack, qty_raw, amount_p) VALUES (?,'medical',?,?,0,1,?,?,?,?,1000)",
                   (eid, D(k), "W417S%04d" % sn, item, item, packing, raw))
# the orthotic: on the section map, counted 3 on the count, the owner keeps 5 -> short 2, shelf 3 pieces
CID = db.execute("SELECT id FROM stock_count WHERE unit='medical' AND status='submitted' AND id NOT IN (SELECT count_id FROM stock_count_part) ORDER BY id LIMIT 1").fetchone()[0]
db.execute("INSERT INTO stock_item_section (item_key, item, section, source, by_user, at) VALUES (?,?,?,?,?,?)", ("W417 ORTHO BELT", "W417 ORTHO BELT", "Orthotics", "walk", "walk", NOW))
db.execute("INSERT INTO stock_count_item (count_id, item, packing, pack_size, marg_qty, counted_qty, counted_by, entered_by, at) VALUES (?,?,?,?,?,?,?,?,?)", (CID, "W417 ORTHO BELT", "1*1", 1, 3, 3, "walk", "walk", NOW))
db.execute("INSERT INTO porder_keep (item, keep, source, set_by, set_at) VALUES (?,?,?,?,?)", ("W417 ORTHO BELT", 5, "owner", "walk", NOW))
# the day's proposal (order_rules' table) for a day of our own
PROP_LINES = [dict(item="W417 STRIP TEN", on_hand=124, qty=20, unit="strip", pack_size=10, packing="1*10", rate_p=30000, per_day=50.0, cover_after=None, value_p=600000, confirm=False, why=[]),
              dict(item="W417 PLAIN", on_hand=5, qty=10, unit="unit", pack_size=1, packing="1*1", rate_p=30000, per_day=2.0, cover_after=None, value_p=300000, confirm=False, why=[])]
db.execute("INSERT INTO order_proposal (day, supplier_norm, vendor, kind, status, lines, total_p, reason, prepared_at) VALUES (?,?,?,?,?,?,?,?,?)",
           (ORDER_DAY, SUP, SUP, "fixed", "open", json.dumps(PROP_LINES), 900000, "walk", NOW))
# 4: the name search's own names (and a decoy)
for item, qty in (("W417 JIARDIANCE 10", 25), ("W417 GRDIANS 25 MG", 0), ("W417 GUARDIAN GEL", 4)):
    db.execute("INSERT INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES (?,?,?,?,?,?,?)", (AS_ON, item, qty, "1*10", 10, NOW, "walk"))
db.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, qty, free, rate_p, amount_p, net_rate_p, net_amount_p, loose_qty, purchase_rate_p, direction, source_md5, line_type) "
           "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ("W417 PHARMA", "W417N1", D(3), D(3)[:7], "W417 JIARDIANCE 10", "1*10", 2, 0, 25000, 50000, 2500, 50000, 20, 25000, "PURCHASE", "w417exp", "ITEMWISE"))
db.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, pack, qty_raw, amount_p) VALUES (?,'medical',?,?,0,1,?,?,?,?,1000)",
           (eid, D(2), "W417SJ", "W417 JIARDIANCE 10", "W417 JIARDIANCE 10", "1*10", "1:0"))
db.commit()
db.close()
copydb(a.db, a.db + ".old")

# 2: the shelf of our own -- the card files and the Excel cleared on this copy, the card slots' tails with them (declared)
P2 = a.db + ".p2"
copydb(a.db, P2)
c2 = sqlite3.connect(P2)
c2.execute("DELETE FROM stmt_file WHERE folder IN ('cards','decrypted','all_txn')")
c2.execute("UPDATE stmt_slot SET ident_tail=NULL, owner_set=NULL WHERE kind='card'")
c2.commit()
c2.close()
copydb(P2, P2 + ".old")
shutil.rmtree(STUB, ignore_errors=True)
for d in ("bank", "cards/ICICI Amazon Pay", "cards/HDFC Business Regalia", "cards/ICICI Coral", "decrypted/ICICI Amazon Pay", "decrypted/HDFC Business Regalia", "decrypted/ICICI Coral"):
    os.makedirs(os.path.join(STUB, d), exist_ok=True)
CARDS = {  # (card folder, file name): lines -- two months each; the Amazon card re-issued between them (…1104 -> …1112)
    ("ICICI Amazon Pay", "2026-07-13_W417_amazon.pdf"): ["CREDIT CARD STATEMENT", "MR W417 TEST", "STATEMENT DATE           All communications are sent to you", "July 12, 2026",
                                                         "Statement period : June 13, 2026 to July 12, 2026", "SPENDS OVERVIEW", "4315XXXXXXXX1104", "maintain sufficient funds in your linked savings account XX7777", "Amazon Pay ICICI Bank Credit Card"],
    ("ICICI Amazon Pay", "2026-08-13_W417_amazon.pdf"): ["CREDIT CARD STATEMENT", "MR W417 TEST", "STATEMENT DATE           All communications are sent to you", "August 12, 2026",
                                                         "Statement period : July 13, 2026 to August 12, 2026", "SPENDS OVERVIEW", "4315XXXXXXXX1112", "maintain sufficient funds in your linked savings account XX7777", "Amazon Pay ICICI Bank Credit Card"],
    ("HDFC Business Regalia", "2026-07-16_W417_hdfc.pdf"): ["Visa Business Regalia Credit Card Statement", "HDFC Bank Credit Cards", "Name : W417 TEST", "Card No: 4572 00XX XXXX 6011", "Statement Date:15/07/2026"],
    ("HDFC Business Regalia", "2026-08-16_W417_hdfc.pdf"): ["Business Regalia Credit Card Statement", "HDFC Bank Credit Cards", "W417 TEST              Credit Card No.        45720000XXXXXX6011",
                                                            "                       Statement Date         15 Aug, 2026", "                       Billing Period         16 Jul, 2026 - 15 Aug, 2026"],
    ("ICICI Coral", "2026-07-03_W417_coral.pdf"): ["CREDIT CARD STATEMENT", "MR W417 TEST", "STATEMENT DATE", "July 2, 2026", "Statement period : June 3, 2026 to July 2, 2026", "5241XXXXXXXX7001", "ICICI Bank Coral Credit Card"],
    ("ICICI Coral", "2026-08-03_W417_coral.pdf"): ["CREDIT CARD STATEMENT", "MR W417 TEST", "STATEMENT DATE", "August 2, 2026", "Statement period : July 3, 2026 to August 2, 2026", "5241XXXXXXXX7001", "ICICI Bank Coral Credit Card"],
}
_t = __import__("time").time()
for (folder, name), lines in CARDS.items():
    text_pdf(os.path.join(STUB, "decrypted", folder, name), lines)
    locked_pdf(os.path.join(STUB, "cards", folder, name), lines)
    os.utime(os.path.join(STUB, "cards", folder, name), (_t - 9 * 86400, _t - 9 * 86400))
# September's Amazon original has NO decrypted twin (the owner's script has not run yet)
locked_pdf(os.path.join(STUB, "cards", "ICICI Amazon Pay", "2026-09-13_W417_amazon.pdf"), CARDS[("ICICI Amazon Pay", "2026-08-13_W417_amazon.pdf")])
os.utime(os.path.join(STUB, "cards", "ICICI Amazon Pay", "2026-09-13_W417_amazon.pdf"), (_t - 5 * 86400, _t - 5 * 86400))
from openpyxl import Workbook  # noqa: E402
wb = Workbook()
wb.active.append(["Date", "Card", "Amount"])
wb.save(os.path.join(STUB, "cards", "All_Transactions.xlsx"))
OLDX = os.path.join(W, "w417_old_all_transactions.xlsx")
shutil.copy(os.path.join(STUB, "cards", "All_Transactions.xlsx"), OLDX)
for dbp in (P2, P2 + ".old"):                        # the row as the box holds it today: the Excel in the cards root, 'which account?'
    c2 = sqlite3.connect(dbp)
    c2.execute("INSERT INTO stmt_file (drive_id, name, mtime, size, folder, subfolder, sha256, fetched_at, local_path, bank, holder, tail, kind, note, identified_at) "
               "VALUES ('w417-old-xlsx','All_Transactions.xlsx','2026-09-20T11:41:03',1,'cards','','w417',?,?,'','','','','not a readable PDF',?)", (NOW, OLDX, NOW))
    c2.commit()
    c2.close()

# 3: the Yes Bank tile on a copy whose NEFT events are cleared (declared) -- every event below is our own
P3 = a.db + ".p3"
copydb(a.db, P3)
c3 = sqlite3.connect(P3)
c3.execute("DELETE FROM purchase_neft_event")
c3.commit()
c3.close()
copydb(P3, P3 + ".old")
print("-- scratch copies made: part 1/4 (%d sale rows, 3 items, an orthotic, a proposal on %s, 3 names), part 2 (a fixture Drive of %d files), part 3 (no NEFT event), part 5 (the real shelf)"
      % (sn + 1, ORDER_DAY, sum(len(f) for _r, _d, f in os.walk(STUB))))

HEAD = r'''
import json, os, sys, sqlite3, re, datetime as dt
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
NEW = os.environ["MODE"] == "new"
import finance_app as fa
c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
def G(u, p):
    r = c.get(p, headers=H(u)); j = r.get_json(silent=True)
    return [r.status_code, j if j is not None else r.get_data(as_text=True)]
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
out = {}
'''

PROBE1 = HEAD + r'''
def row(html, item):
    m = re.search(r"<tr><td>" + re.escape(item) + r"(?:(?!</tr>).)*</tr>", html or "", re.S)
    return m.group(0) if m else ""
def cells(tr):
    return [re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
po = G("manoj", "/finance/purchase/page/orders"); st = G("manoj", "/finance/purchase/page/staff")
out["orders_code"], out["staff_code"] = po[0], st[0]
for it in ("W417 STRIP TEN", "W417 SYRUP", "W417 PLAIN"):
    out["orders:" + it] = cells(row(po[1], it))[:3]
    out["staff:" + it] = cells(row(st[1], it))[:3]
s = G("darpan", "/finance/porders/api/state")[1]
out["state_ok"] = bool(s.get("ok"))
v = next((x for x in (s.get("meds") or {}).get("plan", {}).get("vendors", []) if x["vendor"] == "W417 STRIP CO"), None)
out["plan_lines"] = {l["item"]: [l.get("on_hand"), l.get("stock_text"), l.get("qty"), l.get("unit")] for l in (v or {}).get("lines", [])}
p = next((x for x in (s.get("today") or {}).get("proposals", []) if x.get("supplier_norm") == "W417 STRIP CO"), None)
out["proposal_lines"] = {l["item"]: [l.get("on_hand"), l.get("stock_text"), l.get("qty")] for l in (p or {}).get("lines", [])}
ol = next((x for x in (s.get("ortho") or {}).get("lines", []) if x["item"] == "W417 ORTHO BELT"), None)
out["ortho_line"] = [ol.get("shelf"), ol.get("shelf_text"), ol.get("short")] if ol else None
oa = next((x for x in (s.get("all") or []) if x["item"] == "W417 ORTHO BELT"), None)
out["ortho_all"] = [oa.get("shelf"), oa.get("shelf_text")] if oa else None
import purchase_app as pa
out["wa"] = pa._wa_text([dict(item="W417 STRIP TEN", qty=20, packing="1*10", pack_size=10), dict(item="W417 SYRUP", qty=4, packing="100ML", pack_size=1)])
html = open(os.path.join(APP, "porders.html"), encoding="utf-8").read()
own = open(os.path.join(APP, "finance_ui", "finance_approvals.html"), encoding="utf-8").read()
out["html"] = dict(proposal="esc(l.stock_text!=null?l.stock_text:l.on_hand)" in html, shelf="esc(l.shelf_text||l.shelf)" in html,
                   owner="esc(l.shelf_text||l.shelf)" in own, bare_on_hand=html.count("'+l.on_hand+'"))
if NEW:
    out["unit_cases"] = [pa.stock_text(124, 10, "1*10"), pa.stock_text(3, 1, "", ortho=True), pa.stock_text(5, 1, "1*1"), pa.stock_text(3, 1, "100ML"),
                         pa.stock_text(7, 1, "1*15"), pa.stock_text(-13, 10, "1*10"), pa.stock_text(20, 10, "1*10"), pa.stock_text(0, None, "")]
print("JSON:" + json.dumps(out, default=str))
'''

PROBE2 = HEAD + r'''
import stmt_shelf, packs
new, seen, errors = stmt_shelf.fetch(db)
out["fetch"] = [new, errors]
out["process"] = packs.process_inbox(db)
F = {r["name"] + "|" + r["folder"]: r for r in q("SELECT f.*, s.key AS slot_key FROM stmt_file f LEFT JOIN stmt_slot s ON s.id=f.slot_id WHERE f.name LIKE '%W417%' OR f.name LIKE 'All_Transactions%'")}
out["files"] = {k: [v["slot_key"], v["ident_how"], v["tail"], v["period_from"], v["period_to"], v["read_status"], v["matched_status"], v["folder"]] for k, v in F.items()}
out["xlsx"] = [[r["folder"], r["slot_id"], r["read_status"], r["drive_id"][-12:]] for r in q("SELECT * FROM stmt_file WHERE LOWER(name) LIKE '%.xlsx'")]
out["unplaced"] = [[u["name"], u["folder"]] for u in packs.unplaced(db)]
out["tails"] = {r["key"]: r["ident_tail"] for r in q("SELECT key, ident_tail FROM stmt_slot WHERE kind='card'")}
out["cells"] = {m: {x["slot"]: [x["state"], (x["file"] or {}).get("name"), (x["file"] or {}).get("period_to"), x.get("tail"), x.get("no_decrypted"), x["twin_missing"]]
                    for x in packs.cells(db, m) if x["kind"] == "card"} for m in ("2026-07", "2026-08", "2026-09")}
out["rows"] = {}
for m in ("2026-08", "2026-09"):
    rows, _att = packs.pack_rows(db, m, light=True)
    out["rows"][m] = {r["key"]: [r["status"], r["why"]] for r in rows if r["key"].startswith("card:") or r["key"] == "cards"}
print("JSON:" + json.dumps(out, default=str))
'''

PROBE3 = HEAD + r'''
import sanjeevni_approvals as sa
def tile():
    r = G("manoj", "/finance/sanjeevni/api/bank?month=2026-09"); j = r[1] if isinstance(r[1], dict) else {}
    return r[0], j
def ins_event(month, kind, source, amt, d, confirmed=True, line=None):
    cur = db.execute("INSERT INTO purchase_neft_event (month, kind, source, amount_p, sms_date, bank_line_id, created_at, created_by, confirmed_by, confirmed_at, note) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                     (month, kind, source, amt, d, line, dt.datetime.now().replace(microsecond=0).isoformat(), "w417", "w417" if confirmed else None, None, "walk S417"))
    db.commit(); return cur.lastrowid
code, j0 = tile()
out["t0"] = [code, json.dumps(j0, sort_keys=True)]
yp = sa.yesbank_position(db)
as_on = yp["as_on"] or "2026-09-01"
d_ev = (dt.date.fromisoformat(as_on) + dt.timedelta(days=4)).isoformat()
out["yp0"] = [yp["holds_p"], yp["base_p"], as_on, d_ev]
mine = ins_event("2099-02", "provisional", "owner", 1234500, d_ev)
ins_event("2099-03", "provisional", "sms", 777700, d_ev, confirmed=False)
ins_event("2099-04", "rejected", "owner", 888800, d_ev)
ins_event("2099-05", "provisional", "owner", 55500, d_ev, line=999999)
code, j1 = tile()
y1 = j1.get("yesbank") or {}
out["t1"] = [code, y1.get("holds"), y1.get("incl_provisional"), [[p.get("id"), p.get("amount"), p.get("text")] for p in (y1.get("provisional") or [])], y1.get("before_provisional"), y1.get("provisional_total")]
out["t1_expect"] = [sa.rs(max(yp["holds_p"] - 1234500, 0)), sa.rs(max(yp["holds_p"], 0)), mine]
# the statement confirms it: a NEFT debit of the same amount in the loaded lines -> the line goes, nothing else moves
db.execute("INSERT INTO bank_statement_line (account_ref, txn_date, description, reference, withdrawal_p, deposit_p, balance_p, is_cash_deposit, source_file, ingested_at) VALUES ('W417',?,?,?,?,0,NULL,0,'walk S417',?)",
           ((dt.date.fromisoformat(d_ev) + dt.timedelta(days=1)).isoformat(), "NEFT W417 SUPPLIER TEST", "W417REF", 1234500, dt.datetime.now().isoformat()))
db.commit()
code, j2 = tile()
y2 = j2.get("yesbank") or {}
out["t2"] = [code, y2.get("holds"), y2.get("incl_provisional"), [p.get("id") for p in (y2.get("provisional") or [])]]
out["t2_expect"] = sa.rs(max(sa.yesbank_position(db)["holds_p"], 0))
# a statement arrives whose period covers the NEFT and closes lower by it -> the headline equals the provisional headline (not twice)
db.execute("INSERT INTO bank_statement_period (account_ref, period_from, period_to, opening_p, closing_p, source_file, ingested_at) VALUES ('W417',?,?,?,?,'walk S417',?)",
           ((dt.date.fromisoformat(as_on) + dt.timedelta(days=1)).isoformat(), (dt.date.fromisoformat(d_ev) + dt.timedelta(days=2)).isoformat(), yp["base_p"], yp["base_p"] - 1234500, dt.datetime.now().isoformat()))
db.commit()
code, j3 = tile()
y3 = j3.get("yesbank") or {}
out["t3"] = [code, y3.get("holds"), y3.get("incl_provisional"), y3.get("base")]
own = open(os.path.join(APP, "finance_ui", "finance_approvals.html"), encoding="utf-8").read()
out["page"] = ["provisional NEFT (awaiting statement)" in own, "incl. provisional" in own, "(yb.provisional||[]).map(" in own]
print("JSON:" + json.dumps(out, default=str))
'''

PROBE5 = HEAD + r'''
import packs
def snap():
    s = {}
    s["decrypted"] = q("SELECT COUNT(*) AS n, SUM(CASE WHEN read_status='read' AND period_to IS NOT NULL THEN 1 ELSE 0 END) AS r FROM stmt_file WHERE folder='decrypted'")[0]
    s["originals"] = q("SELECT COUNT(*) AS n, SUM(CASE WHEN read_status='duplicate of decrypted' THEN 1 ELSE 0 END) AS dup FROM stmt_file WHERE folder='cards'")[0]
    s["twins_by_name"] = q("SELECT COUNT(*) AS n FROM stmt_file o WHERE o.folder='cards' AND EXISTS (SELECT 1 FROM stmt_file d WHERE d.folder='decrypted' AND LOWER(d.name)=LOWER(o.name) AND COALESCE(d.subfolder,'')=COALESCE(o.subfolder,''))")[0]["n"]
    s["tails"] = {r["key"]: len([t for t in (r["ident_tail"] or "").split(",") if t]) for r in q("SELECT key, ident_tail FROM stmt_slot WHERE kind='card'")}
    s["cells_aug"] = {x["slot"]: x["state"] for x in packs.cells(db, "2026-08") if x["kind"] == "card"}
    rows, _a = packs.pack_rows(db, "2026-08", light=True)
    s["rows_aug"] = {r["key"]: r["status"] for r in rows if r["key"].startswith("card:") or r["key"] == "cards"}
    s["unplaced_xlsx"] = [u["name"] for u in packs.unplaced(db) if str(u["name"]).lower().endswith(".xlsx")]
    s["xlsx_rows"] = [[r["folder"], r["slot_id"]] for r in q("SELECT folder, slot_id FROM stmt_file WHERE LOWER(name) LIKE '%.xls%' ORDER BY id")]
    s["bank_rows"] = [[r["read_status"], r["n"]] for r in q("SELECT COALESCE(read_status,'-') AS read_status, COUNT(*) AS n FROM stmt_file WHERE folder='bank' GROUP BY 1 ORDER BY 1")]
    s["bank_tables"] = [q("SELECT COUNT(*) AS n FROM %s" % t)[0]["n"] for t in ("icici_statement_line", "icici_statement_period", "bank_statement_line", "bank_statement_period")]
    s["bank_slot_tails"] = [[r["key"], r["ident_tail"]] for r in q("SELECT key, ident_tail FROM stmt_slot WHERE kind<>'card' ORDER BY key")]
    return s
out["snap"] = snap()
print("JSON:" + json.dumps(out, default=str))
'''


def probe(appdir, mode, dbpath, script, extra=None):
    env = dict(os.environ, APPDIR=appdir, MODE=mode, FINANCE_DB=dbpath, FINANCE_DIR=appdir, FINANCE_UI_DIR=os.path.join(appdir, "finance_ui"), FINANCE_ALLOW_HEADER_AUTH="1",
               PORDERS_SOURCE="tables", ORDER_TODAY=ORDER_DAY, STMT_DRIVE_STUB=STUB, STMT_INBOX=os.path.join(W, "inbox417_" + mode), PACKS_TODAY="2026-09-26",
               STMT_VENV_PYTHON=sys.executable)
    env.update(extra or {})
    p = subprocess.run([sys.executable, "-B", "-c", script], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=appdir, timeout=1200)
    O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
    if not O:
        sys.exit("!! the %s app did not answer: %s\n%s" % (mode, p.stderr[-3000:], p.stdout[-800:]))
    return O


# ============================================================================ 1  the stock in the order's own unit
N1, O1 = probe(a.app, "new", a.db, PROBE1), probe(a.old, "old", a.db + ".old", PROBE1)
print("-- 1  the stock beside an order, in the order's own unit")
check("the unit words: 124 of a 10-strip -> '12 strips + 4'; an orthotic -> '3 pcs'; a '1*1' item (pack size unknown) -> '5 units' (the raw count WITH its word); a syrup -> '3 bottles'; "
      "the packing decides when the pack size says 1 ('1*15' -> strips); a negative figure; a whole number of strips; nothing known -> '0 units'",
      N1["unit_cases"] == ["12 strips + 4", "3 pcs", "5 units", "3 bottles", "0 strips + 7", "−(1 strip + 3)", "2 strips", "0 units"], N1["unit_cases"])
S, T, P_ = "W417 STRIP TEN", "W417 SYRUP", "W417 PLAIN"
check("/page/orders (the doctor's): On hand reads '12 strips + 4' beside the order in strips, '3 bottles' beside bottles, '5 units' beside units -- the order qty cell exactly as before",
      N1["orders_code"] == 200 and N1["orders:" + S][1] == "12 strips + 4" and N1["orders:" + T][1] == "3 bottles" and N1["orders:" + P_][1] == "5 units"
      and [N1["orders:" + k][2] for k in (S, T, P_)] == [O1["orders:" + k][2] for k in (S, T, P_)] and "strip" in N1["orders:" + S][2],
      {k: N1["orders:" + k] for k in (S, T, P_)})
check("/page/staff (Order medicines): Stock now reads '12 strips + 4' / '3 bottles' / '5 units'; the order qty cell exactly as before",
      N1["staff_code"] == 200 and N1["staff:" + S][1] == "12 strips + 4" and N1["staff:" + T][1] == "3 bottles" and N1["staff:" + P_][1] == "5 units"
      and [N1["staff:" + k][2] for k in (S, T, P_)] == [O1["staff:" + k][2] for k in (S, T, P_)], {k: N1["staff:" + k] for k in (S, T, P_)})
check("the Purchase orders screen: the engine's plan lines carry stock_text ('12 strips + 4', '3 bottles', '5 units') beside the same on_hand and qty; the day's proposal lines carry it "
      "('12 strips + 4', '5 units'); the orthotic line and the owner's full list carry shelf_text '3 pcs' (shelf 3, short 2)",
      N1["state_ok"] and N1["plan_lines"].get(S, [None, None])[1] == "12 strips + 4" and N1["plan_lines"].get(T, [None, None])[1] == "3 bottles" and N1["plan_lines"].get(P_, [None, None])[1] == "5 units"
      and {k: v[0] for k, v in N1["plan_lines"].items()} == {k: v[0] for k, v in O1["plan_lines"].items()} and {k: v[2] for k, v in N1["plan_lines"].items()} == {k: v[2] for k, v in O1["plan_lines"].items()}
      and N1["proposal_lines"] == {S: [124, "12 strips + 4", 20], P_: [5, "5 units", 10]} and N1["ortho_line"] == [3, "3 pcs", 2] and N1["ortho_all"] == [3, "3 pcs"],
      (N1["plan_lines"], N1["proposal_lines"], N1["ortho_line"], N1["ortho_all"]))
check("the screens print those words: porders.html section 4 (the proposal and the engine's plan -- no bare on_hand left) and section 1 (the shelf), the owner's Purchase orders table (shelf in pieces)",
      N1["html"] == dict(proposal=True, shelf=True, owner=True, bare_on_hand=0), N1["html"])
check("the WhatsApp text is byte-identical to the box as it is (the D-decided format: 'Item — qty unit')", N1["wa"] == O1["wa"] and "W417 STRIP TEN — 20 strips" in N1["wa"], N1["wa"])
check("NEGATIVE (the box as it is): /page/staff prints the bare 124 / 3 / 5; /page/orders the bare 124; no stock_text on the plan or the proposal, no shelf_text on the orthotic; the pages print on_hand bare",
      O1["staff:" + S][1] == "124" and O1["staff:" + T][1] == "3" and O1["staff:" + P_][1] == "5" and O1["orders:" + S][1] == "124"
      and all(v[1] is None for v in O1["plan_lines"].values()) and all(v[1] is None for v in O1["proposal_lines"].values()) and O1["ortho_line"] and O1["ortho_line"][1] is None
      and O1["html"]["bare_on_hand"] == 2 and not O1["html"]["owner"], (O1["staff:" + S], O1["orders:" + S], O1["plan_lines"], O1["ortho_line"], O1["html"]))

# ============================================================================ 2  the card shelf
N2, O2 = probe(a.app, "new", P2, PROBE2), probe(a.old, "old", P2 + ".old", PROBE2)
print("-- 2  the card shelf")
f = N2["files"]
A7, A8, A9 = "2026-07-13_W417_amazon.pdf", "2026-08-13_W417_amazon.pdf", "2026-09-13_W417_amazon.pdf"
H7, H8, C7, C8 = "2026-07-16_W417_hdfc.pdf", "2026-08-16_W417_hdfc.pdf", "2026-07-03_W417_coral.pdf", "2026-08-03_W417_coral.pdf"
dec = lambda nm: f.get(nm + "|decrypted") or [None] * 8        # noqa: E731
org = lambda nm: f.get(nm + "|cards") or [None] * 8            # noqa: E731
check("the fetch took the fixture Drive with no error; every decrypted card statement is READ from its own text: statement date = period_to, the billing period "
      "(HDFC's older layout prints none -> the month up to the statement date), the card number(s) -- never the 'linked savings account' line",
      N2["fetch"][1] == [] and N2["fetch"][0] >= 14
      and dec(A7)[2:6] == ["1104", "2026-06-13", "2026-07-12", "read"] and dec(A8)[2:6] == ["1112", "2026-07-13", "2026-08-12", "read"]
      and dec(H7)[2:6] == ["6011", "2026-06-16", "2026-07-15", "read"] and dec(H8)[2:6] == ["6011", "2026-07-16", "2026-08-15", "read"]
      and dec(C7)[2:6] == ["7001", "2026-06-03", "2026-07-02", "read"] and dec(C8)[2:6] == ["7001", "2026-07-03", "2026-08-02", "read"]
      and dec(A8)[0] == "card_icici_amazon" and dec(H8)[0] == "card_hdfc_regalia" and dec(C8)[0] == "card_icici_coral",
      {k: v[:6] for k, v in f.items() if k.endswith("|decrypted")})
check("each card slot LEARNS its number(s): the Amazon card both forms, the newest first ('1112,1104' -- one card re-issued), HDFC '6011', Coral '7001'; the cell shows '1112 / 1104'",
      N2["tails"] == {"card_hdfc_regalia": "6011", "card_icici_amazon": "1112,1104", "card_icici_coral": "7001"} and N2["cells"]["2026-08"]["card_icici_amazon"][3] == "1112 / 1104", N2["tails"])
ca, cj, cs = N2["cells"]["2026-08"], N2["cells"]["2026-07"], N2["cells"]["2026-09"]
check("the month cells fill from the statement DATED in the month: August -> Amazon 12-Aug, HDFC 15-Aug, Coral 02-Aug (read); July -> the three July statements",
      [ca[k][:3] for k in ("card_icici_amazon", "card_hdfc_regalia", "card_icici_coral")] == [["read", A8, "2026-08-12"], ["read", H8, "2026-08-15"], ["read", C8, "2026-08-02"]]
      and [cj[k][:3] for k in ("card_icici_amazon", "card_hdfc_regalia", "card_icici_coral")] == [["read", A7, "2026-07-12"], ["read", H7, "2026-07-15"], ["read", C7, "2026-07-02"]], (ca, cj))
ra, rs_ = N2["rows"]["2026-08"], N2["rows"]["2026-09"]
check("pack row 4 finds August's three decrypted statements (ready, 'statement dated …'); All_Transactions.xlsx ready",
      [ra.get("card:" + k, ["", ""])[0] for k in ("card_hdfc_regalia", "card_icici_amazon", "card_icici_coral")] == ["ready"] * 3
      and ra["card:card_icici_amazon"][1] == "statement dated 12-Aug-2026" and ra["cards"][0] == "ready", ra)
check("a locked original whose decrypted twin (same name, same card folder) exists is 'duplicate of decrypted' and carries the twin's month; the September Amazon original "
      "with NO twin stays 'locked original', its month (the name's date less a day) reads 'decrypted copy not yet made' on the cell and on pack row 4",
      all(org(nm)[5] == "duplicate of decrypted" and org(nm)[4] == dec(nm)[4] for nm in (A7, A8, H7, H8, C7, C8))
      and org(A9)[5] == "locked original" and org(A9)[6] == "decrypted copy not yet made" and org(A9)[4] == "2026-09-12"
      and cs["card_icici_amazon"][0] == "empty" and cs["card_icici_amazon"][4] is True and rs_["card:card_icici_amazon"] == ["missing", "decrypted copy not yet made"]
      and rs_["card:card_hdfc_regalia"] == ["missing", "no decrypted statement on the shelf"], ({k: v[5:8] for k, v in f.items() if k.endswith("|cards")}, cs, rs_))
check("the Excel in the Credit Card Statements root is the running Excel: the fetched one AND the row as the box holds it today both folder all_txn, never in 'which account?'",
      len(N2["xlsx"]) == 2 and all(x[0] == "all_txn" and x[1] is None and x[2] == "n/a" for x in N2["xlsx"]) and not any(u[0].lower().endswith(".xlsx") for u in N2["unplaced"]), (N2["xlsx"], N2["unplaced"]))
check("NEGATIVE (the box as it is, same fixture): the card slots learn nothing, the August Amazon and Coral cells stay empty, no original is a duplicate, "
      "and both Excel rows sit in 'which account?'",
      all(v is None for v in O2["tails"].values()) and O2["cells"]["2026-08"]["card_icici_amazon"][0] == "empty" and O2["cells"]["2026-08"]["card_icici_coral"][0] == "empty"
      and not any(v[5] == "duplicate of decrypted" for v in O2["files"].values()) and sum(1 for u in O2["unplaced"] if u[0].lower().endswith(".xlsx")) == 2,
      (O2["tails"], O2["cells"]["2026-08"], O2["unplaced"]))

# ============================================================================ 3  the Yes Bank tile
N3, O3 = probe(a.app, "new", P3, PROBE3), probe(a.old, "old", P3 + ".old", PROBE3)
print("-- 3  the Yes Bank tile and a provisional NEFT")
check("no NEFT event: the Bank answer (the tile's figures and everything else) is BYTE-IDENTICAL to the box as it is", N3["t0"][0] == 200 and N3["t0"] == O3["t0"], (N3["t0"][1][:200], O3["t0"][1][:200]))
t1, e1 = N3["t1"], N3["t1_expect"]
check("a provisional NEFT (the owner's tap, dated after the statement's end): the tile carries ONE line '− ₹12,345 provisional NEFT' (ours, by id) and the headline net of it, "
      "marked 'incl. provisional' (%s, was %s); the unconfirmed SMS event, the rejected one and the one S407 already matched to a statement line are NOT on it" % (e1[0], e1[1]),
      t1[0] == 200 and t1[1] == e1[0] and t1[2] is True and [x[0] for x in t1[3]] == [e1[2]] and t1[3][0][1] == "12,345" and "you tapped NEFT done" in t1[3][0][2]
      and t1[4] == e1[1] and t1[5] == "12,345", (t1, e1))
check("the statement confirms it (a NEFT debit of the same amount in the loaded lines): the line disappears and the headline is the statement's figure again -- nothing taken twice",
      N3["t2"][0] == 200 and N3["t2"][2] is None and N3["t2"][3] == [] and N3["t2"][1] == N3["t2_expect"], (N3["t2"], N3["t2_expect"]))
check("a statement whose period covers the NEFT and closes lower by it: the headline equals the provisional headline above (%s) -- the debit counted once" % e1[0],
      N3["t3"][0] == 200 and N3["t3"][1] == e1[0] and N3["t3"][2] is None, N3["t3"])
check("the owner's page draws the line and the mark only from the answer's provisional list (nothing else on the tile moves)", all(N3["page"]), N3["page"])
check("NEGATIVE (the box as it is): with the same provisional NEFT the tile does not move -- no line, the headline the statement's figure (%s)" % e1[1],
      O3["t1"][1] == e1[1] and O3["t1"][2] is None and O3["t1"][3] == [] and not any(O3["page"][:2]), (O3["t1"], O3["page"]))

# ============================================================================ 4  the name search (facts only)
def names(dbp, pattern=None):
    cmd = [sys.executable, "-B", os.path.join(KIT, "name_search_s417.py"), "--db", dbp, "--json"] + (["--pattern", pattern] if pattern else [])
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300)
    return next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None) or []


print("-- 4  the name search (JARDIAN / JIARDIAN / GRDIAN, spelling-tolerant; read-only)")
before = os.path.getmtime(a.db)
R4 = {r["item"]: r for r in names(a.db) if r["item"].startswith("W417")}
J, G = R4.get("W417 JIARDIANCE 10") or {}, R4.get("W417 GRDIANS 25 MG") or {}
check("both crafted spellings are found, the GUARDIAN decoy is not; each with its strength, packing, stock, supplier, last purchase and last sale",
      sorted(R4) == ["W417 GRDIANS 25 MG", "W417 JIARDIANCE 10"] and J.get("strength") == "10 (the name prints no unit)" and J.get("packing") == "1*10"
      and (J.get("stock") or {}).get("qty") == 25 and J.get("suppliers") == ["W417 PHARMA"] and (J.get("last_purchase") or {}).get("date") == D(3)
      and (J.get("last_sale") or {}).get("date") == D(2) and G.get("strength") == "25 mg" and G.get("last_sale") is None and (G.get("stock") or {}).get("qty") == 0,
      {k: [v.get("strength"), v.get("packing"), (v.get("stock") or {}).get("qty"), v.get("suppliers"), v.get("last_purchase"), v.get("last_sale")] for k, v in R4.items()})
exact = sorted(r["item"] for r in names(a.db, "JARDIANCE") if r["item"].startswith("W417"))
check("CONTROL: an exact 'JARDIANCE' search misses both crafted spellings -- the spelling tolerance is what finds GRDIANS; the search wrote nothing (the scratch file untouched)",
      exact == [] and os.path.getmtime(a.db) == before, (exact, os.path.getmtime(a.db) == before))

# ============================================================================ 5  the real shelf: seed_s417 on a scratch copy as the box is
print("-- 5  the real card shelf (a scratch copy of the box as it is)")
R0 = probe(a.app, "new", REAL, PROBE5)["snap"]
sp = subprocess.run([sys.executable, "-B", os.path.join(KIT, "seed_s417.py"), "--app", a.app, "--db", REAL], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1200,
                    env=dict(os.environ, FINANCE_DB=REAL, FINANCE_DIR=a.app, STMT_INBOX=os.path.join(W, "inbox417_real"), PACKS_TODAY="2026-09-26"))
print(re.sub(r"\d{6,}(\d{4})", r"XXXX\1", sp.stdout.rstrip()))
R1 = probe(a.app, "new", REAL, PROBE5)["snap"]
if R0["decrypted"]["n"]:
    check("before: the decrypted card statements carry no statement date (%d of %d read) and the August card cells are not all read; after seed_s417: every one of the %d is READ with its "
          "statement date" % (R0["decrypted"]["r"] or 0, R0["decrypted"]["n"], R1["decrypted"]["n"]),
          sp.returncode == 0 and (R0["decrypted"]["r"] or 0) == 0 and R1["decrypted"]["r"] == R1["decrypted"]["n"] == R0["decrypted"]["n"], (R0["decrypted"], R1["decrypted"], sp.stderr[-400:]))
    check("every card slot learned its number(s) (the Amazon card two, the other two one each); the August cells of the three cards read; pack row 4 ready for all three; "
          "every locked original with a same-name decrypted twin (%d) is 'duplicate of decrypted'" % R1["twins_by_name"],
          R1["tails"] == {"card_hdfc_regalia": 1, "card_icici_amazon": 2, "card_icici_coral": 1} and set(R1["cells_aug"].values()) == {"read"}
          and R1["rows_aug"].get("card:card_hdfc_regalia") == R1["rows_aug"].get("card:card_icici_amazon") == R1["rows_aug"].get("card:card_icici_coral") == "ready"
          and R1["originals"]["dup"] == R1["twins_by_name"], (R1["tails"], R1["cells_aug"], R1["rows_aug"], R1["originals"], R1["twins_by_name"]))
else:
    check("the box holds no card file (nothing to re-read)", True)
check("the Excel rows: before %s (folder, slot) -> after %s -- every one the running Excel (all_txn), none in 'which account?'; the bank-folder rows, the bank slots' tails and the four bank "
      "tables are exactly as before" % (R0["xlsx_rows"], R1["xlsx_rows"]),
      R1["unplaced_xlsx"] == [] and all(x[0] == "all_txn" for x in R1["xlsx_rows"]) and len(R1["xlsx_rows"]) == len(R0["xlsx_rows"])
      and R1["bank_rows"] == R0["bank_rows"] and R1["bank_tables"] == R0["bank_tables"] and R1["bank_slot_tails"] == R0["bank_slot_tails"],
      (R0["xlsx_rows"], R1["xlsx_rows"], R1["unplaced_xlsx"], R1["bank_rows"] == R0["bank_rows"], R1["bank_tables"], R0["bank_tables"]))

print(("WALK_S417 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S417 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
