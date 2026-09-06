"""LIVE-SHAPE WALK -- S226_F322_SUBSET.  Pure stdlib; runs on manojz.

F-322 was raised at the S225 close as a candidate. On the morning of 06-Sep it
happened for real, in front of the owner:

    he merged a duplicate item in Marg -- the cleanup he had been asked for --
    re-exported the closing stock, and the drift page kept showing the gap he
    had just closed.

Two faults, compounding:

  1. `newest_full()` used ROW COUNT as a tiebreaker, so the merged export (one
     row smaller, and legitimately so) lost to the pre-merge file. The log then
     said "pushed and marked" naming the merged file, because the marker records
     what TRIGGERED the run, not what was sent.
  2. Inside the pre-merge file, `LACTOVAX SYP` appears TWICE -- two item masters
     under one name, -2 and 7. The sender kept the first and DROPPED the second
     in silence. The server was told -2. Our books said 5. The page showed a
     seven-unit gap that was never on the shelf.

Sections 1 and 2 below run against the OWNER'S OWN ARCHIVE, read-only, and both
fail on the live file. Section 3 proves the F-235 guard that F-322 corrects is
still doing its job.
"""
import os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import push_snapshot as PS                                   # noqa: E402

ARCHIVE = os.environ.get("MARG_ARCHIVE", PS.DEF_ARCHIVE)
OK, BAD = [], []


def chk(n, c, d=""):
    (OK if c else BAD).append(n + (("  -- " + str(d)) if d and not c else ""))
    print(("  ok   " if c else "  FAIL ") + n + (("   " + str(d)) if d else ""))


print("== S226_F322_SUBSET -- live-shape walk ==")
print("   archive: %s" % ARCHIVE)

# ------------------------------------------------- 1 the owner's own archive
if not os.path.isdir(ARCHIVE):
    print("   ARCHIVE NOT REACHABLE -- sections 1 and 2 skipped")
else:
    full, rejected = PS.newest_full(ARCHIVE)
    chk("a whole-store export is found", full is not None)
    names = {n: (k, why) for n, k, why in rejected}
    chk("the MERGED export is the one chosen, not a rejected one",
        not any("030421" in n for n in names), list(names))
    chk("the two earlier full exports are named SUPERSEDED, not 'a category filter'",
        all(w == "older" for (_, w) in names.values()) and len(names) == 2,
        [(n, names[n]) for n in names])
    chk("nothing full is called a subset any more",
        not any(w == "subset" for (_, w) in names.values()), names)
    lac = [r for r in full["rows"] if "LACTOVAX" in str(r["item"]).upper()]
    chk("the chosen export carries the merged LACTOVAX, once",
        len(lac) == 1 and int(lac[0]["units"]) == 5, lac)

# ------------------------------------------------- 2 the duplicate masters
    tmp = tempfile.mkdtemp(prefix="s226f322_")
    try:
        d = os.path.join(tmp, "STOCK_CLOSING", "2026-09")
        os.makedirs(d)
        src = os.path.join(ARCHIVE, "STOCK_CLOSING", "2026-09")
        pre = [f for f in os.listdir(src) if "2026-09-05" in f and "0114" in f]
        for f in pre:
            shutil.copy2(os.path.join(src, f), d)
        chk("the pre-merge exports are there to test with", len(pre) == 2, pre)
        full2, _ = PS.newest_full(tmp)
        rows = [r for r in full2["rows"] if "LACTOVAX" in str(r["item"]).upper()]
        chk("the pre-merge file really does hold the name twice", len(rows) == 2,
            [(r["item"], r["units"]) for r in rows])
        seen, qty, merged = {}, {}, []
        for row in full2["rows"]:
            n = row["item"]
            if not n or str(n).upper() in ("DESCRIPTION", "TOTAL"):
                continue
            if n in qty:
                qty[n] += int(row["units"] or 0)
                merged.append(n)
            else:
                qty[n] = int(row["units"] or 0)
        chk("two masters under one name ADD UP instead of one being dropped",
            qty.get("LACTOVAX SYP") == 5, qty.get("LACTOVAX SYP"))
        chk("...and the merge is something the run can say out loud",
            "LACTOVAX SYP" in merged, merged)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

