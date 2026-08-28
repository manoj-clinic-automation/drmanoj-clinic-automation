#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""po_page.py — turn po_plan.json into the order page."""
import io, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))

def rs(p): return "{:,}".format(int(p) // 100)


def esc(x):
    return (str(x).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _noprice(w):
    """Strip rupee figures from a reason before it is shown where staff work.
    The engine keeps its thresholds; the page does not print them."""
    import re
    w = re.sub(r"one line over Rs\s*[\d,]+", "a large line", w)
    w = re.sub(r"under Rs\s*[\d,]+", "a very small line", w)
    return re.sub(r"Rs\s*[\d,]+", "", w).strip()


def rate(units_per_day, size):
    """How fast it goes, in strips and tablets, over a period that fits.

    Two wrong versions before this one. A bare `71.3` in a column headed
    "/day", beside an order in strips -- ORICOX P sells seventy-one TABLETS a
    day. Then `7.1 strips`, and the owner asked how a tablet is sold in
    decimals. It is not, and a tenth of a strip is a different number of
    tablets for every different pack.

    So the decimal is spent on WHOLE TABLETS, never on part of a strip, and
    something too slow for a daily figure is told in weeks or months rather
    than as 0.2 of anything."""
    size = max(1, int(size or 1))
    for per, word in ((units_per_day, "a day"),
                      (units_per_day * 7, "a week"),
                      (units_per_day * 30, "a month")):
        n = int(round(per))
        if n >= 1:
            return "%s %s" % (qty(n, size), word)
    return "less than 1 a month"


def qty(units, size):
    """Strips and tablets — Marg's own convention, and the shop's.

    Marg writes a quantity as `strips:tablets`: `1:5` is one strip and five
    tablets, `3:0` is three strips, and a single-piece item writes a plain
    number. Verified against a real BILL WISE SALES export.

    This page has been through two wrong versions. First `42+2`, which was
    notation. Then plain `42 strips`, which threw the loose tablets away. The
    fraction is never a fraction OF A STRIP -- strip sizes differ, so "7.1
    strips" means eleven different things across eleven items."""
    size = max(1, int(size or 1))
    units = int(units)
    if units < 0:
        # the sign covers the whole quantity, never the parts -- Marg's rule
        return "short " + qty(-units, size)
    if size == 1:
        return "1 pc" if units == 1 else "%d pcs" % units
    st, tb = divmod(units, size)
    bits = []
    if st:
        bits.append("1 strip" if st == 1 else "%d strips" % st)
    if tb:
        bits.append("1 tablet" if tb == 1 else "%d tablets" % tb)
    return " ".join(bits) if bits else "0 strips"


def main():
    d = json.load(io.open(os.path.join(HERE, "po_plan.json"), encoding="utf-8"))
    # Numbers from Marg's own purchase-party list, matched to the vendor names,
    # seeded so nobody types a number the shop already has written down.
    #
    # THEY LIVE OUTSIDE THE REPOSITORY, DELIBERATELY (F-185)
    #     The standing rule is that no phone number goes into the repository.
    #     This file held 18 real supplier numbers inside deploy_kits and would
    #     have been published by the next PUBLISH_ALL run -- .gitignore blocks
    #     .csv, .tsv, .xls and .xlsx under its PATIENT-DATA heading but says
    #     nothing about .json, so nothing would have stopped it. A rule that
    #     depends on remembering it is not a rule; the file now sits in the
    #     config store beside the archive, and the kit ships without it.
    #
    #     A missing file is not an error: the page then shows an empty box per
    #     vendor and staff type the number once, exactly as before seeding.
    PHONES = os.environ.get("SANJ_PHONES") or os.path.expanduser(
        os.path.join("~", "mnt", "Downloads", "margsync", "_config",
                     "stockist_phones.json"))
    if not os.path.exists(PHONES):
        PHONES = r"D:\Downloads\margsync\_config\stockist_phones.json"
    try:
        PH = json.load(io.open(PHONES, encoding="utf-8")).get("pairs", {})
    except Exception:
        PH = {}
    t = d["totals"]
    cards = []
    for v in d["vendors"]:
        lines = "".join(
            '<div class="line" data-item="%s" data-vendor="%s">'
            '<div class="lh"><b>%s</b></div>'
            '<div class="lf"><span>in stock <b>%s</b></span></div>'
            '<div class="lo">order <b>%s</b></div>'
            '<div class="st"><button type="button" data-s="ok" aria-pressed="true">ordered</button>'
            '<button type="button" class="no" data-s="out">out of stock</button></div></div>'
            % (esc(l["item"]), esc(v["vendor"]), l["item"],
               qty(l["on_hand"], l["pack_size"]),
               qty(l["order_strips"] * l["pack_size"], l["pack_size"]))
            for l in v["lines"])
        payload = esc(json.dumps([{"i": l["item"], "n": l["order_strips"]}
                                  for l in v["lines"]], separators=(",", ":")))
        cards.append(
            '<section class="v" data-vendor="%s"><div class="vh"><h2>%s</h2>'
            '<span class="cad">%s</span><span class="tot">%d lines</span></div>'
            '<div class="lines">%s</div>'
            '<div class="vfoot"><button class="cp" data-lines="%s">Copy this order</button>'
            '<a class="call" href="#">Call</a></div>'
            '<input class="tel" type="tel" inputmode="tel" autocomplete="off" value="%s" '
            'placeholder="No number on record — add one and it becomes a tap to call" '
            'aria-label="Phone number for %s"></section>'
            % (esc(v["vendor"]), v["vendor"], v["cadence"], len(v["lines"]), lines,
               payload, esc(PH.get(v["vendor"], "")), esc(v["vendor"])))
    conf = "".join(
        '<div class="ask"><div class="ai"><b>%s</b><span>%d strips</span></div>'
        '<ul>%s</ul></div>'
        % (l["item"], l["order_strips"],
           "".join("<li>%s</li>" % _noprice(w) for w in l["why"]))
        for l in sorted(d["confirm"], key=lambda x: -x["value_p"]))
    # out of stock first: those are the ones where not knowing the stockist
    # is already costing a sale, not merely untidy.
    orows = sorted(d["orphans"], key=lambda o: (o["on_hand"] > 0, o["on_hand"], -o["sold"]))
    def _sug(o):
        if not o.get("suggest"):
            return ('<p class="guess none">Company <b>%s</b> — but nothing has ever been '
                    'bought from that company, so there is no clue at all.</p>'
                    % esc(o.get("company") or "not known")) if o.get("company") else ""
        return ('<p class="guess %s"><b>%s?</b> &nbsp;They supply %d other %s item%s. '
                '<span>Tap to accept, or type the right one.</span></p>'
                % (o["strength"], esc(o["suggest"]), o["behind"], esc(o["company"]),
                   "" if o["behind"] == 1 else "s"))

    orph = "".join(
        '<div class="orow%s" data-item="%s" data-sug="%s"><div class="oh"><b>%s</b>'
        '<span class="%s">%s</span><span>%d sold</span></div>%s'
        '<input class="sup" type="text" autocomplete="off" '
        'placeholder="Stockist name — type it when you next order this" '
        'aria-label="Stockist for %s"></div>'
        % (" low" if o["on_hand"] <= 0 else "", esc(o["item"]), esc(o.get("suggest") or ""),
           o["item"], "out" if o["on_hand"] <= 0 else "",
           "OUT OF STOCK" if o["on_hand"] <= 0 else ("%d left" % o["on_hand"]),
           o["sold"], _sug(o), esc(o["item"]))
        for o in orows)
    html = (io.open(os.path.join(HERE, "po_template.html"), encoding="utf-8").read()
            .replace("__ASON__", d["as_on"]).replace("__CARDS__", "\n".join(cards))
            .replace("__CONFIRM__", conf).replace("__ORPH__", orph)
            .replace("__NV__", str(len(d["vendors"]))).replace("__NL__", str(t["included"]))
            .replace("__NC__", str(t["confirm"])).replace("__NO__", str(t["orphans"])))
    # the page has to be able to republish ITSELF when someone records a
    # shortfall, so it carries its own source with two holes in it. COUNT=1 on
    # both replaces: each token appears twice -- the carrier, and the line of
    # JavaScript that refills the carrier. Replacing both destroys the script.
    cut = html.find("</style>")
    if cut < 0:
        raise SystemExit("FAILED: no </style> to split head from body")
    cut += len("</style>")
    head, rest = html[:cut], html[cut:]
    full = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            + head + "\n</head>\n<body>\n" + rest + "\n</body>\n</html>\n")
    import base64
    skel = base64.b64encode(full.encode("utf-8")).decode("ascii")
    html = html.replace("__SHARED__", '{"e":{}}', 1).replace("__SKEL__", skel, 1)
    if html.count("__SHARED__") != 1 or html.count("__SKEL__") != 1:
        raise SystemExit("FAILED: expected exactly one surviving token of each; got %d/%d"
                         % (html.count("__SHARED__"), html.count("__SKEL__")))

    out = os.path.expanduser("~/mnt/Downloads/margsync/_analysis/PURCHASE_ORDER.html")
    io.open(out, "w", encoding="utf-8", newline="\n").write(html)
    print("%d vendors, %d lines, Rs %s -> %s" % (len(d["vendors"]), t["included"], rs(t["value_p"]), out))
    return 0

if __name__ == "__main__":
    sys.exit(main())
