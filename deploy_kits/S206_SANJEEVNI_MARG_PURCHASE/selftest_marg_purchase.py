#!/usr/bin/python3
"""
selftest_marg_purchase.py — asserts marg_purchase.py against the REAL archive.

Written BEFORE the reporting code, per the Q1 instruction, and it asserts
against real archived files rather than fixtures, because the whole risk in
this parser is the shapes Marg actually emits.

IT MUST BE ABLE TO FAIL ON THE MACHINE IT RUNS ON. Section 6 proves that: it
feeds the parser a real SALE export and requires a refusal. If section 6 ever
passes silently, the refusal path is dead and every other check is worthless.

Run:  python3 selftest_marg_purchase.py [ARCHIVE_DIR]
Exit: 0 all passed, 1 any failed.
"""
import os
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import marg_purchase as MP

ARCHIVE = sys.argv[1] if len(sys.argv) > 1 else \
    os.path.expanduser("~/mnt/Downloads/margsync/MargArchive")

_fail = []
_pass = 0


def ck(label, cond, detail=""):
    global _pass
    if cond:
        _pass += 1
        print("  ok   %s" % label)
    else:
        _fail.append(label)
        print("  FAIL %s   %s" % (label, detail))


print("selftest_marg_purchase — archive: %s" % ARCHIVE)

files = sorted(glob.glob(os.path.join(ARCHIVE, "PURCHASE_ITEMWISE", "*", "*.XLS")))
print("\n[1] the archive is where the queue says it is")
ck("found PURCHASE_ITEMWISE exports", len(files) >= 5, "found %d" % len(files))
if not files:
    print("\nnothing to test against — stopping"); sys.exit(1)

print("\n[2] every archived month parses, and its own arithmetic closes")
parsed = {}
for p in files:
    month = os.path.basename(os.path.dirname(p))
    try:
        rep = MP.read_purchase(p)
        parsed[month] = rep
        ck("%s parses (%d rows, %d suppliers)"
           % (month, len(rep["rows"]), len(rep["suppliers"])), True)
    except MP.Refused as e:
        ck("%s parses" % month, False, str(e)[:160])

if not parsed:
    print("\nno month parsed — stopping"); sys.exit(1)

print("\n[2b] THE CHECK THAT ACTUALLY CLOSES — TOTAL rows must sum to GRAND TOTAL")
for m, rep in sorted(parsed.items()):
    g = rep["grand_amount"]; t = rep["totals_sum"]
    ck("%s  totals %.2f == GRAND %.2f" % (m, t, g or -1),
       g is not None and abs(t - g) <= 0.05)

print("\n[3] BOTH column layouts are exercised by real data")
lay_a = lay_b = 0
for rep in parsed.values():
    for r in rep["rows"]:
        if r["batch"] and r["expiry"]:
            lay_a += 1
ck("rows with BOTH batch and expiry recovered", lay_a > 0, "%d" % lay_a)

