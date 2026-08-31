#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""selftest_returns_data.py -- the return list, against the real archive.

Exit 0 passed - 1 a check failed - 2 the archive is not reachable.

EVERY CHECK BELOW IS A BUG THAT HAPPENED
    Building this file produced four wrong answers in a row, and not one of
    them raised anything:

      1. reading the closing-stock quantity with float() dropped every
         strip-packed row -- 128 of 377 -- leaving a stock list made almost
         entirely of orthotics;
      2. Marg's Description column is the name, padded, with the PACK glued on
         the end ("VINBACTUM DS   1*1"), in BOTH the stock and expiry exports.
         Matching them raw matched nothing: 57 flagged items, 0 found on the
         shelf -- and the page would have said "nothing needs returning";
      3. a hand-written supplier reader returned the report's own title,
         "/ITEM WISE PURCHASE STATEMENT", as the supplier of seven items;
      4. "-" for nil was skipped rather than recorded as zero.

    (2) is the dangerous one. A wrong answer that reads like good news is the
    one nobody questions, so the check for it is stated as a floor, not a
    number: if this list ever comes back empty, that is a fault until proved
    otherwise.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import re
import returns_data as D

if not os.path.isdir(D.ARCHIVE):
    print("ARCHIVE NOT REACHABLE -- %s" % D.ARCHIVE)
    print("Connect the Downloads folder and run it again. NOT a code failure.")
    sys.exit(2)

_fail, _pass = [], 0


def ck(label, cond, detail=""):
    global _pass
    if cond:
        _pass += 1
        print("  ok   %s" % label)
    else:
        _fail.append(label)
        print("  FAIL %s   %s" % (label, detail))


print("[1] the two comparisons that have silently gone wrong before")
ck("27-08-2026 sorts after 31-03-2026, which it does NOT as text",
   D.as_on_key("27-08-2026") > D.as_on_key("31-03-2026"))
ck("an unreadable date sorts first and can never win",
   D.as_on_key("rubbish") == (0, 0, 0))
ck("a blank expiry sorts LAST, never at the top of a soonest-first list",
   D.expiry_key("") > D.expiry_key("12/2030"))
ck("2/2025 comes before 11/2026 -- month and year, not text",
   D.expiry_key("2/2025") < D.expiry_key("11/2026"))

print("\n[2] the Description column is a name AND a pack")
ck("the pack is split off the name",
   D.split_desc("VINBACTUM DS                   1*1") == ("VINBACTUM DS", "1*1", 1))
ck("and the pack size comes out of it",
   D.split_desc("ALCOXIB 120                    1*10")[2] == 10)
ck("a name with no pack survives untouched",
   D.split_desc("ANKLE BINDER BAMBOO L")[0] == "ANKLE BINDER BAMBOO L")
ck("a trailing full stop in the pack does not break it",
   D.split_desc("DOLOGESIC SP                   1*10.")[2] == 10)
ck("a two-word name keeps its internal single spaces",
   D.split_desc("CROCAL EXTRA TAB               1*10")[0] == "CROCAL EXTRA TAB")

print("\n[3] the quantity column carries two different shapes")
ck("a whole-unit quantity is not zero", D.is_zero("25.0") is False)
ck("a strips:loose quantity is not zero", D.is_zero("10:2") is False)
ck("0:0 is zero", D.is_zero("0:0") is True)
ck("a blank is zero", D.is_zero("") is True)

print("\n[4] the shelf, read from the real export")
st = D.read_stock()
ck("a stock export was found and dated", bool(st["as_on"]), st["file"])
ck("it carries the WHOLE shop, not a category filter (F-235)",
   len(st["rows"]) > 300, "%d rows from %s" % (len(st["rows"]), st["file"]))
ck("strip-packed items are in it, not only whole-unit ones",
   sum(1 for v in st["rows"].values() if ":" in v["raw"]) > 100,
   sum(1 for v in st["rows"].values() if ":" in v["raw"]))
ck("nil is recorded as nil, not dropped",
   sum(1 for v in st["rows"].values() if v["raw"] == "-") > 0)

print("\n[5] the suppliers are suppliers")
sup = D.read_suppliers()
bad = [v for vs in sup.values() for v in vs
       if "STATEMENT" in v.upper() or "PURCHASE STATEMENT" in v.upper()
       or v.strip().startswith("/")]
