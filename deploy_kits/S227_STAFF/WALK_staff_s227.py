"""LIVE-SHAPE WALK -- S227 STAFF: consumables, orthotics families, merged spans,
Darpan's lists in turns, Amir's board, the actionable audit.

The owner, 06-Sep-2026, reading the first live lookup list and the audit workbook:
"attached file has multiple entries for same item -- correct it"; "blade, gloves,
fibre casts are never tracked and billed to patients"; "orthotics is the biggest
puzzle -- same items from different companies, bought one, sold another";
"hand sheet for Darpan: keep orthotics separate; 5 highest-value and 5 routine at a
time, quantities only, no rates"; "purchase data audit should show only the ones
that need Amir"; "all uploads and downloads on the staff page meant for it";
"2 items over -- check all such with exact salts"; "explain this over to me".

The shop here: a syringe (consumable, short), two brands of one knee support (one
over, one short -- a family swap), a TYRO-shaped item whose export spans show the
same move twice with opposite signs (-74s 3t then +34s 3t = -40 strips net), a
3-tab boundary wobble, a purchase line whose packing disagrees with the stock
item, and enough medicines for two Darpan lists.
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

SYR = "DISPO SYRINGE NIPRO 3ML"; KT = "KNEE SUPPORT HINGED M TYNOR"; KU = "KNEE SUPPORT HINGED M UNISON"; KL = "KNEE SUPPORT HINGED L TYNOR"
TYR = "TYRO BR TAB"; WOB = "WOBBLE TAB"; PCK = "PACKCLASH TAB"
ITEMS = [dict(item=SYR, packing="1*1", pack_size=1), dict(item=KT, packing="1*1", pack_size=1), dict(item=KU, packing="1*1", pack_size=1),
         dict(item=KL, packing="1*1", pack_size=1), dict(item=TYR, packing="1*10", pack_size=10), dict(item=WOB, packing="1*10", pack_size=10),
         dict(item=PCK, packing="1*10", pack_size=10)]
for i in range(1, 25):
    ITEMS.append(dict(item="MED-%03d DOLO TAB" % i, packing="1*10", pack_size=10))
names = [r["item"] for r in ITEMS]; PS = {r["item"]: r["pack_size"] for r in ITEMS}
MEDS = [n for n in names if n.startswith("MED-")]

R.DB = os.path.join(HERE, "_walkstaff.db"); con = R.build(); R.fill(con)
con.execute("DELETE FROM stock_snapshot"); con.execute("DELETE FROM purchase_bill"); con.execute("DELETE FROM purchase_line"); con.execute("DELETE FROM sale_line_item")
con.execute("DELETE FROM purchase_export")
MARG = {SYR: 62, KT: 3, KU: 4, KL: 2, TYR: 700, WOB: 300, PCK: 50}
for i, n in enumerate(MEDS): MARG[n] = 100 + 10 * i
for r in ITEMS:
    con.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,pack_size,source,loaded_at) VALUES (?,?,?,?,?,?,?)",
                ("06-09-2026", r["item"], MARG[r["item"]], r["packing"], PS[r["item"]], "p", "2026-09-06T09:00:59"))
    con.execute("INSERT OR REPLACE INTO stock_rate (item, rate_p, as_of, source) VALUES (?,?,?,?)", (r["item"], 2500, "2026-09-06", "walk"))
seq = 500
def sale(nm, day, qraw, pack="1*10", amt=12000):
    global seq; seq += 1
    con.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, qty_raw, pack, amount_p) "
                "VALUES (1,'medical',?,?,0,?,?,?,?,?,?)", (day, "A00%04d" % seq, seq, nm, sale_key(nm), qraw, pack, amt))
for nm in (SYR, KT, KU, TYR, WOB, PCK) + tuple(MEDS):
    for k in range(3): sale(nm, "2026-09-0%d" % (k + 1), "1:0", "1*1" if PS[nm] == 1 else "1*10", 40000 if PS[nm] == 1 else 12000 * (1 + names.index(nm) % 5))
# TYRO: exports 27-08 (700) -> 02-09 (-73) -> 03-09 (280) -> 06-09 (270); sold 30 (01..03-09) -- the 02-09 export was taken
# before that day's purchase entries: -743 then +343 = -400 net, one question
for day, q in (("27-08-2026", 700), ("02-09-2026", -63), ("03-09-2026", 270)):
    con.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,pack_size,source,loaded_at) VALUES (?,?,?,?,?,?,?)", (day, TYR, q, "1*10", 10, "p", "2026-09-06T09:00:00"))
MARG[TYR] = 270
con.execute("UPDATE stock_snapshot SET qty=270 WHERE item=? AND as_on='06-09-2026'", (TYR,))
# WOBBLE: 27-08 (300) -> 02-09 (277) -> 06-09 (270): sold 20 by 02-09 and 10 after; 3 tabs wobble each way -> nothing
for day, q in (("27-08-2026", 300), ("02-09-2026", 277)):
    con.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,pack_size,source,loaded_at) VALUES (?,?,?,?,?,?,?)", (day, WOB, q, "1*10", 10, "p", "2026-09-06T09:00:00"))
MARG[WOB] = 270; con.execute("UPDATE stock_snapshot SET qty=270 WHERE item=? AND as_on='06-09-2026'", (WOB,))
# a purchase line whose packing (1*15) disagrees with the stock item (1*10)
con.execute("INSERT INTO purchase_export (md5,type,file,period_from,period_to,export_stamp,received_at,n_rows,superseded_by) VALUES ('live','BILLITEMWISE','c.xls','2026-04-01','2026-09-06','20260906-100000','2026-09-06T10:00:00',9,NULL)")
con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p) VALUES (?,?,?,?,?,?)", ("anmol agencies", "ANMOL AGENCIES", "77", "2026-08-10", "2026-08", 100))
con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, batch, qty, free, loose_qty, rate_p, direction, source_md5) "
            "VALUES ('anmol agencies','77','2026-08-10','2026-08',?, '1*15', 'P1', 10, 0, 150, 9000, 'PURCHASE', 'live')", (PCK,))
con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, batch, qty, free, loose_qty, rate_p, direction, source_md5) "
            "VALUES ('anmol agencies','77','2026-08-10','2026-08',?, '1*10', 'P2', 2, 4, 20, 9000, 'PURCHASE', 'live')", (MEDS[0],))
con.commit()

ARCH = os.path.join(HERE, "pad_uploads")
if os.path.isdir(ARCH): shutil.rmtree(ARCH)
app = R.app_for(con)
threading.Thread(target=lambda: app.run(port=8847, threaded=False), daemon=True).start()
time.sleep(1.5)
HOST = "http://127.0.0.1:8847"; URL = HOST + "/finance/stock/page/count"
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
    ps = PS[nm]; q = MARG[nm]
    tgt = {SYR: 0, KT: 4, KU: 3, KL: 2, TYR: q - 230, WOB: q, PCK: q - 7}.get(nm, q - (3 + 7 * (names.index(nm) % 4)))
    good[nm] = (tgt // ps, tgt % ps)
N_DIFF = sum(1 for nm in names if good[nm][0] * PS[nm] + good[nm][1] != MARG[nm])


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
    PAD = os.path.join(HERE, "pad_prefilled_s.xlsx"); dl.value.save_as(PAD)
    pg.set_input_files("#padfile", fill_pad(PAD, os.path.join(HERE, "pad_filled_s.xlsx"), good)); pg.wait_for_timeout(2500)
    chk("the count is recorded: %d differences" % N_DIFF, "Recorded as count #1" in pg.inner_text("#padout"))
    chk("the count page links to Amir's board", pg.locator('#padout a[href$="/page/amir?count=1"]').count() >= 1)

    # ------------------------------------------------------------ 1 the lanes
    rep = pg.request.get(HOST + "/finance/stock/api/pad/report/1").json(); lane = {d["item"]: d for d in rep["differences"]}
    chk("A CONSUMABLE (syringes, 62 short) lands in the consumables lane: 'used in the clinic, never billed ... write off as consumption'",
        lane[SYR]["lane"] == "consume" and lane[SYR]["consumable"] and "62 pcs used" in lane[SYR]["why"] and "Write off as consumption" in lane[SYR]["why"], (lane[SYR]["lane"], lane[SYR]["why"]))
    chk("THE ORTHOTICS FAMILY: TYNOR over 1, UNISON short 1 -> one family 'KNEE SUPPORT HINGED M', net 0, 'brand swap'",
        lane[KT]["lane"] == "ortho" and lane[KU]["lane"] == "ortho" and lane[KT]["family"] == "KNEE SUPPORT HINGED M" and lane[KU]["family"] == "KNEE SUPPORT HINGED M"
        and "nets to zero" in lane[KU]["why"] and "brand swap" in (lane[KU]["family_verdict"] or ""), (lane[KT]["family"], lane[KU]["why"], lane[KU]["family_verdict"]))
    fam = {f["key"]: f for f in rep["ortho_families"]}
    chk("...the families list carries the L size as its own family (matched, not swapped) and the M family with both members",
        "KNEE SUPPORT HINGED L" in fam and fam["KNEE SUPPORT HINGED L"]["verdict"] == "all agree" and len(fam["KNEE SUPPORT HINGED M"]["members"]) == 2, list(fam))
    jt = pg.request.get(HOST + "/finance/stock/api/pad/item/1/" + TYR.replace(" ", "%20")).json(); t = jt["detector"]
    chk("TYRO: -76 strips 3 tabs then +34 strips 3 tabs are MERGED into one span 27-08 -> 03-09 and ONE question: 40 strips OUT",
        t["residue"] == -400 and len(t["lookups"]) == 1 and "27-08-2026 to 03-09-2026" in t["lookups"][0] and "40 strips OUT" in t["lookups"][0]
        and any(x.get("merged") == 2 for x in t["spans"]), (t["residue"], t["lookups"], [(x["from_text"], x["to_text"], x["residue"], x.get("merged")) for x in t["spans"]]))
    jw = pg.request.get(HOST + "/finance/stock/api/pad/item/1/" + WOB.replace(" ", "%20")).json(); t = jw["detector"]
    chk("WOBBLE: 3 tabs one way then 3 tabs back is boundary noise -- clean, no question", t["kind"] == "clean" and not t["lookups"] and t["residue"] == 0, (t["kind"], t["lookups"], t["conclusion"]))
    r = pg.request.get(HOST + "/finance/stock/api/pad/lookups/1.xlsx"); LK = os.path.join(HERE, "_lookups_s.xlsx"); open(LK, "wb").write(r.body())
    ws = load_workbook(LK).worksheets[0]; rows = [[c.value for c in row] for row in ws.iter_rows(min_row=5) if row[0].value]
    chk("AMIR'S LOOKUP LIST: ONE row per item (TYRO only), the question inside it", len(rows) == 1 and rows[0][0] == TYR and "40 strips OUT" in rows[0][5], rows)
    chk("the 'over' total is explained in the report data: pairs list present", "pairs" in rep)

    # ------------------------------------------------------------ 2 the actionable audit
    a = pg.request.get(HOST + "/finance/stock/api/pad/audit").json()
    chk("AUDIT JSON: the packing conflict (bill says 1*15, stock says 1*10) and the free-too-high line; needs_amir = 2",
        [x["item"] for x in a["packing_conflicts"]] == [PCK] and [x["item"] for x in a["odd_free"]] == [MEDS[0]] and a["needs_amir"] == 2, (a["packing_conflicts"], a["odd_free"], a["needs_amir"]))
    r = pg.request.get(HOST + "/finance/stock/api/pad/audit.xlsx"); XL = os.path.join(HERE, "_audit_s.xlsx"); open(XL, "wb").write(r.body())
    ws = load_workbook(XL).worksheets[0]; rows = [[c.value for c in row] for row in ws.iter_rows(min_row=5) if row[0].value]
    chk("AUDIT WORKBOOK for Amir: only the 2 lines that need him, each with the exact thing to do; loose-is-total rows NOT on it",
        len(rows) == 2 and sorted(r[0] for r in rows) == ["FREE TOO HIGH", "PACKING DIFFERS"] and all("Marg" in str(r[10]) for r in rows) and "2 need Amir" in ws.cell(row=1, column=1).value, rows)

    # ------------------------------------------------------------ 3 Darpan's lists in turns
    j = pg.request.post(HOST + "/finance/stock/api/pad/tranche/1/next", data=json.dumps(dict(kind="med")), headers={"Content-Type": "application/json"}).json()
    chk("LIST 1 (medicines) cut: 10 items -- 5 by value, 5 routine; no orthotic, no consumable on it",
        j["ok"] and j["tranche"]["no"] == 1 and len(j["tranche"]["items"]) == 10 and not any(i in (SYR, KT, KU, KL) for i in j["tranche"]["items"]), j)
    T1 = j["tranche"]
    j2 = pg.request.post(HOST + "/finance/stock/api/pad/tranche/1/next", data=json.dumps(dict(kind="med")), headers={"Content-Type": "application/json"}).json()
    chk("...a second medicines list is REFUSED while Darpan still has list 1", not j2["ok"] and "still has list 1" in j2["message"], j2)
    jo = pg.request.post(HOST + "/finance/stock/api/pad/tranche/1/next", data=json.dumps(dict(kind="ortho")), headers={"Content-Type": "application/json"}).json()
    chk("...the ORTHOTICS list is separate: cut with the two knee supports", jo["ok"] and sorted(jo["tranche"]["items"]) == sorted([KT, KU]), jo)
    r = pg.request.get(HOST + "/finance/stock/api/pad/tranche/1/%d.pdf" % T1["id"])
    PDF = os.path.join(HERE, "_tranche1.pdf"); open(PDF, "wb").write(r.body())
    import subprocess
    txt = subprocess.run(["pdftotext", "-layout", PDF, "-"], capture_output=True, text=True).stdout
    chk("THE PAPER LIST: 'LIST 1 FOR DARPAN - MEDICINES - COUNT AGAIN', 10 rows, quantities only -- NO 'Rs', no 'MRP', no 'At MRP'",
        r.status == 200 and "LIST 1 FOR DARPAN" in txt and "MEDICINES" in txt and "Rs " not in txt and "MRP" not in txt and all(i in txt for i in T1["items"]), txt[:600])
    pg.request.post(HOST + "/finance/stock/api/pad/tranche/1/%d/returned" % T1["id"])
    j3 = pg.request.post(HOST + "/finance/stock/api/pad/tranche/1/next", data=json.dumps(dict(kind="med")), headers={"Content-Type": "application/json"}).json()
    chk("...returned: list 2 cuts with the NEXT 10, none repeated", j3["ok"] and j3["tranche"]["no"] == 2 and not set(j3["tranche"]["items"]) & set(T1["items"]), j3)
    ja = pg.request.post(HOST + "/finance/stock/api/pad/answers/1", data=json.dumps(dict(answers=[dict(item=T1["items"][0], reason="3", note="one strip crushed"), dict(item=T1["items"][1], reason="", note="")])), headers={"Content-Type": "application/json"}).json()
    ans = con.execute("SELECT d.item, a.reason, a.note FROM stock_diff_answer a JOIN stock_diff d ON d.id=a.diff_id").fetchall()
    chk("THE TYPING BOARD records Darpan's answer on the S221 layer (reason 3 = breakage, the note); the empty line is skipped",
        ja["ok"] and ja["recorded"] == 1 and ans == [(T1["items"][0], "breakage", "one strip crushed")], (ja, ans))

    # ------------------------------------------------------------ 4 AMIR'S BOARD, on the phone
    pg.goto(HOST + "/finance/stock/page/amir?count=1"); pg.wait_for_timeout(1500)
    body = pg.inner_text("#body")
    chk("AMIR'S BOARD: the four boxes -- Marg's reports (with the upload box), vouchers, Darpan's lists, files; and the orthotics families",
        "Reports the server still needs from Marg" in body and "Vouchers to post in Marg" in body and "Darpan's lists" in body and "Files on the server" in body and "Orthotics — by family" in body
        and pg.locator("#margform #margfile").count() == 1, body[:300])
    chk("...box 1 carries TYRO's one question in words and a Hindi line", TYR in body and "40 strips OUT" in body and "Marg से" in body)
    chk("...box 3 shows list 1 returned, list 2 with Darpan, the orthotics list with Darpan, and the typing board for list 1 with the answer on record",
        "List 1 — medicines" in body and "List 2 — medicines" in body and "List 1 — orthotics" in body and "with Darpan" in body and "on record: breakage" in body and pg.locator("table.board tr[data-item]").count() == 10, body[:1500])
    pg.screenshot(path=os.path.join(HERE, "_shot_staff_amir.png"), full_page=True)
    # type one more answer from the board and send a file
    row = pg.locator('table.board tr[data-item="%s"]' % T1["items"][2]); row.locator("select").select_option("1"); row.locator("input").fill("recount 9 strips 4 tabs")
    pg.locator("#saveans").click(); pg.wait_for_timeout(1500)
    ans = con.execute("SELECT d.item, a.reason, a.note FROM stock_diff_answer a JOIN stock_diff d ON d.id=a.diff_id ORDER BY a.id").fetchall()
    chk("...an answer typed on the board is recorded (count error, the recount in the note)", ans[-1] == (T1["items"][2], "count_error", "recount 9 strips 4 tabs"), ans)
    ANS = os.path.join(HERE, "_marg_ledger.txt"); open(ANS, "w").write("TYRO BR ledger")
    pg.set_input_files("#margfile", ANS); pg.fill("#margitem", TYR); pg.locator("#margform button[type=submit]").click(); pg.wait_for_timeout(1800)
    chk("...a file sent from Amir's board is kept and listed in box 4", "_marg_ledger.txt" in pg.inner_text("#body") and con.execute("SELECT COUNT(*) FROM stock_marg_answer").fetchone()[0] == 1)

    # ------------------------------------------------------------ 5 THE DESK: the new cards, the over words, the upload box on top
    pg.goto(HOST + "/finance/stock/page/desk?count=1"); pg.wait_for_timeout(1500)
    chk("DESK: 'over' is explained in the numbers strip", "more on the shelf than Marg" in pg.inner_text("#nums"))
    chk("DESK: the upload box sits in the foot from the first card, and Amir's board is the first link",
        pg.locator("#foot #margform").count() == 1 and pg.locator('#foot a[href$="/page/amir?count=1"]').count() == 1)
    seen = []; n = 0
    while n < 30:
        card = pg.inner_text("#card"); seen.append(card[:120])
        if "Procedure consumables".upper() in card.upper() and "syringe" in card.lower() + "consumable": pass
        sk = pg.locator("button[data-skip]")
        if not sk.count(): break
        sk.first.click(); pg.wait_for_timeout(200); n += 1
    allc = " || ".join(seen)
    chk("...a PROCEDURE CONSUMABLES card ('Write off all as used') and an ORTHOTICS card ('read the family, not the line') are in the queue",
        "PROCEDURE CONSUMABLES" in allc.upper() and "ORTHOTICS" in allc.upper(), allc[:800])
    pg.goto(HOST + "/finance/stock/page/desk?count=1"); pg.wait_for_timeout(1200)
    n = 0
    while n < 30 and "ORTHOTICS" not in pg.inner_text("#card").upper():
        pg.locator("button[data-skip]").first.click(); pg.wait_for_timeout(150); n += 1
    pg.locator("button[data-list]").click(); pg.wait_for_timeout(200)
    lst = pg.inner_text("#list")
    chk("...the orthotics card's list names the family verdict on each line", "family KNEE SUPPORT HINGED M: brand swap" in lst, lst[:400])
    pg.screenshot(path=os.path.join(HERE, "_shot_staff_ortho.png"), full_page=True)
    chk("no page errors", not errs, errs)
    b.close()

print("\n%d ok, %d FAIL" % (len(OK), len(BAD)))
for x in BAD: print("  FAIL", x)
sys.exit(1 if BAD else 0)
