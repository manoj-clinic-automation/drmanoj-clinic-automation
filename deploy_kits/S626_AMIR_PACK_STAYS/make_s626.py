#!/usr/bin/env python3
"""make_s626.py -- kit S626_AMIR_PACK_STAYS (F-988), Sanjeevni session 338, 22-Oct-2026.

Builds the NEW /root/finance/amir_day.py from the LIVE bytes by two anchored replacements; refuses unless the input is at FROM and
the output at TO.  Usage: python3 -B make_s626.py <live amir_day.py> <out path>
"""
import hashlib
import sys

FROM = "1169a3d6ae451ebb4c9806052de0856c"
TO = "2c99c29eff254c9abfe1374b2e3f8ba3"

OLD_FN = '''def _s446_packs(cx):
    out = []
    try:
        import packs                                           # noqa: PLC0415 -- READ ONLY: amir_pack(con, month)
        for m in _s446_prev_months(3):
            p = packs.amir_pack(cx, m)
            if p.get("ready") and not p.get("seen"):
                out.append(m)
    except Exception:                                          # noqa: BLE001
        pass
    return out
'''
NEW_FN = '''def _s446_packs(cx):
    """S626 (F-988): the month packs on Amir's page, as [(month, seen)] oldest first -- every ready month he has not marked seen, and
    the NEWEST ready month always, seen or not, so the two statements stay on his page until the next month's pack is ready (the
    owner's note of 22-Oct, point 5).  A month with nothing on the shelf is never listed."""
    out = []
    try:
        import packs                                           # noqa: PLC0415 -- READ ONLY: amir_pack(con, month)
        got = []
        for m in _s446_prev_months(3):
            p = packs.amir_pack(cx, m)
            if p.get("ready"):
                got.append((m, bool(p.get("seen"))))
        newest = got[-1][0] if got else None
        out = [(m, s) for (m, s) in got if (not s) or m == newest]
    except Exception:                                          # noqa: BLE001
        out = []
    return out
'''

OLD_ROW = '''    for m in S.packs or []:
        rows.append(("packs", "<div class=line><span class=big>Mahine ka pack &mdash; %s</span>%s"
                     "<p><a class='btn plain' href='/finance/amir/pack/%s/yes'>Yes Bank Sanjeevni statement (PDF)</a></p>"
                     "<p><a class='btn plain' href='/finance/amir/pack/%s/icici'>ICICI Sanjeevni statement (PDF)</a></p>"
                     "<form method=post action='/finance/amir/pack/%s/seen'><button class=btn name=go value=1>Dekh liya</button></form></div>"
                     % (_esc(_s446_month_name(m)),
                        ("<p><a class='btn plain' href='/finance/amir/pack/%s/neft'>Paid NEFT sheet (PDF)</a></p>" % m) if (S.neft_ok or {}).get(m) else "",
                        m, m, m), "", False))
'''
NEW_ROW = '''    for m, seen in S.packs or []:                              # S626 (F-988): a seen month keeps its links; only the button goes
        rows.append(("packs", "<div class=line><span class=big>Mahine ka pack &mdash; %s</span>%s"
                     "<p><a class='btn plain' href='/finance/amir/pack/%s/yes'>Yes Bank Sanjeevni statement (PDF)</a></p>"
                     "<p><a class='btn plain' href='/finance/amir/pack/%s/icici'>ICICI Sanjeevni statement (PDF)</a></p>"
                     "%s</div>"
                     % (_esc(_s446_month_name(m)),
                        ("<p><a class='btn plain' href='/finance/amir/pack/%s/neft'>Paid NEFT sheet (PDF)</a></p>" % m) if (S.neft_ok or {}).get(m) else "",
                        m, m,
                        "" if seen else ("<form method=post action='/finance/amir/pack/%s/seen'><button class=btn name=go value=1>Dekh liya</button></form>" % m)),
                     "", False))
'''


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    src, out = sys.argv[1], sys.argv[2]
    b = open(src, "rb").read()
    if md5(b) != FROM:
        sys.exit("!! %s is %s, not FROM %s -- nothing built" % (src, md5(b), FROM))
    t = b.decode("utf-8")
    for old, new, name in ((OLD_FN, NEW_FN, "_s446_packs"), (OLD_ROW, NEW_ROW, "the pack row")):
        n = t.count(old)
        if n != 1:
            sys.exit("!! the anchor for %s occurs %d times, not once -- nothing built" % (name, n))
        t = t.replace(old, new)
    nb = t.encode("utf-8")
    if TO != "__TO" + "__" and md5(nb) != TO:
        sys.exit("!! the built file is %s, not TO %s -- nothing built" % (md5(nb), TO))
    open(out, "wb").write(nb)
    print("built %s %s (FROM %s)" % (out, md5(nb), FROM[:8]))


if __name__ == "__main__":
    main()
