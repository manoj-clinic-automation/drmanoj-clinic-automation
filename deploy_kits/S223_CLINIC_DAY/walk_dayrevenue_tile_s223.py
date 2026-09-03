#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_dayrevenue_tile_s223.py -- who gains the Day Revenue tile, measured over every combination."""
import io, os, sys
OLD_P, OLD_G, NEW_P, NEW_G = [os.path.abspath(a) for a in sys.argv[1:5]]
USERS = ["manoj", "bhawna", "darpan", "shavez", "alisha", "shivani", "amir", "nobody"]
ROLES = ["doctor", "manager", "staff"]
WANT = {"manoj", "bhawna", "shavez", "shivani", "alisha"}
F = []
def ck(l, c, d=""):
    print("  %s  %s%s" % ("PASS" if c else "FAIL", l, ("   [%s]" % d) if d else ""))
    if not c: F.append(l)
def snap(portal, grants):
    src = io.open(portal, encoding="utf-8").read()
    head = src[:src.index("# ---------------------------------------------------------------------------\n# AUTH HELPERS")]
    live = os.path.join(os.path.dirname(portal), "tile_grants.json")
    if grants: io.open(live, "w", encoding="utf-8").write(io.open(grants, encoding="utf-8").read())
    elif os.path.exists(live): os.remove(live)
    ns = {"__name__": "p", "__file__": portal}
    exec(compile(head, "<p>", "exec"), ns)
    return {(u, r, pc): sorted(sum([[t["name"] for t in ts]
            for g, ts in ns["_visible_sections"](r, pc, u)], []))
            for u in USERS for r in ROLES for pc in (False, True)}
before, after = snap(OLD_P, OLD_G), snap(NEW_P, NEW_G)
changed = sorted(k for k in before if before[k] != after[k])
print("-- 1  every change, over %d combinations ----------------------------" % len(before))
for k in changed:
    print("     %-8s role=%-8s pc=%-5s  +%s  -%s" % (k[0], k[1], k[2],
          sorted(set(after[k]) - set(before[k])), sorted(set(before[k]) - set(after[k]))))
ck("the only thing gained anywhere is Day Revenue",
   all(set(after[k]) - set(before[k]) == {"Day Revenue"} for k in changed))
ck("nothing is lost anywhere", all(not (set(before[k]) - set(after[k])) for k in changed))
print("\n-- 2  the owner's list, exactly -------------------------------------")
got_staff = {u for u in USERS if "Day Revenue" in after[(u, "staff", False)]}
# A by-name grant applies whatever role the login carries, so all five named people show the
# tile in a staff session -- that is the grant working, not a leak. The assertion is the SET.
ck("the tile reaches exactly the five he named, and nobody else",
   got_staff == WANT, "got %s, wanted %s" % (sorted(got_staff), sorted(WANT)))
ck("the owner and Dr Bhawna have it as doctors",
   all("Day Revenue" in after[(u, "doctor", False)] for u in ("manoj", "bhawna")))
ck("darpan does NOT have it (he was not on the list)",
   "Day Revenue" not in after[("darpan", "staff", False)])
ck("amir does NOT have it", "Day Revenue" not in after[("amir", "staff", False)])
ck("a brand-new staff login does NOT have it",
   "Day Revenue" not in after[("nobody", "staff", False)])
print("\n-- 3  fail-safe: grants file gone -----------------------------------")
fb = snap(NEW_P, None)
ck("no staff login sees it without the grants file (fail CLOSED)",
   not any("Day Revenue" in fb[(u, "staff", False)] for u in USERS))
ck("the owner still sees it without the grants file (never locked out)",
   "Day Revenue" in fb[("manoj", "doctor", False)])
print("\n-- 4  where it lands ------------------------------------------------")
src = io.open(NEW_P, encoding="utf-8").read()
head = src[:src.index("# ---------------------------------------------------------------------------\n# AUTH HELPERS")]
io.open(os.path.join(os.path.dirname(NEW_P), "tile_grants.json"), "w", encoding="utf-8").write(
    io.open(NEW_G, encoding="utf-8").read())
ns = {"__name__": "p", "__file__": NEW_P}; exec(compile(head, "<p>", "exec"), ns)
for who, role in (("manoj", "doctor"), ("shavez", "staff")):
    for sec, tiles in ns["_visible_sections"](role, False, who):
        if sec == "Money & Accounts":
            print("     %-7s %-7s [%s] %s" % (who, role, sec, ", ".join(t["name"] for t in tiles)))
print("\n%s  8 checks, %d failed" % ("RED" if F else "GREEN", len(F)))
sys.exit(1 if F else 0)
