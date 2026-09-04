#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_staff_tile_s225.py -- proves patch_portal_staff_order_s225.py against a portal.py whose
bytes are the LIVE ones, rebuilt from the repository chain (S204 root copy + every portal patch
S218..S224, the S224 Docterz names last) = d2803804... (the pin read back from the box at the
S224 close), then this kit's patcher on top. Touches no live file; works in a scratch directory.

Run from inside the kit folder:   python3 -B selftest_staff_tile_s225.py
"""
import hashlib, io, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
KITS = os.path.dirname(HERE)
LIVE_PIN = "d28038047d81abd290d58ed15f9a1482"      # /root/portal/portal.py, read back 04-Sep 13:05
GRANTS_LIVE_PIN = "578702a5a10e1487e0f320c6f1b75755"  # tile_grants.json v7, read back 04-Sep 13:05
CHAIN = [
    ("S218_PORTAL_TILE/patch_portal_vaapsi_tile.py", None),
    ("S222_PORTAL_ENTRY/patch_portal_users_entry_s222.py", None),
    ("S222_SCANAPP_INAPP/patch_portal_scanapp_tiles_s222.py", None),
    ("S222_TILE_GRANTS/patch_portal_grants_s222.py", None),
    ("S223_LAUNCH_TILES/patch_portal_launch_tiles_s223.py", None),
    ("S223_CORRECTIONS_TILE/patch_portal_corrections_tile_s223.py", None),
    ("S223_CLINIC_DAY/patch_portal_dayrevenue_tile_s223.py", None),
    ("S223_REGISTER_CARD/patch_portal_register_tile_s223.py", None),
    ("S224_MARG_PURCHASES/patch_portal_purchase_tile_s224.py", "md5"),
    ("S224_DOCTERZ_TILE_NAMES/patch_portal_docterz_names_s224.py", "md5"),
]
PATCHER = os.path.join(HERE, "patch_portal_staff_order_s225.py")
GRANTS_V7 = os.path.join(KITS, "S224_DOCTERZ_TILE_NAMES", "tile_grants.json")
GRANTS_V8 = os.path.join(HERE, "tile_grants.json")
NEW = "Order Medicines"
FIVE = {"amir", "shavez", "darpan", "alisha", "shivani"}
USERS = ["manoj", "bhawna", "darpan", "shavez", "alisha", "shivani", "amir", "nobody"]
ROLES = ["doctor", "manager", "staff"]
F = []


def ck(label, cond, detail=""):
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label, ("   [%s]" % detail) if detail else ""))
    if not cond:
        F.append(label)


def md5(p):
    return hashlib.md5(io.open(p, "rb").read()).hexdigest()


def run(script, portal, arg=None):
    env = dict(os.environ, PORTAL_PATH=portal)
    cmd = [sys.executable, "-B", script] + ([arg] if arg else [])
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=os.path.dirname(portal))
    return r.returncode, (r.stdout + r.stderr)


def load_head(portal, grants):
    src = io.open(portal, encoding="utf-8").read()
    head = src[:src.index("# ---------------------------------------------------------------------------\n# AUTH HELPERS")]
    live = os.path.join(os.path.dirname(portal), "tile_grants.json")
    if grants:
        shutil.copy(grants, live)
    elif os.path.exists(live):
        os.remove(live)
    ns = {"__name__": "p", "__file__": portal}
    exec(compile(head, portal, "exec"), ns)
    return ns


def snap(ns):
    return {(u, r, pc): sorted(sum([[t["name"] for t in ts]
                                   for g, ts in ns["_visible_sections"](r, pc, u)], []))
            for u in USERS for r in ROLES for pc in (False, True)}


W = tempfile.mkdtemp(prefix="s225tile_")
live = os.path.join(W, "portal.py")
shutil.copy(os.path.join(KITS, "S204_VPS_LIVE", "root__portal__portal.py"), live)

print("-- 1  rebuild the live portal.py from the repository chain ------------")
for rel, arg in CHAIN:
    a = md5(live) if arg == "md5" else None
    rc, out = run(os.path.join(KITS, rel), live, a)
    ck("%-58s -> %s" % (rel.split("/")[0], md5(live)), rc == 0, out.strip()[-160:] if rc else "")
exact = md5(live) == LIVE_PIN
ck("the rebuilt file IS the live pin %s (read back from the box 04-Sep 13:05)" % LIVE_PIN, exact, md5(live))
ck("tile_grants.json v7 in the repo IS the live pin %s" % GRANTS_LIVE_PIN, md5(GRANTS_V7) == GRANTS_LIVE_PIN, md5(GRANTS_V7))
shutil.copy(live, os.path.join(W, "before.py"))

print("\n-- 2  the anchors, each exactly once, in the live bytes ---------------")
sys.path.insert(0, HERE)
import patch_portal_staff_order_s225 as P  # noqa: E402
src0 = io.open(live, encoding="utf-8").read()
for label, old, new in P.PAIRS:
    ck("anchor %r matches exactly once" % label, src0.count(old) == 1, str(src0.count(old)))
    ck("replacement for %r is not already present" % label, new not in src0)
ck("MARK absent before", P.MARK not in src0)

print("\n-- 3  refusals -----------------------------------------------------------")
rc, out = run(PATCHER, live, "0" * 32)
ck("wrong md5 REFUSES and changes nothing", rc != 0 and "REFUSING" in out and md5(live) == LIVE_PIN)
rc, out = run(PATCHER, live)
ck("no argument -> USAGE, nothing changed", rc != 0 and "USAGE" in out and md5(live) == LIVE_PIN)

print("\n-- 4  apply ----------------------------------------------------------------")
rc, out = run(PATCHER, live, md5(live))
ck("patcher exits 0 and prints NEW PIN", rc == 0 and "NEW PIN" in out, out.strip()[-160:] if rc else "")
new_pin = md5(live)
print("     NEW PIN (predicted%s)  %s" % ("" if exact else ", SIMULATED", new_pin))
rc2, out2 = run(PATCHER, live, new_pin)
ck("second run says ALREADY PATCHED and leaves the pin alone", rc2 == 0 and "ALREADY PATCHED" in out2 and md5(live) == new_pin)
baks = [f for f in os.listdir(W) if f.startswith("portal.py.bak_S225_ordertile_")]
ck("exactly one timestamped backup, equal to the live bytes", len(baks) == 1 and md5(os.path.join(W, baks[0])) == LIVE_PIN)
src1 = io.open(live, encoding="utf-8").read()
ck("LF only, no CRLF", "\r" not in src1)
ck("exactly 8 lines added (the tile block) and 1 line changed (the group row)",
   len(src1.splitlines()) == len(src0.splitlines()) + 8)

print("\n-- 5  the tile, word for word ----------------------------------------------")
ns = load_head(live, GRANTS_V8)
after = snap(ns)
tiles = {t["name"]: t for t in ns["TILES"]}
ck("_visible_sections present (module head executed)", "_visible_sections" in ns)
t = tiles.get(NEW)
ck("%s exists, url /finance/purchase/page/staff, roles ['doctor'], live" % NEW,
   bool(t) and t["url"] == "/finance/purchase/page/staff" and t["roles"] == ["doctor"] and t.get("live") is True)
ck("  desc = 'Item · stock · quantity — send to the stockist on WhatsApp'",
   bool(t) and t["desc"] == "Item · stock · quantity — send to the stockist on WhatsApp", t and t["desc"])
ck("  icon is the cart", bool(t) and t["icon"] == "\U0001F6D2")
ck("  sits in Money & Accounts", ns["_TILE_GROUP"].get(NEW) == "Money & Accounts")
names = [x["name"] for x in ns["TILES"]]
ck("  placed immediately after Marg Purchases", names.index(NEW) == names.index("Marg Purchases") + 1)
ns0 = load_head(os.path.join(W, "before.py"), GRANTS_V7)
before = snap(ns0)
tiles0 = {x["name"]: x for x in ns0["TILES"]}
ck("every OTHER tile (%d) is byte-identical: name, desc, url, roles, icon" % len(tiles0),
   all(tiles0[n] == tiles[n] for n in tiles0) and len(tiles) == len(tiles0) + 1)
ck("tile order otherwise unchanged", [n for n in names if n != NEW] == [x["name"] for x in ns0["TILES"]])

print("\n-- 6  tile_grants.json v8 --------------------------------------------------")
g7 = json.load(io.open(GRANTS_V7, encoding="utf-8"))
g8 = json.load(io.open(GRANTS_V8, encoding="utf-8"))
ck("v8 says version 8", g8["version"] == 8)
ck("same users, same defaults", set(g7["users"]) == set(g8["users"]) and g7["defaults"] == g8["defaults"])
ok = True
for u in g7["users"]:
    for k in ("mask", "extra"):
        a = sorted(g7["users"][u].get(k) or []); b = sorted(g8["users"][u].get(k) or [])
        want = sorted(a + [NEW]) if (k == "extra" and u in FIVE) else a
        ok = ok and b == want
ck("v8 = v7 + '%s' in the extra of exactly amir, shavez, darpan, alisha, shivani; nothing else moves" % NEW, ok)
ck("every name in v8 mask/extra is a real tile after the patch",
   all(x in tiles for u in g8["users"].values() for k in ("mask", "extra") for x in (u.get(k) or [])))
ck("the v8 note carries the S225 history and keeps the old", "S225 v8" in g8["_note"] and g8["_note"].startswith(g7["_note"]))

print("\n-- 7  who sees what: before (live + v7) vs after (patched + v8) ---------")
gain = {k for k in before if after[k] != before[k]}
ck("the only change over %d user/role/pc combinations is '%s' appearing" % (len(before), NEW),
   all(sorted(before[k] + [NEW]) == after[k] for k in gain) and all(after[k] == before[k] for k in before if k not in gain))
staff_see = {u for u in USERS if NEW in after[(u, "staff", False)]}
ck("as staff, exactly the five see it", staff_see == FIVE, str(sorted(staff_see)))
ck("as doctor, manoj sees it (by role)", NEW in after[("manoj", "doctor", False)])
ck("bhawna and 'nobody' do not", NEW not in after[("bhawna", "staff", False)] and NEW not in after[("nobody", "staff", False)])
ns_stale = load_head(live, GRANTS_V7)
stale = snap(ns_stale)
ck("with the OLD grants file (v7) beside the NEW portal.py, staff LOSE the tile and the doctor keeps it (fail closed, never locked out)",
   not {u for u in USERS if NEW in stale[(u, "staff", False)]} and NEW in stale[("manoj", "doctor", False)])
ns_none = load_head(live, None)
none = snap(ns_none)
ck("with NO grants file, same shape", not {u for u in USERS if NEW in none[(u, "staff", False)]} and NEW in none[("manoj", "doctor", False)])

with io.open(os.path.join(HERE, "PREDICTED_PINS_portal.txt"), "w", encoding="utf-8") as fh:
    fh.write("portal.py  before %s  after %s%s\ntile_grants.json v8  %s\n" % (LIVE_PIN, new_pin, "" if exact else "  (SIMULATED)", md5(GRANTS_V8)))
shutil.rmtree(W, ignore_errors=True)
print("\n%s  (%d FAIL)" % ("ALL PASS" if not F else "FAILED", len(F)))
for f in F:
    print("  FAILED: " + f)
sys.exit(1 if F else 0)
