"""LIVE-SHAPE WALK -- S227 DIFF SHEET.

The owner, 06-Sep-2026, after the first real count closed: the differences as a
PDF for the counter to fill by hand; someone types his answers into the Excel;
the value of the stock mismatch at MRP, item-wise and in total, as a separate
output and part of the processing.

This drives the stock-check page at phone width the way Amir does: a pad comes
down, is filled with differences, uploaded; then it LOOKS at the box (the
mismatch line, the DIFFERENCES link), reads the hand-fill PDF back as text, reads
the mismatch JSON, opens the result workbook in a second reader, types answers
into the DIFFERENCES tab the way an assistant would (a recount, a reason number,
a remark, everything else blank), uploads it, and checks what joined the count,
what landed on the explanation layer, and that blank rows changed nothing.

Run from inside the kit folder. Needs playwright + openpyxl and pdftotext.
"""
import hashlib, os, shutil, subprocess, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import padreader, padwriter
import WALK_readiness_s226 as R
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright

OK, BAD = [], []
def chk(n, c, d=""):
    (OK if c else BAD).append(n + (("  -- " + str(d)) if d and not c else ""))
    print(("  ok   " if c else "  FAIL ") + n + (("   " + str(d)) if d else ""))

import random; random.seed(2270)
FORMS = [("TAB", "1*10", 10), ("TAB", "1*15", 15), ("CAP", "1*10", 10), ("SYP 100ML", "1*1", 1),
         ("INJ", "1*1", 1), ("OINT 30G", "1*1", 1), ("TAB", "1*30", 30)]
ITEMS = []
for i in range(1, 121):
    f = FORMS[i % len(FORMS)]
    nm = "WALK-%03d %s %s" % (i, random.choice(["ZINC", "CALPOL", "PANTO", "DOLO", "MOX", "ORTHO"]), f[0])
    if i % 9 == 0:
        nm = nm.replace(" ", "-", 1) + " 5\""          # names with punctuation: the MRP key must still find them
    ITEMS.append(dict(item=nm, packing=f[1], pack_size=f[2]))
names = [r["item"] for r in ITEMS]
PS = {r["item"]: r["pack_size"] for r in ITEMS}

R.DB = os.path.join(HERE, "_walkdiff.db"); con = R.build(); R.fill(con)
con.execute("DELETE FROM stock_snapshot")
MARG, STRIP_P = {}, {}
for r in ITEMS:
    q = random.choice([0, 4, 13, 40, 137, 405]); MARG[r["item"]] = q
    con.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,pack_size,source,loaded_at) "
                "VALUES (?,?,?,?,?,?,?)", ("06-09-2026", r["item"], q, r["packing"], PS[r["item"]], "p", "2026-09-06T09:00:59"))
# cost rates for the first 50; SALE LINES (the MRP source) for the first 30 -- keyed the way the
# live ingest keys them (finance_returns.norm_item: upper, non-alphanumerics -> space)
import re as _re
def sale_key(s): return _re.sub(r"\s+", " ", _re.sub(r"[^A-Z0-9 ]+", " ", s.upper())).strip()
for r in ITEMS[:50]:
    con.execute("INSERT OR REPLACE INTO stock_rate (item, rate_p, as_of, source) VALUES (?,?,?,?)",
                (r["item"], 2500, "2026-09-06", "walk"))
seq = 500
for n, r in enumerate(ITEMS[:30]):
    strip_p = 1000 + n * 350                                   # the printed strip rate, paise
    STRIP_P[r["item"]] = strip_p
    for k in range(3):
        seq += 1
        con.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, "
                    "item_name, item_key, qty_raw, pack, amount_p) VALUES (1,'medical',?,?,0,?,?,?,?,?,?)",
                    ("2026-09-0%d" % (k + 1), "A0035%02d" % (seq % 100), seq, r["item"], sale_key(r["item"]),
                     "1:0", r["packing"], strip_p))
con.commit()
ARCH = os.path.join(HERE, "pad_uploads")
if os.path.isdir(ARCH):
    shutil.rmtree(ARCH)
app = R.app_for(con)
threading.Thread(target=lambda: app.run(port=8831, threaded=False), daemon=True).start()
time.sleep(1.5)
HOST = "http://127.0.0.1:8831"
URL = HOST + "/finance/stock/page/count"
errs = []


