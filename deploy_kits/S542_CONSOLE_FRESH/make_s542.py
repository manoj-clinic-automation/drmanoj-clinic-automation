#!/usr/bin/env python3
"""make_s542.py -- kit S542 (session 313, 13-Oct-2026). Builds the new /root/finance/owner_console.py and owner_console.html
from their LIVE bytes (c09321e2, e6d35d88) by exact, counted, anchored edits, built in memory first (F-792); nothing is written
unless every anchor occurs exactly once.
    python3 make_s542.py <owner_console.py FROM> <out> <owner_console.html FROM> <out>"""
import hashlib
import sys

FROM = {"py": "c09321e2356f6b1bc441bb1f75118cbc", "html": "e6d35d88b87890911124b9778a43c5d2"}
N = {"py": 0, "html": 0}

PY = [
    ('VERSION = "S512 1.2"\n', '''VERSION = "S542 1.3"
# S542 (13-Oct-2026, the owner 07:26: "check why my command console does not show the amounts. Although the 12th October amounts
# are showing in the relevant page of doctor's revenue ... whenever I update something through the command console, and then I
# come back to command console and even refresh it, then also those stale messages are not cleared"): the clinic's day reads
# Docterz's own day total while the counter sheet is not filled (it read Rs 0 -- the match stops early and carries no totals);
# the page asks for a fresh reading when it is opened and when he comes back to it (owner_console.html).
'''),
    ('''        amt = int(p1.get("docterz_p") or 0) if m.get("doc_known") else (int(p1.get("counter_p") or 0) if m.get("filled") else None)
''', '''        rev = con.execute("SELECT total_amount_p FROM clinic_day_revenue WHERE business_date=?", (D,)).fetchone()
        if p1 and m.get("doc_known"):                                  # the match ran: its own Docterz figure
            amt = int(p1.get("docterz_p") or 0)
        elif rev is not None:                                          # S542: no match yet -- Docterz's day, as the Revenue page shows it
            amt = int(rev[0] or 0)
        elif m.get("filled"):                                          # S542: the counter sheet in, Docterz not yet -- the sheet's total
            try:
                amt = sum(CM._reg_totals(CM._register(con, D))[0].values())
            except Exception:                                          # noqa: BLE001
                amt = None
        else:
            amt = None
'''),
]
HTML = [
    ("""  document.addEventListener('visibilitychange',function(){ if(!document.hidden){tries=0; load(false);} });""",
     """  document.addEventListener('visibilitychange',function(){ if(!document.hidden){tries=0; load(true); loadFills(); loadSwitch();} });  // S542: back on the page = a fresh reading"""),
    ("""  load(false); loadFills(); loadSwitch();
})();""", """  load(true); loadFills(); loadSwitch();   // S542: opening (or reloading) the page asks for a fresh reading, not one up to 5 minutes old
})();"""),
]


def apply(src, pairs, k):
    for old, new in pairs:
        if src.count(old) != 1:
            raise SystemExit("REFUSED: %s anchor found %d times: %r" % (k, src.count(old), old[:80]))
        src = src.replace(old, new, 1)
        N[k] += 1
    return src


def main(a):
    if len(a) != 4:
        print(__doc__)
        return 2
    out = []
    for k, src_p, dst_p, pairs in (("py", a[0], a[1], PY), ("html", a[2], a[3], HTML)):
        raw = open(src_p, "rb").read()
        if hashlib.md5(raw).hexdigest() != FROM[k]:
            print("REFUSED: %s is %s, expected %s" % (src_p, hashlib.md5(raw).hexdigest(), FROM[k]))
            return 1
        out.append((dst_p, apply(raw.decode("utf-8"), pairs, k).encode("utf-8")))
    for dst_p, b in out:
        open(dst_p, "wb").write(b)
        print("%s  %s" % (hashlib.md5(b).hexdigest(), dst_p))
    print("edits: owner_console.py %(py)d · owner_console.html %(html)d" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
