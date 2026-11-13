#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s810.py ROUTER_DIR TILE_DIR [--control] -- kit S810's walk, on made-up sheets (no Marg file, no number).

ROUTER_DIR holds marg_router.py (+ signatures.json, xlsx_stdlib.py beside it or on sys.path);
TILE_DIR holds reports_tile.py (its sibling modules on sys.path).  Last line:
  WALK S810 GREEN                     -- every check on the built files
  CONTROL S810 RED as it must be      -- with --control on the live files (the store checks must fail there)"""
import importlib.util, io, os, sqlite3, sys, contextlib

rdir, tdir = sys.argv[1], sys.argv[2]
control = "--control" in sys.argv
for p in (tdir, rdir):
    if p not in sys.path:
        sys.path.insert(0, p)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


R = load(os.path.join(rdir, "marg_router.py"), "marg_router")
sys.modules["marg_router"] = R
sigs = R.load_signatures(os.path.join(rdir, "signatures.json") if os.path.exists(os.path.join(rdir, "signatures.json"))
                         else os.path.join(os.path.dirname(rdir), "signatures.json"))
T = load(os.path.join(tdir, "reports_tile.py"), "reports_tile_s810")
res = []


def ck(n, c):
    res.append((n, bool(c)))
    print(("  ok   " if c else "  RED  ") + n)


class Sh(object):
    def __init__(self, rows):
        self.rows = rows; self.nrows = len(rows); self.ncols = max(len(r) for r in rows)

    def cell_value(self, r, c):
        return self.rows[r][c] if c < len(self.rows[r]) else ""


TOT = ["S.No.", "Description", "Total Stock", "Unit"]
BAT = ["S.No. Description", "Batch", "Expiry", "Stock Unit"]
VAL = ["S.No. Description", "Stock", "Rate", "Value"]
CASES = [  # title, header, body rows, (want verdict, want words in the reason)
    ("WHOLE STORES CLOSING STOCK AS ON 12-11-2026", TOT, [["1.0", "A", "1", "PCS"], ["TOTAL", "", "1", ""]], ("VERIFIED", "")),
    ("MAIN STORE CLOSING STOCK AS ON 12-11-2026", TOT, [["1.0", "A", "1", "PCS"], ["TOTAL", "", "1", ""]], ("REFUSED", "MAIN STORE only -- the WHOLE STORES report is needed")),
    ("DTH,MAIN STORE,CLOSING STOCK AS ON 12-11-2026", TOT, [["1.0", "A", "1", "PCS"], ["TOTAL", "", "1", ""]], ("REFUSED", "DTH, MAIN STORE only -- the WHOLE STORES report is needed")),
    ("SCRAP STORE,WHOLE,CLOSING STOCK AS ON 12-11-2026", TOT, [["1.0", "A", "1", "PCS"], ["TOTAL", "", "1", ""]], ("VERIFIED", "")),
    ("SCRAP STORE CLOSING STOCK AS ON 12-11-2026", BAT, [["1 A 1*10", "B1", "10/2027", "1"], ["TOTAL", "", "", "1"]], ("REFUSED", "SCRAP STORE only -- the WHOLE STORES report is needed")),
    ("WHOLE STORES CLOSING STOCK AS ON 12-11-2026", BAT, [["1 A 1*10", "B1", "10/2027", "1"], ["TOTAL", "", "", "1"]], ("VERIFIED", "")),
    ("DTH,MAIN STORE,STOCK VALUATION AS ON 31-10-2026", VAL, [["1 A", "1", "2", "2"], ["TOTAL", "", "", "2"]], ("REFUSED", "DTH, MAIN STORE only -- the WHOLE STORES report is needed")),
    ("WHOLE STORES STOCK VALUATION AS ON 31-10-2026", VAL, [["1 A", "1", "2", "2"], ["TOTAL", "", "", "2"]], ("VERIFIED", "")),
]
for title, hdr, body, (wv, wr) in CASES:
    sh = Sh([[title], hdr] + body)
    sig, st, why = R.identify(title, hdr, sigs)
    d = R.dates_from(title, sh, 1, 0)
    v, r = R.verify("", sh, sig, title, hdr, 1, d[0], d[1], d[2], d[3]) if sig else ("?", why)
    ck("door: %-48s [%s] -> %s" % (title[:48], (sig or {}).get("type", "?"), wv if not wr else "REFUSED, the store named"),
       st == "IDENTIFIED" and v == wv and (wr in (r or "") if wr else True))
ck("door: an expiry report is never judged by store", R.verify("", Sh([["EXP. BEFORE *BA., 0"], BAT, ["TOTAL"]]),
   {"type": "STOCK_EXPIRY", "end_marker": "TOTAL"}, "EXP. BEFORE *BA., 0", BAT, 1, "2026-11-12", "2026-11-12", None, None)[0] == "VERIFIED")
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = R.selftest(print)
ck("the router's own selftest, with the S810 checks in it", rc == 0 and "S810 store rule" in buf.getvalue())

# the staff tile: the refusal shown in Hindi, the store named, WHOLE asked for, the second try counted
hi = T.hindi_reason("MAIN STORE only -- the WHOLE STORES report is needed", "REFUSED")
ck("tile: the Hindi line names the store and asks for WHOLE",
   hi == "Yeh sirf MAIN STORE ki report hai. Select Store mein WHOLE chuniye, phir dobara nikaaliye.")
ck("tile: another word in the reason does not hide it",
   "DTH, MAIN STORE ki" in T.hindi_reason("TRUNCATED -- x | DTH, MAIN STORE only -- the WHOLE STORES report is needed", "REFUSED"))
ck("tile: the router's other reasons keep their Hindi lines",
   "pehchan" in T.hindi_reason("no signature matches this title: 'X'", "UNKNOWN")
   and "ant tak" in T.hindi_reason("TRUNCATED -- the completeness marker 'TOTAL' is missing", "REFUSED"))
cx = sqlite3.connect(":memory:"); cx.row_factory = sqlite3.Row
f = T._s500_stock_file(cx, {"verdict": "REFUSED", "reason": "MAIN STORE only -- the WHOLE STORES report is needed",
                            "received_at": "2026-11-13T08:10:00+05:30", "stamp": "20261113-080900", "md5": "x" * 32,
                            "type": "STOCK_CLOSING", "variant": "TOTALS", "date_from": "2026-11-12", "date_to": "2026-11-12"})
ck("tile: a refused closing is a WRONG try on Shavez's tile, the Hindi line on it, the closing-stock steps offered",
   f.get("j") == "wrong" and f.get("door") is True and f.get("fix") == "stock25" and "sirf MAIN STORE" in (f.get("why_hi") or ""))

n_red = sum(1 for _, c in res if not c)
print("%d checks, %d red" % (len(res), n_red))
if control:
    print("CONTROL S810 RED as it must be" if n_red >= 6 else "CONTROL S810 NOT RED -- the walk proves nothing")
else:
    print("WALK S810 GREEN" if n_red == 0 else "WALK S810 RED")
