#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s880.py -- kit S880 (the parent, S484, 18-Nov-2026), on a MADE-UP root: a made-up finance db (packs.ensure, card_lines.ensure,
a made-up payment register, made-up card and bank statement lines), invented vendors, no real number, dates in 2031.
    python3 walk_s880.py <dir holding packs.py + card_lines.py> <scratch>            last line 'WALK n/m'
Control: the live packs.py (S877's) goes red -- card-paid papers still on sheet 7, no receipt column on the card sheet."""
import io
import os
import sqlite3
import sys

d, scr = sys.argv[1:3]
here = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != here]          # F-1441: never the kit's own folder
sys.path.insert(0, d)
os.makedirs(scr, exist_ok=True)
for f in ("fin.db",):
    if os.path.exists(os.path.join(scr, f)):
        os.remove(os.path.join(scr, f))
os.environ["FINANCE_DB"] = os.path.join(scr, "fin.db")
os.environ["ASSETS_UPLOADS"] = os.path.join(scr, "uploads")
os.environ["PACKS_MAIL_STUB"] = os.path.join(scr, "mail")
ok, n = 0, 0


def chk(name, cond, info=""):
    global ok, n
    n += 1
    ok += bool(cond)
    print(("ok   " if cond else "FAIL ") + name + (("  [" + str(info)[:220] + "]") if (info and not cond) else ""))


try:
    import packs as p
    import card_lines as cl
except Exception as e:                                   # noqa: BLE001
    print("FAIL import: %s" % e)
    print("WALK 0/28")
    sys.exit(1)

con = sqlite3.connect(os.environ["FINANCE_DB"])
con.row_factory = sqlite3.Row
p.ensure(con)
cl.ensure(con)
con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT)")
con.execute("CREATE TABLE IF NOT EXISTS payment_register (row_no INTEGER, date_iso TEXT, vendor TEXT, description TEXT, amount_raw TEXT, "
            "amount_paise INTEGER, in_drive INTEGER, gmail_link TEXT)")
con.execute("CREATE TABLE IF NOT EXISTS icici_statement_line (id INTEGER PRIMARY KEY, account_ref TEXT, txn_date TEXT, value_date TEXT, description TEXT, "
            "reference TEXT, withdrawal_p INTEGER DEFAULT 0, deposit_p INTEGER DEFAULT 0, balance_p INTEGER)")
con.execute("CREATE TABLE IF NOT EXISTS yesbank_account_statement_line (id INTEGER PRIMARY KEY, account_ref TEXT, slot_key TEXT, txn_date TEXT, value_date TEXT, "
            "description TEXT, reference TEXT, withdrawal_p INTEGER DEFAULT 0, deposit_p INTEGER DEFAULT 0, balance_p INTEGER)")
# the slots (made-up tails)
for key, bank, label, kind, tail, sort in (("icici_made", "ICICI", "Made Up Clinic (ICICI)", "current", "7777", 1),
                                          ("yes_sav_x", "YES", "Made Up Person (Yes Bank savings)", "savings", "6666", 2),
                                          ("card_a", "ICICI", "Made Up Card A (card)", "card", "1111", 3),
                                          ("card_b", "HDFC", "Made Up Card B (card)", "card", "2222", 4)):
    con.execute("INSERT OR IGNORE INTO stmt_slot (key, bank, holder_label, kind, ident_tail, sort) VALUES (?,?,?,?,?,?)", (key, bank, label, kind, tail, sort))
con.execute("DELETE FROM stmt_slot WHERE kind='card' AND key NOT IN ('card_a','card_b')")        # only the made-up cards exist here
# the card statements DATED in the month, covering the month before (as the real ones do), proved
con.execute("INSERT INTO card_stmt (id, file_id, slot_key, bank, layout, card_tail, statement_date, period_from, period_to, printed_debits_p, printed_credits_p, "
            "read_debits_p, read_credits_p, proof_ok, proof, lines, sha256, read_at) VALUES (1, 0, 'card_a', 'ICICI', 'x', '1111', '2031-10-12', '2031-09-13', '2031-10-12', "
            "500000, 0, 500000, 0, 1, 'proved', 2, 'shaA', 'x')")
con.execute("INSERT INTO card_stmt (id, file_id, slot_key, bank, layout, card_tail, statement_date, period_from, period_to, printed_debits_p, printed_credits_p, "
            "read_debits_p, read_credits_p, proof_ok, proof, lines, sha256, read_at) VALUES (2, 0, 'card_b', 'HDFC', 'x', '2222', '2031-10-20', '2031-09-21', '2031-10-20', "
            "291433, 0, 291433, 0, 1, 'proved', 1, 'shaB', 'x')")
