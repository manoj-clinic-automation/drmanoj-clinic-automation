#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s930.py -- kit S930_STOCK_CHECK_PAGE (22-Nov-2026, Sanjeevni session 503). The TO files by EXACT anchors (each once, F-472) from:
   sanjeevni_day.py c01bf05b (S927's) · stock_watch.py 02727b0f (S928's TO) · finance_ui/finance_approvals.html bc5d52c9 (S927's).
    python3 -B make_s930.py <live_dir> <out_dir>   (live_dir holds sanjeevni_day.py, stock_watch.py, finance_ui/finance_approvals.html)"""
import hashlib
import io
import os
import sys

FROM = {"sanjeevni_day.py": "c01bf05b", "stock_watch.py": "02727b0f", "finance_ui/finance_approvals.html": "bc5d52c9"}


def rd(p):
    with io.open(p, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def wr(p, t):
    with io.open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(t)


def sub(t, a, b, what):
    n = t.count(a)
    if n != 1:
        raise SystemExit("anchor %s occurs %d times, not once" % (what, n))
    return t.replace(a, b)


def main():
    live, out = sys.argv[1], sys.argv[2]
    for f, h in FROM.items():
        got = hashlib.md5(open(os.path.join(live, f), "rb").read()).hexdigest()[:8]
        if got != h:
            raise SystemExit("%s is %s, the kit was written on %s" % (f, got, h))
    t = rd(os.path.join(live, "sanjeevni_day.py"))
    t = sub(t, '        print("hub_panels not mounted: %s" % ex)\n',
            '        print("hub_panels not mounted: %s" % ex)\n'
            '    try:                                                     # S930: the owner\'s Stock check page (stock_check.py) -- Marg against the shelf\n'
            '        import stock_check\n'
            '        stock_check.init(app, db_getter, require_fn, unit)\n'
            '    except Exception as ex:                                  # noqa: BLE001 -- the old stock pages then stand as before\n'
            '        print("stock_check not mounted: %s" % ex)\n', "A1 mount")
    wr(os.path.join(out, "sanjeevni_day.py"), t)
    w = rd(os.path.join(live, "stock_watch.py"))
    w = sub(w, '                out.append(dict(cls=_s928_cls(n), target="stock", text=n["text"]))   # S436: ortho_closed; S894: asked_count; S928: count_day',
            '                out.append(dict(cls=_s928_cls(n), target="stock", text=n["text"],\n'
            '                                href=("/finance/stockcheck/" if n["kind"] in ("count_day", "asked_count") else None)))   # S436: ortho_closed; S894: asked_count; S928: count_day; S930: a count line opens the Stock check page', "B1 href")
    wr(os.path.join(out, "stock_watch.py"), w)
    h = rd(os.path.join(live, "finance_ui/finance_approvals.html"))
    h = sub(h, '        <a href="/finance/stock/page/hub">Stock Check — every step</a>\n',
            '        <a href="/finance/stockcheck/"><b>Stock check</b> — Marg against the shelf, Darpan\'s counts, Count this</a>\n', "C1 goto stock check")
    h = sub(h, '        <a href="/finance/stock/page/now">Stock now</a>\n',
            '        <a href="/finance/stock/page/hub">Count of 06-Sep — every step (closed)</a>\n', "C2 goto archive")
    os.makedirs(os.path.join(out, "finance_ui"), exist_ok=True)
    wr(os.path.join(out, "finance_ui", "finance_approvals.html"), h)
    for f in ("sanjeevni_day.py", "stock_watch.py", "finance_ui/finance_approvals.html"):
        print("%s -> %s" % (f, hashlib.md5(open(os.path.join(out, f), "rb").read()).hexdigest()[:8]))


if __name__ == "__main__":
    main()
