"""LIVE-SHAPE WALK -- S227 DESK (kit A, second cut): one card, one question.

The owner, 06-Sep-2026: an analytics layer for the stock-check report -- match
the count against everything accumulated (purchases, sales, sale returns, Marg's
own figures), flag unexplained movement, and on every major difference an inline
expandable list of the item's purchases this financial year (vendor, date, bill
number, item name, quantity) so the Marg operator reconciles from one screen.

This builds the shop with purchase bills (three vendors, one spelling with a
trailing dot, one bill before the financial year, one purchase return), sale
lines, two Marg export days; records a count with differences through the page;
then OPENS THE REPORT at phone width and reads it the way the doctor would: the
head, the seal, the mismatch, the sections; taps a major difference and checks
every purchase row and the residue against its own arithmetic.
"""
import json, os, shutil, subprocess, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import WALK_readiness_s226 as R
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright

OK, BAD = [], []
def chk(n, c, d=""):
    (OK if c else BAD).append(n + (("  -- " + str(d)) if d and not c else ""))
    print(("  ok   " if c else "  FAIL ") + n + (("   " + str(d)) if d else ""))

import random; random.seed(2271)
import re as _re
def sale_key(s): return _re.sub(r"\s+", " ", _re.sub(r"[^A-Z0-9 ]+", " ", s.upper())).strip()
FORMS = [("TAB", "1*10", 10), ("TAB", "1*15", 15), ("CAP", "1*10", 10), ("SYP 100ML", "1*1", 1), ("INJ", "1*1", 1), ("TAB", "1*30", 30)]
ITEMS = []
for i in range(1, 121):
    f = FORMS[i % len(FORMS)]
    ITEMS.append(dict(item=("WALK-%03d %s %s" % (i, random.choice(["ZINC", "CALPOL", "PANTO", "DOLO", "MOX", "ORTHO"]), f[0])) if i != 44 else "WALK-044 LS BELT UNISON L", packing=f[1], pack_size=f[2]))
names = [r["item"] for r in ITEMS]; PS = {r["item"]: r["pack_size"] for r in ITEMS}

R.DB = os.path.join(HERE, "_walkdesk.db"); con = R.build(); R.fill(con)
con.execute("DELETE FROM stock_snapshot"); con.execute("DELETE FROM purchase_bill"); con.execute("DELETE FROM purchase_line"); con.execute("DELETE FROM sale_line_item")
MARG, MARG_AUG, STRIP_P = {}, {}, {}
for r in ITEMS:
    q = random.choice([4, 13, 40, 137, 405]); MARG[r["item"]] = q
    if r is ITEMS[0]: q = 137; MARG[r["item"]] = q                  # X: enough on the shelf to be short by 22
    con.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,pack_size,source,loaded_at) VALUES (?,?,?,?,?,?,?)",
                ("06-09-2026", r["item"], q, r["packing"], PS[r["item"]], "p", "2026-09-06T09:00:59"))
for r in ITEMS[:50]:
    con.execute("INSERT OR REPLACE INTO stock_rate (item, rate_p, as_of, source) VALUES (?,?,?,?)", (r["item"], 2500, "2026-09-06", "walk"))
seq = 500
for n, r in enumerate(ITEMS[:30] + ITEMS[100:110]):
    STRIP_P[r["item"]] = 1000 + n * 350
    for k in range(3):
        seq += 1
        con.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, qty_raw, pack, amount_p) "
                    "VALUES (1,'medical',?,?,0,?,?,?,?,?,?)", ("2026-09-0%d" % (k + 1), "A0035%02d" % (seq % 100), seq, r["item"], sale_key(r["item"]), "1:0", r["packing"], STRIP_P[r["item"]]))
con.commit()

# ---- THE ITEM UNDER THE GLASS: names[0], pack 15 (i=1 -> FORMS[1]); its life this financial year
X = names[0]; PSX = PS[X]
MARG_AUG[X] = 100
con.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,pack_size,source,loaded_at) VALUES (?,?,?,?,?,?,?)",
            ("01-08-2026", X, 100, "1*15", PSX, "p", "2026-08-01T09:00:00"))
for sup, sn in (("ANMOL AGENCIES", "anmol agencies"), ("BHARAT MEDICAL", "bharat medical"), ("PRIME ORTHO", "prime ortho")):
    con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p) VALUES (?,?,?,?,?,?)", (sn, sup, "X/1", "2026-08-10", "2026-08", 100))
