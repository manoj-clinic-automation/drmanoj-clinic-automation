#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_docterz_names_s224.py -- proves patch_portal_docterz_names_s224.py against a portal.py
whose bytes are the LIVE ones, rebuilt here from the repository:

    deploy_kits/S204_VPS_LIVE/root__portal__portal.py          24ea2c0b...
      + S218_PORTAL_TILE, S222_PORTAL_ENTRY, S222_SCANAPP_INAPP, S222_TILE_GRANTS,
      + S223_LAUNCH_TILES, S223_CORRECTIONS_TILE, S223_CLINIC_DAY, S223_REGISTER_CARD,
      + S224_MARG_PURCHASES (portal leg)                        = 3530f637... (the live pin)

then this kit's patcher on top. Touches no live file; works in a scratch directory.

Run from inside the kit folder:   python3 -B selftest_docterz_names_s224.py
"""
import hashlib, io, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
KITS = os.path.dirname(HERE)
LIVE_PIN = "3530f637d620c225906f9c0113b1f0b0"
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
]
PATCHER = os.path.join(HERE, "patch_portal_docterz_names_s224.py")
GRANTS_V6 = os.path.join(KITS, "S224_MARG_PURCHASES", "tile_grants.json")
GRANTS_V7 = os.path.join(HERE, "tile_grants.json")
REN = {"Day Revenue": "Docterz Revenue", "Daily Register": "Docterz daily collection"}
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
    """exec the tile/grant half of portal.py (up to AUTH HELPERS) with the given grants file."""
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


W = tempfile.mkdtemp(prefix="s224dz_")
live = os.path.join(W, "portal.py")
shutil.copy(os.path.join(KITS, "S204_VPS_LIVE", "root__portal__portal.py"), live)

print("-- 1  rebuild the live portal.py from the repository chain ------------")
for rel, arg in CHAIN:
    a = md5(live) if arg == "md5" else None
    rc, out = run(os.path.join(KITS, rel), live, a)
    ck("%-58s -> %s" % (rel.split("/")[0], md5(live)), rc == 0 and "NEW PIN" in out or "16bfd590" in md5(live), out.strip()[-120:] if rc else "")
exact = md5(live) == LIVE_PIN
ck("the rebuilt file IS the live pin %s" % LIVE_PIN, exact, md5(live))
shutil.copy(live, os.path.join(W, "before.py"))

print("\n-- 2  the anchors, each exactly once, in the live bytes ---------------")
sys.path.insert(0, HERE)
import patch_portal_docterz_names_s224 as P  # noqa: E402
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
ck("patcher exits 0 and prints NEW PIN", rc == 0 and "NEW PIN" in out, out.strip().splitlines()[-1][:60] if rc else "")
new_pin = md5(live)
print("     NEW PIN (predicted%s)  %s" % ("" if exact else ", SIMULATED", new_pin))
rc2, out2 = run(PATCHER, live, new_pin)
ck("second run says ALREADY PATCHED and leaves the pin alone", rc2 == 0 and "ALREADY PATCHED" in out2 and md5(live) == new_pin)
baks = [f for f in os.listdir(W) if f.startswith("portal.py.bak_S224_dznames_")]
ck("exactly one timestamped backup, equal to the live bytes", len(baks) == 1 and md5(os.path.join(W, baks[0])) == LIVE_PIN)
src1 = io.open(live, encoding="utf-8").read()
ck("LF only, no CRLF", "\r" not in src1)
b0, b1 = src0.splitlines(), src1.splitlines()
changed = [(i + 1, x, y) for i, (x, y) in enumerate(zip(b0, b1)) if x != y]
ck("same line count; exactly SIX lines differ (2 names, 2 descs, 2 group rows)", len(b0) == len(b1) and len(changed) == 6, str(len(changed)))
for ln, x, y in changed:
    print("     L%-5d %s\n            -> %s" % (ln, x.strip(), y.strip()))

print("\n-- 5  the ruling, word for word ------------------------------------------")
ns = load_head(live, GRANTS_V7)
after = snap(ns)                       # snapshot NOW: the grants file is read lazily by mtime
tiles = {t["name"]: t for t in ns["TILES"]}
ck("_TILE_GROUP import-assert passed (module head executed)", "_visible_sections" in ns)
ck("'Day Revenue' is gone", "Day Revenue" not in tiles)
ck("'Daily Register' is gone", "Daily Register" not in tiles)
t = tiles.get("Docterz Revenue")
ck("Docterz Revenue exists, url /finance/clinic/day, roles ['doctor']", bool(t) and t["url"] == "/finance/clinic/day" and t["roles"] == ["doctor"])
ck("  desc = 'Clinic collection by day — from Docterz'", bool(t) and t["desc"] == "Clinic collection by day — from Docterz", t and t["desc"])
ck("  'takings' nowhere in it", bool(t) and "takings" not in t["desc"])
t = tiles.get("Docterz daily collection")
ck("Docterz daily collection exists, url /finance/clinic/register, roles ['doctor']", bool(t) and t["url"] == "/finance/clinic/register" and t["roles"] == ["doctor"])
ck("  desc = \"Reception's day totals — cash, UPI, card\"", bool(t) and t["desc"] == "Reception's day totals — cash, UPI, card", t and t["desc"])
ck("  'counter' nowhere in it", bool(t) and "counter" not in t["desc"].lower())
ck("both sit in Money & Accounts", all(ns["_TILE_GROUP"].get(n) == "Money & Accounts" for n in REN.values()))
ck("both keep their S223 icons", tiles["Docterz Revenue"]["icon"] == "\U0001F4C8" and tiles["Docterz daily collection"]["icon"] == "\U0001F4D2")
ck("no tile name starts with Day/Daily/Clinic AND points at a Docterz-fed page",
   not [n for n, t in tiles.items() if re.match(r"(Day|Daily|Clinic)\b", n) and t["url"] in ("/finance/clinic/day", "/finance/clinic/register")])
ns0 = load_head(os.path.join(W, "before.py"), GRANTS_V6)
before = snap(ns0)
tiles0 = {t["name"]: t for t in ns0["TILES"]}
untouched = [n for n in tiles0 if n not in REN]
ck("every OTHER tile (%d) is byte-identical: name, desc, url, roles, icon" % len(untouched),
   all(tiles0[n] == tiles[n] for n in untouched) and len(tiles) == len(tiles0))
ck("Daily Collection and Clinic (manual clinic-entry, S182) are NOT touched",
   tiles["Daily Collection"] == tiles0["Daily Collection"] and tiles["Clinic"] == tiles0["Clinic"])
ck("tile order unchanged", [REN.get(t["name"], t["name"]) for t in ns0["TILES"]] == [t["name"] for t in ns["TILES"]])

print("\n-- 6  tile_grants.json v7 --------------------------------------------------")
g6 = json.load(io.open(GRANTS_V6, encoding="utf-8"))
g7 = json.load(io.open(GRANTS_V7, encoding="utf-8"))
ck("v6 is the live c4d01ade... ; v7 says version 7", md5(GRANTS_V6) == "c4d01adeba0d5bbc570db992064b2ff5" and g7["version"] == 7)
same_users = set(g6["users"]) == set(g7["users"])
ren_ok = all(sorted(REN.get(x, x) for x in (g6["users"][u].get(k) or [])) == sorted(g7["users"][u].get(k) or [])
             for u in g6["users"] for k in ("mask", "extra"))
ck("v7 = v6 with the two names renamed and nothing else (users, masks, extras, defaults)",
   same_users and ren_ok and g6["defaults"] == g7["defaults"])
ck("no old name survives in any v7 mask/extra (the _note keeps the history)",
   not [x for u in g7["users"].values() for k in ("mask", "extra") for x in (u.get(k) or []) if x in REN])
ck("every name in v7 mask/extra is a real tile after the patch",
   all(x in tiles for u in g7["users"].values() for k in ("mask", "extra") for x in (u.get(k) or [])))

print("\n-- 7  who sees what: before (live + v6) vs after (patched + v7) ---------")
expect = {k: sorted(REN.get(n, n) for n in v) for k, v in before.items()}
diff = [k for k in before if expect[k] != after[k]]
ck("over %d user/role/pc combinations nobody gains or loses a tile -- only the two names change" % len(before), not diff, str(diff[:3]))
five = {u for u in USERS if "Docterz Revenue" in after[(u, "staff", False)]}
ck("the five the owner named still see both", five == {"manoj", "bhawna", "shavez", "shivani", "alisha"}
   and all("Docterz daily collection" in after[(u, "staff", False)] for u in five), str(sorted(five)))
ns_stale = load_head(live, GRANTS_V6)
stale = snap(ns_stale)
lost = sorted(u for u in USERS if u != "manoj" and "Docterz Revenue" not in stale[(u, "staff", False)] and u in five)
ck("with a STALE v6 the four staff logins would lose both tiles (why v7 ships with the patch)", lost == ["alisha", "bhawna", "shavez", "shivani"], str(lost))
ns_none = load_head(live, None)
nog = snap(ns_none)
ck("grants file gone: no staff sees them (fail closed); the owner keeps them as doctor",
   not any("Docterz Revenue" in nog[(u, "staff", False)] for u in USERS) and "Docterz Revenue" in nog[("manoj", "doctor", False)])
ns = load_head(live, GRANTS_V7)
for who, role in (("manoj", "doctor"), ("shavez", "staff")):
    for sec, ts in ns["_visible_sections"](role, False, who):
        if sec == "Money & Accounts":
            print("     %-7s %-7s [%s] %s" % (who, role, sec, ", ".join(t["name"] for t in ts)))

print("\n-- 8  hygiene ----------------------------------------------------------------")
for p in (PATCHER, GRANTS_V7, os.path.abspath(__file__)):
    s = io.open(p, encoding="utf-8").read()
    ck("no 10-digit run in %s" % os.path.basename(p), not re.search(r"\d{10}", s))
    ck("LF only in %s" % os.path.basename(p), "\r" not in s)
ck("no 10-digit run introduced into portal.py by the patch", not any(re.search(r"\d{10}", y) for _, _, y in changed))
rc = subprocess.run([sys.executable, "-m", "py_compile", live], capture_output=True).returncode
ck("patched portal.py py_compiles", rc == 0)

shutil.rmtree(W, ignore_errors=True)
print("\n%s  %d failed" % ("RED" if F else "GREEN", len(F)))
if not F:
    print("PREDICTED PIN  /root/portal/portal.py  %s -> %s%s" % (LIVE_PIN, new_pin, "" if exact else "  (SIMULATED, not exact)"))
    print("PREDICTED PIN  /root/portal/tile_grants.json  %s -> %s (v7)" % (md5(GRANTS_V6), md5(GRANTS_V7)))
sys.exit(1 if F else 0)
