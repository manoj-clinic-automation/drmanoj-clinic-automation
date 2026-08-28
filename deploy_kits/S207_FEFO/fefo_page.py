#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""fefo_page.py — build Darpan's "sell this batch" card from fefo_data.json."""
import io, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))

def band(m):
    if m <= 1:  return ("now",   "expires this month or next")
    if m <= 3:  return ("soon",  "under three months")
    if m <= 6:  return ("watch", "under six months")
    return ("ok", "")

def main():
    d = json.load(io.open(os.path.join(HERE, "fefo_data.json"), encoding="utf-8"))
    cards = d["cards"]
    urgent = [c for c in cards if c["months"] <= 6]
    wrong = sum(c["wrong_units"] for c in cards)
    rows = []
    for c in cards:
        b, _ = band(c["months"])
        others = "".join(
            '<div class="alt"><span class="bt">%s</span><span class="ex">exp %s</span></div>'
            % (o["b"], o["exp"]) for o in c["others"])
        rows.append(
            '<article class="card %s" data-m="%d" data-w="%d">'
            '<div class="hd"><h3>%s</h3><span class="stk">%d<small>in stock</small></span></div>'
            '<div class="sell"><span class="lbl">sell this batch</span>'
            '<span class="bat">%s</span><span class="exp">expires %s</span>'
            '<span class="mo">%s</span></div>'
            '%s%s</article>'
            % (b, c["months"], c["wrong_units"], c["item"], c["stock"], c["sell"],
               c["sell_exp"], (("%d month%s" % (c["months"], "" if c["months"] == 1 else "s"))
                if c["months"] > 0 else ("EXPIRED" if c["months"] < 0 else "expires this month")),
               ('<div class="alts"><span class="lbl">not these yet</span>%s</div>' % others) if others else "",
               ('<p class="warn">%d units already went out of a newer batch while this one sat here.</p>'
                % c["wrong_units"]) if c["wrong_units"] else ""))
    html = TPL.replace("__ROWS__", "\n".join(rows)) \
              .replace("__N__", str(len(cards))) \
              .replace("__URGENT__", str(len(urgent))) \
              .replace("__WRONG__", "{:,}".format(wrong)) \
              .replace("__ASON__", d["as_on"])
    out = os.path.expanduser("~/mnt/Downloads/margsync/_analysis/FEFO_CARD.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    io.open(out, "w", encoding="utf-8", newline="\n").write(html)
    print("%d items, %d urgent, %d bytes -> %s" % (len(cards), len(urgent), len(html), out))
    return 0

TPL = io.open(os.path.join(HERE,"fefo_template.html"),encoding="utf-8").read()

if __name__ == "__main__":
    sys.exit(main())
