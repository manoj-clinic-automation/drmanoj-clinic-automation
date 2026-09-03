#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_corrections_s223.py -- prove the Corrections tile reaches the owner and nobody else."""
import io, os, sys
OLD_P, NEW_P, G = [os.path.abspath(a) for a in sys.argv[1:4]]
USERS = ["manoj", "bhawna", "darpan", "shavez", "alisha", "shivani", "amir", "nobody"]
ROLES = ["doctor", "manager", "staff"]
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
before, after = snap(OLD_P, G), snap(NEW_P, G)
changed = sorted(k for k in before if before[k] != after[k])
print("-- 1  who changes (%d combinations) ---------------------------------" % len(before))
for k in changed:
    print("     %-8s role=%-8s pc=%-5s  +%s  -%s" % (k[0], k[1], k[2],
          sorted(set(after[k]) - set(before[k])), sorted(set(before[k]) - set(after[k]))))
ck("every change is a doctor session", all(k[1] == "doctor" for k in changed))
ck("the only thing gained anywhere is Corrections",
   all(set(after[k]) - set(before[k]) == {"Corrections"} for k in changed))
ck("nothing is lost anywhere", all(not (set(before[k]) - set(after[k])) for k in changed))
ck("no staff or manager session sees it",
   not any("Corrections" in after[(u, r, pc)] for u in USERS for r in ("staff", "manager") for pc in (False, True)))
ck("the owner sees it on the phone", "Corrections" in after[("manoj", "doctor", False)])
print("\n-- 2  fail-safe: grants file gone ----------------------------------")
fb = snap(NEW_P, None)
ck("the owner still sees it with no grants file", "Corrections" in fb[("manoj", "doctor", False)])
ck("no staff session sees it with no grants file",
   not any("Corrections" in fb[(u, "staff", False)] for u in USERS))
print("\n-- 3  the owner's Money & Accounts section, after -------------------")
src = io.open(NEW_P, encoding="utf-8").read()
head = src[:src.index("# ---------------------------------------------------------------------------\n# AUTH HELPERS")]
io.open(os.path.join(os.path.dirname(NEW_P), "tile_grants.json"), "w", encoding="utf-8").write(io.open(G, encoding="utf-8").read())
ns = {"__name__": "p", "__file__": NEW_P}; exec(compile(head, "<p>", "exec"), ns)
for sec, tiles in ns["_visible_sections"]("doctor", False, "manoj"):
    if sec == "Money & Accounts":
        print("     [%s] %s" % (sec, ", ".join(t["name"] for t in tiles)))
print("\n%s  7 checks, %d failed" % ("RED" if F else "GREEN", len(F)))
sys.exit(1 if F else 0)