for sid, slot, day, desc, merch, amt, seq, cr in ((1, "card_a", "2031-09-16", "MADEUP PHONE CO", "MADEUP PHONE CO", 210000, 1, 0),
                                                   (1, "card_a", "2031-10-02", "MADEUP CLOUD", "MADEUP CLOUD", 290000, 2, 0),
                                                   (2, "card_b", "2031-10-19", "MADEUP TELECOM", "MADEUP TELECOM", 291433, 1, 0),
                                                   (2, "card_b", "2031-10-11", "MADEUP GADGETS", "MADEUP GADGETS", 555550, 2, 0),      # the paper is Rs 0.50 off
                                                   (2, "card_b", "2031-10-10", "MADEUP CASH SHOP REFUND", "MADEUP CASH SHOP", 99900, 3, 1),   # a CREDIT of the cash paper's figure
                                                   (2, "card_b", "2031-10-06", "MADEUP RETAIL PVT", "MADEUP RETAIL PVT", 370000, 4, 0)):      # the same figure as the UPI paper's bank line
    con.execute("INSERT INTO card_line (stmt_id, slot_key, card_tail, txn_date, description, merchant, kind, amount_p, credit, intl, seq) VALUES (?,?,?,?,?,?,?,?,?,'',?)",
                (sid, slot, "1111" if slot == "card_a" else "2222", day, desc, merch, "purchase", amt, cr, seq))
# the bank lines
con.execute("INSERT INTO icici_statement_line (account_ref, txn_date, description, withdrawal_p) VALUES ('7777', '2031-10-16', 'ACH D- MADEUP POWER', 1053600)")
con.execute("INSERT INTO icici_statement_line (account_ref, txn_date, description, deposit_p) VALUES ('7777', '2031-10-16', 'a deposit of the same figure', 370000)")   # never a match: a deposit
con.execute("INSERT INTO yesbank_account_statement_line (account_ref, slot_key, txn_date, description, withdrawal_p) VALUES ('6666', 'yes_sav_x', '2031-10-07', 'UPI MADEUP RETAIL', 370000)")
# the papers of October: 1 card-paid (the Sep line on Oct's card sheet), 2 card-paid (Oct lines), bank-paid x2, receipt-only, not-yet-covered, no amount, NK
pr = [(1, "2031-10-05", "Hostinger & Razorpay", "Payment successful for Madeup Retail Pvt", "", 370000, 0, "g1"),      # UPI -> the Yes Bank line of 07-Oct
      (2, "2031-10-06", "Agilus (NK Pathology)", "Invoice for N K PATHOLOGY", "", 35000, 1, "g2"),                      # NK's sheet; receipt only
      (3, "2031-10-03", "Madeup Cloud", "Your receipt from Madeup Cloud.", "", 290000, 0, "g3"),                       # card_a line 02-Oct -> leaves 7
      (4, "2031-10-20", "Airtel", "Here's your Airtel payment receipt!", "", 291433, 1, "g4"),                         # card_b line 19-Oct -> leaves 7
      (5, "2031-10-15", "Madeup Power", "Here's your payment receipt!", "", 1053600, 1, "g5"),                         # ICICI auto-pay 16-Oct
      (6, "2031-10-28", "Madeup Hotel", "Your receipt from Madeup Hotel", "", 150000, 0, "g6"),                         # after every card period: 'not yet read'
      (7, "2031-10-09", "Madeup Books", "Invoice for books", "", 0, 1, "g7"),                                           # no amount read
      (8, "2031-10-10", "Madeup Cash Shop", "Invoice for a cash purchase", "", 99900, 0, "g8"),                         # inside the card periods, on no statement: receipt only
      (9, "2031-09-17", "Madeup Phone Co", "Your receipt from Madeup Phone Co", "", 210000, 1, "g9"),                   # September's paper: the receipt of a line on OCTOBER's card sheet
      (10, "2031-10-12", "Madeup Gadgets", "Your receipt from Madeup Gadgets", "", 555600, 0, "g10")]                  # Rs 0.50 off its card line: moves, and MUST show on 4.4
con.executemany("INSERT INTO payment_register VALUES (?,?,?,?,?,?,?,?)", pr)
con.commit()
M = "2031-10"

