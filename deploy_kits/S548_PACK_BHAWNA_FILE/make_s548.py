#!/usr/bin/env python3
"""S548_PACK_BHAWNA_FILE (D721) -- exact, counted edits on the md5-pinned live /root/finance/packs.py (the parent's file; S541's TO).
usage: make_s548.py <live packs.py> <out file>
Dr Bhawna's personal expenses (the scan app's bills.pe_who = 'bhawna', S544) become the pack's own item 8.3; item 8.2, Dr
Manoj's expense file, keeps only Dr MK's. The column is read only when present, so the pack is unchanged before S544."""
import hashlib, sys

FROM_MD5 = "ada0860ad0b64e95836b24880927071f"
src, out = sys.argv[1], sys.argv[2]
raw = open(src, "rb").read()
if hashlib.md5(raw).hexdigest() != FROM_MD5:
    sys.exit("REFUSED: packs.py is not the pinned " + FROM_MD5)
s = raw.decode("utf-8")
EDITS = [
    ("E1 the bundle: which person's expense file",
     '        mcol = "COALESCE(NULLIF(bill_month,\'\'), substr(bill_date,1,7))" if "bill_month" in cols else "substr(bill_date,1,7)"      # S434/S435 (F-658)\n',
     '        mcol = "COALESCE(NULLIF(bill_month,\'\'), substr(bill_date,1,7))" if "bill_month" in cols else "substr(bill_date,1,7)"      # S434/S435 (F-658)\n'
     '        qlane, who_sql = lane, ""                                    # S548 (D721): Dr Bhawna\'s expense file apart from Dr Manoj\'s\n'
     '        if lane == "owner_expense_bhawna":\n'
     '            if "pe_who" not in cols:\n'
     '                return None, "no personal expense is marked Dr Bhawna yet"\n'
     '            qlane, who_sql = "owner_expense", " AND COALESCE(pe_who,\'\')=\'bhawna\'"\n'
     '        elif lane == "owner_expense" and "pe_who" in cols:\n'
     '            who_sql = " AND COALESCE(pe_who,\'\')<>\'bhawna\'"\n'),
    ("E2 the bundle's query",
     "%s AS bmonth FROM bills WHERE lane=? AND status<>'rejected' \"\n"
     "            \"AND ((%s=?) OR (substr(created_at,1,7)=? AND late_for IS NOT NULL AND %s<>?)) ORDER BY late_for IS NOT NULL, bill_date, id\" % (mcol, mcol, mcol), (lane, month, month, month))]\n",
     "%s AS bmonth FROM bills WHERE lane=? AND status<>'rejected'%s \"\n"
     "            \"AND ((%s=?) OR (substr(created_at,1,7)=? AND late_for IS NOT NULL AND %s<>?)) ORDER BY late_for IS NOT NULL, bill_date, id\" % (mcol, who_sql, mcol, mcol), (qlane, month, month, month))]\n"),
    ("E4 the words when the month has none",
     '        return None, "no %s scans for %s" % (lane.replace("_", " "), _month_name(month))\n',
     '        return None, "no %s scans for %s" % ({"owner_expense_bhawna": "Dr Bhawna expense"}.get(lane, lane.replace("_", " ")), _month_name(month))   # S548\n'),
    ("E5 the index page's title",
     '            fh.write(_text_pdf("%s bills -- %s (%d)" % (lane.replace("_", " ").title(), _month_name(month), len(rows)), idx))\n',
     '            fh.write(_text_pdf("%s bills -- %s (%d)" % ({"owner_expense_bhawna": "Dr Bhawna Expense"}.get(lane, lane.replace("_", " ").title()), _month_name(month), len(rows)), idx))   # S548\n'),
    ("E3 item 8: the third file",
     "enumerate(((\"lab_purchase\", \"Dr Bhawna's lab-purchase bills\"), (\"owner_expense\", \"Dr Manoj's expense-file bills\")), 1):",
     "enumerate(((\"lab_purchase\", \"Dr Bhawna's lab-purchase bills\"), (\"owner_expense\", \"Dr Manoj's expense-file bills\"),\n"
     "                                         (\"owner_expense_bhawna\", \"Dr Bhawna's expense-file bills\")), 1):     # S548 (D721)"),
]
for name, old, new in EDITS:
    n = s.count(old)
    if n != 1:
        sys.exit("REFUSED: %s -- anchor found %d times (must be 1)" % (name, n))
    s = s.replace(old, new, 1)
    print("OK", name)
b = s.encode("utf-8")
open(out, "wb").write(b)
print("written", out, hashlib.md5(b).hexdigest())
