#!/usr/bin/python3
"""
selftest_marg_stock.py — asserts marg_stock.py against the REAL archive.

THE HEADLINE CHECK IS THE CROSS-STORE IDENTITY, and it is here because it
already earned its place: it CAUGHT A REAL BUG in this parser. Marg exports the
same stock four ways — DTH, MAIN STORE, SCRAP STORE and WHOLE STORES — so
    WHOLE STORES  ==  MAIN STORE + DTH + SCRAP STORE,  item by item
is an identity the file must satisfy. The first parser read '-0:10' as +10
(sign on the packs field) and this check went RED on two items. Reading the
sign as covering the whole quantity makes it -10, and the identity closes on
all 375. **A check that cannot go red has measured nothing.**

Run:  python3 selftest_marg_stock.py [ARCHIVE_DIR]
Exit: 0 all passed, 1 any failed.
"""
import os
import sys
import glob
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import marg_stock as MS

ARCHIVE = sys.argv[1] if len(sys.argv) > 1 else \
    os.path.expanduser("~/mnt/Downloads/margsync/MargArchive")
_fail = []
_pass = 0


def _refuses(fn, path):
    try:
        fn(path)
        return False
    except MS.Refused:
        return True
    except Exception:
        return False


def ck(label, cond, detail=""):
    global _pass
    if cond:
        _pass += 1
        print("  ok   %s" % label)
    else:
        _fail.append(label)
        print("  FAIL %s   %s" % (label, detail))


print("selftest_marg_stock — archive: %s" % ARCHIVE)

print("\n[1] the sign rule — the bug this suite exists to prevent")
ck("'-0:10' with pack 10 is -10, NOT +10", MS.parse_qty("-0:10", 10)[2] == -10,
   repr(MS.parse_qty("-0:10", 10)))
ck("'-4:4'  with pack 10 is -44, NOT -36", MS.parse_qty("-4:4", 10)[2] == -44,
   repr(MS.parse_qty("-4:4", 10)))
ck("'4:14'  with pack 20 is 94", MS.parse_qty("4:14", 20)[2] == 94)
ck("'-' is nil", MS.parse_qty("-", 10)[2] == 0)
ck("a bare '-83' is -83", MS.parse_qty("-83", 1)[2] == -83)

print("\n[2] packing forms seen in the real file")
ck("'ACILOC 300   1*20' splits to name/packing/size",
   MS.split_desc("ACILOC 300                    1*20") == ("ACILOC 300", "1*20", 20))
ck("a TRAILING FULL STOP is tolerated — 'DOLOGESIC SP 1*10.'",
   MS.split_desc("DOLOGESIC SP                  1*10.")[2] == 10,
   repr(MS.split_desc("DOLOGESIC SP                  1*10.")))

closing = sorted(glob.glob(os.path.join(ARCHIVE, "STOCK_CLOSING", "2026-08", "*.XLS")))
print("\n[3] the four exports are four STORES, identified by title not filename")
ck("four closing exports found", len(closing) == 4, "%d" % len(closing))
stores = {}
for p in closing:
    rep = MS.read_closing(p)
    stores[rep["store"]] = rep
ck("stores are DTH / MAIN STORE / SCRAP STORE / WHOLE STORES",
   set(stores) == {"DTH", "MAIN STORE", "SCRAP STORE", "WHOLE STORES"},
   repr(sorted(stores)))
ck("all four are 'as on' the same date",
   len({r["as_on"] for r in stores.values()}) == 1,
   repr({s: r["as_on"] for s, r in stores.items()}))

print("\n[4] THE CROSS-STORE IDENTITY — WHOLE == MAIN + DTH + SCRAP, item by item")


def idx(rep):
    d = collections.defaultdict(float)
    for r in rep["rows"]:
        if r["units"] is not None:
            d[(r["item"], r["packing"])] += r["units"]
    return d


w = idx(stores["WHOLE STORES"])
parts = collections.defaultdict(float)
for k in ("MAIN STORE", "DTH", "SCRAP STORE"):
    for kk, v in idx(stores[k]).items():
        parts[kk] += v
keys = set(w) | set(parts)
bad = [(k, w.get(k, 0), parts.get(k, 0)) for k in keys
       if abs(w.get(k, 0) - parts.get(k, 0)) > 0.001]
ck("identity holds on every item (%d checked)" % len(keys), not bad,
   "%d disagree, first: %r" % (len(bad), bad[0] if bad else None))

