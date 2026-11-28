#!/usr/bin/env python3
"""make_s975.py FROM_DIR OUT_DIR -- builds kit S975's four files from the FROM bytes (the 28-Nov bundle) and the blocks beside this file.
Every anchor must be found exactly once; the FROM md5s are checked first. Python 3, no third-party modules."""
import hashlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROM, OUT = sys.argv[1], sys.argv[2]
PINS = {"stock_check.py": "623c10528fead13397ac7e7067eb9935", "stock_check.html": "225af840770e22779bd5b670f15fb22a",
        "voucher_judge.py": "0a066f960fba1a110084121a82d4ede3", "item_ledger.py": "6735167f3b56793ae6edbfd504f5584e"}


def rd(p):
    with open(p, "rb") as fh:
        return fh.read()


def blk(n):
    return rd(os.path.join(HERE, "blocks", n)).decode("utf-8")


def once(s, old, new, what):
    n = s.count(old)
    if n != 1:
        sys.exit("ANCHOR %s found %d times -- nothing built" % (what, n))
    return s.replace(old, new)


src = {}
for f, m in PINS.items():
    b = rd(os.path.join(FROM, f))
    if hashlib.md5(b).hexdigest() != m:
        sys.exit("FROM %s is %s, not %s -- nothing built" % (f, hashlib.md5(b).hexdigest()[:8], m[:8]))
    src[f] = b.decode("utf-8")

s = src["stock_check.py"]
s = once(s, 'tagc = dict(settled="grn", count_first="blu", fresh_gap="red", held="gry", look="amb", unknown="gry")[V["v"]]',
         'tagc = dict(settled="grn", count_first="blu", fresh_gap="red", held="gry", look="amb", unknown="gry", surplus="gry").get(V["v"], "gry")   # S975 (F-1738)',
         "sc.tagc")
s = once(s, 'path.append(["ok" if V["v"] in ("settled", "held") else "now", "Whole item today: " + V["word"]])',
         'path.append(["ok" if V["v"] in ("settled", "held", "surplus") else "now", "Whole item today: " + V["word"]])   # S975 (F-1738): a surplus waits for nobody',
         "sc.path")
s = s.rstrip("\n") + "\n" + blk("block_sc.py").rstrip("\n") + "\n"
src["stock_check.py"] = s

v = src["voucher_judge.py"]
src["voucher_judge.py"] = v.rstrip("\n") + "\n" + blk("block_vj.py").rstrip("\n") + "\n"

L = src["item_ledger.py"]
L = once(L, 'bal=("%s counted" % U.fmt(e["counted"])) if e.get("counted") is not None else "—",',
         'bal=("%s counted" % (e.get("counted_t") or U.fmt(e["counted"]))) if e.get("counted") is not None else "—",   # S975 (F-1739)', "il.fold")
L = once(L, 'esc(U.fmt(e["counted"])) if e.get("counted") is not None else "—"',
         'esc(e.get("counted_t") or U.fmt(e["counted"])) if e.get("counted") is not None else "—"', "il.page")
L = once(L, '\nif __name__ == "__main__":', "\n" + blk("block_il.py").strip("\n") + "\n\n\nif __name__ == \"__main__\":", "il.main")
src["item_ledger.py"] = L

h = src["stock_check.html"]
h = once(h, "</style></head>", blk("block_css.txt").rstrip("\n") + "\n</style></head>", "html.css")
h = once(h, "<!-- S967 (27-Nov): THE ONE PAGE",
         "<!-- S975 (28-Nov): the page in three bands (mock-up v10, his 'OK' 11:52 IST, D1106): your write-offs waiting for Amir first, today's\n"
         "     counts second, everything waiting on others folded; the S967-S971 boxes are drawn inside the folds by renderDeskV9. -->\n"
         "<!-- S967 (27-Nov): THE ONE PAGE", "html.head")
h = once(h, "function renderDesk(){var K=DK, h='';", "function renderDeskV9(el){var K=DK, h='';", "html.v9")
h = once(h, "  $('desk').innerHTML=h;\n}\nfunction loadDesk(", "  (el||$('desk')).innerHTML=h;\n}\n" + blk("block_js.txt").rstrip("\n") + "\nfunction loadDesk(", "html.v9end")
h = once(h, "  $('body').innerHTML=h;\n}", "  $('body').innerHTML=h;\n  if(DK&&DK.v10&&(DK.band2||[]).concat(DK.week||[]).some(function(r){return r.surplus;})&&!document.querySelector('#desk details.row[open], #desk button.arm'))renderDesk();   /* S975: Marg's purchases-to day for band 2's surplus line -- never under an open row or an armed button */\n}", "html.rows")
src["stock_check.html"] = h

os.makedirs(OUT, exist_ok=True)
for f, t in src.items():
    with open(os.path.join(OUT, f), "wb") as fh:
        fh.write(t.encode("utf-8"))
    print("%-18s %s -> %s" % (f, PINS[f][:8], hashlib.md5(t.encode("utf-8")).hexdigest()[:8]))
