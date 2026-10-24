#!/usr/bin/python3
"""make_s639.py -- kit S639_PARCHI_DESK: the counted edits on the REAL bytes of /root/finance/slip_log.py 2419c536 (the 24-Oct
bundle; F-472). python make_s639.py <slip_log.py> <out_dir>. Every anchor must occur exactly once or nothing is written."""
import hashlib, os, sys

FROM = "2419c5360570a307cad9cf1094cebe68"
EDITS = [
 # 1 -- init mounts the desk beside slip_adjust (guarded: without it the slips are exactly as before)
 ('''    except Exception as _ex_sa:                           # noqa: BLE001 -- the slips work without it
        import sys as _sys                                # noqa: PLC0415
        print("slip_adjust NOT mounted: %s" % _ex_sa, file=_sys.stderr)
    return bp
''', '''    except Exception as _ex_sa:                           # noqa: BLE001 -- the slips work without it
        import sys as _sys                                # noqa: PLC0415
        print("slip_adjust NOT mounted: %s" % _ex_sa, file=_sys.stderr)
    try:                                                  # S639 (D775): the parchi desk, one page, beside this file
        import parchi_desk                                # noqa: PLC0415
        parchi_desk.init(app, db_getter, require_fn, audit_fn, unit=unit)
    except Exception as _ex_pd:                           # noqa: BLE001 -- the slips work without it
        import sys as _sys                                # noqa: PLC0415
        print("parchi_desk NOT mounted: %s" % _ex_pd, file=_sys.stderr)
    return bp
'''),
 # 2 -- the night report no longer asks for the room's Paid / Done (D775: paid comes from Docterz, billed is done)
 ('''        if not s["paid_mode"] or not s["done_at"]:
            miss = [w for w, ok in (("Paid", s["paid_mode"]), ("Done", s["done_at"])) if not ok]
            row["why"].append("room did not tick " + " / ".join(miss))
            flags.append("X-ray/Proc slip %d: room did not tick %s" % (s["slip_no"], " / ".join(miss)))
''', '''        # S639 (D775): the room's Paid / Done ticks are no longer asked for -- Paid comes from Docterz at night, billed is done.
'''),
 # 3 -- nor does the menu's reminder
 ('''    if open_old:
        rem.append("%d purani X-ray/Proc parchi mein Paid/Done baaki: %s" % (
            len(open_old), ", ".join(str(s["slip_no"]) for s in open_old[:8]) + (" …" if len(open_old) > 8 else "")))
''', '''    # S639 (D775): no "Paid/Done baaki" reminder any more -- the room's ticks are not asked for.
'''),
 # 4 -- the menu: the desk first; the room page stays, with no count asking for ticks
 ('''        "room": ('<a class="mi" href="/finance/slips?s=room"><b>X-ray room work</b><span class="%s">%d baaki</span></a>'
                 % ("hot" if room_n else "", room_n)),
''', '''        "room": '<a class="mi small" href="/finance/slips?s=room"><b>X-ray room work</b><span>purana page</span></a>',   # S639
'''),
 ('''    out = ['<nav class="menu">'] + [items[k] for k in order]
''', '''    out = ['<nav class="menu">',                          # S639 (D775): the desk -- every parchi on one page
           '<a class="mi" href="/finance/slips/desk"><b>Parchi desk</b><span>OPD \\u00b7 X-ray/Proc \\u00b7 Blood, ek page</span></a>'] \\
        + [items[k] for k in order]
'''),
 # 6 -- a fault found by this kit's walk: a line with a chhoot on today's list took the whole menu down (three %s, two
 #      values -> TypeError on every /finance/slips screen that day)
 ("""            state = ' <span class="sm">%s %s — %s</span>' % ("FREE" if a["kind"] == "free" else "chhoot " + _rs(a["amount_p"]),""",
  """            state = ' <span class="sm">%s — %s</span>' % ("FREE" if a["kind"] == "free" else "chhoot " + _rs(a["amount_p"]),   # S639"""),
 # 5 -- the owner's report links the desk (he uses it when staff are away)
 ('''           ' · <a href="/finance/slips/discounts">discounts this month</a></p>'
''', '''           ' · <a href="/finance/slips/discounts">discounts this month</a> · <a href="/finance/slips/desk">the parchi desk</a></p>'
'''),
]


def main():
    src, out = sys.argv[1], sys.argv[2]
    h = hashlib.md5(open(src, "rb").read()).hexdigest()
    if h != FROM:
        sys.exit("STOP: %s is %s, not %s" % (src, h[:8], FROM[:8]))
    s = open(src, encoding="utf-8").read()
    for i, (a, b) in enumerate(EDITS, 1):
        n = s.count(a)
        if n != 1:
            sys.exit("STOP: edit %d anchor found %d times" % (i, n))
        s = s.replace(a, b)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "slip_log.py"), "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    print("slip_log.py: %d counted edits -> %s" % (len(EDITS), hashlib.md5(s.encode("utf-8")).hexdigest()))


if __name__ == "__main__":
    main()
