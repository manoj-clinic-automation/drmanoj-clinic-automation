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
TOL = "TOLTRIS PLUS TAB"; TYR = "TYRO BR TAB"; SYP = "LACTOVAX SYP"; ROS = "ROSIKA FORTE TAB"
ITEMS = [dict(item=BIO, packing="1*15", pack_size=15), dict(item=REM, packing="1*10", pack_size=10),
         dict(item=AXI, packing="1*10", pack_size=10), dict(item=PLAIN, packing="1*10", pack_size=10),
         dict(item=TOL, packing="1*10", pack_size=10), dict(item=TYR, packing="1*10", pack_size=10), dict(item=SYP, packing="1*1", pack_size=1),
         dict(item=ROS, packing="1*10", pack_size=10)]
for i in range(1, 21):
    ITEMS.append(dict(item="WALK-%03d DOLO TAB" % i, packing="1*10", pack_size=10))
names = [r["item"] for r in ITEMS]; PS = {r["item"]: r["pack_size"] for r in ITEMS}

R.DB = os.path.join(HERE, "_walkaudit.db"); con = R.build(); R.fill(con)
con.execute("DELETE FROM stock_snapshot"); con.execute("DELETE FROM purchase_bill"); con.execute("DELETE FROM purchase_line"); con.execute("DELETE FROM sale_line_item")
con.execute("DELETE FROM purchase_export")
MARG = {BIO: 400, REM: 60, AXI: 300, PLAIN: 50, TOL: 189, TYR: 290, SYP: 9, ROS: 570}
for r in ITEMS:
    q = MARG.get(r["item"], 40)
    con.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,pack_size,source,loaded_at) VALUES (?,?,?,?,?,?,?)",
                ("06-09-2026", r["item"], q, r["packing"], PS[r["item"]], "p", "2026-09-06T09:00:59"))
    con.execute("INSERT OR REPLACE INTO stock_rate (item, rate_p, as_of, source) VALUES (?,?,?,?)", (r["item"], 2500, "2026-09-06", "walk"))
seq = 500
for nm in (BIO, REM, AXI, PLAIN, TOL, TYR, SYP, ROS):
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
# TOLTRIS: exports 27-08 (-12) -> 02-09 (357) -> 06-09 (189); a 48-strip bill DATED 27-08 keyed after that day's export;
# sold 111 between 27-08 and 02-09 and 168 after (the three 1:0 lines above are on 01..03-09 = 30; add 81 + 168 more)
for day, q in (("27-08-2026", -12), ("02-09-2026", 357)):
    con.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,pack_size,source,loaded_at) VALUES (?,?,?,?,?,?,?)", (day, TOL, q, "1*10", 10, "p", "2026-09-06T09:00:00"))
con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, batch, qty, free, loose_qty, rate_p, direction, source_md5) "
            "VALUES ('shivaaz formulations bareilly','2767','2026-08-27','2026-08',?, '1*10', '260500', 40, 8, 480, 14214, 'PURCHASE', 'live2')", (TOL,))
for k, (day, u) in enumerate((("2026-08-29", "9:1"), ("2026-09-04", "15:8"))):    # 91 and 158 units; with the 30 generic = 111 before 02-09 and 168 after
    seq += 1
    con.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, qty_raw, pack, amount_p) "
                "VALUES (1,'medical',?,?,0,?,?,?,?,?,?)", (day, "A0039%02d" % k, seq, TOL, sale_key(TOL), u, "1*10", 12000))
# TYRO BR: exports 27-08 (700) -> 02-09 (670) -> 03-09 (270) -> 06-09 (300 after nothing); 40 strips left between 02-09 and 03-09 with no document
for day, q in (("27-08-2026", 720), ("02-09-2026", 700), ("03-09-2026", 290)):
    con.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,pack_size,source,loaded_at) VALUES (?,?,?,?,?,?,?)", (day, TYR, q, "1*10", 10, "p", "2026-09-06T09:00:00"))
# SYP: a bottle item bought '5 + 1 free' (Marg loose 6)
con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, batch, qty, free, loose_qty, rate_p, direction, source_md5) "
            "VALUES ('shivaaz formulations bareilly','1971','2026-07-13','2026-07',?, '1*1', 'YL256A', 5, 1, 6, 9000, 'PURCHASE', 'live2')", (SYP,))
