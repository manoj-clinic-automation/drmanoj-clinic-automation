#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_launch_s223.py -- what the launch changes, for every person, measured not asserted.

Runs the REAL _visible_sections() from portal.py, before (live d15acef3 + the S222 grants) and
after (the S223 patch + the S223 grants), over every user x role x PC.
"""
import io, os, sys, json
OLD_P, OLD_G, NEW_P, NEW_G = [os.path.abspath(a) for a in sys.argv[1:5]]
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

before = snap(OLD_P, OLD_G)
after  = snap(NEW_P, NEW_G)
print("-- 1  what each person's STAFF view becomes -------------------------")
for u in USERS:
    b, a = before[(u, "staff", False)], after[(u, "staff", False)]
    print("   %-8s +%s  -%s" % (u, sorted(set(a) - set(b)), sorted(set(b) - set(a))))
print("\n-- 2  the owner's own view (doctor) ---------------------------------")
for u in ("manoj", "bhawna"):
    b, a = before[(u, "doctor", True)], after[(u, "doctor", True)]
    print("   %-8s +%s  -%s" % (u, sorted(set(a) - set(b)), sorted(set(b) - set(a))))

print("\n-- 3  the rulings, checked one by one -------------------------------")
S = lambda u: set(after[(u, "staff", False)])
D = lambda u: set(after[(u, "doctor", True)])
ck("Daily Sale: darpan yes", "Daily Sale" in S("darpan"))
ck("Daily Sale: manoj and bhawna yes", "Daily Sale" in D("manoj") and "Daily Sale" in D("bhawna"))
ck("Daily Sale: NOBODY else -- alisha/shavez/shivani/amir/new all lose it",
   not any("Daily Sale" in S(u) for u in ("alisha", "shavez", "shivani", "amir", "nobody")))
ck("Stock Check: alisha, shavez, shivani, darpan, amir",
   all("Stock Check" in S(u) for u in ("alisha", "shavez", "shivani", "darpan", "amir")))
ck("Stock Check: manoj and bhawna", "Stock Check" in D("manoj") and "Stock Check" in D("bhawna"))
ck("Stock Check: not a new staff login by default", "Stock Check" not in S("nobody"))
ck("Vaapsi Desk: only the four on the desk list (+ the doctors)",
   all("Vaapsi Desk" in S(u) for u in ("darpan", "shavez", "alisha", "shivani"))
   and not any("Vaapsi Desk" in S(u) for u in ("amir", "nobody")))
ck("Vaapsi Desk: dr bhawna yes", "Vaapsi Desk" in D("bhawna"))
ck("Forms & Downloads: every staff login", all("Forms & Downloads" in S(u) for u in USERS))
ck("Staff Register + Attendance: every staff login",
   all({"Staff Register", "Attendance"} <= S(u) for u in USERS))
ck("Scan Purchase: untouched, every staff login", all("Scan Purchase" in S(u) for u in USERS))

print("\n-- 4  FAIL-SAFE: grants file gone ----------------------------------")
fb = snap(NEW_P, None)
ck("staff lose the three money screens (fail CLOSED)",
   not ({"Daily Sale", "Vaapsi Desk", "Stock Check"} & set(fb[("darpan", "staff", False)])))
ck("the doctor keeps all three (never locked out)",
   {"Daily Sale", "Vaapsi Desk", "Stock Check"} <= set(fb[("manoj", "doctor", True)]))
ck("staff keep Forms, Attendance, Staff Register, Scan Purchase",
   {"Forms & Downloads", "Attendance", "Staff Register", "Scan Purchase"} <= set(fb[("darpan", "staff", False)]))

print("\n-- 5  the launch view, in full -------------------------------------")
for u in ("darpan", "alisha", "amir", "nobody"):
    print("   %-8s staff: %s" % (u, after[(u, "staff", False)]))
print("\n%s  %d checks, %d failed" % ("RED" if F else "GREEN", 12, len(F)))
sys.exit(1 if F else 0)