def unit_mrp(nm):
    """the price ladder (kit A): the sale price; else the purchase rate / 0.8, provisional (the first 50 items carry a rate)"""
    if nm in STRIP_P:
        return int(round(STRIP_P[nm] / float(PS[nm])))
    return int(round(2500 / 0.8)) if nm in names[:50] else None


def fill_pad(src, dst, entries):
    shutil.copy(src, dst)
    wb = load_workbook(dst); ws = wb.worksheets[0]
    where = {}
    for r in range(9, 400):
        nm = ws.cell(row=r, column=2).value
        if isinstance(nm, str) and nm.strip():
            where[nm.strip()] = r
    for it, (st, lo) in entries.items():
        r = where[it]
        if st is not None: ws.cell(row=r, column=5, value=st)
        if lo is not None: ws.cell(row=r, column=6, value=lo)
    wb.save(dst)
    return dst


def pdf_text(b):
    p = subprocess.run(["pdftotext", "-layout", "-", "-"], input=b, stdout=subprocess.PIPE)
    return p.stdout.decode("utf-8", "replace")


def rs(p):
    n = abs(int(p)); whole, paise = divmod(n, 100); s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]; parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:]); head = head[:-2]
        if head: parts.insert(0, head)
        s = ",".join(parts + [tail])
    return "Rs %s" % s + ("" if paise == 0 else ".%02d" % paise)