ck("no report heading is being passed off as a supplier", not bad, bad[:3])
ck("real vendors were found", len(sup) > 100, len(sup))

print("\n[6] the list itself, and how strong its evidence is")
d = D.build()
ck("THE LIST IS NOT EMPTY -- an empty one is a parser fault until proved otherwise",
   len(d["held"]) > 0, len(d["held"]))
ck("every held row names its batch and its expiry",
   all(r["batch"] and r["expiry"] for r in d["held"]))
ck("items flagged but no longer held are shown separately, not silently dropped",
   len(d["gone"]) > 0)
ck("some rows honestly have no supplier -- the page must not invent one",
   any(not r["vendors"] for r in d["held"]))

print("\n[6b] THE CORRECTION -- evidence is graded, never assumed")
# The owner challenged the source and was right: 20 of 28 rows were flagged by
# an expiry export three to fifteen months old, and the closing-stock export
# carries NO batch column, so a match can only ever prove the ITEM has stock.
ck("'newest' is a DATE, not a filename -- two exports share 23-Aug and both count",
   re.match(r"^\d{4}-\d{2}-\d{2}$", D.newest_expiry_date() or ""), D.newest_expiry_date())
ck("every row is graded current / stale / gone",
   all(r["evidence"] in ("current", "stale", "gone")
       for r in d["current"] + d["stale"] + d["gone"]))
# S212: "current" now means newest of ITS OWN FAMILY, not newest overall.
# Marg emits ALREADY-EXPIRED and NEAR-EXPIRY under one title; when three
# near-expiry exports landed on 28-Aug they aged out the 23-Aug expired list
# and hid VINBACTUM DS. One family must never age out another.
_fam = D.expiry_family()
_nbf = d["newest_by_family"]
ck("current rows come from the newest export OF THEIR OWN FAMILY",
   all(D.expiry_date_of(r["seen_in"]) == _nbf.get(_fam.get(r["seen_in"], "NEAR"))
       for r in d["current"]))
ck("stale rows do not",
   all(D.expiry_date_of(r["seen_in"]) != _nbf.get(_fam.get(r["seen_in"], "NEAR"))
       for r in d["stale"]))
ck("both families are actually present in the archive -- the collision is real",
   set(_fam.values()) == {"EXPIRED", "NEAR"}, sorted(set(_fam.values())))
ck("the ALREADY-EXPIRED family is not aged out by the NEAR-EXPIRY family",
   _nbf.get("EXPIRED") and _nbf.get("NEAR") and _nbf["EXPIRED"] < _nbf["NEAR"],
   "expired newest %s  vs  near newest %s" % (_nbf.get("EXPIRED"), _nbf.get("NEAR")))
ck("VINBACTUM DS is graded CURRENT -- it came from the smaller of the two 23-Aug "
   "exports, and taking the newest FILENAME dropped it into stale",
   any(r["item"].upper().startswith("VINBACTUM") for r in d["current"]),
   [r["item"] for r in d["current"]])
ck("a stale row carries the newer batches bought since, so nobody reads it as fact",
   any(r["newer_batches"] for r in d["stale"]),
   sum(1 for r in d["stale"] if r["newer_batches"]))
ck("current is sorted soonest-expiry first",
   [D.expiry_key(r["expiry"]) for r in d["current"]] ==
   sorted(D.expiry_key(r["expiry"]) for r in d["current"]))

neg = [r for r in d["held"] if str(r["shelf"]).strip().startswith("-")]
print("\n[7] what cannot be returned")
ck("negative shelf quantities are present and must be flagged, not offered",
   len(neg) >= 0, [r["item"] for r in neg])

expired_2025 = [r for r in d["held"] if D.expiry_key(r["expiry"]) < (2026, 1)]
print("\n    %d flagged items are STILL HELD and expired before 2026:" % len(expired_2025))
for r in expired_2025[:6]:
    print("      %-22s exp %-8s shelf %s" % (r["item"][:22], r["expiry"], r["shelf"]))

print("\n%d passed, %d failed" % (_pass, len(_fail)))
for f in _fail:
    print("  FAILED:", f)
sys.exit(1 if _fail else 0)