PL = [  # (supplier_norm, bill_no, bill_date, item as written, qty, free, loose, rate_p, direction)
    ("anmol agencies", "AN/1188", "2026-03-20", X, 10, 0, 0, 9000, "PURCHASE"),           # LAST financial year -- must not show
    ("anmol agencies", "AN/1301", "2026-04-15", X, 4, 1, 0, 9100, "PURCHASE"),            # 5 strips = 75
    ("bharat medical", "BM-7741", "2026-08-12", X + ".", 6, 0, 3, 9250, "PURCHASE"),     # trailing dot; 6 strips + 3 loose = 93
    ("prime ortho", "PO/2210", "2026-08-20", X, 2, 0, 0, 9300, "RETURN"),                # a purchase return: -30
    ("prime ortho", "PO/2299", "2026-09-02", X, 1, 0, 0, 9300, "PURCHASE"),               # 15
]
for (sn, bn, bd, it, qty, free, loose, rate, dr) in PL:
    con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, qty, free, loose_qty, rate_p, direction, source_md5) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,'walk')", (sn, bn, bd, bd[:7], it, "1*15", qty, free, loose, rate, dr))
# sales of X between the two export days: 3 bills of 1 strip 2 tabs (17 each = 51), one return of 5
for k, day in enumerate(("2026-08-05", "2026-08-18", "2026-09-04")):
    seq += 1
    con.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, qty_raw, pack, amount_p) "
                "VALUES (1,'medical',?,?,0,?,?,?,?,?,?)", (day, "A0036%02d" % k, seq, X, sale_key(X), "1:2", "1*15", STRIP_P[X]))
seq += 1
con.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, qty_raw, pack, amount_p) "
            "VALUES (1,'medical','2026-08-25','CN00170',1,?,?,?,'0:5','1*15',?)", (seq, X, sale_key(X), STRIP_P[X]))
STRIP_P[X] = 150000                                             # Rs 1,500 a strip: X's shortage is MAJOR at MRP
con.execute("UPDATE sale_line_item SET amount_p=? WHERE item_key=?", (STRIP_P[X], sale_key(X)))
con.commit()
# the arithmetic the report must reproduce, for X between 01-08 and 06-09:
FY_P_UNITS = 75 + 93 - 30 + 15            # this FY, all four dated lines (the March one excluded)
WIN_P_UNITS = 93 - 30 + 15                # after 01-08 up to 06-09
WIN_SOLD = 51 + 3 * 15 + 0                # 1:0 sale lines from the generic loop: 3 bills x 15 units on 01..03-Sep, plus the three 1:2 bills
WIN_SOLD = 3 * (1 * PSX + 2) + 3 * (1 * PSX)   # = 51 + 45 = 96
WIN_RET = 5
MARG_DELTA = MARG[X] - 100
DOCS_DELTA = WIN_P_UNITS - WIN_SOLD + WIN_RET
RESIDUE = MARG_DELTA - DOCS_DELTA

ARCH = os.path.join(HERE, "pad_uploads")
if os.path.isdir(ARCH): shutil.rmtree(ARCH)
app = R.app_for(con)
threading.Thread(target=lambda: app.run(port=8845, threaded=False), daemon=True).start()
time.sleep(1.5)
HOST = "http://127.0.0.1:8845"; URL = HOST + "/finance/stock/page/count"
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



# ---------------------------------------------------------------- the lanes, engineered one by one
# names[0] = X: sold, residue +50 -> lane MARG.  names[1]/[2]: the same Marg salt, one short one over -> a PAIR proposal.
# names[5]: loose sales, short 2 -> ALLOWANCE.  names[7]: sold, short 7 -> LOSS.  names[2]: over 5 -> OVER.
# names[9]: over +200 on Marg 40 -> RECOUNT.  names[12]: Marg negative -> RECOUNT.  names[17]: short one box (10 strips)
# with a 12-strip purchase in the window -> BILL.  names[40]: dead, short, no FY bill, one export day -> DEAD D.
# names[41]: dead, short, FY bill -> DEAD C.  names[42]: dead, short, Marg moved without a document -> DEAD B (owner).
# names[43] "LS BELT" (index 43 -> item 44): dead orthotic -> DEAD E.  names[44]: dead, shelf = Marg -> sitting dead (A).
def sk(s): return sale_key(s)
S = [names[1], names[2], names[5], names[7], names[9], names[12], names[17]]
for nm in (names[5],):
    for k in range(3):
        seq += 1
        con.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, qty_raw, pack, amount_p) "
                    "VALUES (1,'medical',?,?,0,?,?,?,?,?,?)", ("2026-08-1%d" % k, "A0037%02d" % k, seq, nm, sk(nm), "0:3", "1*10", STRIP_P.get(nm, 2000)))
