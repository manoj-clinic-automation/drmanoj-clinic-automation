#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s880.py <dir holding packs.py at its FROM pin> <out dir> -- kit S880_SHEET7_VOUCHERS (the parent, S484, 18-Nov-2026).
His word 17:23: sheet 7 must not repeat the card spends. A payment paper whose charge is on a card statement leaves sheet 7 and
becomes the receipt column of its line in the card sheet (4.4); sheet 7 keeps only the payments on no card, each with where its
debit is (the bank statement line it matches, or 'receipt only'). Seven anchored patches on packs.py + one appended block (the cold review's two MUSTs and SHOULDs 3-7 built in).
Every anchor must match exactly once; the FROM pin is checked first (F-472)."""
import hashlib
import os
import sys

SRC, OUT = sys.argv[1], sys.argv[2]
FROM = "68c7c79d"
p = os.path.join(SRC, "packs.py")
b = open(p, "rb").read()
h = hashlib.md5(b).hexdigest()
assert h.startswith(FROM), "packs.py is %s, not at the FROM pin %s" % (h[:8], FROM)
s = b.decode("utf-8")


def one(old, new):
    global s
    assert s.count(old) == 1, "anchor not found once (%d): %r" % (s.count(old), old[:90])
    s = s.replace(old, new)


# A1 build_digest: split the papers; the empty case worded
one('''    kept, dropped, total = digest_rows(con, month)
    if not kept:
        return None, "no payments in the payment register for %s" % _month_name(month)
    head = ("Date", "Vendor", "Description", "Amount Rs", "Paid by card (its line in the card sheet, 4.4)", "Attachment in Drive")   # S875
''', '''    kept, dropped, total = digest_rows(con, month)
    kept, dropped, moved = _s880_split(con, kept, dropped)                # S880: card-paid papers go to the card sheet's receipt column
    if not kept and not moved:
        return None, "no payments in the payment register for %s" % _month_name(month)
    head = ("Date", "Vendor", "Description", "Amount Rs", "Where the debit is", "Attachment in Drive")   # S880
''')
# A1b the moved papers' own sheet (the trace), and no empty first sheet
one('''    if nk:                                                              # S875: the lab's papers on their own sheet
        sheets.append(("NK Pathology %s" % month, sheet(nk, "NK Pathology's payment papers, %s -- the lab's own books" % _month_name(month))))
    return _s877_xlsx(sheets, S877_DIGEST), None                        # S877: laid out to be read
''', '''    if nk:                                                              # S875: the lab's papers on their own sheet
        sheets.append(("NK Pathology %s" % month, sheet(nk, "NK Pathology's payment papers, %s -- the lab's own books" % _month_name(month))))
    if moved:                                                           # S880: the trace of every paper that went to the card sheet
        sheets.append(("Paid by card %s" % month, _s880_moved_sheet(moved, month)))
    if not mine:
        sheets = sheets[1:]
    return _s877_xlsx(sheets, S877_DIGEST), None                        # S877: laid out to be read
''')
# A2 the row: the debit column
one('''                        r.get("card") or "not on a card statement", "yes" if r["in_drive"] else ""))''',
    '''                        r.get("debit") or "", "yes" if r["in_drive"] else ""))                      # S880''')
# A3 the sheet's title
one('''"Payment papers found in mail, %s -- one row per charge; a card payment is also a line of the card sheet (4.4)" % _month_name(month)''',
    '''"Payments not on any card, %s -- one row per charge, each with where its debit is; card-paid papers sit in the receipt column of the card sheet (4.4)" % _month_name(month)''')
# A4 the page's row label
one('''"7 · Payment papers found in mail (one row per charge; they overlap the card spends)"''',
    '''"7 · Payment papers not on a card (one row per charge, each with where its debit is; card-paid papers are on the card sheet, 4.4)"''')
# A5 the card sheet: the receipt column
one('''        sheets[0] = (t0, [["Card statements DATED in %s -- each covers its own billing cycle, so many lines fall in the month before:" % _month_name(month)]]
                     + [[c] for c in cov] + [[]] + list(r0))
    return _xlsx(sheets), None
''', '''        sheets[0] = (t0, [["Card statements DATED in %s -- each covers its own billing cycle, so many lines fall in the month before:" % _month_name(month)]]
                     + [[c] for c in cov] + [[]] + list(r0))
    sheets = _s880_receipt_column(con, sheets)                               # S880: each line's payment paper, when there is one
    return _xlsx(sheets), None
''')
# A6 the appended block, before build_neft
one('''def build_neft(con, month):
    """(6, Sanjeevni) the NEFT advice Excel + the covering letter, from purchase_app's own routes' code."""
''', '''# ---- S880 (the parent, S484, 18-Nov-2026): sheet 7 stops repeating the card spends ------------------------------------------
S880_DAYS = 7                                                             # a debit within this many days of the paper's date


def _s880_card_line(con, r):
    """S880: the card line a paper matches -- (slot_key, txn_date, amount_p) or None; the S875 rule (amount within Rs 1, 7 days)."""
    amt = r.get("amount")
    if not amt or not _has(con, "card_line"):
        return None
    try:
        d0 = dt.date.fromisoformat(str(r.get("date") or "")[:10])
    except ValueError:
        return None
    row = con.execute("SELECT l.slot_key, l.txn_date, l.amount_p, s.statement_date FROM card_line l LEFT JOIN card_stmt s ON s.id=l.stmt_id "
                      "WHERE COALESCE(l.credit,0)=0 AND ABS(l.amount_p - ?) <= 100 AND l.txn_date BETWEEN ? AND ? "
                      "ORDER BY ABS(julianday(l.txn_date) - julianday(?)), l.id LIMIT 1",
                      (int(round(float(amt) * 100)), (d0 - dt.timedelta(days=S880_DAYS)).isoformat(),
                       (d0 + dt.timedelta(days=S880_DAYS)).isoformat(), d0.isoformat())).fetchone()
    return (row[0], row[1], row[2], str(row[3] or "")[:7]) if row else None


def _s880_cards_covered(con, date):
    """S880: is the date inside a read statement of EVERY card on the shelf (so a missing card line means something)?"""
    if not _has(con, "card_stmt"):
        return False
    try:
        d0 = dt.date.fromisoformat(str(date or "")[:10]).isoformat()
    except ValueError:
        return False
    cards = [r[0] for r in con.execute("SELECT key FROM stmt_slot WHERE kind='card'")]
    if not cards:
        return False
    for k in cards:
        if con.execute("SELECT 1 FROM card_stmt WHERE slot_key=? AND period_from<=? AND period_to>=? LIMIT 1", (k, d0, d0)).fetchone() is None:
            return False
    return True


def _s880_bank_covered(con, date):
    """S880: has any bank statement line of that date or later been read (the shelf's three line tables)?"""
    try:
        d0 = dt.date.fromisoformat(str(date or "")[:10]).isoformat()
    except ValueError:
        return False
    for table in ("icici_statement_line", "bank_statement_line", "yesbank_account_statement_line"):
        if not _has(con, table):
            continue
        try:
            if con.execute("SELECT 1 FROM %s WHERE txn_date >= ? LIMIT 1" % table, (d0,)).fetchone():
                return True
        except Exception:                                                # noqa: BLE001
            continue
    return False


def _s880_slot_labels(con):
    """S880: account tail -> the holder's label, from stmt_slot (ident_tail may carry two tails); slot key -> label too."""
    out = {}
    for key, label, tails in con.execute("SELECT key, holder_label, COALESCE(ident_tail,'') FROM stmt_slot"):
        out[key] = label
        for t in str(tails).split(","):
            if t.strip():
                out[t.strip()] = label
    return out


def _s880_bank_line(con, r):
    """S880: the bank statement line a paper's debit matches -- 'Dr Manoj Agarwal Clinic (ICICI) statement, 15-Oct-2026' -- or ''.
    Reads the three statement-line tables the shelf fills; amount within Rs 1, date within S880_DAYS; withdrawals only."""
    amt = r.get("amount")
    if not amt:
        return ""
    try:
        d0 = dt.date.fromisoformat(str(r.get("date") or "")[:10])
    except ValueError:
        return ""
    lo, hi = (d0 - dt.timedelta(days=S880_DAYS)).isoformat(), (d0 + dt.timedelta(days=S880_DAYS)).isoformat()
    ap = int(round(float(amt) * 100))
    labels = _s880_slot_labels(con)
    best = None
    for table, refcol in (("icici_statement_line", "account_ref"), ("bank_statement_line", "account_ref"),
                          ("yesbank_account_statement_line", "COALESCE(slot_key, account_ref)")):
        if not _has(con, table):
            continue
        try:
            row = con.execute("SELECT %s, txn_date FROM %s WHERE withdrawal_p > 0 AND ABS(withdrawal_p - ?) <= 100 AND txn_date BETWEEN ? AND ? "
                              "ORDER BY ABS(julianday(txn_date) - julianday(?)), id LIMIT 1" % (refcol, table), (ap, lo, hi, d0.isoformat())).fetchone()
        except Exception:                                                # noqa: BLE001 -- a table shaped otherwise is skipped
            row = None
        if row:
            gap = abs((dt.date.fromisoformat(str(row[1])[:10]) - d0).days)
            if best is None or gap < best[0]:
                best = (gap, str(row[0]), str(row[1]))
    if not best:
        return ""
    ref = best[1]
    return "%s statement, %s" % (labels.get(ref) or labels.get(ref[-4:]) or ("account ..." + ref[-4:]), _dmy(best[2]))


def _s880_split(con, kept, dropped):
    """S880: a paper whose charge is a card line leaves sheet 7 -- it goes to the workbook's own 'Paid by card' sheet (the trace) and
    is the receipt column of that line in the card sheet; the rest get 'debit' -- the bank line, or why none. A paper that matches
    both a bank line and a card line stays on sheet 7 with both named. (kept, dropped, moved)."""
    out, moved = [], []
    for r in kept:
        cl = _s880_card_line(con, r)
        bank = _s880_bank_line(con, r)
        if cl and bank:
            r["debit"] = "%s; a card line of the same figure too (%s, %s) -- check which" % (bank, _card_labels(con).get(cl[0], cl[0]), _dmy(cl[1]))
            out.append(r)
            continue
        if cl:
            r["card"] = "%s, %s" % (_card_labels(con).get(cl[0], cl[0]), _dmy(cl[1]))
            r["card_month"] = _month_name(cl[3]) if cl[3] else ""
            moved.append(r)
            dropped.append(dict(date=r["date"], vendor=r["vendor"], why="paid by card -- %s; its receipt is on the card sheet (4.4) of %s and on this workbook's 'Paid by card' sheet"
                                % (r["card"], r["card_month"] or "that statement's month")))
            continue
        if bank:
            r["debit"] = bank
        elif not r.get("amount"):
            r["debit"] = "amount on the receipt -- not matched to a statement"
        else:
            cc, bc = _s880_cards_covered(con, r.get("date")), _s880_bank_covered(con, r.get("date"))
            if not cc and not bc:
                r["debit"] = "card and bank statements of this date not yet read -- moves to the card sheet if one carries it"
            elif not cc:
                r["debit"] = "no bank line; not every card's statement of this date is read yet -- moves to the card sheet if one carries it"
            elif not bc:
                r["debit"] = "no card line; the bank statements of this date are not yet read"
            else:
                r["debit"] = "receipt only -- no card or bank statement of this date carries it (cash, an account not on the shelf, or a later debit)"
        out.append(r)
    return out, dropped, moved


def _s880_moved_sheet(moved, month):
    """S880: the digest workbook's 'Paid by card' sheet -- every paper of the month that left sheet 7 for the card sheet."""
    out = [("Paid by card, %s -- these papers are the receipts of lines in the card sheet (4.4); not a second list of spends" % _month_name(month), "", "", "", "", ""),
           ("Date", "Vendor", "Description", "Amount Rs", "The card line (its sheet 4.4 is the statement's month)", "Attachment in Drive")]
    for r in moved:
        out.append((r["date"], r["vendor"], r["desc"], r["amount"] if r["amount"] is not None else "see the receipt",
                    "%s -- card sheet of %s" % (r.get("card") or "", r.get("card_month") or "its statement's month"), "yes" if r.get("in_drive") else ""))
    out.append(("", "", "TOTAL (rows with an amount)", round(sum((r["amount"] or 0) for r in moved), 2), "", ""))
    return out


def _s880_receipt_column(con, sheets):
    """S880: the card sheet's 'Every line' gets two columns -- the payment paper (sheet 7's register) that is this line's
    receipt, and whether it is in Drive. One paper serves one line (the nearest by date). Other sheets untouched."""
    if not _has(con, "payment_register"):
        return sheets
    out = []
    for title, rows in sheets:
        if title != "Every line" or not rows:
            out.append((title, rows))
            continue
        months = sorted({str(x[0])[6:10] + "-" + str(x[0])[3:5] for x in rows[1:] if x and x[0] and len(str(x[0])) == 10})
        papers = []
        for m in months:
            try:
                k, _d, _t = digest_rows(con, m)
            except Exception:                                            # noqa: BLE001
                k = []
            papers += [x for x in k if x.get("amount")]
            try:                                                         # the month before too: a paper of the 30th, a line of the 2nd
                k2, _d2, _t2 = digest_rows(con, _prev_month(m))
            except Exception:                                            # noqa: BLE001
                k2 = []
            papers += [x for x in k2 if x.get("amount")]
        seen, uniq = set(), []
        for x in papers:
            key = (x.get("date"), x.get("vendor"), x.get("amount"), x.get("desc"))
            if key not in seen:
                seen.add(key)
                uniq.append(x)
        head = list(rows[0])
        idr = head.index("Dr (Rs)") if "Dr (Rs)" in head else 6
        new = [head + ["Receipt (payment paper found in mail)", "Receipt in Drive"]]
        for x in rows[1:]:
            x = list(x)
            cell, drive = "", ""
            try:
                d0 = dt.date(int(str(x[0])[6:10]), int(str(x[0])[3:5]), int(str(x[0])[0:2]))
                dr = float(x[idr]) if len(x) > idr and x[idr] not in (None, "") else None
            except (TypeError, ValueError):
                d0, dr = None, None
            if d0 and dr:
                hits = []
                for pr in uniq:
                    if abs(float(pr["amount"]) - dr) > 1.0 + 1e-9:                 # the split's rule: within Rs 1
                        continue
                    try:
                        gap = abs((dt.date.fromisoformat(str(pr["date"])[:10]) - d0).days)
                    except ValueError:
                        continue
                    if gap <= S880_DAYS:
                        hits.append((gap, pr))
                hits.sort(key=lambda t: t[0])
                cell = " | ".join("%s · %s" % (_dmy(pr["date"]), str(pr.get("vendor") or "")[:40]) for _g, pr in hits)   # every paper of the charge
                drive = "yes" if any(pr.get("in_drive") for _g, pr in hits) else ""
            new.append(x + [cell, drive])
        out.append((title, new))
    return out


def build_neft(con, month):
    """(6, Sanjeevni) the NEFT advice Excel + the covering letter, from purchase_app's own routes' code."""
''')
os.makedirs(OUT, exist_ok=True)
o = os.path.join(OUT, "packs.py")
open(o, "wb").write(s.encode("utf-8"))
print("packs.py %s -> %s (%d -> %d bytes)" % (h[:8], hashlib.md5(s.encode("utf-8")).hexdigest()[:8], len(b), len(s.encode("utf-8"))))