# ROSIKA: exports 27-08 (0) -> 02-09 (-20) -> 03-09 (570) -> 06-09 (560); bill 545 dated 01-09 (60 strips) keyed after the
# 02-09 export: span 1 shows -60 strips (the bill is dated in it but Marg had not got it), span 2 shows +60. Same entry.
for day, q in (("27-08-2026", 0), ("02-09-2026", -20), ("03-09-2026", 570)):
    con.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,pack_size,source,loaded_at) VALUES (?,?,?,?,?,?,?)", (day, ROS, q, "1*10", 10, "p", "2026-09-06T09:00:00"))
con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, batch, qty, free, loose_qty, rate_p, direction, source_md5) "
            "VALUES ('anmol agencies','545','2026-09-01','2026-09',?, '1*10', 'R1', 50, 10, 600, 9000, 'PURCHASE', 'live2')", (ROS,))
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
    tgt = {BIO: q - 60, AXI: q - 286, PLAIN: q - 7, TOL: q - 18, TYR: q - 230, SYP: q - 2, ROS: q - 12}.get(nm, q)
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
    chk("AUDIT: loose-is-total instances: 1971 (6, was 12), 2767 (480, was 960), 50428 (300, was 600), 53875 (165, was 315), 545 (600, was 1200), PO-9 (300, was 600) -- nothing else",
        lt == [("1971", 6, 12), ("2767", 480, 960), ("50428", 300, 600), ("53875", 165, 315), ("545", 600, 1200), ("PO-9", 300, 600)], lt)
    chk("AUDIT: the odd free quantity is flagged (4 free on 2 paid)", [x["bill_no"] for x in a["odd_free"]] == ["BM-2"], a["odd_free"])
    chk("AUDIT: lines checked = the 10 live-or-duplicate lines + 1 superseded = 11", a["lines"] == 11, a["lines"])
    r = pg.request.get(HOST + "/finance/stock/api/pad/audit.xlsx")
    XL = os.path.join(HERE, "_audit.xlsx"); open(XL, "wb").write(r.body())
    ws = load_workbook(XL).worksheets[0]
    rows = [[c.value for c in row] for row in ws.iter_rows(min_row=5) if row[0].value]
    kinds = sorted(set(r[0] for r in rows))
    chk("AUDIT WORKBOOK: %d rows, the four kinds, a WHY column and a tick column" % len(rows),
        len(rows) == 9 and kinds == ["DOUBLE ENTRY", "FREE TOO HIGH", "LOOSE = TOTAL", "OLD EXPORT"] and ws.cell(row=4, column=11).value.startswith("WHY"), (len(rows), kinds))
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
    pg.locator('.row[data-item="%s"] button.tg' % BIO).click(); pg.wait_for_timeout(200)
    life = pg.inner_text('.row[data-item="%s"]' % BIO)
    pg.screenshot(path=os.path.join(HERE, "_shot_audit_life.png"), full_page=True)
    chk("the report's purchase list says '20 strips' in the shop's words -- no 'units', no 'Marg loose' -- and the dropped double entries",
        "20 strips" in life and "11 strips" in life and "(10 + 1 free on the bill)" in life and "units" not in life.split("Sold:")[0] and "Marg loose" not in life and "600" not in life and "double entr" in life, life[:700])

    pg.goto(HOST + "/finance/stock/page/desk?count=1"); pg.wait_for_timeout(1500)
    pg.fill("#q", "Axemal"); pg.wait_for_timeout(400)
    qr = pg.inner_text("#qr")
    chk("DESK find 'Axemal' -> 'nearest' + AXIMAL 200", "nearest" in qr and AXI in qr, qr)
    pg.screenshot(path=os.path.join(HERE, "_shot_audit_find.png"), full_page=False)
    pg.locator('#qr [data-find]').first.click(); pg.wait_for_timeout(600)
    pg.screenshot(path=os.path.join(HERE, "_shot_audit_jump.png"), full_page=True)
    card = pg.inner_text("#card")
    chk("...tapping it jumps to the box-sized-gaps card with the AXIMAL line opened", "BOX-SIZED" in card.upper() and AXI in card and "Hide the 1 item" in card, card[:300])

    # ------------------------------------------------------------ 4 PINPOINTING (the owner: "find and pinpoint, otherwise ask for a specific lookup")
    jt = pg.request.get(HOST + "/finance/stock/api/pad/item/1/" + TOL.replace(" ", "%20")).json(); t = jt["detector"]
    chk("TOLTRIS: Marg -12 -> 189 (+20 strips 1 tab); documents in the window explain -27 strips 9 tabs (bought 0); raw residue +48 strips",
        t["marg_delta"] == 201 and t["docs_delta"] == -279 and t["raw_residue"] == 480, (t["marg_delta"], t["docs_delta"], t["raw_residue"]))
    sp = [x for x in t["spans"] if x["residue"]]
    chk("...PINPOINTED to the span 27-08 -> 02-09 and EXPLAINED: bill 2767 of 27-08-2026 (48 strips) keyed after that day's export; residue left 0",
        len(sp) == 1 and sp[0]["from_text"] == "27-08-2026" and sp[0]["to_text"] == "02-09-2026" and sp[0]["explained"] and sp[0]["explained"]["bills"][0]["bill_no"] == "2767"
        and "48 strips" in sp[0]["explained"]["sentence"] and "a purchase entry keyed in Marg after that day's export" in sp[0]["explained"]["sentence"] and t["residue"] == 0 and not t["lookups"], sp)
    chk("...THE CONCLUSION is one line: 'Nothing to chase in Marg: +48 strips is bill 2767 ...'", t["kind"] == "explained" and t["conclusion"].startswith("Nothing to chase in Marg: +48 strips is bill 2767 of 27-08-2026 (48 strips, 8 free on the bill)"), t["conclusion"])
    chk("...the details speak in strips, never units; the window line first, then one line per span", "units" not in " ".join(t["details"]) and t["details"][0].startswith("Window 27-08-2026 to 06-09-2026: Marg's figure -12 -> 189 (+20 strips 1 tab)") and len(t["details"]) == 3, t["details"])
    chk("...the purchase line reads '48 strips (40 + 8 free on the bill)'", jt["purchases"][0]["qty_text"] == "48 strips" and jt["purchases"][0]["on_bill"] == "40 + 8 free", jt["purchases"][0])
    jy = pg.request.get(HOST + "/finance/stock/api/pad/item/1/" + TYR.replace(" ", "%20")).json(); t = jy["detector"]
    sp = [x for x in t["spans"] if x["residue"]]
    chk("TYRO BR: the -40 strips is PINPOINTED to 02-09 -> 03-09 and turned into ONE question for Amir",
        t["residue"] == -400 and len(sp) == 1 and sp[0]["from_text"] == "02-09-2026" and sp[0]["to_text"] == "03-09-2026" and sp[0]["lookup"]
        and sp[0]["lookup"].startswith("Marg > item ledger > TYRO BR TAB > 02-09-2026 to 03-09-2026: which voucher took 40 strips OUT?") and t["lookups"] == [sp[0]["lookup"]], (t["residue"], sp))
    chk("...THE CONCLUSION says OUT, the span, and who looks: '40 strips OUT between 02-09-2026 and 03-09-2026 of Marg with no document ... Amir looks it up'",
        t["kind"] == "lookup" and t["conclusion"].startswith("40 strips OUT between 02-09-2026 and 03-09-2026 of Marg with no document on the server -- the one thing to chase. Amir looks it up"), t["conclusion"])
    jr = pg.request.get(HOST + "/finance/stock/api/pad/item/1/" + ROS.replace(" ", "%20")).json(); t = jr["detector"]
    chk("ROSIKA (the owner's confusing case): -60 strips in span 1 and +60 in span 2 are ONE late-keyed bill -- both spans settled, no lookup, residue 0",
        t["residue"] == 0 and t["raw_residue"] == 0 and not t["lookups"] and all(x["explained"] for x in t["spans"] if x["residue"]) and t["kind"] == "explained", t["spans"])
    chk("...its ONE conclusion: nothing to chase; bill 545 of 01-09 was not yet in Marg at the 02-09 export",
        t["conclusion"].startswith("Nothing to chase in Marg:") and "bill 545 of 01-09-2026 was not yet in Marg at the 02-09-2026 export" in t["conclusion"] and "Same entry, nothing to chase" in t["conclusion"], t["conclusion"])
    js = pg.request.get(HOST + "/finance/stock/api/pad/item/1/" + SYP.replace(" ", "%20")).json()
    chk("A SYRUP is counted in pcs: '6 pcs (5 + 1 free on the bill)', never strips", js["purchases"][0]["qty_text"] == "6 pcs" and js["purchases"][0]["on_bill"] == "5 + 1 free", js["purchases"][0])
    rep = pg.request.get(HOST + "/finance/stock/api/pad/report/1").json(); lane = {d["item"]: d for d in rep["differences"]}
    chk("LANES: TOLTRIS is NOT a 'Marg moved' line any more -- its move is the late-keyed bill; it lands in loss with the note",
        lane[TOL]["lane"] in ("loss", "allowance") and "bill 2767" in lane[TOL]["why"] and "keyed after an export" in lane[TOL]["why"], (lane[TOL]["lane"], lane[TOL]["why"]))
    chk("LANES: TYRO BR is the Marg lane, the reason names the span and the strips, and carries its lookup",
        lane[TYR]["lane"] == "marg" and lane[TYR]["why"].startswith("40 strips OUT of Marg between 02-09-2026 and 03-09-2026 with no document on the server") and "units" not in lane[TYR]["why"] and lane[TYR]["lookups"], (lane[TYR]["lane"], lane[TYR]["why"]))
    chk("LANES: ROSIKA is not a Marg-lane line either; short 1 strip 2 tabs is the loss, the note says the bill was keyed after an export",
        lane[ROS]["lane"] in ("loss", "allowance") and "bill 545" in lane[ROS]["why"], (lane[ROS]["lane"], lane[ROS]["why"]))
    chk("...every lane reason on this count speaks strips/tabs/pcs, not units", not any("unit" in d["why"] for d in rep["differences"]), [d["why"] for d in rep["differences"] if "unit" in d["why"]])
    chk("the SYRUP line reads 'short 2 pcs'", "2 pcs" in lane[SYP]["why"], lane[SYP]["why"])
    r = pg.request.get(HOST + "/finance/stock/api/pad/lookups/1.xlsx"); LK = os.path.join(HERE, "_lookups.xlsx"); open(LK, "wb").write(r.body())
    ws = load_workbook(LK).worksheets[0]; rows = [[c.value for c in row] for row in ws.iter_rows(min_row=5) if row[0].value]
    chk("AMIR'S LOOKUP LIST: one row -- TYRO BR, the question, a write-in column and a tick", len(rows) == 1 and rows[0][0] == TYR and rows[0][5].startswith("Marg > item ledger > TYRO BR TAB")
        and ws.cell(row=4, column=7).value.startswith("WHAT THE LEDGER SAYS"), rows)
    chk("the report links carry the lookup list", rep["links"]["lookups"].endswith("/api/pad/lookups/1.xlsx"))
    # the pages
    pg.goto(HOST + "/finance/stock/page/report?count=1"); pg.wait_for_timeout(1500)
    pg.fill("#q", "toltris"); pg.wait_for_timeout(300); pg.locator('.row[data-item="%s"] .h' % TOL).first.click(); pg.wait_for_timeout(900)
    life = pg.inner_text('.row[data-item="%s"]' % TOL)
    chk("REPORT, TOLTRIS opened: THE CONCLUSION FIRST, the workings folded behind 'Show how this was decided'",
        "CONCLUSION" in life.upper() and "Nothing to chase in Marg: +48 strips is bill 2767" in life and "Show how this was decided" in life and "Window 27-08-2026" not in life and "units" not in life.lower() and "Marg loose" not in life, life[:900])
    pg.locator('.row[data-item="%s"] button.tg' % TOL).click(); pg.wait_for_timeout(200)
    life = pg.inner_text('.row[data-item="%s"]' % TOL)
    chk("...opened: the window line, each span, the purchase lines, the sales, Marg by export day", "Window 27-08-2026 to 06-09-2026" in life and "27-08-2026 -> 02-09-2026" in life and "bill 2767" in life and "Sold:" in life and "Marg's own figure by export day" in life, life[:1200])
    pg.screenshot(path=os.path.join(HERE, "_shot_conc_toltris.png"), full_page=True)
    pg.fill("#q", "tyro"); pg.wait_for_timeout(300); pg.locator('.row[data-item="%s"] .h' % TYR).first.click(); pg.wait_for_timeout(900)
    life = pg.inner_text('.row[data-item="%s"]' % TYR)
    chk("REPORT, TYRO opened: the conclusion names 40 strips OUT, the span, and Amir", "CONCLUSION" in life.upper() and "40 strips OUT between 02-09-2026 and 03-09-2026 of Marg with no document" in life and "Amir looks it up" in life, life[:900])
    chk("...the Marg-answer upload box is on the report with its list", pg.locator("#margform #margfile").count() == 1 and "Send Marg" in pg.inner_text("#margbox"))
    pg.screenshot(path=os.path.join(HERE, "_shot_conc_tyro.png"), full_page=True)
    chk("the report's tools strip carries the lookup list", pg.locator('a[href$="/api/pad/lookups/1.xlsx"]').count() >= 1)
    pg.goto(HOST + "/finance/stock/page/desk?count=1"); pg.wait_for_timeout(1500)
    n = 0
    while n < 40 and "carried forward" not in pg.inner_text("#card"):
        sk = pg.locator("button[data-skip]"); 
        if not sk.count(): break
        sk.first.click(); pg.wait_for_timeout(250); n += 1
    card = pg.inner_text("#card")
    chk("DESK: the last card is 'FIRST WRITE-OFF CANDIDATES -- no movement since April', 20 items carried forward with stock, the cost total, Darpan/Amir confirm first",
        "FIRST WRITE-OFF CANDIDATES" in card.upper() and "20 items carried forward with stock" in card and "at cost" in card and "Darpan confirms" in card and pg.locator('#card a[href$="/api/pad/amir/1.xlsx"]').count() == 1, card[:300])
    pg.locator("button[data-list]").click(); pg.wait_for_timeout(200)
    chk("...See the 20 items lists them with 'Marg N strips = shelf' and a value each", pg.locator("#list .li").count() == 20 and "= shelf" in pg.inner_text("#list") and pg.locator("#list .li .v").count() == 20)
    pg.screenshot(path=os.path.join(HERE, "_shot_conc_deadcard.png"), full_page=True)
    pg.locator("button[data-skip]").first.click(); pg.wait_for_timeout(300)
    card = pg.inner_text("#card")
    chk("...the closing card offers Amir the Marg ledger lookups (1 span)", "Give Amir the Marg ledger lookups" in card and "1 span where Marg moved" in card, card[:400])
    # the Marg answer upload from the closing card
    ANS = os.path.join(HERE, "_marg_answer.txt"); open(ANS, "w").write("TYRO BR ledger 02-09..03-09: stock adjustment voucher SA/12, -40 strips, reason 'expiry return'")
    pg.set_input_files("#margfile", ANS); pg.fill("#margitem", TYR); pg.fill("#margnote", "ledger page"); pg.locator("#margform button[type=submit]").click(); pg.wait_for_timeout(1800)
    rows = con.execute("SELECT count_id, item, note, orig, bytes, by_user FROM stock_marg_answer").fetchall()
    kept = os.listdir(os.path.join(HERE, "pad_uploads", "marg_answers"))
    chk("MARG'S ANSWER UPLOADED from the desk: a row (count, item, note, name, bytes, who) and the file kept byte for byte in pad_uploads/marg_answers/",
        rows == [(1, TYR, "ledger page", "_marg_answer.txt", os.path.getsize(ANS), "walk")] and len(kept) == 1 and kept[0].endswith("_marg_answer.txt")
        and open(os.path.join(HERE, "pad_uploads", "marg_answers", kept[0])).read() == open(ANS).read(), (rows, kept))
    chk("...and the page lists it", "_marg_answer.txt" in pg.inner_text("#margbox") and "ledger page" in pg.inner_text("#margbox"), pg.inner_text("#margbox")[:300])
    pg.screenshot(path=os.path.join(HERE, "_shot_conc_closing.png"), full_page=True)
    r = pg.request.post(HOST + "/finance/stock/api/pad/marg_answer/1", multipart={"note": "x"})
    chk("...no file -> refused, in words", r.status == 400 and "Choose the file" in r.json()["message"])
    chk("no page errors", not errs, errs)
    b.close()

print("\n%d ok, %d FAIL" % (len(OK), len(BAD)))
for x in BAD: print("  FAIL", x)
sys.exit(1 if BAD else 0)