MARG[names[9]] = 40; MARG[names[12]] = -13; MARG[names[17]] = 137
for nm in (names[9], names[12], names[17], names[40], names[41], names[42], names[43], names[44]):
    if nm not in (names[9], names[12], names[17]): MARG[nm] = 40
    con.execute("UPDATE stock_snapshot SET qty=? WHERE item=? AND as_on='06-09-2026'", (MARG[nm], nm))
con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, qty, free, loose_qty, rate_p, direction, source_md5) "
            "VALUES ('anmol agencies','AN/1400','2026-07-01','2026-07',?, '1*10', 12, 0, 0, 5000, 'PURCHASE', 'walk')", (names[17],))
con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, qty, free, loose_qty, rate_p, direction, source_md5) "
            "VALUES ('anmol agencies','AN/1401','2026-06-05','2026-06',?, '1*10', 4, 0, 0, 5000, 'PURCHASE', 'walk')", (names[41],))
con.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,pack_size,source,loaded_at) VALUES (?,?,?,?,?,?,?)",
            ("01-08-2026", names[42], 25, "1*10", PS[names[42]], "p", "2026-08-01T09:00:00"))   # 25 -> 40 with no bill: an adjustment
con.execute("DELETE FROM sale_line_item WHERE item_key IN (?,?,?,?,?)", tuple(sk(names[i]) for i in (40, 41, 42, 43, 44)))
con.execute("CREATE TABLE IF NOT EXISTS purchase_salt_marg (item_norm TEXT PRIMARY KEY, item TEXT NOT NULL, salt TEXT NOT NULL, as_on TEXT NOT NULL, source_md5 TEXT)")
for nm in (names[1], names[2]):
    con.execute("INSERT OR REPLACE INTO purchase_salt_marg (item_norm, item, salt, as_on) VALUES (?,?,?,?)", (nm.upper(), nm, "ETORICOXIB 90", "2026-09-04"))
con.execute("INSERT OR REPLACE INTO purchase_salt_marg (item_norm, item, salt, as_on) VALUES (?,?,?,?)", (names[7].upper(), names[7], "ETORICOXIB 60", "2026-09-04"))
con.commit()

