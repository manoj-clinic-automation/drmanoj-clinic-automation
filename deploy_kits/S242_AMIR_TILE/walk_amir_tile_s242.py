# -*- coding: utf-8 -*-
"""LIVE-SHAPE WALK -- the patched portal.py itself, with the v12 grants file beside it, asked what
each person is shown. Not a reading of the JSON: portal's own `_visible_sections` decides."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["TILE_GRANTS_FILE"] = os.path.join(HERE, "tile_grants.json")
os.environ.setdefault("PORTAL_PIN_SALT", "walk")
os.environ.setdefault("PORTAL_TOKEN_SEED", "walk")
sys.path.insert(0, HERE)
import portal  # noqa: E402  -- the import asserts every tile is grouped; that is check 0

fails = []
def check(label, got, want):
    ok = got == want
    print(("  PASS  " if ok else "  FAIL  ") + label + "   got=%r want=%r" % (got, want))
    if not ok:
        fails.append(label)

def tiles(user, role="staff", pc=False):
    out = []
    for _g, items in portal._visible_sections(role, pc, user):
        out += [t["name"] for t in items]
    return out

print("0 - portal.py imported: every tile is grouped (its own assert) and the module compiles")
print("    grants file in use: %s  version %s" % (os.path.basename(os.environ["TILE_GRANTS_FILE"]),
                                                  portal._tile_grants().get("version")))

print("\n1 - AMIR sees exactly one tile, and it is his own page")
a = tiles("amir")
check("amir's tiles", a, ["Amir ka kaam"])
url = [t["url"] for t in portal.TILES if t["name"] == "Amir ka kaam"]
check("where it goes", url, ["/finance/amir"])

print("\n2 - the five parked tiles are gone FOR AMIR")
for t in ("Forms & Downloads", "Scan Purchase", "Marg Purchases", "Order Medicines", "Stock Check"):
    check("amir cannot see %r" % t, t in a, False)

print("\n3 - PARKED, NOT REMOVED: every one still exists in portal.py with its roles intact")
for t, roles in (("Forms & Downloads", ["doctor", "manager", "staff"]),
                 ("Scan Purchase", ["staff", "manager"]),
                 ("Marg Purchases", ["doctor"]),
                 ("Order Medicines", ["doctor"]),
                 ("Stock Check", ["doctor"])):
    got = [x["roles"] for x in portal.TILES if x["name"] == t]
    check("%r still defined, roles unchanged" % t, got, [roles])

print("\n4 - nobody else moved")
check("shavez", tiles("shavez"), ["Call Tracker", "Forms & Downloads", "Asset Register",
                                  "Scan Purchase", "Vaapsi Desk", "Docterz Revenue",
                                  "Docterz daily collection"])
check("shivani", tiles("shivani"), ["Call Tracker", "Forms & Downloads", "Scan Purchase",
                                    "Vaapsi Desk", "Docterz Revenue",
                                    "Docterz daily collection"])
check("alisha", tiles("alisha"), tiles("shivani"))
check("darpan", tiles("darpan"), ["Forms & Downloads", "Scan Purchase", "Daily Sale",
                                  "Vaapsi Desk"])
check("a bare staff login is untouched", tiles("nobody"),
      ["Forms & Downloads", "Scan Purchase", "Attendance", "Staff Register"])

print("\n5 - the doctor keeps everything, including the new tile")
d = tiles("manoj", role="doctor")
check("doctor has the new tile", "Amir ka kaam" in d, True)
for t in ("Forms & Downloads", "Marg Purchases", "Order Medicines", "Stock Check",
          "Docterz daily collection", "Salary — approve & lock"):
    check("doctor still has %r" % t, t in d, True)

print("\n6 - FAIL CLOSED: with no grants file at all, Amir loses the tile and the doctor keeps it")
portal.TILE_GRANTS_FILE = os.path.join(HERE, "no_such_grants.json")
portal._GRANTS_CACHE["mtime"] = None
portal._GRANTS_CACHE["data"] = None
check("amir without grants", "Amir ka kaam" in tiles("amir"), False)
check("doctor without grants", "Amir ka kaam" in tiles("manoj", role="doctor"), True)

print("\n%s" % ("ALL CHECKS PASSED" if not fails else "FAILURES: %r" % fails))
sys.exit(1 if fails else 0)
