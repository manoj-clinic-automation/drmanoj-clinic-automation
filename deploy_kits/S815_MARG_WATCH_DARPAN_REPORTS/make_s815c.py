#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s815c.py LIVE OUT -- kit S815 (13-Nov-2026, Sanjeevni session 446): reports_tile.py a96bcad5 (S810) -> Shavez's Aaj ki reports shows a
sale report the owner (or the Marg watch by itself, D929) asked for again: the dates, the same Sale Detail report of his REPORT login, the steps
link; it ticks when the files have come and leaves the page when the Marg watch closes it. READ ONLY like the rest of this page; it is not
counted in the day's totals, the banner or the owner's line. One block appended before the command-line guard; anything else stops the build."""
import hashlib, sys

FROM = "a96bcad5acb429699465557b66b40665"
GUARD = '\nif __name__ == "__main__":\n    sys.exit(selftest())\n'
BLOCK = '''
# ---- S815_MARG_WATCH_DARPAN_REPORTS (13-Nov-2026, Sanjeevni session 446): a sale report asked for again (the owner's 'looks right' of 11:33) ----
#  The asks live in finance.db marg_watch_report, made by the Marg watch (marg_billwatch.rpt_*); this page only READS them (rpt_open) and shows
#  each as one card line: the dates and "abhi baaki", or a tick once VERIFIED sale (Detail) files received after the ask cover the days.
#  Fail-soft: no table, no module, any fault -> no card, the page whole.
def _s815_asked(cx):
    try:
        import marg_billwatch as BW                            # noqa: PLC0415
        return BW.rpt_open(cx)
    except Exception:                                          # noqa: BLE001
        return []


_status_before_s815 = status


def status(cx, today=None, now=None):                          # noqa: F811 -- S815: + the asks, apart from the day's counts
    s = _status_before_s815(cx, today, now)
    s["asked"] = _s815_asked(cx)
    return s


def _s815_card(asked):
    if not asked:
        return ""
    fid = _s716_flow_of("SALE_BILLWISE")
    steps = (" <a class=small href='/finance/flows/%s'>Kaise banayein &rsaquo;</a>" % _esc(fid)) if fid else ""
    lines = []
    for a in asked:
        one_day = a["day_from"] == a["day_to"]
        days = _ddmm(a["day_from"]) if one_day else "%s se %s" % (_ddmm(a["day_from"]), _ddmm(a["day_to"]))
        tareekh = ("tareekh %s" % _ddmm(a["day_from"])) if one_day else ("From %s &middot; To %s" % (_ddmm(a["day_from"]), _ddmm(a["day_to"])))
        state = ("<span class='state good'>&#10003; aa gayi, sahi hai</span>" if a.get("arrived")
                 else "<span class='state due'>&#9675; abhi baaki</span>")
        lines.append("<div class=line><span class=big>Doctor sahab ne yeh report dobara maangi hai</span><br>"
                     "Bikri report (Detail) &mdash; <b>%s</b><br><span class=small>Roz wali bikri report hi hai (DAILY SALES &middot; Detail &middot; "
                     "With Item Deta. Yes), sirf %s daaliye. Marg ki REPORT wali ID se. File yahan khud aa jaati hai.</span>%s%s</div>"
                     % (_esc(days), tareekh, state, steps))
    return "<div class='card' id=s815asked style='border:2px solid #f0b400;background:#fffdf3'>%s</div>" % "".join(lines)


_render_before_s815 = render


def render(s, picked_date=False):                              # noqa: F811 -- S815: the card above the day's done / count line (S448 review S4)
    page = _render_before_s815(s, picked_date)
    card = _s815_card(s.get("asked") or [])
    if card:
        for mark in ("<div class='card done'>", "<div class='card'><p class='big wait'", "<p class=foot>", "<div class=card id=s714flows>"):
            if page.count(mark) == 1:
                return page.replace(mark, card + mark)
    return page
# ---- S815 end ----------------------------------------------------------------------------------------------------------------------------
'''


def main():
    src, out = sys.argv[1:3]
    raw = open(src, "rb").read()
    if hashlib.md5(raw).hexdigest() != FROM:
        raise SystemExit("the live file is not %s -- stopped" % FROM[:8])
    s = raw.decode("utf-8")
    if s.count(GUARD) != 1:
        raise SystemExit("the guard is not found once -- stopped")
    s = s.replace(GUARD, "\n" + BLOCK + GUARD)
    b = s.encode("utf-8")
    open(out, "wb").write(b)
    print(hashlib.md5(b).hexdigest())


if __name__ == "__main__":
    main()
