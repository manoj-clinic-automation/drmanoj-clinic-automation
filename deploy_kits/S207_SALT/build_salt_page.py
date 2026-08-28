#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""build_salt_page.py — the approval list for same-salt alternatives."""
import glob, io, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "S206_SANJEEVNI_MARG_PURCHASE")))
import salt_alternatives as SA

ARCHIVE = os.path.expanduser("~/mnt/Downloads/margsync/MargArchive")
OUT = os.path.expanduser("~/mnt/Downloads/margsync/_analysis/SALT_ALTERNATIVES.html")

# Pairs that read wrong to me. Flagged so the doctor reviews 40 rows with the
# doubtful ones marked, instead of 40 blind. My reading is not a ruling -- his
# is -- but a wrist brace is not a pelvic traction belt, and saying so saves him
# finding it himself.
SUSPECT = {
    "PELVIC TRACTION BELT XL": "a wrist brace is not a pelvic traction belt",
    "TELM 80 + HYDROCHL 12.5": "one of these looks like a pantoprazole, not a telmisartan",
    "DROTAVERINE MEFNAMIC ACID": "one of these looks like a calcium, not a drotaverine",
}


def find_export():
    from xlsx_sheet import open_sheet_any
    best = None
    for p in glob.glob(os.path.join(ARCHIVE, "**", "*.xls*"), recursive=True):
        try:
            sh = open_sheet_any(p)
        except Exception:
            continue
        head = " ".join(str(sh.cell_value(r, 0)) for r in range(0, 4)).upper()
        if "SALT WISE ITEM LIST" in head:
            m = os.path.getmtime(p)
            if best is None or m > best[0]:
                best = (m, p, sh)
    return best[1:] if best else (None, None)


def stock_map():
    import marg_stock as MS
    def k(s):
        t = (s or "").replace("/", "-").split("-")
        try:
            d, mo, y = (int(x) for x in t)
            return (y, mo, d) if y > 1900 else (0, 0, 0)
        except Exception:
            return (0, 0, 0)
    best = None
    for p in glob.glob(os.path.join(ARCHIVE, "STOCK_CLOSING", "*", "*")):
        try:
            r = MS.read_closing(p)
        except Exception:
            continue
        if r.get("store") != "WHOLE STORES":
            continue
        if best is None or (k(r.get("as_on")), len(r["rows"])) > (k(best.get("as_on")), len(best["rows"])):
            best = r
    return ({x["item"]: int(x["units"] or 0) for x in best["rows"]},
            {x["item"]: int(x["pack_size"] or 1) for x in best["rows"]},
            best.get("as_on")) if best else ({}, {}, None)


def qty(u, size):
    size = max(1, int(size or 1))
    if u < 0:
        return "short " + qty(-u, size)
    if size == 1:
        return "1 pc" if u == 1 else "%d pcs" % u
    st, tb = divmod(int(u), size)
    bits = []
    if st:
        bits.append("1 strip" if st == 1 else "%d strips" % st)
    if tb:
        bits.append("1 tablet" if tb == 1 else "%d tablets" % tb)
    return " ".join(bits) or "none"


def main():
    p, sh = find_export()
    if sh is None:
        print("SALT WISE ITEM LIST not found in the archive"); return 2
    rows = [[sh.cell_value(r, c) for c in range(sh.ncols)] for r in range(sh.nrows)]
    groups, furniture = SA.parse(rows)
    keep, rejected = SA.usable(groups)
    stock, sizes, as_on = stock_map()

    cards = []
    for salt in sorted(keep):
        names, _ = keep[salt]
        sus = SA.__dict__ and SUSPECT.get(salt)
        items = "".join(
            '<li><b>%s</b><span>%s</span></li>'
            % (n, qty(stock.get(n, 0), sizes.get(n, 1)) if n in stock else "not in stock list")
            for n in names)
        cards.append(
            '<div class="grp%s" data-salt="%s"><div class="gh"><h3>%s</h3>%s</div>'
            '<ul>%s</ul>'
            '<div class="ga"><button type="button" data-a="yes">These are interchangeable</button>'
            '<button type="button" data-a="no">No</button></div></div>'
            % (" sus" if sus else "", salt.replace('"', "&quot;"), salt,
               ('<p class="flag">%s</p>' % sus) if sus else "", items))

    rej = "".join('<li><b>%s</b> — %s<span>%s</span></li>'
                  % (s, w, ", ".join(n)) for s, (n, w) in
                  sorted(rejected.items(), key=lambda x: -len(x[1][0]))[:12])

    tpl = io.open(os.path.join(HERE, "salt_template.html"), encoding="utf-8").read()
    html = (tpl.replace("__CARDS__", "\n".join(cards))
               .replace("__REJ__", rej)
               .replace("__NG__", str(len(keep)))
               .replace("__NB__", str(len({n for n, _ in keep.values() for n in n})))
               .replace("__NR__", str(len(rejected)))
               .replace("__NF__", str(furniture))
               .replace("__ASON__", as_on or "—"))
    cut = html.find("</style>") + len("</style>")
    full = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            + html[:cut] + "\n</head>\n<body>\n" + html[cut:] + "\n</body>\n</html>\n")
    import base64
    skel = base64.b64encode(full.encode("utf-8")).decode("ascii")
    html = html.replace("__SHARED__", '{"a":{}}', 1).replace("__SKEL__", skel, 1)
    assert html.count("__SHARED__") == 1 and html.count("__SKEL__") == 1
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(html)
    print("groups to approve %d · brands %d · rejected %d · furniture rows %d"
          % (len(keep), len({n for n, _ in keep.values() for n in n}), len(rejected), furniture))
    print("written:", OUT, len(html), "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
