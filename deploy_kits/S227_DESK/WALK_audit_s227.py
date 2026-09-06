"""LIVE-SHAPE WALK -- S227 PURCHASE DATA AUDIT + forgiving search.

The owner, 06-Sep-2026, on BIO D3 MAX's purchase lines ('20 + 300 loose = 600',
the same bill four times): "this seems our fault ... our data is wrong ... look
for all other instances, do a complete data audit. also I could not find Axemal,
might be Aximal, Darpan reports 3 boxes missing".

This builds a shop with (1) a BIO-D3-MAX-shaped item whose Marg 'loose' column
is the WHOLE quantity in units and whose bills came in through two overlapping
exports, one of them since superseded; (2) an item with a true loose remainder;
(3) AXIMAL 200, short 286 units (3 boxes less a fistful) with a 30-strip bill in
the window. Then it reads the item life, the audit JSON, the audit workbook, and
searches 'Axemal' on the report and on the desk at phone width.
"""
import json, os, shutil, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import WALK_readiness_s226 as R
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright

OK, BAD = [], []
def chk(n, c, d=""):
    (OK if c else BAD).append(n + (("  -- " + str(d)) if d and not c else ""))
    print(("  ok   " if c else "  FAIL ") + n + (("   " + str(d)) if d else ""))

import re as _re
def sale_key(s): return _re.sub(r"\s+", " ", _re.sub(r"[^A-Z0-9 ]+", " ", s.upper())).strip()

BIO = "BIO D3 MAX CAP"; REM = "REMAIN TAB"; AXI = "AXIMAL 200 TAB"; PLAIN = "PLAINLY SOLD TAB"
ITEMS = [dict(item=BIO, packing="1*15", pack_size=15), dict(item=REM, packing="1*10", pack_size=10),
         dict(item=AXI, packing="1*10", pack_size=10), dict(item=PLAIN, packing="1*10", pack_size=10)]
for i in range(1, 21):
    ITEMS.append(dict(item="WALK-%03d DOLO TAB" % i, packing="1*10", pack_size=10))
names = [r["item"] for r in ITEMS]; PS = {r["item"]: r["pack_size"] for r in ITEMS}

R.DB = os.path.join(HERE, "_walkaudit.db"); con = R.build(); R.fill(con)
con.execute("DELETE FROM stock_snapshot"); con.execute("DELETE FROM purchase_bill"); con.execute("DELETE FROM purchase_line"); con.execute("DELETE FROM sale_line_item")
con.execute("DELETE FROM purchase_export")
MARG = {BIO: 400, REM: 60, AXI: 300, PLAIN: 50}
for r in ITEMS:
    q = MARG.get(r["item"], 40)
    con.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,pack_size,source,loaded_at) VALUES (?,?,?,?,?,?,?)",
                ("06-09-2026", r["item"], q, r["packing"], PS[r["item"]], "p", "2026-09-06T09:00:59"))
    con.execute("INSERT OR REPLACE INTO stock_rate (item, rate_p, as_of, source) VALUES (?,?,?,?)", (r["item"], 2500, "2026-09-06", "walk"))
seq = 500
for nm in (BIO, REM, AXI, PLAIN):
    for k in range(3):
        seq += 1
        con.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, qty_raw, pack, amount_p) "
                    "VALUES (1,'medical',?,?,0,?,?,?,?,?,?)", ("2026-09-0%d" % (k + 1), "A0035%02d" % (seq % 100), seq, nm, sale_key(nm), "1:0", "1*15" if nm == BIO else "1*10", 12000))
