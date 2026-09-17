#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_supplier_check_s285.py -- S285: Amir's bill list warns when a bill names a
supplier who has never supplied that item, while another supplier always has.

THE FAULT (owner, 17-Sep): in August Amir entered a purchase under the wrong
supplier; it was found later and corrected by hand. Marg itself is consistent
with such a mistake -- every export repeats the wrong name -- so nothing in the
system could see it. The witness is history: 1,500+ purchase lines since April,
and for almost every item exactly one supplier has ever supplied it.

THE RULE. For each bill still waiting for his Theek hai / Theek nahi: for each
item on it, if THIS supplier has never supplied the item before and ANOTHER
supplier has supplied it on two or more earlier bills, the bill carries a warning
naming the item and the usual supplier. A never-bought item raises nothing (the
new-item list already does). A genuine second source trips once; after he marks
it Theek hai that pair is history and it never trips again.

WHERE. On the bill itself, in step 4, above Theek hai -- in his words, in Hindi.
One more reason under Theek nahi: "Supplier galat likha" (not a claim for Darpan
to chase -- the vendor owes nothing; it is Amir's own correction in Marg).

AND THE CLEAR. A bill he corrects in Marg comes back under the right supplier in
the next export, and the wrong one is gone from Marg. Until now the wrong one
stayed on his list for ever (its export row lives on, superseded). The list now
shows only bills that a LIVE export still carries: the corrected bill appears,
the wrong one disappears by itself.

FIVE anchored edits and one helper appended. Nothing else is touched:

  A  REASONS gains ("supplier", "Supplier galat likha")   -- not in CLAIM_REASONS
  B  _bills(): only bills a live export still carries (the self-clear)
  C  _bills(): the warning computed for today's and carried bills
  D  _bill_block(): the warning rendered above Theek hai
  E  the stylesheet: one rule for the warning box
  F  _supplier_warn_s285() appended at the end of the file

    python3 -B patch_supplier_check_s285.py --file /root/finance/amir_day.py --from <md5>
"""
import argparse
import hashlib
import io
import os
import shutil
import sys

MARK = "_supplier_warn_s285"

EDITS = [
    # A -- the reason
    ('''    ("discount",  "Discount kam"),
    ("other",     "Aur koi baat"),
)''',
     '''    ("discount",  "Discount kam"),
    ("supplier",  "Supplier galat likha"),
    ("other",     "Aur koi baat"),
)'''),
    # B -- only bills a live export still carries
    ('''            WHERE (d.reason IS NULL OR d.reason <> 'ok')
              AND e.type = 'BILLWISE'
              AND b.bill_date >= ?
         GROUP BY b.supplier_norm, b.bill_no, b.bill_date, d.reason""",''',
     '''            WHERE (d.reason IS NULL OR d.reason <> 'ok')
              AND e.type = 'BILLWISE'
              AND b.bill_date >= ?
              AND EXISTS (SELECT 1 FROM purchase_bill b2
                            JOIN purchase_export e2 ON e2.md5 = b2.bw_md5
                           WHERE e2.superseded_by IS NULL AND e2.type = 'BILLWISE'
                             AND b2.supplier_norm = b.supplier_norm
                             AND b2.bill_no = b.bill_no AND b2.bill_date = b.bill_date)
         GROUP BY b.supplier_norm, b.bill_no, b.bill_date, d.reason""",'''),
    # C -- the warning on the unanswered bills
    ('''    for lst in (today_rows, carry, flagged):
        lst.sort(key=lambda x: ((x.get("bill_date") or ""), (x.get("supplier") or "")),
                 reverse=True)
    return today_rows, carry, flagged''',
     '''    for lst in (today_rows, carry, flagged):
        lst.sort(key=lambda x: ((x.get("bill_date") or ""), (x.get("supplier") or "")),
                 reverse=True)
    for d in today_rows + carry:
        d["warn"] = _supplier_warn_s285(cx, d)
    return today_rows, carry, flagged'''),
    # D -- rendered above Theek hai
    ('''    return ("<div class=bill><div class=who>%s</div>"
            "<div class=meta>Bill %s &middot; %s &middot; &#8377;%s</div>%s"
            "<input type=hidden name='k_%d' value='%s'>"''',
     '''    for item, usual, n in (b.get("warn") or []):
        was += ("<div class=swarn>&#9888; <b>%s</b> pehle hamesha <b>%s</b> se aaya hai "
                "(%d bill). Is bill par <b>%s</b> likha hai &mdash; Marg mein bill dekh lijiye.</div>"
                % (_esc(item), _esc(usual), n, _esc(b.get("supplier") or b.get("supplier_norm"))))
    return ("<div class=bill><div class=who>%s</div>"
            "<div class=meta>Bill %s &middot; %s &middot; &#8377;%s</div>%s"
            "<input type=hidden name='k_%d' value='%s'>"'''),
    # E -- the stylesheet
    ('''.bill details.notok{border:1px solid var(--line);border-radius:10px;background:#fff}''',
     '''.bill .swarn{margin:0 0 8px;padding:11px 13px;border:1px solid #f0c36d;border-radius:10px;
            background:#fff8e6;color:#6b4e00;font-size:15px;line-height:1.45}
.bill details.notok{border:1px solid var(--line);border-radius:10px;background:#fff}'''),
]

APPEND = '''

def _supplier_warn_s285(cx, b):
    """S285: does every item on this bill belong to the supplier the bill names?

    For each item on the bill (its lines in a live export): the suppliers who have
    supplied that item on EARLIER bills, counted by bill. If this supplier has
    never supplied it and another has on two or more bills, one warning:
    (item, that supplier, how many bills). Never-bought items raise nothing. Any
    failure to read -- no line table yet, an odd row -- means no warning, never a
    broken page."""
    out = []
    try:
        if not _table_exists(cx, "purchase_line"):
            return out
        live = ("EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL "
                "AND e.md5 = l.source_md5)")
        items = cx.execute(
            "SELECT DISTINCT l.item FROM purchase_line l WHERE l.supplier_norm = ? "
            "AND l.bill_no = ? AND l.bill_date = ? AND l.item IS NOT NULL AND " + live +
            " ORDER BY l.item",
            (b.get("supplier_norm"), b.get("bill_no"), b.get("bill_date"))).fetchall()
        for (item,) in items:
            hist = cx.execute(
                "SELECT l.supplier_norm, COUNT(DISTINCT l.bill_no || '|' || l.bill_date) AS n "
                "FROM purchase_line l WHERE l.item = ? AND l.supplier_norm IS NOT NULL "
                "AND l.bill_date < ? AND " + live + " GROUP BY l.supplier_norm",
                (item, b.get("bill_date"))).fetchall()
            mine = sum(int(n) for s, n in hist if s == b.get("supplier_norm"))
            others = sorted(((int(n), s) for s, n in hist if s != b.get("supplier_norm")),
                            reverse=True)
            if mine == 0 and others and others[0][0] >= 2:
                out.append((item, others[0][1], others[0][0]))
    except Exception:
        return out
    return out
'''


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--from", dest="from_md5", default=None)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)

    if not os.path.exists(a.file):
        sys.exit("REFUSING: %s not found" % a.file)
    raw = io.open(a.file, "rb").read()
    cur = md5(raw)
    src = raw.decode("utf-8")

    if MARK in src:
        print("ALREADY PATCHED (%s present); pin %s -- nothing to do" % (MARK, cur))
        return 0
    if a.from_md5 and cur != a.from_md5.lower():
        sys.exit("REFUSING: %s is %s, you said %s" % (a.file, cur, a.from_md5))
    for need in ("def _bills(cx, day):", "def _bill_block(i, b):", "def _table_exists(cx, name):",
                 'CLAIM_REASONS = ("short", "nodeal", "discount", "other")'):
        if need not in src:
            sys.exit("REFUSING: %s is not in this file. S285 has nothing to patch." % need)
    for i, (old, _new) in enumerate(EDITS):
        n = src.count(old)
        if n != 1:
            sys.exit("REFUSING: anchor %s matched %d times, expected exactly 1.\n"
                     "          Nothing was written. The file is at %s." % ("ABCDE"[i], n, cur))

    out = src
    for old, new in EDITS:
        out = out.replace(old, new)
    out = out.rstrip("\n") + "\n" + APPEND
    new = out.encode("utf-8")
    if a.check:
        print("would write %s -> %s  (+%d bytes)" % (cur, md5(new), len(new) - len(raw)))
        return 0
    bak = "%s.bak_S285_%s" % (a.file, cur[:8])
    if not os.path.exists(bak):
        shutil.copy2(a.file, bak)
    io.open(a.file, "wb").write(new)
    back = md5(io.open(a.file, "rb").read())
    print("patched %s" % a.file)
    print("   was  %s" % cur)
    print("   now  %s   <-- READ BACK FROM DISK. This is the pin." % back)
    print("   backup %s" % bak)
    return 0 if back == md5(new) else 4


if __name__ == "__main__":
    sys.exit(main())