# ---- A. sheet 7
b, why = p.build_digest(con, M)
chk("A0 the digest builds", bool(b), why)
kept, dropped, total = p.digest_rows(con, M)
kept2, dropped2, moved2 = (p._s880_split(con, list(kept), list(dropped)) if hasattr(p, "_s880_split") else (kept, dropped, []))
vend = {r["vendor"]: r for r in kept2}
chk("A1 the card-paid papers (one Rs 0.50 off its line) are no longer rows of sheet 7", "Madeup Cloud" not in vend and "Airtel" not in vend and "Madeup Gadgets" not in vend, sorted(vend))
chk("A2 ... and are the moved list, each with the card, the date and the statement's month", {m["vendor"] for m in moved2} == {"Madeup Cloud", "Airtel", "Madeup Gadgets"}
    and all(m.get("card_month") == "October 2031" for m in moved2) and any(m["card"] == "Made Up Card A, 02-Oct-2031" for m in moved2), [(m["vendor"], m.get("card"), m.get("card_month")) for m in moved2])
chk("A3 the UPI paper (the shop named, S875) matches a bank line AND a card line of the same figure: stays on 7, both named",
    str(vend.get("Madeup Retail Pvt", {}).get("debit", "")).startswith("Made Up Person (Yes Bank savings) statement, 07-Oct-2031; a card line of the same figure too (Made Up Card B, 06-Oct-2031)"), vend.get("Madeup Retail Pvt", {}).get("debit"))
chk("A3b a card CREDIT of a paper's figure never takes the paper", "Madeup Cash Shop" in vend and "card line" not in str(vend["Madeup Cash Shop"].get("debit")))
chk("A4 the auto-pay names its ICICI statement line", vend.get("Madeup Power", {}).get("debit") == "Made Up Clinic (ICICI) statement, 16-Oct-2031", vend.get("Madeup Power", {}).get("debit"))
chk("A5 a deposit of the same figure is never the debit", "Madeup Retail Pvt" in vend and "deposit" not in str(vend["Madeup Retail Pvt"].get("debit")))
chk("A6 a paper after every card period and every bank line read: 'card and bank statements ... not yet read'", str(vend.get("Madeup Hotel", {}).get("debit", "")).startswith("card and bank statements of this date not yet read"), vend.get("Madeup Hotel", {}).get("debit"))
chk("A7 a paper inside every card's period, bank lines read past it, on no statement: 'receipt only'", str(vend.get("Madeup Cash Shop", {}).get("debit", "")).startswith("receipt only"), vend.get("Madeup Cash Shop", {}).get("debit"))
chk("A8 a paper with no amount read says so", "amount on the receipt" in str(vend.get("Madeup Books", {}).get("debit")), vend.get("Madeup Books", {}).get("debit"))
chk("A9 NK Pathology's paper stays, on its own books", vend.get("Agilus (NK Pathology)", {}).get("books") == "NK Pathology")
try:
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(b or b""))
    ws = wb.worksheets[0]
    hdr = [c.value for c in ws[2]]
    chk("A10 the sheet's column E is 'Where the debit is'", hdr[4] == "Where the debit is", hdr)
    vals = [[c.value for c in r] for r in ws.iter_rows(min_row=3)]
    chk("A11 the sheet carries the bank line words and no card-paid row", any("statement, 16-Oct-2031" in str(r[4]) for r in vals) and not any(r[1] in ("Airtel", "Madeup Cloud") for r in vals), [(r[1], r[4]) for r in vals][:8])
    chk("A12 the title says what the sheet now is", "Payments not on any card" in str(ws["A1"].value) and "receipt column of the card sheet (4.4)" in str(ws["A1"].value), ws["A1"].value)
    chk("A13 the layout kept (frozen header, filter, widths)", str(ws.freeze_panes) == "A3" and bool(ws.auto_filter.ref) and (ws.column_dimensions["C"].width or 0) >= 40)
    chk("A14 the total counts only the rows left", abs(float(ws.cell(row=ws.max_row, column=4).value or 0) - round(sum((r["amount"] or 0) for r in kept2 if not r.get("books")), 2)) < 0.01,
        (ws.cell(row=ws.max_row, column=4).value, sum((r["amount"] or 0) for r in kept2 if not r.get("books"))))
    pc = [w_ for w_ in wb.worksheets if w_.title.startswith("Paid by card")]
    chk("A15 the workbook's own 'Paid by card' sheet lists every moved paper with its card line and the card sheet's month", bool(pc) and pc[0].max_row == 2 + 3 + 1
        and any("Made Up Card B, 11-Oct-2031 -- card sheet of October 2031" == str(c.value) for row in pc[0].iter_rows(min_row=3) for c in row), [[c.value for c in r][:5] for r in pc[0].iter_rows(min_row=3)] if pc else "no sheet")
except Exception as e:                                   # noqa: BLE001
    chk("A10-14 the sheet could be read", False, "%s: %s" % (type(e).__name__, e))

