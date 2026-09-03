#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_grants_s222.py -- prove that moving per-person tiles out of portal.py changes NOTHING.

The whole claim of this kit is that five imperative places in portal.py become one JSON file and
every person still sees exactly what they saw. That is not a claim you can read; it is a claim
you check by walking every combination. This walks EVERY user x EVERY role x PC on and off, with
the file and without it, and asserts the set of visible tiles is identical.

It also proves the three fail-safes (missing / malformed / shapeless file all fall back to the
code dicts), that ordering moved only for staff, and that the file can actually grant and mask.

    python3 -B selftest_grants_s222.py /path/to/patched/portal.py /path/to/tile_grants.json
"""
import io
import json
import os
import sys

PORTAL = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "portal.py")
GRANTS = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else "tile_grants.json")
USERS = ["manoj", "bhawna", "darpan", "shavez", "alisha", "shivani", "amir", "nobody"]
ROLES = ["doctor", "manager", "staff"]
F = []


def ck(l, c, d=""):
    print("  %s  %s%s" % ("PASS" if c else "FAIL", l, ("   [%s]" % d) if d else ""))
    if not c:
        F.append(l)


def main():
    src = io.open(PORTAL, encoding="utf-8").read()
    head = src[:src.index("# ---------------------------------------------------------------------------\n# AUTH HELPERS")]
    seed = io.open(GRANTS, encoding="utf-8").read()
    live = os.path.join(os.path.dirname(PORTAL), "tile_grants.json")

    def load(present, body=None):
        if present:
            io.open(live, "w", encoding="utf-8").write(body if body is not None else seed)
        elif os.path.exists(live):
            os.remove(live)
        ns = {"__name__": "p", "__file__": PORTAL}
        exec(compile(head, "<p>", "exec"), ns)
        return ns

    def names(ns, r, pc, u):
        return sorted(sum([[t["name"] for t in ts]
                           for g, ts in ns["_visible_sections"](r, pc, u)], []))

    print("-- 0  what is under test ------------------------------------------")
    ck("portal.py carries the S222 grants reader", "S222 TILE GRANTS" in src)
    ck("the code dicts are STILL there as the fallback", "USER_TILE_MASK = {" in src)

    print("\n-- 1  WITHOUT the file: the code dicts still rule -------------------")
    off = load(False)
    base = {(u, r, pc): names(off, r, pc, u)
            for u in USERS for r in ROLES for pc in (False, True)}
    order0 = {(u, r, pc): [g for g, _ in off["_visible_sections"](r, pc, u)]
              for u in USERS for r in ROLES for pc in (False, True)}
    ck("the portal renders with no grants file at all", any(base.values()))

    print("\n-- 2  WITH the seed: MEMBERSHIP identical for every user x role -----")
    on = load(True)
    diffs = [(u, r, pc) for u in USERS for r in ROLES for pc in (False, True)
             if base[(u, r, pc)] != names(on, r, pc, u)]
    ck("no tile appeared or disappeared for ANYONE (%d combinations)"
       % (len(USERS) * len(ROLES) * 2), not diffs, str(diffs[:3]))

    print("\n-- 3  ORDER: untouched for doctor/manager, reordered for staff ------")
    same, staff_order = [], None
    for u in USERS:
        for r in ROLES:
            for pc in (False, True):
                new = [g for g, _ in on["_visible_sections"](r, pc, u)]
                if r != "staff":
                    same.append(order0[(u, r, pc)] == new)
                elif len(new) > 1:
                    staff_order = new
    ck("doctor and manager see the same order as before", all(same))
    ck("Clinic (where Scan Purchase lives) is first for staff",
       bool(staff_order) and staff_order[0] == "Clinic", str(staff_order))
    ck("Staff (attendance, register) sits LAST for them",
       bool(staff_order) and staff_order[-1] == "Staff", str(staff_order))

    print("\n-- 4  THE FAIL-SAFES ------------------------------------------------")
    for label, body in (("malformed file", "{ this is not json"),
                        ("a file with no users map", '{"nope":1}')):
        ns = load(True, body)
        ck("%s -> exactly the code behaviour" % label,
           names(ns, "doctor", False, "bhawna") == base[("bhawna", "doctor", False)])
    ns = load(False)
    ck("deleted file -> exactly the code behaviour",
       names(ns, "doctor", False, "bhawna") == base[("bhawna", "doctor", False)])

    print("\n-- 5  AND IT ACTUALLY GRANTS AND MASKS FROM THE FILE ----------------")
    d = json.loads(seed)
    d["users"]["amir"] = {"extra": ["Asset Register"]}
    liv = load(True, json.dumps(d))
    ck("a doctor/manager tile granted in the FILE reaches Amir",
       "Asset Register" in names(liv, "staff", False, "amir"))
    ck("and no other staff login got it",
       "Asset Register" not in names(liv, "staff", False, "shivani"))
    d["users"]["shivani"] = {"mask": ["Attendance"]}
    liv = load(True, json.dumps(d))
    ck("a mask in the FILE hides a tile",
       "Attendance" not in names(liv, "staff", False, "shivani"))

    io.open(live, "w", encoding="utf-8").write(seed)
    print("\n%s -- %d failed" % ("GRANTS GREEN" if not F else "GRANTS RED", len(F)))
    for x in F:
        print("   FAILED:", x)
    return 1 if F else 0


if __name__ == "__main__":
    sys.exit(main())
