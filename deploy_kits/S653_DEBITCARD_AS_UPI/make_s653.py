#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s653.py -- builds kit S653_DEBITCARD_AS_UPI's day_check.py from the LIVE bytes (D788, F-1022; session 354, 25-Oct-2026).

  python3 make_s653.py <dir holding the live day_check.py> <out dir>

Three counted edits in the payment-mode step: when that step moves a Docterz 'Debit Card' payment to UPI (the register does not
hold it as card) and the bank shows its exact amount as UPI, no 'Payment mode wrong' line is written for it; one note on the page
says so. Every other move -- and a Debit Card the register holds as card, or the bank does not show -- is exactly as before."""
import hashlib
import os
import sys

BASE = "da63a5806f0264188a7872ed4b786d99"
HEAD = """# S653 (D788, F-1022 -- the owner, 25-Oct-2026: "Reception staff wrongly chooses the debit card option most of the times
# when the payment is through UPI. The debit card option is very, very rare. And if at all there is a debit card used, then it
# will reflect in the next day's bank MDR report"): when the move below takes a Docterz 'Debit Card' payment to UPI -- the
# register does not hold it as card -- and the bank shows its exact amount as UPI, it IS UPI: counted so, no correction
# asked; one plain note says so. Every other move, and its words, is exactly as before.
"""
EDITS = [
    ("    moved = set()\n    for _guard in range(12):\n",
     HEAD.replace("# S653", "    # S653").replace("\n# ", "\n    # ") + "    as_upi = []\n    moved = set()\n    for _guard in range(12):\n"),
    ("""            if b == "upi" and un["amount_p"] in bank_left:
                bank_left.remove(un["amount_p"])
            cards.append(_card("mode", """,
     """            in_bank = b == "upi" and un["amount_p"] in bank_left
            if in_bank:
                bank_left.remove(un["amount_p"])
            if (a == "card" and b == "upi" and in_bank and not un["wallet"]
                    and (un.get("mode") or "").strip() == "Debit Card"):
                as_upi.append(un["amount_p"])                # S653 (D788): UPI, not a correction
                continue
            cards.append(_card("mode", """),
    ("    # --- 4 \u00b7 what is left\n",
     """    if as_upi:                                       # S653 (D788)
        out["notes"].append((
            "%s written as Debit Card in Docterz was paid by UPI (the bank has it) -- counted as UPI, nothing to change "
            "(%d bill%s). For UPI, Online Payment is the right choice in Docterz." % (rs(sum(as_upi)), len(as_upi),
                                                                                   "" if len(as_upi) == 1 else "s"),
            "%s Docterz mein Debit Card likha tha, paisa UPI se aaya (bank mein hai) -- UPI maana gaya, kuch badalna nahin "
            "(%d bill). UPI ke liye Docterz mein Online Payment chuniye." % (rs(sum(as_upi)), len(as_upi))))
    # --- 4 \u00b7 what is left\n"""),
]


def main(src, out):
    raw = open(os.path.join(src, "day_check.py"), "rb").read()
    if hashlib.md5(raw).hexdigest() != BASE:
        sys.exit("STOP: day_check.py is not the pinned live %s -- nothing written" % BASE[:8])
    txt = raw.decode("utf-8")
    for i, (old, new) in enumerate(EDITS, 1):
        n = txt.count(old)
        if n != 1:
            sys.exit("STOP: edit %d: the piece occurs %d times, not once -- nothing written" % (i, n))
        txt = txt.replace(old, new, 1)
    b = txt.encode("utf-8")
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "day_check.py"), "wb").write(b)
    print("day_check.py  %s -> %s  3 counted edits" % (BASE[:8], hashlib.md5(b).hexdigest()))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