con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p) VALUES (?,?,?,?,?,?)", ("anmol agencies", "ANMOL AGENCIES", "50428", "2026-05-10", "2026-05", 100))
# two exports: the first (md5 'old') replaced by the second ('new'); a third live export ('live2') overlaps 'new'
con.execute("INSERT INTO purchase_export (md5,type,file,period_from,period_to,export_stamp,received_at,n_rows,superseded_by) VALUES ('old','BILLITEMWISE','a.xls','2026-04-01','2026-06-30','20260701-100000','2026-09-06T10:00:00',9,'new')")
con.execute("INSERT INTO purchase_export (md5,type,file,period_from,period_to,export_stamp,received_at,n_rows,superseded_by) VALUES ('new','BILLITEMWISE','b.xls','2026-04-01','2026-08-31','20260901-100000','2026-09-06T10:00:00',9,NULL)")
con.execute("INSERT INTO purchase_export (md5,type,file,period_from,period_to,export_stamp,received_at,n_rows,superseded_by) VALUES ('live2','BILLITEMWISE','c.xls','2026-06-01','2026-09-06','20260906-100000','2026-09-06T10:00:00',9,NULL)")
PL = [  # (supplier_norm, bill_no, bill_date, item, packing, qty, free, loose, batch, direction, source_md5)
    ("anmol agencies", "50428", "2026-05-10", BIO, "1*15", 20, 0, 300, "B1", "PURCHASE", "old"),      # superseded export -- not counted
    ("anmol agencies", "50428", "2026-05-10", BIO, "1*15", 20, 0, 300, "B1", "PURCHASE", "new"),      # THE line: 20 strips = 300 units
    ("anmol agencies", "53875", "2026-06-20", BIO, "1*15", 10, 1, 150, "B2", "PURCHASE", "new"),      # 10 + 1 free, loose 150 = paid strips -> 165
    ("anmol agencies", "53875", "2026-06-20", BIO, "1*15", 10, 1, 150, "B2", "PURCHASE", "live2"),    # the same line from the overlapping export -- once
    ("anmol agencies", "62695", "2026-08-02", BIO, "1*15", 4, 0, 0, "B3", "PURCHASE", "live2"),      # 60
    ("bharat medical", "BM-1", "2026-08-12", REM, "1*10", 6, 0, 3, "R1", "PURCHASE", "live2"),       # a true remainder: 63
    ("bharat medical", "BM-2", "2026-08-13", REM, "1*10", 2, 4, 0, "R2", "PURCHASE", "live2"),       # free 4 on 2 paid: odd
    ("prime ortho", "PO-9", "2026-08-20", AXI, "1*10", 30, 0, 300, "A1", "PURCHASE", "live2"),      # 30 strips = 300 units, a box-sized bill
]
for (sn, bn, bd, it, pk, qty, free, loose, batch, dr, md5) in PL:
    con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, batch, qty, free, loose_qty, rate_p, direction, source_md5) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (sn, bn, bd, bd[:7], it, pk, batch, qty, free, loose, 9000, dr, md5))
con.commit()

ARCH = os.path.join(HERE, "pad_uploads")
if os.path.isdir(ARCH): shutil.rmtree(ARCH)
app = R.app_for(con)
threading.Thread(target=lambda: app.run(port=8846, threaded=False), daemon=True).start()
time.sleep(1.5)
HOST = "http://127.0.0.1:8846"; URL = HOST + "/finance/stock/page/count"
errs = []


def fill_pad(src, dst, entries):
    shutil.copy(src, dst); wb = load_workbook(dst); ws = wb.worksheets[0]; where = {}
    for r in range(9, 400):
        nm = ws.cell(row=r, column=2).value
        if isinstance(nm, str) and nm.strip(): where[nm.strip()] = r
    for it, (st, lo) in entries.items():
        r = where[it]
        if st is not None: ws.cell(row=r, column=5, value=st)
        if lo is not None: ws.cell(row=r, column=6, value=lo)
    wb.save(dst); return dst


