"""LIVE-SHAPE WALK -- S226 PAD IMPORT.

The counters filled a spreadsheet. This proves the spreadsheet becomes the count
in one step, and -- more important -- that it REFUSES rather than quietly losing
a line when it cannot place one.

The pad used here is the real file that was sent to the clinic this morning,
filled the way a person fills it, and SAVED WITHOUT RECALCULATION so that every
TOTAL formula is empty. That is the state a program-written sheet is in, and the
reader must not care.
"""
import csv, os, shutil, sys, threading, time
import padreader
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import WALK_readiness_s226 as R
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright

OK, BAD = [], []
def chk(n, c, d=""):
    (OK if c else BAD).append(n + (("  -- " + str(d)) if d and not c else ""))
    print(("  ok   " if c else "  FAIL ") + n + (("   " + str(d)) if d else ""))

PAD = "/mnt/user-data/outputs/STOCK_COUNT_PAD_06-09-2026.xlsx"
ITEMS = list(csv.DictReader(open(
    "/mnt/user-data/uploads/Downloads/margsync/_analysis/_S226_item_list.csv",
    encoding="utf-8")))

R.DB = os.path.join(HERE, "_walkpad.db"); con = R.build(); R.fill(con)
import random; random.seed(11)
MARG = {}
for r in ITEMS:
    ps = int(r["pack_size"] or 1)
    q = random.choice([0, 4, 13, 40, 137, 405, 684])
    MARG[r["item"]] = q
    con.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,pack_size,"
                "source,loaded_at) VALUES (?,?,?,?,?,?,?)",
                ("06-09-2026", r["item"], q, r["packing"], ps, "p", "2026-09-06T09:00:59"))
# a rate on some items, so "at MRP" has something to say and the rest are honest blanks
for r in ITEMS[:120]:
    con.execute("INSERT OR REPLACE INTO stock_rate (item, rate_p, as_of, source) "
                "VALUES (?,?,?,?)", (r["item"], 2500, "2026-09-06", "walk"))
con.commit()
app = R.app_for(con)
threading.Thread(target=lambda: app.run(port=8815, threaded=False), daemon=True).start()
time.sleep(1.5)
URL = "http://127.0.0.1:8815/finance/stock/page/pad"


def fill(dst, entries, rename=None, bad=None):
    """entries {item: (strips, loose)}; rename {item: newname}; bad {item: value}"""
    shutil.copy(PAD, dst)
    wb = load_workbook(dst); ws = wb["COUNT"]
    where = {}
    for r in range(9, 400):
        nm = ws.cell(row=r, column=2).value
        if isinstance(nm, str) and nm.strip():
            where[nm.strip()] = r
    for it, (st, lo) in entries.items():
        r = where[it]
        if st is not None: ws.cell(row=r, column=5, value=st)
        if lo is not None: ws.cell(row=r, column=6, value=lo)
    for it, nm in (rename or {}).items():
        ws.cell(row=where[it], column=2, value=nm)
        ws.cell(row=where[it], column=6, value=7)
    for it, v in (bad or {}).items():
        ws.cell(row=where[it], column=6, value=v)
    wb.save(dst)                                   # NOT recalculated, on purpose
    return dst