# 40 items counted; every third one differs (some short, some over)
good, EXPECT = {}, {}
for i, nm in enumerate(names[:40]):
    ps = PS[nm]; q = MARG[nm]
    tgt = q if i % 3 else (max(q - 7, 0) if i % 2 else q + 5)
    good[nm] = (tgt // ps if ps > 1 else None, tgt % ps if ps > 1 else tgt)
    EXPECT[nm] = tgt
DIFF_ITEMS = [nm for nm in good if EXPECT[nm] != MARG[nm]]
exp_short = sum(-(EXPECT[nm] - MARG[nm]) * unit_mrp(nm) for nm in DIFF_ITEMS if unit_mrp(nm) and EXPECT[nm] < MARG[nm])
exp_over = sum((EXPECT[nm] - MARG[nm]) * unit_mrp(nm) for nm in DIFF_ITEMS if unit_mrp(nm) and EXPECT[nm] > MARG[nm])
exp_unpriced = sum(1 for nm in DIFF_ITEMS if not unit_mrp(nm))


def gate(pg, cby="Darpan", eby="Amir", bill="A003425", bdate="2026-09-06"):
    pg.locator('#whoC button[data-u="%s"]' % cby).click()
    pg.locator('#whoE button[data-u="%s"]' % eby).click()
    pg.fill("#bill", bill); pg.fill("#billdate", bdate); pg.wait_for_timeout(150)


with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    ctx = b.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True)
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text)
          if m.type == "error" and "Failed to load resource" not in m.text else None)
    pg.on("dialog", lambda d: d.accept())

    # ------------------------------------------------------------ 1 the count, with differences
    pg.goto(URL); pg.wait_for_timeout(700)
    gate(pg)
    with pg.expect_download() as dl:
        pg.locator("#padget").click()
    PAD = os.path.join(HERE, "pad_prefilled.xlsx"); dl.value.save_as(PAD)
    FILLED = fill_pad(PAD, os.path.join(HERE, "pad_filled.xlsx"), good)
    pg.set_input_files("#padfile", FILLED); pg.wait_for_timeout(3000)
    out = pg.inner_text("#padout")
    chk("the sheet is recorded: 40 counted, %d differ" % len(DIFF_ITEMS),
        "Recorded as count #1" in out and "%d differ from Marg" % len(DIFF_ITEMS) in out, out[:300])
    chk("THE BOX SAYS THE VALUE OF THE MISMATCH AT MRP: short, over, and the lines without an MRP",
        "Stock mismatch at MRP:" in out and "short " + rs(exp_short) in out and "over " + rs(exp_over) in out
        and (("%d line%s with no MRP on record" % (exp_unpriced, "" if exp_unpriced == 1 else "s")) in out if exp_unpriced else "at a provisional price" in out), out[:600])
    chk("...AND OFFERS THE DIFFERENCES SHEET FOR THE COUNTER TO FILL BY HAND",
        pg.locator("#padout a.dl.diffs").count() == 1 and "Download DIFFERENCES TO CHECK (PDF)" in out
        and "fill by hand" in out and "DIFFERENCES" in out and "typed there" in out, out[-600:])
    chk("...the downloads in the box, in order: proof, the remaining sheet, the desk, the report, Amir's board, the differences sheet",
        [a.get_attribute("class").split()[-1] for a in pg.locator("#padout a.dl").all()] == ["proof", "dl", "desk", "report", "report", "diffs"],
        [a.get_attribute("class") for a in pg.locator("#padout a.dl").all()])
    pg.locator("#padout").screenshot(path=os.path.join(HERE, "_shot_diff_box.png"))

    # ------------------------------------------------------------ 2 the mismatch, as its own output
    j = pg.request.get(HOST + "/finance/stock/api/pad/mismatch/1").json()
    t = j["totals"]
    chk("THE MISMATCH JSON: basis MRP, one row per difference, totals short / over / net / unpriced",
        j["ok"] and j["basis"] == "MRP" and len(j["items"]) == len(DIFF_ITEMS) and t["lines"] == len(DIFF_ITEMS)
        and t["mrp_short_p"] == exp_short and t["mrp_over_p"] == exp_over and t["mrp_net_p"] == exp_over - exp_short
        and t["mrp_unpriced"] == exp_unpriced and t["mrp_priced"] + t["mrp_unpriced"] == t["lines"], t)
    first = j["items"][0]
    chk("...ordered by MRP value, largest first; each row carries item, Marg, counted, diff, cost and MRP values",
        first["mrp_p"] is not None and abs(first["mrp_p"]) == max(abs(x["mrp_p"]) for x in j["items"] if x["mrp_p"] is not None)
        and set(first) >= {"item", "marg", "counted", "diff", "cost_p", "mrp_p", "pack", "packing", "answer"}, first)
    row = [x for x in j["items"] if x["item"] == DIFF_ITEMS[0]][0]
    chk("...AN ITEM'S MRP VALUE IS ITS DIFFERENCE TIMES ITS OWN STRIP RATE OVER THE PACK",
        row["mrp_p"] == (EXPECT[DIFF_ITEMS[0]] - MARG[DIFF_ITEMS[0]]) * unit_mrp(DIFF_ITEMS[0]), (row, unit_mrp(DIFF_ITEMS[0])))
    punct = [nm for nm in DIFF_ITEMS if '"' in nm or "-" in nm.split(" ")[0] and nm in STRIP_P]
    if punct:
        prow = [x for x in j["items"] if x["item"] == punct[0]][0]
        chk("...AN ITEM WITH A HYPHEN OR A QUOTE IN ITS NAME IS PRICED TOO (the sale key, not the raw name)",
            prow["mrp_p"] is not None, (punct[0], prow))
    unp = [x for x in j["items"] if x["mrp_p"] is None]
    prov = [x for x in j["items"] if x["mrp_source"] == "provisional"]
    chk("an item the shop never sold carries a PROVISIONAL price from its purchase rate, and says so (never a cost wearing an MRP label unmarked)",
        len(unp) == exp_unpriced and prov and all(x["item"] not in STRIP_P and x["mrp_p"] == x["diff"] * int(round(2500 / 0.8)) for x in prov), prov[:1])
    chk("the cost totals sit beside, for reference", t["cost_priced"] + t["cost_unpriced"] == t["lines"] and t["cost_short_p"] >= 0)

    # ------------------------------------------------------------ 3 the hand-fill PDF
    r = pg.request.get(HOST + "/finance/stock/api/pad/diffs/1.pdf")
    DIFFS_PDF = r.body(); txt = pdf_text(DIFFS_PDF)
    chk("THE DIFFERENCES SHEET IS A PDF, landscape, named STOCK_COUNT_<day>_DIFFERENCES_TO_CHECK.pdf",
        r.status == 200 and DIFFS_PDF[:5] == b"%PDF-" and b"/MediaBox [0 0 841.89 595.28]" in DIFFS_PDF
        and "STOCK_COUNT_06-09-2026_DIFFERENCES_TO_CHECK.pdf" in r.headers.get("content-disposition", ""), r.headers.get("content-disposition"))
    chk("...its head: the clinic, the count, who counted, the bill, Marg as-on",
        "STOCK COUNT #1 - DIFFERENCES TO CHECK" in txt and "Darpan" in txt and "A003425" in txt and "06-09-2026" in txt, txt[:300])
    chk("...THE VALUE OF THE MISMATCH AT MRP on the sheet, the same figures as the box",
        "VALUE OF THE MISMATCH AT MRP:" in txt and "short " + rs(exp_short) in txt and "over " + rs(exp_over) in txt
        and "%d of %d lines have no MRP on record" % (exp_unpriced, len(DIFF_ITEMS)) in txt, [l for l in txt.splitlines() if "MISMATCH" in l])
    chk("...how to fill it, in plain words, and the reason legend 1-7",
        "HOW TO FILL THIS SHEET" in txt and "count it again" in txt
        and "1 = count error" in txt and "7 = don't know" in txt and "5 = sample / given to doctor" in txt)
    chk("...the columns: #, Item, Pack, Marg, Counted, Difference, At MRP, RECOUNT strips, loose, REASON, REMARKS",
        all(c in txt for c in ("Item", "Pack", "Marg", "Counted", "Difference", "At MRP", "RECOUNT strips", "loose", "REASON", "REMARKS")))
    body = txt[txt.find("REMARKS"):]
    chk("...EVERY DIFFERENCE IS ON IT, and none of the matched items", all(nm in body for nm in DIFF_ITEMS)
        and not any(nm in body for nm in good if nm not in DIFF_ITEMS))
    lines = [l for l in body.splitlines() if _re.match(r"^\s*\d+\s+WALK", l) and any(nm in l for nm in DIFF_ITEMS)]
    chk("...%d numbered rows, largest MRP value first, a provisional price marked with *" % len(DIFF_ITEMS),
        len(lines) == len(DIFF_ITEMS) and DIFF_ITEMS and first["item"] in lines[0] and any(" (p)" in l for l in lines) and "(p) = a provisional price" in txt, (lines[0], lines[-1]))
    short_row = [l for l in lines if "short" in l]
    chk("...a shortage carries the sign in the word: 'short 7t', never a minus on a strip",
        short_row and all("-" not in l.split("short")[1].split()[0] for l in short_row), short_row[:1])
    chk("...the totals bar and the signature line for the counter and the typist",
        "%d differences - short at MRP %s - over at MRP %s" % (len(DIFF_ITEMS), rs(exp_short), rs(exp_over)) in txt
        and "Counted again by:" in txt and "Typed into the Excel by:" in txt)
    pages = DIFFS_PDF.count(b"/Type /Page ")
    subprocess.run(["pdftoppm", "-r", "70", "-png", "-f", "1", "-l", "1", "-", os.path.join(HERE, "_shot_diffs_pdf")], input=DIFFS_PDF)

    # ------------------------------------------------------------ 4 the result workbook: the DIFFERENCES tab is now a fill-in tab
    fu = pg.request.get(HOST + "/finance/stock/api/pad/followup/1.xlsx")
    RES = os.path.join(HERE, "result_1.xlsx"); open(RES, "wb").write(fu.body())
    wb = load_workbook(RES)
    chk("the result workbook still has the five tabs", wb.sheetnames == ["SUMMARY", "DIFFERENCES", "NOT COUNTED", "SENT BACK TO FIX", "MATCHED"], wb.sheetnames)
    sm = wb["SUMMARY"]; smtxt = "\n".join("%s | %s" % (sm.cell(row=r, column=1).value or "", sm.cell(row=r, column=2).value or "") for r in range(1, 60))
    chk("...SUMMARY carries the VALUE OF THE STOCK MISMATCH at MRP: short, over, net, lines without an MRP, cost beside",
        "VALUE OF THE STOCK MISMATCH (at MRP" in smtxt and "Short on the shelf, at MRP | %s" % padwriter.rupees(exp_short) in smtxt
        and "Over on the shelf, at MRP | %s" % padwriter.rupees(exp_over) in smtxt and "Net, at MRP" in smtxt
        and "Lines with no MRP on record | %d of %d" % (exp_unpriced, len(DIFF_ITEMS)) in smtxt and "At cost (last purchase rate)" in smtxt, smtxt[smtxt.find("VALUE"):][:400])
    df = wb["DIFFERENCES"]
    heads = [df.cell(row=5, column=c).value for c in range(1, 12)]
    chk("...THE DIFFERENCES TAB HAS THE FILL-IN COLUMNS: RECOUNT STRIPS, RECOUNT LOOSE, REASON (1-7), REMARKS, after AT MRP and AT COST",
        heads == ["ITEM", "PACKING", "MARG STOCK (strips & tabs)", "PHYSICAL COUNT (strips & tabs)", "DIFFERENCE (strips & tabs)",
                  "AT MRP", "AT COST", "RECOUNT STRIPS", "RECOUNT LOOSE", "REASON (1-7)", "REMARKS"], heads)
    chk("...the shaded cells are the four answer cells, the figures are not", df.cell(row=6, column=8).fill.fgColor.rgb == "FFFFF3C4"
        and df.cell(row=6, column=11).fill.fgColor.rgb == "FFFFF3C4" and df.cell(row=6, column=4).fill.fgColor.rgb != "FFFFF3C4")
    chk("...the note says what the numbers mean and that a blank row is no change",
        "1 count error" in str(df.cell(row=2, column=1).value) and "blank row means no change" in str(df.cell(row=2, column=1).value))
    rows = {}
    for r in range(6, 200):
        v = df.cell(row=r, column=1).value
        if isinstance(v, str) and v.strip():
            rows[v.strip()] = r
    chk("...one row per difference, the same order as the PDF (MRP first)", list(rows) == [x["item"] for x in j["items"]])
    chk("...AT MRP is a rupee figure on every line (sale price, or the provisional one)",
        all("Rs " in str(df.cell(row=rows[it], column=6).value) for it in rows))

    # ------------------------------------------------------------ 5 the assistant types Darpan's answers in, uploads
    A, B, C, D, E = DIFF_ITEMS[0], DIFF_ITEMS[1], DIFF_ITEMS[2], DIFF_ITEMS[3], DIFF_ITEMS[4]
    ps = PS[A]; df.cell(row=rows[A], column=8, value=MARG[A] // ps if ps > 1 else None); df.cell(row=rows[A], column=9, value=MARG[A] % ps if ps > 1 else MARG[A])   # recount = Marg: agrees now
    psb = PS[B]; newB = MARG[B] + 2; df.cell(row=rows[B], column=8, value=newB // psb if psb > 1 else None); df.cell(row=rows[B], column=9, value=newB % psb if psb > 1 else newB)
    df.cell(row=rows[B], column=10, value=1)                                                 # ... and reason 1: count error
    df.cell(row=rows[C], column=10, value=3); df.cell(row=rows[C], column=11, value="two strips crushed in the drawer")
    df.cell(row=rows[D], column=10, value="7")
    df.cell(row=rows[E], column=11, value="Darpan says it was given to the OT")
    wb.save(RES)
    pg.set_input_files("#padfile", RES); pg.wait_for_timeout(3000)
    out = pg.inner_text("#padout")
    chk("THE TYPED-IN DIFFERENCES TAB JOINS THE COUNT: 2 recounts recorded as part of count #1",
        "Recorded as part of count #1" in out and "This sheet: 2 counted" in out, out[:300])
    chk("...A NOW AGREES (one difference fewer), B carries its new figure -- the sealed first count untouched",
        ("%d differ from Marg" % (len(DIFF_ITEMS) - 1)) in out
        and con.execute("SELECT counted_qty FROM stock_count_item WHERE count_id=2 AND item=?", (B,)).fetchone() == (newB,)
        and con.execute("SELECT counted_qty FROM stock_count_item WHERE count_id=1 AND item=?", (A,)).fetchone() == (EXPECT[A],), out[:400])
    chk("...THE BLANK DIFFERENCES ROWS CHANGED NOTHING: still 80 not counted, nothing sent back",
        "80 items not counted" in out and "to fix" not in out.split("Some stock count is left")[1][:80], out[out.find("Some stock"):][:200])
    ans = con.execute("SELECT d.item, a.reason, a.note, a.answered_by FROM stock_diff_answer a JOIN stock_diff d ON d.id=a.diff_id ORDER BY a.id").fetchall()
    chk("THE REASONS LANDED ON THE EXPLANATION LAYER: B count error, C breakage + remark, D don't know, E remark only as don't know",
        sorted(ans) == sorted([(B, "count_error", None, "walk"), (C, "breakage", "two strips crushed in the drawer", "walk"),
                (D, "dont_know", None, "walk"), (E, "dont_know", "(no reason given) Darpan says it was given to the OT", "walk")]), ans)
    j2 = pg.request.get(HOST + "/finance/stock/api/pad/mismatch/1").json()
    chk("the mismatch is re-valued on the family: one line fewer, B at its new figure, 4 explained",
        j2["totals"]["lines"] == len(DIFF_ITEMS) - 1 and [x for x in j2["items"] if x["item"] == B][0]["diff"] == 2
        and j2["explained"] == 4 and not any(x["item"] == A for x in j2["items"]), (j2["totals"]["lines"], j2["explained"]))
    chk("...and the answer travels with its item", [x for x in j2["items"] if x["item"] == C][0]["answer"]["label"] == "breakage")
    txt2 = pdf_text(pg.request.get(HOST + "/finance/stock/api/pad/diffs/1.pdf").body())
    chk("THE NEXT HAND-FILL SHEET shows the reason already on record in the item's box, so it is not asked twice",
        "on record: breakage - two strip" in txt2 and "4 reasons already on record" in txt2 and A not in txt2[txt2.find("REMARKS"):],
        [l for l in txt2.splitlines() if "on record" in l or "already" in l])
    chk("...and the recent list carries the mismatch line and the differences links for the count",
        "Stock mismatch at MRP" in pg.inner_text("#recent") and "sheet to check by hand (PDF)" in pg.inner_text("#recent")
        and "value at MRP" in pg.inner_text("#recent"), pg.inner_text("#recent")[:400])
    r = pg.request.get(HOST + "/finance/stock/api/pad/receipt/2.pdf"); t2 = pdf_text(r.body())
    chk("the part's receipt: 2 items recorded from this sheet, A and B", "EVERY ITEM RECORDED FROM THIS SHEET (2)" in t2 and A in t2 and B in t2)

    # ------------------------------------------------------------ 6 an UNTOUCHED result workbook is not a count
    fu = pg.request.get(HOST + "/finance/stock/api/pad/followup/1.xlsx")
    RES2 = os.path.join(HERE, "result_2_blank.xlsx"); open(RES2, "wb").write(fu.body())
    pg.set_input_files("#padfile", RES2); pg.wait_for_timeout(2500)
    out = pg.inner_text("#padout")
    chk("AN UNTOUCHED RESULT WORKBOOK (blank DIFFERENCES, blank NOT COUNTED) IS REFUSED IN WORDS, nothing recorded",
        "Not recorded" in out and "nothing to record" in out and con.execute("SELECT COUNT(*) FROM stock_count").fetchone()[0] == 2, out[:200])
    chk("...and no answer was invented from blank rows", con.execute("SELECT COUNT(*) FROM stock_diff_answer").fetchone()[0] == 4)
    rp = padreader.read_pad(RES2)
    chk("the reader hands on NO row from a blank DIFFERENCES tab, and every NOT COUNTED row as before",
        not [x for x in rp["rows"] if x["kind"] == "diff"] and len([x for x in rp["rows"] if x["kind"] == "count"]) == 80, len(rp["rows"]))

    # ------------------------------------------------------------ 7 the close: the differences sheet stays offered
    wb3 = load_workbook(RES2); nc = wb3["NOT COUNTED"]
    r_ = 5
    while nc.cell(row=r_, column=2).value:
        nm = nc.cell(row=r_, column=2).value; ps = PS[nm]; q = MARG[nm]
        if ps > 1: nc.cell(row=r_, column=4, value=q // ps); nc.cell(row=r_, column=5, value=q % ps)
        else: nc.cell(row=r_, column=5, value=q)
        r_ += 1
    RES3 = os.path.join(HERE, "result_3.xlsx"); wb3.save(RES3)
    pg.set_input_files("#padfile", RES3); pg.wait_for_timeout(3500)
    pg.locator("#padout button.close").click(); pg.wait_for_timeout(1500)
    out = pg.inner_text("#padout")
    chk("CLOSED: the mismatch line, the FINAL RESULT sheet, the DIFFERENCES sheet and the proofs are all in the box",
        "STOCK CHECK COMPLETED" in out and "Stock mismatch at MRP" in out and "FINAL RESULT" in out
        and "DIFFERENCES TO CHECK (PDF)" in out and "Proof of each sheet" in out, out[:500])
    pg.locator("#padout").screenshot(path=os.path.join(HERE, "_shot_diff_closed.png"))
    chk("a mismatch for a count that does not exist is 404", pg.request.get(HOST + "/finance/stock/api/pad/mismatch/99").status == 404)
    chk("THE PAGE THREW NO ERROR THROUGH ALL OF IT", not errs, errs)
    b.close()

print("\n%d ok, %d FAIL" % (len(OK), len(BAD)))
for x in BAD:
    print("  FAIL " + x)
sys.exit(1 if BAD else 0)