good = {}
for nm in names:
    ps = PS[nm]; q = MARG.get(nm, 40)
    tgt = {BIO: q - 60, AXI: q - 286, PLAIN: q - 7}.get(nm, q)
    good[nm] = (tgt // ps, tgt % ps)


def gate(pg):
    pg.locator('#whoC button[data-u="Darpan"]').click(); pg.locator('#whoE button[data-u="Amir"]').click()
    pg.fill("#bill", "A003425"); pg.fill("#billdate", "2026-09-06"); pg.wait_for_timeout(150)


with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    ctx = b.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True)
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
    pg.on("dialog", lambda d: d.accept())
    pg.goto(URL); pg.wait_for_timeout(700); gate(pg)
    with pg.expect_download() as dl:
        pg.locator("#padget").click()
    PAD = os.path.join(HERE, "pad_prefilled_a.xlsx"); dl.value.save_as(PAD)
    pg.set_input_files("#padfile", fill_pad(PAD, os.path.join(HERE, "pad_filled_a.xlsx"), good)); pg.wait_for_timeout(2500)
    chk("the count is recorded", "Recorded as count #1" in pg.inner_text("#padout"))

    # ------------------------------------------------------------ 1 the item life reads the purchase lines the way Marg means them
    j = pg.request.get(HOST + "/finance/stock/api/pad/item/1/" + BIO.replace(" ", "%20")).json()
    P = j["purchases"]
    chk("BIO D3 MAX: three bill lines counted, not six (a superseded export and a double entry dropped)",
        j["purchase_lines"] == 3 and j["purchase_lines_dropped"] == 2, (j["purchase_lines"], j["purchase_lines_dropped"]))
    u = {p["bill_no"]: p["units"] for p in P}
    chk("'20 strips, loose 300' = 300 units (not 600)", u.get("50428") == 300, u)
    chk("'10 + 1 free, loose 150' = 165 units (the free strip is not inside the loose figure)", u.get("53875") == 165, u)
    chk("'4 strips, no loose' = 60 units", u.get("62695") == 60, u)
    chk("bought this FY = 525 units", j["purchased_units"] == 525, j["purchased_units"])
    chk("...each line says how it was read", all(p.get("basis") for p in P) and P[0]["basis"].startswith("loose column = the units"), [p.get("basis") for p in P])
    j2 = pg.request.get(HOST + "/finance/stock/api/pad/item/1/" + REM.replace(" ", "%20")).json()
    u2 = {p["bill_no"]: p["units"] for p in j2["purchases"]}
    chk("a TRUE loose remainder still adds: '6 strips + 3 loose' = 63; '2 + 4 free' = 60", u2.get("BM-1") == 63 and u2.get("BM-2") == 60, u2)

    # ------------------------------------------------------------ 2 the audit
    a = pg.request.get(HOST + "/finance/stock/api/pad/audit").json()
    chk("AUDIT: one double entry (bill 53875, the overlapping export)", len(a["duplicates"]) == 1 and a["duplicates"][0]["bill_no"] == "53875", a["duplicates"])
    chk("AUDIT: one line from a superseded export (bill 50428, the old file)", len(a["superseded"]) == 1 and a["superseded"][0]["bill_no"] == "50428", a["superseded"])
    lt = sorted((x["bill_no"], x["units"], x["was"]) for x in a["loose_is_total"])
    chk("AUDIT: loose-is-total instances: 50428 (300, was read 600), 53875 (165, was 315), PO-9 (300, was 600) -- nothing else",
        lt == [("50428", 300, 600), ("53875", 165, 315), ("PO-9", 300, 600)], lt)
    chk("AUDIT: the odd free quantity is flagged (4 free on 2 paid)", [x["bill_no"] for x in a["odd_free"]] == ["BM-2"], a["odd_free"])
    chk("AUDIT: lines checked = the 7 live-or-duplicate lines + 1 superseded = 8", a["lines"] == 8, a["lines"])
    r = pg.request.get(HOST + "/finance/stock/api/pad/audit.xlsx")
    XL = os.path.join(HERE, "_audit.xlsx"); open(XL, "wb").write(r.body())
    ws = load_workbook(XL).worksheets[0]
    rows = [[c.value for c in row] for row in ws.iter_rows(min_row=5) if row[0].value]
    kinds = sorted(set(r[0] for r in rows))
    chk("AUDIT WORKBOOK: %d rows, the four kinds, a WHY column and a tick column" % len(rows),
        len(rows) == 6 and kinds == ["DOUBLE ENTRY", "FREE TOO HIGH", "LOOSE = TOTAL", "OLD EXPORT"] and ws.cell(row=4, column=11).value.startswith("WHY"), (len(rows), kinds))
    chk("...the BIO D3 MAX why-line reads in plain words", any("300" in str(r[10]) and "whole quantity" in str(r[10]) for r in rows), [r[10] for r in rows][:3])

    # ------------------------------------------------------------ 3 AXIMAL: 286 short with a 30-strip bill -> the bill lane; 'Axemal' finds it
    rep = pg.request.get(HOST + "/finance/stock/api/pad/report/1").json()
    lane = {d["item"]: d for d in rep["differences"]}
    chk("AXIMAL 200 short 286 (3 boxes less 14) -> BILL lane, '3 boxes'", lane[AXI]["lane"] == "bill" and "3 boxes" in lane[AXI]["why"], (lane[AXI]["lane"], lane[AXI]["why"]))
    chk("BIO D3 MAX short 60 with purchases read right -> not a Marg-moved line", lane[BIO]["lane"] in ("loss", "allowance"), (lane[BIO]["lane"], lane[BIO]["why"]))
    chk("the report links carry the audit workbook", rep["links"]["audit"].endswith("/api/pad/audit.xlsx"), rep["links"])
    pg.goto(HOST + "/finance/stock/page/report?count=1"); pg.wait_for_timeout(1500)
    pg.fill("#q", "Axemal"); pg.wait_for_timeout(400)
    qn = pg.inner_text("#qn")
    vis = [e.get_attribute("data-item") for e in pg.locator(".row[data-item]:not([hidden])").all()]
    chk("REPORT search 'Axemal' -> the AXIMAL row alone, marked as a near match", vis == [AXI] and "near" in qn, (vis, qn))
    pg.fill("#q", "bio d3"); pg.wait_for_timeout(400)
    vis = [e.get_attribute("data-item") for e in pg.locator(".row[data-item]:not([hidden])").all()]
    chk("REPORT search 'bio d3' -> exact", vis == [BIO], vis)
    pg.fill("#q", "zzqx"); pg.wait_for_timeout(400)
    chk("REPORT search for nonsense says so", "nothing like that" in pg.inner_text("#qn"), pg.inner_text("#qn"))
    chk("the audit workbook link is on the report page", pg.locator('a[href$="/api/pad/audit.xlsx"]').count() >= 1)
    pg.fill("#q", "bio d3"); pg.wait_for_timeout(300)
    pg.locator('.row[data-item="%s"] .h' % BIO).first.click(); pg.wait_for_timeout(900)
    life = pg.inner_text('.row[data-item="%s"]' % BIO)
    pg.screenshot(path=os.path.join(HERE, "_shot_audit_life.png"), full_page=True)
    chk("the report's purchase list shows '20 strips (Marg loose 300) = 300 units' and the dropped double entries",
        "20 strips" in life and "300 units" in life and "600" not in life and "double entr" in life, life[:600])

    pg.goto(HOST + "/finance/stock/page/desk?count=1"); pg.wait_for_timeout(1500)
    pg.fill("#q", "Axemal"); pg.wait_for_timeout(400)
    qr = pg.inner_text("#qr")
    chk("DESK find 'Axemal' -> 'nearest' + AXIMAL 200", "nearest" in qr and AXI in qr, qr)
    pg.screenshot(path=os.path.join(HERE, "_shot_audit_find.png"), full_page=False)
    pg.locator('#qr [data-find]').first.click(); pg.wait_for_timeout(600)
    pg.screenshot(path=os.path.join(HERE, "_shot_audit_jump.png"), full_page=True)
    card = pg.inner_text("#card")
    chk("...tapping it jumps to the box-sized-gaps card with the AXIMAL line opened", "BOX-SIZED" in card.upper() and AXI in card and "Hide the 1 item" in card, card[:300])
    chk("no page errors", not errs, errs)
    b.close()

print("\n%d ok, %d FAIL" % (len(OK), len(BAD)))
for x in BAD: print("  FAIL", x)
sys.exit(1 if BAD else 0)