# ------------------------------------------------- 3 the F-235 guard still bites
import types                                                  # noqa: E402


def fake_archive(sizes, as_on="05-09-2026", dates=None):
    """sizes: {filename: n_rows}; dates: {filename: as_on} for the ones that
    differ. Returns newest_full() over synthetic files by standing in for the
    reader -- the guard is about counts and dates, not bytes."""
    dates = dates or {}
    import marg_stock as MS
    real_glob = PS.glob.glob
    real_read = MS.read_closing
    paths = [os.path.join("A", "STOCK_CLOSING", "2026-09", n) for n in sizes]

    def g(pattern):
        return paths if "STOCK_CLOSING" in pattern else real_glob(pattern)

    def rd(p):
        n = sizes[os.path.basename(p)]
        return {"store": "WHOLE STORES",
                "as_on": dates.get(os.path.basename(p), as_on),
                "rows": [{"item": "I%04d" % i, "units": 1, "packing": "1*1",
                          "pack_size": 1} for i in range(n)]}
    PS.glob = types.SimpleNamespace(glob=g)
    MS.read_closing = rd
    try:
        return PS.newest_full("A")
    finally:
        PS.glob = types.SimpleNamespace(glob=real_glob)
        MS.read_closing = real_read


best, rej = fake_archive({
    "STOCK_CLOSING_TOTALS__2026-09-05__20260906-011453__aaaaaaaa.XLS": 374,
    "STOCK_CLOSING_TOTALS__2026-09-05__20260906-030421__bbbbbbbb.XLS": 373})
chk("438-of-439 shape: the LATER, ONE-SMALLER export wins",
    len(best["rows"]) == 373, len(best["rows"]))
chk("...and the earlier one is 'older', not 'subset'",
    rej and rej[0][2] == "older", rej)

best, rej = fake_archive({
    "STOCK_CLOSING_TOTALS__2026-09-05__20260906-011453__aaaaaaaa.XLS": 374,
    "STOCK_CLOSING_TOTALS__2026-09-05__20260906-235959__cccccccc.XLS": 81})
chk("THE ORTHOTICS SHAPE: 81 of 374 is still refused, however late it is",
    len(best["rows"]) == 374, len(best["rows"]))
chk("...and it is named a category filter",
    rej and rej[0][2] == "subset", rej)

best, rej = fake_archive({
    "STOCK_CLOSING_TOTALS__2026-09-05__20260906-011453__aaaaaaaa.XLS": 374,
    "STOCK_CLOSING_TOTALS__2026-09-05__20260906-235959__dddddddd.XLS": 224})
chk("exactly at the 60% line, a late export is still a filter",
    len(best["rows"]) == 374, len(best["rows"]))
best, rej = fake_archive({
    "STOCK_CLOSING_TOTALS__2026-09-05__20260906-011453__aaaaaaaa.XLS": 374,
    "STOCK_CLOSING_TOTALS__2026-09-05__20260906-235959__eeeeeeee.XLS": 226})
chk("just above it, a late export supersedes", len(best["rows"]) == 226,
    len(best["rows"]))

best, rej = fake_archive(
    {"STOCK_CLOSING_TOTALS__2026-09-04__20260905-090000__ffffffff.XLS": 900,
     "STOCK_CLOSING_TOTALS__2026-09-05__20260906-030421__bbbbbbbb.XLS": 373},
    dates={"STOCK_CLOSING_TOTALS__2026-09-04__20260905-090000__ffffffff.XLS":
           "04-09-2026"})
chk("a BIGGER export of an OLDER day never wins -- the day is chosen first",
    best["as_on"] == "05-09-2026" and len(best["rows"]) == 373,
    (best["as_on"], len(best["rows"])))
chk("...and a different day is not reported as a rejection at all", rej == [], rej)

chk("the two rules are ONE number",
    PS.SUBSET_MAX_FRACTION == 0.60, PS.SUBSET_MAX_FRACTION)

print("\n%d ok, %d FAILED" % (len(OK), len(BAD)))
for b in BAD:
    print("   FAILED: " + b)
sys.exit(1 if BAD else 0)
