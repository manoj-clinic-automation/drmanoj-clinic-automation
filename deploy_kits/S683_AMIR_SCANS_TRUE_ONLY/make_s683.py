#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s683.py -- kit S683_AMIR_SCANS_TRUE_ONLY (30-Oct-2026, Sanjeevni session 369).

    python3 -B make_s683.py <root> <outdir>        reads <root>/finance/purchase_app.py, writes <outdir>/finance/purchase_app.py

WHY.  The owner, 30-Oct 17:56 IST: Amir's step 2 (#scans) listed six scans -- four of September, a month he has FINALISED, and two of
October -- "why this unnecessary alert?"; 18:05: "build only the fix ... any pdf misread might confuse him?"  Every one was a paper Marg
already has, or a paper that is not this year's: a second scan whose bill number OCR misread (KT-078347 for Marg's 783473; A0001575 for
575), a second scan a person had refused to pair (SF 003499 = Marg's 3499, which already has its scan), a 2023 paper.  scans_for_amir
listed every captured pharmacy scan with no link, whatever its month and however close a Marg bill of its supplier stood.

WHAT.  One file, purchase_app.py, three anchored edits (each anchor must occur exactly once, else the builder refuses):
  1. _s683_final_months and _s683_hold(...) just above scans_for_amir: a scan that passed S452's rules is still HELD (never on Amir's
     list) when
       a. its month is FINALISED (purchase_month.status = 'final'): the scan day's month -- and, when the paper's bill date is read
          within S452_DATE_DAYS of the scan, that month too (a misread paper date never hides an open month's bill) -- "month finalised";
       b. its supplier has a Marg bill (live export) within S439_HINT_DAYS whose number is the scan's number: a digit run equal, or one
          run of 4+ digits inside the other -- or, within S439_DATE_DAYS, the last three digits alike (A0006678 read for A000678) --
          "in Marg: second scan of bill N" when that bill has a scan, else "in Marg: bill N not yet paired".
     A scan Marg does not have, from an open month, stays on his list exactly as before.  (Cold review, F: a rule "an unscanned Marg bill
     of the supplier within 7 days" held 13 of October's 82 bills as if missing -- KEDAR and A.A. bill every 2-3 days; dropped.)
  2. scans_for_amir reads the bills that have a scan and the finalised months once.
  3. ... and calls _s683_hold after S452's rules, once the paper's date is known.
Nothing else changes: the matcher, the links, reception's questions, Amir's screen and its words, the download guard (a held scan
answers "reception ki jaanch mein", as every held scan does), the owner's Scan links line ("N to enter . M held").
"""
import hashlib
import os
import sys

REL = "finance/purchase_app.py"
FROM = "da04d546a27efece47764abea1872151"

EDITS = [
    # 1 -- the hold rule, just above scans_for_amir
    ('\ndef scans_for_amir(con):\n',
     '\n'
     'def _s683_final_months(con):\n'
     '    """S683: the months the owner has finalised on the purchase page (purchase_month.status = \'final\')."""\n'
     '    try:\n'
     '        return {str(r[0]) for r in con.execute("SELECT month FROM purchase_month WHERE status=\'final\'")}\n'
     '    except sqlite3.Error:\n'
     '        return set()\n'
     '\n\n'
     'def _s683_hold(r, sup, cday, bdd, bills, taken, final):\n'
     '    """S683 (the owner, 30-Oct 17:56 / 18:05): a scan S452 would list is HELD -- never on Amir\'s list -- when it is not clearly a bill\n'
     '    missing from Marg.  r: the scan row; sup: its supplier key; cday: the scan day; bdd: the paper\'s bill date when within\n'
     '    S452_DATE_DAYS of the scan, else None; bills: the live export\'s bills; taken: the bill ids that have a scan; final: finalised\n'
     '    months.  -> the reason, or None (the scan stays on his list).  (No unscanned-bill-nearby rule: it hid genuine bills.)"""\n'
     '    if cday is not None and cday.strftime("%Y-%m") in final and (bdd is None or bdd.strftime("%Y-%m") in final):\n'
     '        return "month finalised"                         # the scan day\'s month, and the paper\'s when read near it\n'
     '    stails = _bill_tails_s439(r.get("bill_no"))\n'
     '\n'
     '    def gap(b):\n'
     '        bd = _date_or_none_s439(b.get("bill_date"))\n'
     '        g = [abs((d - bd).days) for d in (bdd, cday) if d is not None and bd is not None]\n'
     '        return min(g) if g else 9999\n'
     '\n'
     '    def same_no(b, tight):\n'
     '        for x in stails:\n'
     '            for y in _bill_tails_s439(b.get("bill_no")):\n'
     '                if x == y or (min(len(x), len(y)) >= 4 and (x in y or y in x)):\n'
     '                    return True\n'
     '                if tight and min(len(x), len(y)) >= 3 and x[-3:] == y[-3:]:      # A0006678 read for A000678, days apart\n'
     '                    return True\n'
     '        return False\n'
     '    mine = [b for b in bills if supplier_key(b.get("supplier")) == sup]\n'
     '    hit = sorted((b for b in mine if stails and ((gap(b) <= S439_HINT_DAYS and same_no(b, False))\n'
     '                                             or (gap(b) <= S439_DATE_DAYS and same_no(b, True)))), key=lambda b: (gap(b), b["id"]))\n'
     '    if hit:\n'
     '        b = hit[0]\n'
     '        return ("in Marg: second scan of bill %s" if b["id"] in taken else "in Marg: bill %s not yet paired") % b["bill_no"]\n'
     '    return None\n'
     '\n\n'
     'def scans_for_amir(con):\n'),

    # 2 -- read once, call after S452's rules
    ('    today = dt.date.today()\n'
     '    out, held = [], []\n'
     '    for r in rows:\n'
     '        sid = int(r["id"])\n'
     '        if sid in linked:\n'
     '            continue\n',
     '    today = dt.date.today()\n'
     '    out, held = [], []\n'
     '    final = _s683_final_months(con)                             # S683: read once\n'
     '    try:\n'
     '        taken = {int(x[0]) for x in con.execute("SELECT bill_id FROM purchase_scan_link")}\n'
     '    except sqlite3.Error:\n'
     '        taken = set()\n'
     '    taken |= {int(b["id"]) for b in bills if b.get("scan_bill_id")}\n'
     '    for r in rows:\n'
     '        sid = int(r["id"])\n'
     '        if sid in linked:\n'
     '            continue\n'),

    # 3 -- the hold, after the bill date is known
    ('        near = bdd is not None and cday is not None and abs((cday - bdd).days) <= S452_DATE_DAYS\n'
     '        item.update(supplier=sup, bill_date=(bd if near else ""),\n',
     '        near = bdd is not None and cday is not None and abs((cday - bdd).days) <= S452_DATE_DAYS\n'
     '        hold = _s683_hold(r, sup, cday, bdd if near else None, bills, taken, final)     # S683: only a bill clearly missing from Marg\n'
     '        if hold:\n'
     '            item["held"] = hold\n'
     '            held.append(item)\n'
     '            continue\n'
     '        item.update(supplier=sup, bill_date=(bd if near else ""),\n'),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(src_bytes):
    if md5(src_bytes) != FROM:
        raise SystemExit("REFUSED: %s is %s, not the FROM pin %s" % (REL, md5(src_bytes)[:8], FROM[:8]))
    s = src_bytes.decode("utf-8")
    for i, (old, new) in enumerate(EDITS, 1):
        n = s.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %d occurs %d times (must be exactly once)" % (i, n))
        s = s.replace(old, new, 1)
    return s.encode("utf-8")


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    root, outdir = sys.argv[1], sys.argv[2]
    with open(os.path.join(root, REL), "rb") as fh:
        out = build(fh.read())
    dst = os.path.join(outdir, REL)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "wb") as fh:
        fh.write(out)
    print("built %s %s -> %s (%d edits)" % (REL, FROM[:8], md5(out)[:8], len(EDITS)))


if __name__ == "__main__":
    main()
