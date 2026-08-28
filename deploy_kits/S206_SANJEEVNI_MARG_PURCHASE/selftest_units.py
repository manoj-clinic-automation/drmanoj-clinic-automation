#!/usr/bin/python3
"""selftest_units.py — asserted on the real 26-Aug stock vocabulary."""
import sys, os, glob, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import units as U, marg_stock as MS
_f, _p = [], 0
def ck(l, c, d=""):
    global _p
    if c: _p += 1; print("  ok   %s" % l)
    else: _f.append(l); print("  FAIL %s   %s" % (l, d))

def _no_archive(what, archive, passed):
    """Stop cleanly, and loudly, when the Marg archive is not reachable.

    S207. Before this, three of the four selftests in this kit CRASHED at this
    point when the Downloads folder was not connected -- a KeyError, an
    IndexError, and a bare FAILED line. A traceback looks exactly like a real
    regression, and a check that always looks broken is the one that gets
    waved through (D316). It is not a regression: everything below here
    asserts against the real Marg exports, and with no exports there is
    nothing to assert.

    Exit 2 = no data.  Exit 1 = a check genuinely failed.  Exit 0 = passed.
    A runner can now tell the three apart.
    """
    print("")
    print("  ARCHIVE NOT REACHABLE -- %s" % what)
    print("  looked in: %s" % archive)
    print("  %d data-free check(s) passed before this point." % passed)
    print("")
    print("  THIS IS NOT A CODE FAILURE. Connect the Downloads folder, or pass")
    print("  the archive path as the first argument, and run it again.")
    sys.exit(2)


print("[1] strip-packed medicines read as strips + loose")
ck("279 of 1*10 STRI -> 27 strips + 9 tabs",
   U.describe(279, "1*10", "STRI").startswith("27 strips + 9 tabs"), U.describe(279,"1*10","STRI"))
ck("86 of 1*8 STRI -> 10 strips + 6 tabs",
   U.describe(86, "1*8", "STRI").startswith("10 strips + 6 tabs"), U.describe(86,"1*8","STRI"))
ck("an exact multiple has no '+ loose' tail",
   U.describe(280, "1*10", "STRI").startswith("28 strips  ("), U.describe(280,"1*10","STRI"))
ck("a trailing full stop in the pack still parses", U.pack_size("1*10.") == 10)

print("\n[2] whole-unit items are not forced into strips")
ck("-83 of 1*1 PCS -> '-83 pcs'", U.describe(-83, "1*1", "PCS") == "-83 pcs", U.describe(-83,"1*1","PCS"))
ck("15 TUBE with no packing -> tubes", U.describe(15, None, "TUBE") == "15 tubes", U.describe(15,None,"TUBE"))
ck("an INJ vial is a vial", U.describe(25, "1*1", "INJ") == "25 vials", U.describe(25,"1*1","INJ"))

print("\n[3] a negative reads as SHORT, not as a strange strip count")
ck("-132 of 1*10 says 'short'", "short" in U.describe(-132, "1*10", "STRI"), U.describe(-132,"1*10","STRI"))

print("\n[4] the count form asks in Marg's own format")
p = U.count_prompt("1*10", "STRI")
ck("strip item asks TWO boxes", p["boxes"] == 2, repr(p))
ck("and states 1 strip = 10 tabs", p["hint"] == "1 strip = 10 tabs", p["hint"])
q = U.count_prompt("1*1", "PCS")
ck("whole item asks ONE box", q["boxes"] == 1, repr(q))

print("\n[5] THE ARM-SLING CASE — the label must never be trusted over the packing")
ck("'TAB.' on a 1*1 item is flagged suspect", U.label_is_suspect("1*1", "TAB."))
ck("'STRI' on a 1*10 item is NOT suspect", not U.label_is_suspect("1*10", "STRI"))
ck("an arm sling is described as pcs, not tabs",
   U.describe(4, "1*1", "TAB.") == "4 pcs", U.describe(4,"1*1","TAB."))

print("\n[6] against the whole real stock file")
A = sys.argv[1] if len(sys.argv) > 1 else \
    os.path.expanduser("~/mnt/Downloads/margsync/MargArchive")
_closing = sorted(glob.glob(A + "/STOCK_CLOSING/2026-08/*.XLS"))
if not _closing:
    _no_archive("no STOCK_CLOSING export for 2026-08", A, _p)
w = None
for p2 in _closing:
    r = MS.read_closing(p2)
    if r["store"] == "WHOLE STORES": w = r
ck("whole-stores export loaded", w is not None)
if w:
    bad = [r for r in w["rows"] if U.describe(r["units"], r["packing"], r["unit"]) in ("", "?")
           and r["units"] is not None]
    ck("every row renders a description", not bad, repr(bad[:2]))
    susp = [r for r in w["rows"] if U.label_is_suspect(r["packing"], r["unit"])]
    strip = [r for r in w["rows"] if U.is_strip_packed(r["packing"])]
    print("     strip-packed items      : %d" % len(strip))
    print("     whole-unit items        : %d" % (len(w["rows"]) - len(strip)))
    print("     SUSPECT unit labels     : %d  (packing and label disagree)" % len(susp))
    for r in susp[:5]:
        print("        %-32s packing=%-6s label=%-6s -> %s"
              % (r["item"][:32], r["packing"], r["unit"], U.describe(r["units"], r["packing"], r["unit"])))
    ck("suspect labels are found, not silently trusted", len(susp) > 0)

print("\n%d passed, %d failed" % (_p, len(_f)))
for f in _f: print("  FAILED:", f)
sys.exit(1 if _f else 0)