apr = parsed.get("2026-04")
if apr:
    rows = {(r["row"]): r for r in apr["rows"]}
    r6 = rows.get(6)
    r10 = rows.get(10)
    print("\n[4] April spot-checks — layout A (batch in col2, expiry in col3)")
    ck("row 6 item is RYCOBAL D3", r6 and r6["item"] == "RYCOBAL D3",
       repr(r6 and r6["item"]))
    ck("row 6 batch HT122559", r6 and r6["batch"] == "HT122559",
       repr(r6 and r6["batch"]))
    ck("row 6 expiry 5/27", r6 and r6["expiry"] == "5/27", repr(r6 and r6["expiry"]))
    ck("row 6 packing 1*10", r6 and r6["packing"] == "1*10", repr(r6 and r6["packing"]))
    ck("row 6 qty 20", r6 and r6["qty"] == 20, repr(r6 and r6["qty"]))
    ck("row 6 amount 1890", r6 and r6["amount"] == 1890, repr(r6 and r6["amount"]))
    ck("row 6 net_amount 1895.26 and net_rate 9.48 split from one cell",
       r6 and r6["net_amount"] == 1895.26 and r6["net_rate"] == 9.48,
       repr(r6 and (r6["net_amount"], r6["net_rate"])))

    print("\n[5] April spot-check — layout B (THE TRAP: batch+expiry concatenated)")
    ck("row 10 batch HT072565 recovered from 'HT07256512/26'",
       r10 and r10["batch"] == "HT072565", repr(r10 and r10["batch"]))
    ck("row 10 expiry 12/26", r10 and r10["expiry"] == "12/26",
       repr(r10 and r10["expiry"]))
    ck("row 10 packing 1*10 (col2 held packing only)",
       r10 and r10["packing"] == "1*10", repr(r10 and r10["packing"]))

    print("\n[5b] supplier heading split across cells is joined, not truncated")
    names = [s["name"] for s in apr["suppliers"]]
    ck("'DRUG DEAL BAREILLY' joined from three cells",
       any(n and n.startswith("DRUG DEAL") for n in names),
       repr([n for n in names][:6]))
    ck("'ESSENTIAL PHARMA BAREILLY' found though col0 was empty",
       any(n and n.startswith("ESSENTIAL PHARMA") for n in names))
    ck("first supplier total is 9080 (its own TOTAL row)",
       apr["suppliers"] and apr["suppliers"][0]["total_amount"] == 9080,
       repr(apr["suppliers"][0] if apr["suppliers"] else None))

print("\n[5c] THE MEASURED VARIANCE — item rows over-sum, totals do not")
for m, rep in sorted(parsed.items()):
    g = rep["grand_amount"] or 0
    exc = round(rep["items_sum"] - g, 2)
    pct = (100.0 * exc / g) if g else 0
    flag = "" if abs(exc) <= 0.05 else "  <-- %d group(s) over-sum" % len(rep["variances"])
    print("  %s  items %12.2f  grand %12.2f  excess %+9.2f (%+.2f%%)%s"
          % (m, rep["items_sum"], g, exc, pct, flag))
ck("at least one month shows the over-sum (it is real, not a parser artefact)",
   any(abs(r["items_sum"] - (r["grand_amount"] or 0)) > 0.05 for r in parsed.values()))
ck("every over-sum is itemised in rep['variances'], never swallowed",
   all((abs(r["items_sum"] - (r["grand_amount"] or 0)) <= 0.05) or r["variances"]
       for r in parsed.values()))

print("\n[6] THE REFUSAL PATH MUST WORK — feed it a SALE export")
sale = sorted(glob.glob(os.path.join(ARCHIVE, "SALE_BILLWISE", "*", "*.XLS")))
if not sale:
    ck("a sale export exists to test refusal with", False, "none found")
else:
    refused = False
    try:
        MP.read_purchase(sale[0])
    except MP.Refused:
        refused = True
    except Exception as e:
        ck("refusal is a Refused, not a crash", False, "%s: %s" % (type(e).__name__, e))
    ck("a SALE export is REFUSED, not half-parsed", refused,
       "it returned data — the refusal path is dead")

print("\n[7] what the parser could NOT do — reported, never hidden")
tot = unsplit = noexp = 0
for m, rep in sorted(parsed.items()):
    tot += len(rep["rows"]); unsplit += len(rep["unsplit"]); noexp += len(rep["no_expiry"])
    print("  %s  rows=%-5d bill-merged-into-item=%-4d no-expiry=%-4d suppliers=%d"
          % (m, len(rep["rows"]), len(rep["unsplit"]), len(rep["no_expiry"]),
             len(rep["suppliers"])))
print("  TOTAL rows=%d  bill-merged=%d (%.1f%%)  no-expiry=%d (%.1f%%)"
      % (tot, unsplit, 100.0*unsplit/tot if tot else 0,
         noexp, 100.0*noexp/tot if tot else 0))
ck("no row was silently dropped (unparsed is empty or it refused)",
   all(not rep["unparsed"] for rep in parsed.values()))

print("\n%d passed, %d failed" % (_pass, len(_fail)))
for f in _fail:
    print("  FAILED: %s" % f)
sys.exit(1 if _fail else 0)
