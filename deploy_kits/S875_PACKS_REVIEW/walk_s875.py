#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s875.py -- kit S875 (the parent, S480, 18-Nov-2026), on a MADE-UP root: a made-up finance db (packs.ensure + the
payment register + card lines), a made-up asset app (a bills table in its own sqlite), invented vendors, no real number.
    python3 walk_s875.py <dir holding packs.py + packs.html> <scratch>            last line 'WALK n/m'
Control: the live files go red."""
import os
import sqlite3
import sys
import zipfile

d, scr = sys.argv[1:3]
here = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != here]          # F-1441
sys.path.insert(0, d)
os.makedirs(scr, exist_ok=True)
for f in ("fin.db", "assets.db"):
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
    print(("ok   " if cond else "FAIL ") + name + (("  [" + str(info)[:200] + "]") if (info and not cond) else ""))


try:
    import packs as p
except Exception as e:                                   # noqa: BLE001
    print("FAIL import packs: %s" % e)
    print("WALK 0/24")
    sys.exit(1)

con = sqlite3.connect(os.environ["FINANCE_DB"])
con.row_factory = sqlite3.Row
p.ensure(con)
con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT)")
con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('packs.accountant_to', 'made-up@example.invalid')")
con.execute("CREATE TABLE IF NOT EXISTS payment_register (row_no INTEGER, date_iso TEXT, vendor TEXT, description TEXT, amount_raw TEXT, "
            "amount_paise INTEGER, in_drive INTEGER, gmail_link TEXT)")
pr = [(1, "2031-10-05", "Hostinger & Razorpay", "Payment successful for Madeup Retail Pvt", "", 370000, 0, "g1"),
      (2, "2031-10-06", "Agilus (NK Pathology)", "Invoice for N K PATHOLOGY", "", 35000, 1, "g2"),
      (3, "2031-10-09", "Apple", "Your Subscription Renewal", "", 2490000, 0, "g3"),         # a notice, no receipt, no card line: out
      (4, "2031-10-15", "Apple", "Your receipt from Apple.", "", 2110170, 0, "g4"),          # a receipt matching a card line
      (5, "2031-10-17", "Apple", "Your Subscription Renewal", "", 21900, 0, "g5"),            # a notice with a card line: kept
      (6, "2031-10-20", "Airtel", "Here's your Airtel payment receipt!", "", 291433, 1, "g6"),
      (7, "2031-10-28", "Madeup Hotel", "Your order confirmation", "", 150000, 0, "g7")]   # a confirmation on a date no card statement covers: kept
con.executemany("INSERT INTO payment_register VALUES (?,?,?,?,?,?,?,?)", pr)
try:
    import card_lines
    card_lines.ensure(con)
    have_cards = True
except Exception as e:                                   # noqa: BLE001
    have_cards = False
    print("note card_lines not importable here: %s" % e)
if have_cards:
    con.execute("INSERT INTO card_stmt (id, file_id, slot_key, bank, statement_date, period_from, period_to, proof_ok, lines) VALUES "
                "(1, 1, 'card_icici_amazon', 'ICICI', '2031-10-12', '2031-09-13', '2031-10-12', 1, 2)")
    con.execute("INSERT INTO card_line (stmt_id, slot_key, txn_date, description, merchant, kind, amount_p, credit, seq) VALUES "
                "(1, 'card_icici_amazon', '2031-10-14', 'APPLE MADEUP', 'APPLE MADEUP', 'spend', 2110170, 0, 1)")
    con.execute("INSERT INTO card_line (stmt_id, slot_key, txn_date, description, merchant, kind, amount_p, credit, seq) VALUES "
                "(1, 'card_icici_amazon', '2031-10-18', 'APPLE MADEUP', 'APPLE MADEUP', 'spend', 21900, 0, 2)")
con.commit()

# the made-up asset app
acon_path = os.path.join(scr, "assets.db")
a = sqlite3.connect(acon_path)
a.execute("CREATE TABLE bills (id INTEGER PRIMARY KEY, stamp_no TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, bill_month TEXT, total_amount REAL, "
          "source_stored TEXT, late_for TEXT, created_at TEXT, lane TEXT, status TEXT, doc_kind TEXT, subgroup TEXT, to_accountant INTEGER, pe_who TEXT)")
B = [  # id, stamp, vendor, no, date, month, total, late_for, created, lane, doc_kind, pe_who
    (1, "B-9001", "MADEUP SCIENTIFIC", "A1", "2031-10-16", None, 50000.0, None, "2031-10-18 08:00:00", "lab_purchase", "bill", None),
    (2, "B-9002", "MADEUP RADIATION", "R1", "2031-09-30", "2031-10", 1.0, None, "2031-10-08 07:00:00", "lab_purchase", "bill", None),   # Rs 1: held
    (3, "B-9003", "MADEUP CARE", "", "2031-05-21", None, 3969.0, "2031-05", "2031-10-22 17:00:00", "lab_purchase", "bill", None),        # marked late
    (4, "B-9004", "MADEUP CARE", "717", "2031-06-23", None, 12600.0, None, "2031-10-22 17:00:00", "lab_purchase", "bill", None),        # NOT marked: late
    (5, "B-9005", "MADEUP NOTOTAL", "", "2031-10-02", None, None, None, "2031-10-03 06:00:00", "lab_purchase", "bill", None),             # no total: held
    (6, "B-9006", "MADEUP DOUBLE LTD", "D1", "2031-10-10", None, 850.0, None, "2031-10-10 06:00:00", "clinic", "bill", None),
    (7, "B-9007", "Madeup Double Pvt", "D1", "2031-10-10", None, 850.0, None, "2031-10-10 06:05:00", "lab_purchase", "bill", None),   # the same paper: held
    (8, "B-9008", "MADEUP RECEIPT", "", "2031-10-11", None, 850.0, None, "2031-10-11 06:00:00", "lab_purchase", "receipt", None),     # a receipt: never
    (9, "B-9009", "MADEUP NODATE", "", None, None, 500.0, None, "2031-10-12 06:00:00", "lab_purchase", "bill", None),                  # no date: held
    (10, "B-9010", "MADEUP COMPUTERS", "C1", "2031-07-06", None, 32900.0, None, "2031-10-01 12:00:00", "owner_expense", "bill", None),  # unmarked late
    (11, "B-9011", "M/S ALPHA TRADERS", "X1", "2031-10-20", None, 700.0, None, "2031-10-20 06:00:00", "lab_purchase", "bill", None),
    (12, "B-9012", "M/s Alpha Traders", "X2", "2031-10-20", None, 700.0, None, "2031-10-20 06:01:00", "lab_purchase", "bill", None),   # another bill no: both in
    (13, "B-9013", "MADEUP OLDEN", "O1", "2030-06-10", None, 100.0, None, "2031-10-21 06:00:00", "lab_purchase", "bill", None),          # > a year back: held
    (14, "B-9014", "MADEUP SEPT", "S1", "2031-09-20", None, 400.0, None, "2031-10-03 06:00:00", "lab_purchase", "bill", None),           # late, September
]
for r in B:
    a.execute("INSERT INTO bills (id, stamp_no, vendor, bill_no, bill_date, bill_month, total_amount, source_stored, late_for, created_at, lane, status, doc_kind, subgroup, to_accountant, pe_who) "
              "VALUES (?,?,?,?,?,?,?,'',?,?,?, 'captured', ?, '', 0, ?)", (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11]))
a.commit()
a.close()


def _acon():
    c = sqlite3.connect(acon_path)
    c.row_factory = sqlite3.Row
    return c


p._assets_con = _acon
M = "2031-10"

# ---- A. the bundle's papers
br = getattr(p, "bundle_rows", None)
if br:
    rows, held, why = br(con, M, "lab_purchase")
    ids = [r["id"] for r in rows]
    hid = {h["id"]: h["why"] for h in held}
    chk("A1 the month's bills first, then the late ones by month (marked or not)", ids == [1, 11, 12, 3, 4, 14], ids)
    chk("A1b two bills of one vendor, date and total but two bill numbers: both in", 11 in ids and 12 in ids, hid if False else ids)
    chk("A1c a paper from more than a year back is named, not bundled", "more than a year back" in hid.get(13, ""), hid)
    chk("A1d 'M/s Alpha Traders' keys on ALPHA", getattr(p, "_s875_vkey", lambda v: "")("M/s Alpha Traders") == "ALPHA")
    # September's pack sent on 5-Oct WITHOUT the bundle: the late September paper still comes in October
    import json as _json
    con.execute("INSERT INTO pack_send (month, sent_at, sent_by, what, message_id, to_list, parts, bytes, resend) VALUES (?,?,?,?,?,?,?,?,?)",
                ("2031-09", "2031-10-05T10:00:00", "manoj", _json.dumps(["Payment digest - September 2031.xlsx"]), "m1", "x", 1, 1, 0))
    chk("A1e a late paper whose month went WITHOUT the bundle still comes", 14 in [r["id"] for r in br(con, M, "lab_purchase")[0]])
    con.execute("INSERT INTO pack_send (month, sent_at, sent_by, what, message_id, to_list, parts, bytes, resend) VALUES (?,?,?,?,?,?,?,?,?)",
                ("2031-09", "2031-10-06T10:00:00", "manoj", _json.dumps(["Dr Bhawna's lab-purchase bills - September 2031.pdf"]), "m2", "x", 1, 1, 0))
    chk("A1f ... and not once that month's mail carried it", 14 not in [r["id"] for r in br(con, M, "lab_purchase")[0]])
    con.execute("DELETE FROM pack_send")
    con.commit()
    chk("A2 a total of Rs 1 kept out, with its reason", "total read as Rs 1.00" in hid.get(2, ""), hid)
    chk("A3 no total kept out", hid.get(5) == "no total read", hid)
    chk("A4 the same paper in another lane kept out, naming it", "B-9006" in hid.get(7, ""), hid)
    chk("A5 no bill date kept out", hid.get(9) == "no bill date", hid)
    chk("A6 a receipt never in a bundle", 8 not in ids and 8 not in hid)
    r2, _h2, _w = br(con, M, "owner_expense")
    chk("A7 an expense paper scanned after its month (never marked late) is in", [r["id"] for r in r2] == [10], r2)
else:
    for k in range(7):
        chk("A%d bundle_rows exists" % (k + 1), False)

# ---- B. the bundle's index
b, why = p.build_bundle(con, M, "lab_purchase")
txt = (b or b"").decode("latin-1", "replace")
chk("B1 the bundle builds", bool(b), why)
chk("B2 the index heads the month with its count and total", "October 2031 -- 3 bills, Rs 51400.00" in txt, txt[:400])
chk("B3 a part for the papers scanned late, month by month", "Scanned in October 2031 for earlier months -- 3 bills, Rs 16969.00" in txt
    and "May 2031 -- 1 bill, Rs 3969.00" in txt and "June 2031 -- 1 bill, Rs 12600.00" in txt and "September 2031 -- 1 bill, Rs 400.00" in txt)
chk("B4 no kept-out paper in the bundle", not any(s in txt for s in ("B-9002", "B-9005", "B-9007", "B-9009")))

# ---- C. the pack: kept back by default, sent when ticked
rows, att = p.pack_rows(con, M)
r81 = next((r for r in rows if r["key"] == "bundle:lab_purchase"), {})
chk("C1 8.1 is ready but kept back by default", r81.get("status") == "ready" and (r81.get("optin") or {}).get("on") is False
    and "Kept back" in (r81.get("why") or ""), r81)
chk("C2 ... it names the papers kept out", all(s in (r81.get("why") or "") for s in ("B-9002", "B-9005", "B-9007", "B-9009")), r81.get("why"))
chk("C3 ... and it is not among the attachments", not any(x[0].startswith("Dr Bhawna's lab-purchase bills") for x in att), [x[0] for x in att])
body, code = p.send_pack(con, {"user": "manoj"}, M)
mails = sorted(os.listdir(os.environ["PACKS_MAIL_STUB"])) if os.path.isdir(os.environ["PACKS_MAIL_STUB"]) else []
eml = open(os.path.join(os.environ["PACKS_MAIL_STUB"], mails[0]), "rb").read().decode("latin-1") if mails else ""
chk("C4 the mail goes without section 8 and does not name it", code == 200 and "8.1" not in eml and "lab-purchase bills" not in eml, (code, body))
con.execute("INSERT INTO pack_tick (month, item, done_by, done_at) VALUES (?,?,?,?)", (M, "send8:lab_purchase", "manoj", "2031-11-01T10:00:00"))
con.commit()
rows, att = p.pack_rows(con, M)
r81 = next((r for r in rows if r["key"] == "bundle:lab_purchase"), {})
chk("C5 ticked: it goes, with the bundle attached", (r81.get("optin") or {}).get("on") is True
    and any(x[0].startswith("Dr Bhawna's lab-purchase bills") for x in att), r81)
for f in mails:
    os.remove(os.path.join(os.environ["PACKS_MAIL_STUB"], f))
con.execute("DELETE FROM pack_send")
con.commit()
body, code = p.send_pack(con, {"user": "manoj"}, M)
mails = sorted(os.listdir(os.environ["PACKS_MAIL_STUB"]))
eml = open(os.path.join(os.environ["PACKS_MAIL_STUB"], mails[0]), "rb").read().decode("latin-1") if mails else ""
chk("C6 ... the mail names it as enclosed", "8.1" in eml and "[enclosed]" in eml, code)

# ---- D. the payment papers
k, dr, tot = p.digest_rows(con, M)
vend = [r["vendor"] for r in k]
chk("D1 'Payment successful for X' shows X as the vendor", "Madeup Retail Pvt" in vend, vend)
chk("D2 a renewal notice with no receipt and no card line is dropped", not any(r["amount"] == 24900.0 for r in k)
    and any("not a charge" in x["why"] for x in dr), dr)
chk("D3 a notice that matches a card line stays", any(r["amount"] == 219.0 for r in k) if have_cards else True, k)
chk("D3b a confirmation paid otherwise (no card statement covers its date) stays", any(r["amount"] == 1500.0 for r in k), k)
rc = next((r for r in k if r["amount"] == 21101.7), {})
chk("D4 a receipt names its card line", (not have_cards) or ("ICICI Amazon Pay" in (rc.get("card") or "") and "14-Oct-2031" in (rc.get("card") or "")), rc)
db, _w = p.build_digest(con, M)
names = []
if db:
    with open(os.path.join(scr, "d.xlsx"), "wb") as fh:
        fh.write(db)
    from openpyxl import load_workbook
    wb = load_workbook(os.path.join(scr, "d.xlsx"))
    names = wb.sheetnames
    ws = wb[names[0]]
    vals = [[c.value for c in r] for r in ws.iter_rows()]
chk("D5 NK Pathology's papers on their own sheet", len(names) == 2 and names[1].startswith("NK Pathology")
    and not any("PATHOLOGY" in str(v[2] or "").upper() for v in vals[2:]), names)
chk("D6 the sheet has the card column and says 'not on a card statement' where none", db and vals[1][4].startswith("Paid by card")
    and any(v[4] == "not on a card statement" for v in vals[2:]), vals[:3] if db else None)

# ---- E. the card sheet's periods
cov = getattr(p, "_s875_covers", lambda *a: [])(con, [{"slot": "card_icici_amazon", "statement_date": "2031-10-12", "label": "ICICI Amazon Pay"}])
chk("E1 the card sheet names what each statement covers", (not have_cards) or cov == ["ICICI Amazon Pay: 13-Sep-2031 to 12-Oct-2031"], cov)
cs = p.card_spends(con, M) if have_cards else {}
st = [s for s in (cs.get("statements") or []) if s.get("slot") == "card_icici_amazon"]
chk("E2 the page's statement table carries 'covers'", (not have_cards) or (st and st[0].get("covers") == "13-Sep-2031 to 12-Oct-2031"), st)

# ---- F. the door and the page
con.commit()                                             # the walk's own connection holds no lock over the door
try:
    import flask
    app = flask.Flask("w875")
    p.init(app, lambda: sqlite3.connect(os.environ["FINANCE_DB"]), lambda *a, **kw: ({"user": "manoj"}, None))
    cl = app.test_client()
    r = cl.post("/finance/packs/api/send8", json={"month": M, "lane": "lab_purchase", "on": False})
    c2 = sqlite3.connect(os.environ["FINANCE_DB"])
    off = c2.execute("SELECT COUNT(*) FROM pack_tick WHERE month=? AND item='send8:lab_purchase'", (M,)).fetchone()[0]
    chk("F1 the door keeps a bundle back (untick)", r.status_code == 200 and off == 0, (r.status_code, off))
    r = cl.post("/finance/packs/api/send8", json={"month": M, "lane": "nonsense", "on": True})
    chk("F2 the door refuses an unknown lane", r.status_code == 400)
    r = cl.get("/finance/packs?month=" + M)
    page = r.get_data(as_text=True)
    chk("F3 the page renders with the new button and the Covers column", r.status_code == 200 and "function send8(" in page and "<th>Covers</th>" in page, r.status_code)
except Exception as e:                                   # noqa: BLE001
    chk("F0 the door and page could be tried", False, "%s: %s" % (type(e).__name__, e))
print("WALK %d/%d" % (ok, n))
sys.exit(0 if ok == n else 1)
