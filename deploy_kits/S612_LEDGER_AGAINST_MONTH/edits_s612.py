#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""edits_s612.py -- kit S612 (session S331, 22-Oct-2026): exact, counted edits turning the live /root/staff_ledger.py
(S611, 6ee4283c) into the S612 file.     python3 edits_s612.py LIVE OUT [KIT]   (exit 0 only if all anchors occur once, = KIT)

THE OWNER, 22-Oct-2026 05:47 IST, on Surendra's Rs 3,000 of 21 Oct: "advance was given to him against November salary".
The ledger had it right (quota lane, against 2026-11 -- recovered in full at the November close), but the S611
statement called it "open" and "in full".  Now an advance taken against a month's salary says so ("from November
2026 salary"), and one waiting for a later month says "to be cut in Nov 2026".  Also: a negative capitalise row
(Darpan's July correction) reads "Rs 1,000 taken off the loan ... (a correction)", not "Rs -1000 added"; the loan's
interest carries its comma.  Display only: no ledger or salary figure changes.
"""
import hashlib
import sys

EDITS = [
    ('        return "loan, Rs %s a month (Rs %d of it interest)" % ("{:,}".format(int(inst)), INTEREST_RS)',
     '        return "loan, Rs %s a month (Rs %s of it interest)" % ("{:,}".format(int(inst)), "{:,}".format(INTEREST_RS))'),
    ('    if int(inst) >= int(r["amount"]):\n        return "in full"\n    return "Rs %s a month" % "{:,}".format(int(inst))',
     '    if int(inst) >= int(r["amount"]):\n'
     '        _am = r.get("against_month") or ""\n'
     '        return ("from %s salary" % _month_words(_am)) if len(_am) == 7 else "in full"   # S612\n'
     '    return "Rs %s a month" % "{:,}".format(int(inst))'),
    ('            return {"rs": 0, "what": "Rs %d added to the loan of %s (month skipped)" % (r["amount"], when),',
     '            if int(r["amount"]) < 0:                                         # S612: a correction, said plainly\n'
     '                return {"rs": 0, "what": "%s taken off the loan of %s (a correction)" % (_rs(-int(r["amount"])), when),\n'
     '                        "kind": "hold"}\n'
     '            return {"rs": 0, "what": "%s added to the loan of %s (month skipped)" % (_rs(r["amount"]), when),'),
    ('            else:\n                st = "settled%s" % ((" " + _sh(x["last_paid"])) if x.get("last_paid") else "")',
     '            else:\n                st = "settled%s" % ((" " + _sh(x["last_paid"])) if x.get("last_paid") else "")\n'
     '            _am = (_iss.get(x["id"]) or {}).get("against_month") or ""\n'
     '            if st == "open" and len(_am) == 7:                         # S612: waiting for a later month\'s salary\n'
     '                st = "to be cut in %s" % _sh(_am)'),
    ('APP_VERSION = "4.0-S611-STATEMENT"', 'APP_VERSION = "4.1-S612-STATEMENT"'),
]


def main():
    live, out = sys.argv[1], sys.argv[2]
    kit = sys.argv[3] if len(sys.argv) > 3 else None
    s = open(live, encoding="utf-8").read()
    for i, (old, new) in enumerate(EDITS, 1):
        n = s.count(old)
        if n != 1:
            print("  REFUSED: edit %d's anchor occurs %d times (expected 1)" % (i, n))
            return 1
        s = s.replace(old, new)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    a = hashlib.md5(open(out, "rb").read()).hexdigest()
    print("  %d edits applied · rebuilt %s" % (len(EDITS), a[:8]))
    if kit:
        b = hashlib.md5(open(kit, "rb").read()).hexdigest()
        print("  kit %s  %s" % (b[:8], "same" if a == b else "DIFFERENT"))
        return 0 if a == b else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