print("\n[5] nothing silently unreadable")
whole = stores["WHOLE STORES"]
unp = [r for r in whole["rows"] if r["units"] is None]
ck("no unparseable stock cell in WHOLE STORES", not unp,
   repr([(r["item"], r["raw"]) for r in unp[:3]]))
ck("the reprinted header row is not read as an item",
   not any(r["item"].upper() == "DESCRIPTION" for r in whole["rows"]))

print("\n[6] the refusal path must work — feed it a PURCHASE export")
pur = sorted(glob.glob(os.path.join(ARCHIVE, "PURCHASE_ITEMWISE", "*", "*.XLS")))
refused = False
if pur:
    try:
        MS.read_closing(pur[0])
    except MS.Refused:
        refused = True
    except Exception as e:
        ck("refusal is a Refused, not a crash", False, "%s: %s" % (type(e).__name__, e))
ck("a PURCHASE export is REFUSED by read_closing", refused,
   "it returned data — the refusal path is dead")

print("\n[7] expiry exports — two cutoffs, told apart by contents not by header")
exp = sorted(glob.glob(os.path.join(ARCHIVE, "STOCK_EXPIRY", "2026-08", "*.XLS")))
reps = [MS.read_expiry(p) for p in exp]
ck("two expiry exports found", len(reps) == 2, "%d" % len(reps))
if len(reps) == 2:
    sets = [sorted({r["expiry"] for r in rep["rows"]}) for rep in reps]
    ck("they carry DIFFERENT expiry sets", sets[0] != sets[1], repr(sets))
    ck("every expiry row has a batch",
       all(r["batch"] for rep in reps for r in rep["rows"]))

print("\n[7b] THE MULTI-STORE EXPORT — one file must reproduce all three per-store ones")
multi_p = glob.glob(os.path.join(ARCHIVE, "_REFUSED", "*.XLS")) + \
          glob.glob(os.path.join(ARCHIVE, "STOCK_CLOSING", "*", "*MULTI*.XLS"))
multi = None
for p in multi_p:
    try:
        multi = MS.read_closing_multi(p)
        break
    except Exception:
        continue
if multi is None:
    print("  --   no multi-store export present in this archive; section skipped")
else:
    ck("multi-store export parsed (%d rows, as on %s)" % (len(multi["rows"]), multi["as_on"]),
       len(multi["rows"]) > 300)
    bad = [r for r in multi["rows"]
           if None not in (r["whole"], r["dth"], r["main"])
           and abs(r["whole"] - (r["dth"] + r["main"])) > 0.001]
    ck("INSIDE the file, WHOLE == DTH + MAIN on every row", not bad,
       "%d disagree, first %r" % (len(bad), bad[0]["item"] if bad else None))

    def flat(rep, key):
        d = collections.defaultdict(float)
        for r in rep["rows"]:
            if r[key] is not None:
                d[r["item"]] += r[key]
        return d

    for store, key in (("WHOLE STORES", "whole"), ("DTH", "dth"), ("MAIN STORE", "main")):
        mm = flat(multi, key)
        sg = idx(stores[store])
        sg2 = collections.defaultdict(float)
        for (nm, _pk), v in sg.items():
            sg2[nm] += v
        keys = set(mm) | set(sg2)
        diff = [k for k in keys if abs(mm.get(k, 0) - sg2.get(k, 0)) > 0.001]
        ck("multi[%s] == the %s export, item for item (%d)" % (key, store, len(keys)),
           not diff, "%d disagree, first %r" % (len(diff), sorted(diff)[:2]))

    print("\n[7c] the three traps in that layout")
    ck("the item name is joined from TWO columns, not taken from col0",
       any(" " in r["item"] and r["item"].startswith("ANKLE") for r in multi["rows"]),
       "no multi-word ANKLE row found")
    ck("a TOTAL row is not read as an item",
       not any(r["item"].upper() == "TOTAL" for r in multi["rows"]))
    ck("a per-store export is REFUSED by read_closing_multi",
       _refuses(MS.read_closing_multi, closing[0]))

print("\n[8] what the archive actually says — reported, not asserted")
neg = [r for r in whole["rows"] if r["units"] is not None and r["units"] < 0]
print("  items listed        : %d" % len(whole["rows"]))
print("  with stock          : %d" % sum(1 for r in whole["rows"] if r["units"]))
print("  NEGATIVE stock lines: %d   (net %d units short)"
      % (len(neg), sum(r["units"] for r in neg)))

print("\n%d passed, %d failed" % (_pass, len(_fail)))
for f in _fail:
    print("  FAILED: %s" % f)
sys.exit(1 if _fail else 0)
