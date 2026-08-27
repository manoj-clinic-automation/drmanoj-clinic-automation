#!/usr/bin/python3
"""
selftest_reconcile.py -- the reconciliation's own checks. No Marg files needed.

Every check here corresponds to a fault that actually occurred in S206 and cost
real accuracy. A check that has never caught anything is decoration; each of
these caught something.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import packmap as PM, resolve as R, alias as A, classify as C
import rename16 as RN

F = []
def ck(name, cond):
    F.append((name, bool(cond)))

# --- pack sizes -------------------------------------------------------------
ck("1*10 is a strip of ten", PM.pack_size("1*10") == 10)
ck("1*15 is a strip of fifteen", PM.pack_size("1*15") == 15)
ck("trailing dot does not break the pack size", PM.pack_size("1*10.") == 10)
ck("1*1 is a WHOLE unit, not a strip of one", PM.pack_size("1*1") is None)
ck("30GM is a whole unit", PM.pack_size("30GM") is None)
ck("VAIL is a whole unit", PM.pack_size("VAIL") is None)
ck("279 at 1*10 is 27 strips and 9", PM.describe(279, 10) == "27 strips + 9")
ck("a shortage is described as short", PM.describe(-132, 10).startswith("short"))
ck("a whole unit prints as a plain number", PM.describe(6, None) == "6")
ck("packs:loose converts with the pack size", PM.units(27, 9, 10) == 279)
ck("a whole unit ignores the packs field", PM.units(0, 6, None) == 6)

# --- the name key -----------------------------------------------------------
ck("case and spacing collapse", PM.norm("  bio  d3 MAX ") == "BIO D3 MAX")
ck("a trailing dot is not a different item", PM.norm("200ML.") == PM.norm("200ML"))
ck("ALCOXIB 120 keeps its number", PM.norm("ALCOXIB 120") == "ALCOXIB 120")

# --- the glued sale cell ----------------------------------------------------
ck("the glued cell splits", R.unglue('1 *** PRIME CAST 5" 1*1') == ('PRIME CAST 5"', "1*1"))
ck("a normal name is left alone", R.unglue("CROCAL") == ("CROCAL", None))

# --- the 20-character truncation -------------------------------------------
m, a, u = R.build_map(
    ["DISPO SYRINGE NIPRO", "SHOULDER IMMOBILISE", "L S BELT CONT GRAY U", "CROCAL", "THI OQ AP"],
    ["DISPO SYRINGE NIPRO 3ML", "SHOULDER IMMOBILISE UNISON", "L S BELT CONT GRAY UNISON L",
     "L S BELT CONT GRAY UNISON M", "CROCAL", "THIO Q AP"])
# THE FAULT THIS CATCHES: a `len(key) == 20` test misses every truncation whose
# cut landed on a space and was then stripped -- including the largest, 574 units.
ck("a cut that landed on a space is still a truncation",
   m.get("DISPO SYRINGE NIPRO") == "DISPO SYRINGE NIPRO 3ML")
ck("a 19-character cut resolves too", m.get("SHOULDER IMMOBILISE") == "SHOULDER IMMOBILISE UNISON")
ck("several sizes behind one cut stay AMBIGUOUS", "L S BELT CONT GRAY U" in a)
ck("an ambiguous cut is never mapped to a size", "L S BELT CONT GRAY U" not in m)
ck("a name already in the master is left alone", "CROCAL" not in m and "CROCAL" not in u)
ck("an unrelated name is reported unresolved", u == ["THI OQ AP"])

# --- alias / rename ---------------------------------------------------------
ck("a moved space is the same product", A.squash("THIO Q AP") == A.squash("THI OQ AP"))
ck("an inserted token is the same product", bool(A.name_related("PARI 25", "PARI CR 25")))
ck("two real products do not pair", A.name_related("CROCAL", "BIO D3 MAX") is None)
ck("two strengths do not pair", A.name_related("PARI 25", "PARI CR 12.5") is None)
ck("two forms of one brand do not pair",
   A.name_related("GEMCAL 500MG", "GEMCAL XT TABLETS") is None)
# THE FAULT THIS CATCHES: the token tests missed a pure word-reordering,
# because '3ML' and '3 ML' tokenise differently. 'NIPRO 3 ML DISPO SYRINGE'
# sat at MINUS 83 -- 88 sold on a code never purchased -- while
# 'DISPO SYRINGE NIPRO 3ML' held the whole 600-unit purchase.
ck("the same words in a different order are the same product",
   sorted(A.squash("DISPO SYRINGE NIPRO 3ML")) == sorted(A.squash("NIPRO 3 ML DISPO SYRINGE")))
ck("an anagram of a SHORT code is not evidence",
   sorted(A.squash("ACILOC")) != sorted(A.squash("BIO D3")))

def row(k, **kw):
    d = dict(key=k, item=k, opening=0, purchased=0, preturn=0, sold=0, sreturn=0,
             closing=0, expected=0, var=0, size=10, in_master=True, on_list=True,
             family=False, months={})
    d.update(kw); return d

pair = [row("A NAME", purchased=100, var=-50), row("A NAME LONG", sold=100, var=50)]
conf, cand = A.find(pair)
ck("a cancelling pair is confirmed", len(conf) == 1 and abs(conf[0]["residual"]) < 1)
# A merge must IMPROVE the reconciliation, or it is not a merge.
worse = [row("B NAME", purchased=100, var=-5), row("B NAME LONG", sold=100, var=90)]
c2, _ = A.find(worse)
ck("a merge that leaves more than it removes is rejected", not c2)

# --- classification ---------------------------------------------------------
rows = [row("OFF LIST ONE", opening=5, closing=0, var=-5, in_master=False, on_list=False),
        row("ZEROED ONE", opening=5, closing=0, var=-5, in_master=True, on_list=True),
        row("GOODS IN ONE", purchased=10, sold=5, closing=470, var=470),
        row("NEG ONE", opening=-42, purchased=100, sold=58, closing=0, var=42),
        row("BIG NEG", opening=-42, purchased=100, sold=58, closing=280, var=280)]
out, _, _ = C.classify(rows)
by = {r["key"]: r["class"] for r in out}
# THE FAULT THIS CATCHES: one class was covering two different events.
# An item ZEROED BY HAND is still on the list -- that is the owner's expiry
# routine, and it writes no voucher, so no report can show it. An item OFF the
# list entirely is stock a stock-taker can never count. Merging them hid which
# was which.
ck("stock zeroed on a code still listed is ZEROED", by.get("ZEROED ONE") == "ZEROED")
ck("stock on a code no longer listed is OFF_LIST", by.get("OFF LIST ONE") == "OFF_LIST")
ck("unexplained surplus is GOODS_IN", by.get("GOODS IN ONE") == "GOODS_IN")
ck("a negative opening explains its own size", by.get("NEG ONE") == "NEG_CLEARED")
# THE FAULT THIS CATCHES: a -42 opening was absorbing a +280 variance, which
# buried 238 units in a class whose name says 'resolved'.
ck("a small negative cannot absorb a large surplus", by.get("BIG NEG") == "GOODS_IN")
ck("no item is ever silently dropped", len(out) == len(rows))

# --- the 16-character rename ----------------------------------------------
ck("a name inside the limit is left alone", RN.propose("CROCAL")[0] == "CROCAL")
ck("the size survives", RN.propose("SHOULDER IMMOBILISER TYNOR XL")[0].endswith(" XL"))
ck("the strength survives", RN.propose("FOLITRAX 15 MG TAB")[0].endswith("15 MG TAB"))
# THE FAULT THIS CATCHES: body and identifier were cut from two different token
# lists, so a size in the MIDDLE was left in the body AND appended again --
# 'ANKLE BINDER L TYNOR' came out as 'ANKLE BINDER L L'. Nineteen names did.
b, i = RN.split_name(RN.toks("ANKLE BINDER L TYNOR"))
ck("a size in the middle is cut once, not twice", b == ["ANKLE", "BINDER"] and i == ["L"])
ck("and the rename does not double it", RN.propose("ANKLE BINDER L TYNOR")[0] == "ANKLE BINDER L")
# THE FAULT THIS CATCHES: a vendor word sitting AFTER the size stopped the scan,
# so 'KNEE SUPPORT HINGED XXL UNISO' lost its XXL entirely.
ck("a vendor word after the size does not hide it",
   RN.identifier(RN.toks("KNEE SUPPORT HINGED XXL UNISO")) == ["XXL"])
# THE FAULT THIS CATCHES: sizes proposed one at a time got different cores --
# 'KNEE SUPP HNGD L' beside 'KNEE HNGD XL'. Both fit; together they are
# unreadable as one product.
famout, _ = RN.propose_family(["KNEE SUPPORT HINGED L", "KNEE SUPPORT HINGED M",
                               "KNEE SUPPORT HINGED XL"])
cores = {v.rsplit(" ", 1)[0] for v in famout.values()}
ck("every size in a family gets the same core", len(cores) == 1)
ck("every renamed size fits the limit", all(len(v) <= RN.LIMIT for v in famout.values()))
# THE FAULT THIS CATCHES: dropping the longest word turned DECA INSTABOLIN 50
# into DECA 50. Squeezing must be tried before a word is given up.
ck("a brand word is squeezed, not dropped", "INST" in RN.propose("DECA INSTABOLIN 50")[0])
ok2, probs = RN.verify([("A LONG NAME ONE", "SHORT X", ""), ("A LONG NAME TWO", "SHORT X", "")],
                       {"A LONG NAME ONE", "A LONG NAME TWO"})
ck("two renames onto one name are refused", not ok2 and probs)

bad = [n for n, ok in F if not ok]
for n, ok in F:
    print("  %s  %s" % ("ok  " if ok else "FAIL", n))
print("\n%d checks, %d failed" % (len(F), len(bad)))
sys.exit(1 if bad else 0)
