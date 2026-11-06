#!/usr/bin/env python3
"""make_s729.py -- kit S729 (session 390, the parent, 06-Nov-2026). The Union Bank passbooks in the accountants' pack.
   python make_s729.py <live packs.py> <out> [--expect <md5>]
The owner, 16:37-16:38 IST 06-Nov: Union Bank of India savings accounts, his and Dr Bhawna's; "they fill the passbook, it is printed
by the printer, and then we can scan and upload it whenever required" (the board note: Union Bank semi-annual). By counted edits:
  * two half-yearly slots (April - September, October - March), Union Bank a hand-added bank like SBI: an empty cell says to scan
    the printed passbook pages and use the Add statements box; the 'no statement has come by mail' check leaves them out;
  * a Union Bank paper with text is known by 'Union Bank of India' in its first lines (never from a narration); a scanned passbook
    has no text -- the owner's one tap on it (This is ...) files it, as for any unplaced paper;
  * a paper with no printed period is dated the day it was added; a passbook printed July - December belongs to April - September,
    January - June to October - March (a statement with its own period: the half-year its end falls in);
  * filed as the passbook (no bank lines are read from it). No account number is in this file: the slots go by the holder's name."""
import hashlib, sys

EDITS = [
('''    ("zerodha_txn_bhawna",  "ZERODHA", "Dr Bhawna Agarwal (Zerodha statement of transactions)", "savings", "BHAWNA AGARWAL",      0),
''',
'''    ("zerodha_txn_bhawna",  "ZERODHA", "Dr Bhawna Agarwal (Zerodha statement of transactions)", "savings", "BHAWNA AGARWAL",      0),
    # S729: Union Bank of India savings -- the printed passbook, scanned and added by hand, every half-year
    ("union_sav_manoj",     "UNION",   "Dr Manoj Agarwal (Union Bank savings passbook)",        "savings", "MANOJ AGARWAL",       0),
    ("union_sav_bhawna",    "UNION",   "Dr Bhawna Agarwal (Union Bank savings passbook)",       "savings", "BHAWNA AGARWAL",      0),
'''),
('''              "zerodha_txn_manoj": 3, "zerodha_txn_bhawna": 3}   # S728''',
'''              "zerodha_txn_manoj": 3, "zerodha_txn_bhawna": 3,   # S728
              "union_sav_manoj": 6, "union_sav_bhawna": 6}       # S729'''),
('''MANUAL_BANKS = ("SBI",)                     # S621: the banks whose statements the owner downloads and adds himself (no mail road)''',
'''MANUAL_BANKS = ("SBI", "UNION")            # S621: the banks whose statements the owner downloads and adds himself (no mail road); S729 Union
MANUAL_HINT = {"UNION": " — scan the printed passbook pages to a PDF, then use the Add statements box on this page"}   # S729'''),
('''def zerodha_ident(text):''',
'''def is_union(text):
    """S729: a Union Bank of India paper names its bank in its first lines, on a line that is no transaction row."""
    for ln in [x for x in (text or "").splitlines() if x.strip()][:8]:
        if "UNION BANK OF INDIA" in " ".join(ln.upper().split()) and not _Z_NARR.search(ln):
            return True
    return False


def zerodha_ident(text):'''),
('''    bank = _bank_of(hup) or ("SBI" if ("STATE BANK OF INDIA" in hup or "SBIN0" in hup) else "") or _bank_of(up)   # S621: SBI by its head only''',
'''    bank = _bank_of(hup) or ("SBI" if ("STATE BANK OF INDIA" in hup or "SBIN0" in hup) else "") or ("UNION" if is_union(text) else "") or _bank_of(up)   # S621: SBI by its head only; S729 Union
    if bank == "UNION":                                               # S729: Bhavna is Bhawna
        hup = _sbi_fold(hup)'''),
('''        elif slot["bank"] == "ZERODHA":                                # S728: filed as the broker's statement
            return "read", "filed -- the broker's statement (no bank lines are read from it)"''',
'''        elif slot["bank"] == "ZERODHA":                                # S728: filed as the broker's statement
            return "read", "filed -- the broker's statement (no bank lines are read from it)"
        elif slot["bank"] == "UNION":                                  # S729: the passbook; no printed period -> the day it was added
            con.execute("UPDATE stmt_file SET period_to=substr(COALESCE(fetched_at, mtime, ?), 1, 10) WHERE id=? AND period_to IS NULL", (_now(), f["id"]))
            return "read", "filed -- the passbook pages (no bank lines are read from them)"'''),
('''            full, pieces = fs[:1], []
        if s["kind"] == "card":''',
'''            full, pieces = fs[:1], []
        if s["bank"] == "UNION":       # S729: a passbook printed July - December is April - September's; January - June, October - March's
            fs = [dict(r) for r in con.execute(
                "SELECT * FROM stmt_file WHERE slot_id=? AND period_to IS NOT NULL AND period_to >= date(?, 'start of month', '-2 months') "
                "AND period_to < date(?, 'start of month', '+4 months') ORDER BY period_to DESC, id DESC", (s["id"], hi, hi))]
            full, pieces = fs[:1], []
        if s["kind"] == "card":'''),
('''s["bank"] != "ZERODHA") else []),   # S728''',
'''s["bank"] not in ("ZERODHA", "UNION")) else []),   # S728 S729'''),
('''            why_ = "not on the shelf" + ((" — download it from %s, then use the Add statements box on this page" % c["bank"]) if c["bank"] in MANUAL_BANKS else "")   # S621''',
'''            why_ = "not on the shelf" + ((MANUAL_HINT.get(c["bank"]) or (" — download it from %s, then use the Add statements box on this page" % c["bank"])) if c["bank"] in MANUAL_BANKS else "")   # S621 S729'''),
]


def main():
    src, out = sys.argv[1], sys.argv[2]
    s = open(src, encoding="utf-8").read()
    for i, (a, b) in enumerate(EDITS, 1):
        n = s.count(a)
        if n != 1:
            print("make_s729: edit %d matches %d times (must be 1) -- nothing written" % (i, n))
            return 2
        s = s.replace(a, b)
    data = s.encode("utf-8")
    if "--expect" in sys.argv and hashlib.md5(data).hexdigest() != sys.argv[sys.argv.index("--expect") + 1]:
        print("make_s729: the result is %s, not the expected one -- nothing written" % hashlib.md5(data).hexdigest())
        return 3
    open(out, "wb").write(data)
    print("make_s729: %d edits applied -> %s (%s)" % (len(EDITS), out, hashlib.md5(data).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