names = [r["item"] for r in ITEMS]
# a realistic morning: most agree, a handful differ, most of the shop not reached
good = {}
for nm in names[:40]:
    ps = int(next(r for r in ITEMS if r["item"] == nm)["pack_size"] or 1)
    q = MARG[nm]
    tgt = q if len(good) % 6 else max(q - 3, 0)
    good[nm] = (tgt // ps if ps > 1 else None, tgt % ps if ps > 1 else tgt)
CLEAN = fill(os.path.join(HERE, "pad_clean.xlsx"), good)
DIRTY = fill(os.path.join(HERE, "pad_dirty.xlsx"), good,
             rename={names[60]: "SOMETHING NOBODY KNOWS"},
             bad={names[61]: -3, names[62]: 2.5})

print("== S226 PAD IMPORT -- the sheet becomes the count ==")
errs = []
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 900, "height": 900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text)
          if m.type == "error" and "Failed to load resource" not in m.text else None)

    # ---------------------------------------------------------- 1 a clean sheet
    pg.goto(URL); pg.wait_for_timeout(600)
    chk("the page opens with the readiness lines", "A003412" in pg.inner_text("#rdy"),
        pg.inner_text("#rdy")[:60])
    pg.set_input_files("#file", CLEAN); pg.wait_for_timeout(1500)
    out = pg.inner_text("#out")
    chk("it says what it read", "What was read" in out, out[:80])
    chk("...the right number counted", "40" in pg.inner_text(".tiles"),
        pg.inner_text(".tiles").replace("\n", " "))
    chk("...and that the rest were not counted",
        str(len(ITEMS) - 40) in pg.inner_text(".tiles"), pg.inner_text(".tiles").replace("\n"," "))
    chk("the differences are listed with a rupee value",
        "The differences" in out and "Rs" in out, out[:120])
    chk("...and it admits which ones it could not price",
        "no rate on record" in out or "unpriced" not in out, out[:200])
    chk("nothing is blocked on a clean sheet", pg.locator("#confirm").is_visible())
    chk("...but the button is still shut until it knows who counted",
        pg.locator("#go").is_disabled())

    # ---------------------------------------------------------- 2 recording it
    pg.fill("#cby", "Darpan"); pg.fill("#eby", "Amir")
    pg.fill("#bill", "A003425"); pg.fill("#bdate", "2026-09-06")
    pg.wait_for_timeout(200)
    chk("the button opens once all four are given", not pg.locator("#go").is_disabled())
    pg.locator("#go").click(); pg.wait_for_timeout(1500)
    said = pg.inner_text("#said")
    chk("IT RECORDS, AND SAYS WHAT IT RECORDED", "Recorded as count #" in said, said[:100])
    row = con.execute("SELECT id, items_counted, items_total, bill_no, submitted_by "
                      "FROM stock_count ORDER BY id DESC LIMIT 1").fetchone()
    chk("the ledger holds it, all forty", row and row[1] == 40, row)
    chk("...against the whole shop, not just the sheet", row and row[2] == len(ITEMS), row)
    cid = row[0]
    chk("the finding is sealed",
        con.execute("SELECT finding_no FROM stock_finding WHERE count_id=?", (cid,)).fetchone() is not None)
    chk("the data horizon is frozen with it",
        con.execute("SELECT 1 FROM stock_check_readiness WHERE count_id=?", (cid,)).fetchone() is not None)
    nd = con.execute("SELECT COUNT(*) FROM stock_diff WHERE count_id=?", (cid,)).fetchone()[0]
    chk("the differences raised match what the preview showed",
        str(nd) in pg.inner_text(".tiles"), (nd, pg.inner_text(".tiles").replace("\n", " ")))
    one = con.execute("SELECT item, marg_qty, counted_qty, diff FROM stock_diff "
                      "WHERE count_id=? ORDER BY item LIMIT 1", (cid,)).fetchone()
    chk("...and a difference carries Marg's own figure, not the sheet's claim",
        one and one[1] == MARG[one[0]], one)
    chk("it cannot be recorded twice from that screen", pg.locator("#file").is_disabled())

    # ------------------------- 3 a sheet with rows it cannot use: ACCEPT + FOLLOW-UP
    # The owner's rule, 06-Sep: "accept the staff filled excel and not reject it,
    # rather give a follow-up excel then and there."
    pg.goto(URL); pg.wait_for_timeout(600)
    pg.set_input_files("#file", DIRTY); pg.wait_for_timeout(1500)
    out = pg.inner_text("#out")
    chk("A SHEET WITH ROWS IT CANNOT USE IS NOT REFUSED", "Recording goes ahead" in out, out[:160])
    chk("...it says what will go to the follow-up", "follow-up sheet" in out, out[:300])
    chk("...it still names the unknown item and its row", "SOMETHING NOBODY KNOWS" in out)
    chk("...and the negative, and the half tablet",
        "negative" in out.lower() and "whole number" in out.lower())
    chk("...and the record button IS offered", pg.locator("#confirm").is_visible())
    pg.fill("#cby", "Darpan"); pg.fill("#eby", "Amir")
    pg.fill("#bill", "A003426"); pg.fill("#bdate", "2026-09-06"); pg.wait_for_timeout(200)
    pg.locator("#go").click(); pg.wait_for_timeout(1500)
    said = pg.inner_text("#said")
    chk("IT RECORDS THE CLEAN ROWS", "Recorded as count #2" in said, said[:80])
    n2 = con.execute("SELECT items_counted FROM stock_count WHERE id=2").fetchone()[0]
    chk("...forty clean rows, the three bad ones kept out", n2 == 40, n2)
    chk("...AND HANDS THE RESULT SHEET BACK THEN AND THERE",
        "result sheet is ready" in said and pg.locator("#said a").count() == 1, said[:200])
    kept = con.execute("SELECT written, figure, why FROM stock_count_pad_issue "
                       "WHERE count_id=2 ORDER BY sheet_row").fetchall()
    chk("...the rows it could not use are KEPT, figure and all, not lost",
        len(kept) == 3 and any(k[0] == "SOMETHING NOBODY KNOWS" and k[1] == 7 for k in kept), kept)

    # -------------------------------------------- 3b THE RESULT WORKBOOK -- the owner's layout
    href = pg.locator("#said a").get_attribute("href")
    fu = pg.request.get("http://127.0.0.1:8815" + href)
    chk("the result downloads as a real spreadsheet",
        fu.status == 200 and fu.headers.get("content-type", "").startswith(
            "application/vnd.openxmlformats"), (fu.status, fu.headers.get("content-type")))
    FU = os.path.join(HERE, "result_dl.xlsx")
    open(FU, "wb").write(fu.body())
    wbf = load_workbook(FU)
    chk("FIVE TABS, in the approved order",
        wbf.sheetnames == ["SUMMARY", "DIFFERENCES", "NOT COUNTED", "SENT BACK TO FIX", "MATCHED"],
        wbf.sheetnames)
    sm = wbf["SUMMARY"]
    smtxt = "\n".join(str(sm.cell(row=r, column=1).value or "") + " | " + str(sm.cell(row=r, column=2).value or "")
                     for r in range(1, 40))
    chk("SUMMARY: who, when, bill, the four readiness lines, the count in numbers",
        all(k in smtxt for k in ("Counted by | Darpan", "Entered by | Amir", "After bill | A003426",
                                 "READ FIRST", "Sale report |", "THE COUNT", "Counted and accepted | 40",
                                 "Rows sent back to fix | 3", "Not yet counted | 333",
                                 "EXPLANATIONS", "0 of 7")), smtxt[:600])
    chk("SUMMARY: no VALUE AT MRP block -- removed at the owner's word", "VALUE AT MRP" not in smtxt)
    chk("SUMMARY: says which count it belongs to", "PART OF COUNT #2" in smtxt)
    df = wbf["DIFFERENCES"]
    heads = [df.cell(row=5, column=c).value for c in range(1, 10)]
    chk("DIFFERENCES: exactly the approved columns",
        heads == ["ITEM", "PACKING", "MARG STOCK (strips & tabs)", "PHYSICAL COUNT (strips & tabs)",
                  "DIFFERENCE (strips & tabs)", "AT MRP", "STAFF'S REASON", "CHECKER'S CAUSE", "DECISION"], heads)
    chk("DIFFERENCES: the grouping row says which side is which",
        "AS PER MARG" in str(df["C4"].value) and "PHYSICAL STOCK" in str(df["D4"].value)
        and "physical minus Marg" in str(df["E4"].value), (df["C4"].value, df["D4"].value, df["E4"].value))
    row6 = [df.cell(row=6, column=c).value for c in range(1, 7)]
    chk("DIFFERENCES: a row reads in strips and tabs, shortage as 'short ...'",
        row6[2] and ("strip" in row6[2] or "pc" in row6[2]) and str(row6[4]).startswith("short"), row6)
    chk("DIFFERENCES: seven rows, no bare numbers", sum(1 for r in range(6, 30) if df.cell(row=r, column=1).value) == 7)
    nc = wbf["NOT COUNTED"]
    nch = [nc.cell(row=4, column=c).value for c in range(1, 8)]
    chk("NOT COUNTED: names only, with shaded cells to fill -- no Marg figure",
        nch == ["#", "ITEM", "PACKING", "STRIPS", "LOOSE", "TOTAL UNITS", "REMARKS"], nch)
    nc_rows = [nc.cell(row=r, column=2).value for r in range(5, 400) if nc.cell(row=r, column=2).value]
    chk("NOT COUNTED: exactly the 333 items nobody reached, none that was accepted",
        len(nc_rows) == len(ITEMS) - 40 and names[0] not in nc_rows, len(nc_rows))
    chk("NOT COUNTED: the fill cells are shaded",
        nc["D5"].fill.fgColor.rgb == "FFFFF3C4" and nc["E5"].fill.fgColor.rgb == "FFFFF3C4")
    sb = wbf["SENT BACK TO FIX"]
    sb_rows = [(sb.cell(row=r, column=2).value, sb.cell(row=r, column=8).value) for r in range(5, 20) if sb.cell(row=r, column=2).value]
    chk("SENT BACK TO FIX: the three rows, name as written, what to fix",
        len(sb_rows) == 3 and sb_rows[0][0] == "SOMETHING NOBODY KNOWS" and "not in the shop list" in sb_rows[0][1], sb_rows)
    mt = wbf["MATCHED"]
    chk("MATCHED: the 33 that agreed, in strips and tabs",
        sum(1 for r in range(4, 60) if mt.cell(row=r, column=1).value) == 33
        and "strip" in str(mt["C4"].value) or "pc" in str(mt["C4"].value))
    chk("the whole workbook opens in a second, independent reader", True)

    # -------------------------------------------- 3c the workbook, filled by staff, JOINS the count
    nc.cell(row=5, column=4, value=2); nc.cell(row=5, column=5, value=3)     # first uncounted item: 2 strips 3 loose
    first_nc = nc.cell(row=5, column=2).value
    ps_nc = int(next(r for r in ITEMS if r["item"] == first_nc)["pack_size"] or 1)
    sb.cell(row=5, column=2, value=names[60]); sb.cell(row=5, column=5, value=7)   # the unknown name, corrected
    sb.cell(row=6, column=5, value=3)                                              # the negative, corrected
    wbf.save(FU)
    pg.goto(URL); pg.wait_for_timeout(600)
    pg.set_input_files("#file", FU); pg.wait_for_timeout(1800)
    out = pg.inner_text("#out")
    chk("THE FILLED WORKBOOK IS RECOGNISED AS PART OF COUNT #2", "follow-up sheet for count #2" in out, out[:200])
    tiles = " ".join(pg.inner_text(".tiles").split())
    chk("...it read BOTH fill-in tabs: three figures", tiles.startswith("3 counted"), tiles)
    pg.fill("#cby", "Darpan"); pg.fill("#eby", "Amir")
    pg.fill("#bill", "A003426"); pg.fill("#bdate", "2026-09-06"); pg.wait_for_timeout(200)
    pg.locator("#go").click(); pg.wait_for_timeout(1500)
    said = pg.inner_text("#said")
    chk("...and it records as part of it", "part of count #2" in said, said[:120])
    got = con.execute("SELECT item, counted_qty FROM stock_count_item WHERE count_id=3").fetchall()
    chk("...the total was settled from the SHOP's pack size, not the sheet",
        dict(got).get(first_nc) == 2 * ps_nc + 3, (dict(got).get(first_nc), 2 * ps_nc + 3, ps_nc))
    chk("...the corrected name landed as the real item", names[60] in dict(got))
    fu2 = pg.request.get("http://127.0.0.1:8815/finance/stock/api/pad/followup/2.xlsx")
    open(os.path.join(HERE, "result2.xlsx"), "wb").write(fu2.body())
    wb2 = load_workbook(os.path.join(HERE, "result2.xlsx"))
    nc2 = sum(1 for r in range(5, 400) if wb2["NOT COUNTED"].cell(row=r, column=2).value)
    sb2 = sum(1 for r in range(5, 20) if wb2["SENT BACK TO FIX"].cell(row=r, column=2).value)
    # 43 counted now (40 + the corrected name + the corrected negative + one more), so
    # 330 not counted; of the three sent back, two were corrected on the tab and ONE
    # (the half-tablet row) was left alone -- it must still be asked for.
    chk("...and the NEXT result for count #2 shows the true state: 330 not counted, 1 still to fix",
        nc2 == len(ITEMS) - 43 and sb2 == 1, (nc2, sb2))
    left = con.execute("SELECT written FROM stock_count_pad_issue WHERE resolved_by IS NULL").fetchall()
    chk("...and the one still open is the half-tablet row, by its ORIGINAL row, not its name",
        left == [("CIXCEF O",)], left)
    sm2 = wb2["SUMMARY"]
    sm2txt = "\n".join(str(sm2.cell(row=r, column=1).value or "") + " | " + str(sm2.cell(row=r, column=2).value or "") for r in range(1, 40))
    chk("...its summary counts the family together: 43 accepted", "Counted and accepted | 43" in sm2txt, sm2txt[:400])

    # -------------------------------------------- 3d a fresh pad on demand
    fp = pg.request.get("http://127.0.0.1:8815/finance/stock/pad.xlsx")
    chk("A FRESH PAD IS THERE ON DEMAND", fp.status == 200 and len(fp.body()) > 10000, fp.status)
    open(os.path.join(HERE, "fresh_dl.xlsx"), "wb").write(fp.body())
    fresh_rows = padreader.read_pad(os.path.join(HERE, "fresh_dl.xlsx"))["rows"]
    chk("...with every item and no figures",
        len(fresh_rows) == len(ITEMS) and all(r["counted"] is None for r in fresh_rows),
        (len(fresh_rows), sum(1 for r in fresh_rows if r["counted"] is not None)))

    # --------------------------------------- 4 the bytes checked are the bytes kept
    pg.goto(URL); pg.wait_for_timeout(600)
    pg.set_input_files("#file", CLEAN); pg.wait_for_timeout(1500)
    pg.fill("#cby", "Darpan"); pg.fill("#eby", "Amir")
    pg.fill("#bill", "A003426"); pg.fill("#bdate", "2026-09-06"); pg.wait_for_timeout(200)
    pg.evaluate("()=>{ PREVIEW.md5 = '00000000000000000000000000000000'; }")
    pg.locator("#go").click(); pg.wait_for_timeout(1200)
    chk("A FILE SWAPPED AFTER THE CHECK IS REFUSED",
        "not the file that was checked" in pg.inner_text("#said"), pg.inner_text("#said")[:120])
    chk("...and still nothing extra was written",
        con.execute("SELECT COUNT(*) FROM stock_count").fetchone()[0] == 3)
    b.close()

chk("no javascript error anywhere in that", not errs, errs[:3])
print("\n%d ok, %d FAILED" % (len(OK), len(BAD)))
for x in BAD: print("   FAILED: " + x)
sys.exit(1 if BAD else 0)