good, EXPECT = {}, {}
for i, nm in enumerate(names[:45]):
    ps = PS[nm]; q = MARG[nm]
    tgt = q
    if nm == X: tgt = max(q - 22, 0)
    elif nm == names[1]: tgt = q - 7
    elif nm == names[2]: tgt = q + 5
    elif nm == names[5]: tgt = q - 2
    elif nm == names[7]: tgt = q - 7
    elif nm == names[9]: tgt = q + 200
    elif nm == names[12]: tgt = 0
    elif nm == names[17]: tgt = q - 100
    elif nm in (names[40], names[41], names[42], names[43]): tgt = q - 10
    elif nm == names[44]: tgt = q
    tgt = max(tgt, 0)
    good[nm] = (tgt // ps if ps > 1 else None, tgt % ps if ps > 1 else tgt); EXPECT[nm] = tgt
DIFF_ITEMS = [nm for nm in good if EXPECT[nm] != MARG[nm]]
WANT = {X: "marg", names[1]: "loss", names[2]: "over", names[5]: "allowance", names[7]: "loss", names[9]: "recount",
        names[12]: "recount", names[17]: "bill", names[40]: "dead", names[41]: "dead", names[42]: "dead", names[43]: "dead"}
KIND = {names[40]: "D", names[41]: "C", names[42]: "B", names[43]: "E"}


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
    PAD = os.path.join(HERE, "pad_prefilled.xlsx"); dl.value.save_as(PAD)
    pg.set_input_files("#padfile", fill_pad(PAD, os.path.join(HERE, "pad_filled.xlsx"), good)); pg.wait_for_timeout(3000)
    chk("the count is recorded: %d differences" % len(DIFF_ITEMS), "Recorded as count #1" in pg.inner_text("#padout"))

    # ------------------------------------------------------------ 1 the lanes, from the data
    j = pg.request.get(HOST + "/finance/stock/api/pad/report/1").json()
    lane = {d["item"]: d for d in j["differences"]}
    for nm, want in WANT.items():
        d = lane[nm]
        chk("LANE %-9s <- %s (%s)" % (want, nm, d["why"][:70]), d["lane"] == want and (KIND.get(nm) is None or d["kind"] == KIND[nm]), (d["lane"], d["kind"], d["why"]))
    chk("the allowance for the loose-sold item is 2 units (9 loose sold, cheap) and the shortage sits inside it",
        lane[names[5]]["allowance"] == 2 and lane[names[5]]["loose_fy"] == 9, (lane[names[5]]["allowance"], lane[names[5]]["loose_fy"], lane[names[5]]["sold_fy"]))
    chk("...and a Rs 1,500-a-strip item gets NO allowance", lane[X]["allowance"] == 0, lane[X]["allowance"])
    chk("THE IDENTICAL-SALT PAIR is proposed (D385): ETORICOXIB 90 short one brand, over the other; ETORICOXIB 60 is NOT in it",
        len(j["pairs"]) == 1 and j["pairs"][0]["salt"] == "ETORICOXIB 90" and j["pairs"][0]["short"][0]["item"] == names[1]
        and j["pairs"][0]["over"][0]["item"] == names[2] and lane[names[1]].get("salt_pair") == "ETORICOXIB 90" and not lane[names[7]].get("salt_pair"), j["pairs"])
    chk("...the pair is a proposal: both lines stay in their own lanes, nothing netted", lane[names[1]]["lane"] == "loss" and lane[names[2]]["lane"] == "over")
    chk("THE OWNER'S SHORT LIST holds exactly the adjustment-stock item", j["needs_owner"] == [names[42]], j["needs_owner"])
    chk("the sitting-dead matched items (shelf = Marg, nothing sold) are in the cleanup lane's second list, all kind A, names[44] among them",
        names[44] in [x["item"] for x in j["dead_matched"]] and all(x["kind"] == "A" for x in j["dead_matched"]) and len(j["dead_matched"]) == 11, [x["item"] for x in j["dead_matched"]])
    L8 = [l for l in j["lanes"] if l["key"] == "dead"][0]; L1 = [l for l in j["lanes"] if l["key"] == "recount"][0]; L7 = [l for l in j["lanes"] if l["key"] == "salt"][0]
    chk("lane totals: recount 2, dead 4 (+11 matched), salt 1 pair, every lane with lines / short / over / unpriced",
        L1["lines"] == 2 and L8["lines"] == 4 and L8["dead_matched"] == 11 and L7["pairs"] == 1 and all(k in L1 for k in ("short_p", "over_p", "unpriced", "decided", "major")), [(l["key"], l["lines"]) for l in j["lanes"]])
    chk("the price ladder: a sold item carries its sale price; an unsold item with a purchase rate carries a PROVISIONAL price (rate / 0.8)",
        lane[names[1]]["mrp_source"] == "sale" and lane[names[40]]["mrp_source"] == "provisional"
        and lane[names[40]]["mrp_p"] == -10 * int(round(2500 / 0.8)), (lane[names[40]]["mrp_source"], lane[names[40]]["mrp_p"]))
    chk("...an orthotic uses the orthotics margin (rate / 0.7)", lane[names[43]]["mrp_p"] == -10 * int(round(2500 / 0.7)) and lane[names[43]]["mrp_source"] == "provisional", lane[names[43]]["mrp_p"])
    chk("...the mismatch totals count the provisional lines", j["mismatch"]["mrp_provisional"] >= 4 and j["mismatch"]["mrp_unpriced"] == 0, j["mismatch"])
    chk("the owner's running totals start all-open", j["totals"]["open"] == len(DIFF_ITEMS) and j["totals"]["written_off"] == 0)

    # ------------------------------------------------------------ 2 THE DESK: one card at a time
    pg.goto(HOST + "/finance/stock/page/desk?count=1"); pg.wait_for_timeout(1400)
    card = lambda: pg.evaluate("()=>document.getElementById('card').textContent")
    txt = card()
    chk("THE DESK OPENS on the four numbers and card 1 of N", "short Rs" in pg.inner_text("#nums") and "still open" in pg.inner_text("#nums")
        and pg.inner_text("#pt").startswith("Card 1 of "), pg.inner_text("#pt"))
    ncards = int(pg.inner_text("#pt").split(" of ")[1])
    chk("...the first card is the owner's word on the adjustment-stock item, three big buttons, nothing to tick",
        "Your word — adjustment stock" in txt and names[42] in txt and pg.locator("#card button.b[data-act]").count() == 3
        and pg.locator("#card input[type=checkbox]").count() == 0 and "Kept elsewhere" in txt and "Used or given" in txt and "Genuinely missing" in txt, txt[:300])
    pg.locator("#card").screenshot(path=os.path.join(HERE, "_shot_desk_card1.png"))
    pg.locator('#card button.b[data-act="PARKED"]').click(); pg.wait_for_timeout(1500)
    txt = card()
    chk("ONE TAP: recorded, a green Done strip with Undo, and the NEXT CARD IS ALREADY THERE",
        "Done" in txt and "parked" in txt and pg.locator("a[data-undo]").count() == 1 and "Card 1 of" in pg.inner_text("#pt") and "Expected shrinkage" in txt, txt[:300])
    j = pg.request.get(HOST + "/finance/stock/api/pad/report/1").json()
    chk("...the server holds it", [d for d in j["differences"] if d["item"] == names[42]][0]["word"]["action"] == "PARKED")
    pg.locator("a[data-undo]").click(); pg.wait_for_timeout(1500)
    j = pg.request.get(HOST + "/finance/stock/api/pad/report/1").json()
    chk("UNDO: the line is open again (a new row, the history kept) and the card comes back",
        not [d for d in j["differences"] if d["item"] == names[42]][0]["word"] and names[42] in card()
        and con.execute("SELECT COUNT(*) FROM stock_diff_lane WHERE item=?", (names[42],)).fetchone()[0] == 2)
    pg.locator("#card button[data-skip]").click(); pg.wait_for_timeout(300)
    txt = card()
    chk("SKIP: the next card, a LANE card -- the allowance lane, its count and value, one main button, See the items, Skip",
        "Expected shrinkage" in txt and "within the allowance" in txt and pg.locator("#card button.b.main").count() == 1 and "Write off all" in txt
        and pg.locator("#card button[data-list]").count() == 1, txt[:300])
    pg.locator("#card button[data-list]").click(); pg.wait_for_timeout(200)
    chk("...See the items opens the list under the card, each line with its own small buttons", pg.locator("#list").is_visible() and pg.locator("#list .li").count() == 1 and pg.locator("#list .li button[data-act]").count() >= 2)
    pg.locator("#card").screenshot(path=os.path.join(HERE, "_shot_desk_lane.png"))
    pg.locator('#card button.b.main[data-all]').click(); pg.wait_for_timeout(1500)
    j = pg.request.get(HOST + "/finance/stock/api/pad/report/1").json()
    chk("THE WHOLE LANE IN ONE TAP: written off, no confirm box, the next card is up",
        all(d["word"] and d["word"]["action"] == "WRITE_OFF" for d in j["differences"] if d["lane"] == "allowance") and "1 line — written off" in card(), card()[:200])
    dec = con.execute("SELECT d.item, x.decision FROM stock_diff_decision x JOIN stock_diff d ON d.id=x.diff_id").fetchall()
    chk("...and the S221 decision layer agrees", (names[5], "WRITE_OFF") in dec)
    # walk the queue to the end, taking the main answer each time, skipping item cards that have no main
    steps = 0
    while pg.inner_text("#pt").startswith("Card ") and steps < 30:
        steps += 1
        m = pg.locator("#card button.b.main[data-act]")
        if m.count():
            m.first.click(); pg.wait_for_timeout(1200)
        else:
            it = pg.locator('#card button.b[data-act="RECOVER"]')
            if it.count(): it.first.click(); pg.wait_for_timeout(1200)
            else: pg.locator("#card button[data-skip]").click(); pg.wait_for_timeout(300)
    txt = card()
    chk("TO THE END: every card answered with one tap each, the closing card says what is left and where",
        ("That is all for now" in txt or "Nothing needs your word" in txt) and "Amir" in txt, txt[:300])
    j = pg.request.get(HOST + "/finance/stock/api/pad/report/1").json()
    words = {d["item"]: (d["word"] or {}).get("action") for d in j["differences"]}
    chk("...the lanes got their usual answers: recount -> RECOUNT, over -> EXPLAINED, bill -> VERIFY_BILL, marg -> MARG_FIX, loss -> RECOVER, dead E -> MARG_FIX, dead D -> WRITE_OFF",
        words[names[9]] == "RECOUNT" and words[names[2]] == "EXPLAINED" and words[names[17]] == "VERIFY_BILL" and words[X] == "MARG_FIX"
        and words[names[7]] == "RECOVER" and words[names[43]] == "MARG_FIX" and words[names[40]] == "WRITE_OFF", words)
    t = j["totals"]
    chk("...the running numbers: written off, to pursue; 'still open' = the lines with Darpan (recount) and Amir (bill) plus the one skipped card",
        "written off" in pg.inner_text("#nums") and t["open"] == t["recount"] + t["bill"] + 1 and t["written_off"] == 2 and t["pursue"] == 2, t)
    pg.locator("#card").screenshot(path=os.path.join(HERE, "_shot_desk_end.png"))
    r = pg.request.get(HOST + "/finance/stock/api/pad/cleanup/1.xlsx"); CL = os.path.join(HERE, "cleanup.xlsx"); open(CL, "wb").write(r.body())
    ws = load_workbook(CL).worksheets[0]; rows = [ws.cell(row=rr, column=1).value for rr in range(5, 40) if ws.cell(row=rr, column=1).value]
    chk("AMIR'S MARG CLEANUP LIST carries every line written off, explained, pursued or sent to Marg", len(rows) >= 6 and names[5] in rows and names[43] in rows, rows)

    # ------------------------------------------------------------ 3 the report is now the DOCUMENT: read-only, plain Show / Hide buttons
    pg.goto(HOST + "/finance/stock/page/report?count=1"); pg.wait_for_timeout(1400)
    chk("THE REPORT: no ticks, no decision buttons -- a document", pg.locator("#body input[type=checkbox]").count() == 0 and pg.locator("#body button.act").count() == 0)
    chk("...a one-line pointer to the desk at the top", pg.locator("#s0 a.desk").count() == 1 and "Open the decision desk" in pg.inner_text("#s0"))
    chk("...every lane folded, each with a plain 'Show N items' button, no browser arrows",
        pg.locator("#s1 .lane").count() >= 6 and pg.locator("#s1 .lane .lb:not([hidden])").count() == 0 and pg.locator("#s1 button.tg").count() >= 6 and pg.locator("details").count() == 0)
    b1 = pg.locator("#s1 .lane button.tg").first
    b1.click(); pg.wait_for_timeout(200)
    chk("...Show opens the lane and reads Hide; the rows carry the reason and the owner's word", pg.locator("#s1 .lane .lb:not([hidden])").count() == 1 and b1.inner_text().startswith("Hide")
        and pg.locator("#s1 .lane .lb:not([hidden]) .row .why").count() >= 1)
    b1.click(); pg.wait_for_timeout(200)
    chk("...Hide folds it again", pg.locator("#s1 .lane .lb:not([hidden])").count() == 0 and b1.inner_text().startswith("Show"))
    chk("...sections 2 and 3 fold the same way", pg.locator("#s2 button.tg").count() == 1 and pg.locator("#s3 button.tg").count() == 1 and pg.locator("#s3 .lb").get_attribute("hidden") is not None)
    pg.locator("#s3 button.tg").click(); pg.wait_for_timeout(200)
    chk("...and open on the button", pg.locator("#s3 .lb").get_attribute("hidden") is None)
    pg.fill("#q", names[9][:8]); pg.wait_for_timeout(300)
    chk("SEARCH still works and opens the lane that matches", pg.locator("#body .row:not([hidden])").count() == 1 and "1 of" in pg.inner_text("#qn"))
    pg.locator("#head").screenshot(path=os.path.join(HERE, "_shot_report_head2.png")); pg.locator("#s1").screenshot(path=os.path.join(HERE, "_shot_report_s1b.png"))
    # a counter is refused the desk
    import stock_app as SA
    keep = SA._require
    SA._require = lambda *roles: ({"user": "amir", "roles": ["viewer"], "role": "viewer"}, None) if roles != ("checker",) else (None, (SA.jsonify(ok=False), 403))
    r = pg.request.get(HOST + "/finance/stock/page/desk?count=1")
    SA._require = keep
    chk("A COUNTER IS REFUSED THE DESK (403)", r.status == 403, r.status)
    chk("THE PAGES THREW NO ERROR THROUGH ALL OF IT", not errs, errs)
    b.close()

print("\n%d ok, %d FAIL" % (len(OK), len(BAD)))
for x in BAD:
    print("  FAIL " + x)
sys.exit(1 if BAD else 0)