# ---- B. the card sheet's receipt column
cb, cwhy = p.build_card_sheet(con, M)
chk("B0 the card sheet builds", bool(cb), cwhy)
try:
    wb = load_workbook(io.BytesIO(cb or b""))
    ws = wb["Every line"]
    rows = [[c.value for c in r] for r in ws.iter_rows()]
    hdr = rows[0]
    chk("B1 two columns added: the receipt and Drive", hdr[-2:] == ["Receipt (payment paper found in mail)", "Receipt in Drive"], hdr)
    by = {str(r[3]): r for r in rows[1:]}
    chk("B2 the Sep line on Oct's sheet carries September's paper", by.get("MADEUP PHONE CO", [None] * 11)[-2] == "17-Sep-2031 · Madeup Phone Co" and by["MADEUP PHONE CO"][-1] == "yes", by.get("MADEUP PHONE CO"))
    chk("B3 the Oct lines carry their papers", by.get("MADEUP CLOUD", [None] * 11)[-2] == "03-Oct-2031 · Madeup Cloud" and by.get("MADEUP TELECOM", [None] * 11)[-2] == "20-Oct-2031 · Airtel", (by.get("MADEUP CLOUD", [])[-2:], by.get("MADEUP TELECOM", [])[-2:]))
    chk("B3b the line whose paper is Rs 0.50 off carries it (the split's own rule)", by.get("MADEUP GADGETS", [None] * 11)[-2] == "12-Oct-2031 · Madeup Gadgets", by.get("MADEUP GADGETS"))
    chk("B3c a credit line carries no paper; the line of the same figure as the UPI paper carries it (the paper stayed on 7 too, named)", not by.get("MADEUP CASH SHOP", [None] * 11)[-2] and by.get("MADEUP RETAIL PVT", [None] * 11)[-2] == "05-Oct-2031 · Madeup Retail Pvt")
    hdr_led = [c.value for c in wb["By ledger"][1]] if wb["By ledger"].max_row else []
    led_rows = [[c.value for c in r] for r in wb["By ledger"].iter_rows()]
    chk("B4 the other sheets untouched (By ledger's header has its 6 cells; Statements 4)", [w.title for w in wb.worksheets] == ["By ledger", "Every line", "Statements"]
        and any(r[:2] == ["Ledger (accountant)", "What it is (owner)"] and len([c for c in r if c is not None]) == 6 for r in led_rows)
        and [c.value for c in wb["Statements"][1]][:4] == ["Card", "Statement dated", "Lines", "Proof against the statement's own totals"], [w.title for w in wb.worksheets])
    chk("B5 every paper of a charge shows on its line; no line shows a paper it has not", sum(1 for r in rows[1:] if r[-2]) == 5 and all(" | " not in str(r[-2]) for r in rows[1:]))
except Exception as e:                                   # noqa: BLE001
    chk("B1-5 the card sheet could be read", False, "%s: %s" % (type(e).__name__, e))

if os.environ.get("S880_DUMP"):                                          # a picture for the owner: the made-up sheets
    open(os.path.join(scr, "madeup_sheet7.xlsx"), "wb").write(b or b"")
    open(os.path.join(scr, "madeup_card_sheet.xlsx"), "wb").write(cb or b"")
# ---- C. the page's words and the empty case
con.execute("DELETE FROM payment_register WHERE vendor NOT IN ('Madeup Cloud','Airtel')")
con.commit()
b2, why2 = p.build_digest(con, M)
try:
    wb2 = load_workbook(io.BytesIO(b2 or b""))
    chk("C1 every paper card-paid: the workbook is the 'Paid by card' sheet alone (the trace), no empty sheet 7", [w_.title for w_ in wb2.worksheets] == ["Paid by card 2031-10"] and wb2.worksheets[0].max_row == 2 + 2 + 1, [w_.title for w_ in wb2.worksheets])
except Exception as e:                                   # noqa: BLE001
    chk("C1 every paper card-paid: the workbook is the 'Paid by card' sheet alone", False, "%s: %s" % (type(e).__name__, e))
src = open(os.path.join(d, "packs.py"), encoding="utf-8").read()
chk("C2 the page's row 7 label says it", "7 · Payment papers not on a card" in src)
chk("C3 no dialog, no Hindi in the new block", "S880" in src and not any(w in src.split("S880 (the parent")[-1].split("def build_neft")[0] for w in ("confirm(", "alert(")) and not any("ऀ" <= ch <= "ॿ" for ch in src))
print("WALK %d/%d" % (ok, n))
sys.exit(0 if ok == n else 1)
