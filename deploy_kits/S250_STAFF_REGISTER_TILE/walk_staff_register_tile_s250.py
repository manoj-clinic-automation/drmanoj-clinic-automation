#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walk_staff_register_tile_s250.py -- LIVE-SHAPE walk of kit S250_STAFF_REGISTER_TILE.

Not a reading of the JSON. portal.py is imported (its own "every tile is grouped" assert is the
first check) and portal's own _visible_sections is asked what each person is SHOWN -- once with
tile_grants v14 (the live file, the BASELINE) and once with v15 (this kit) -- so "unchanged" is a
measured comparison, not a claim.

    PORTAL_PY=<portal.py> python3 -B walk_staff_register_tile_s250.py     (offline, on a copy)
    /root/wa/venv/bin/python3 -B walk_staff_register_tile_s250.py         (on the box; writes nothing)

Exit 0 when every check passes, 1 otherwise.
"""
import hashlib, importlib.util, json, os, shutil, sys, tempfile

KIT = os.path.dirname(os.path.abspath(__file__))
PORTAL_PY = os.environ.get("PORTAL_PY", "/root/portal/portal.py")
GRANTS_V14 = os.environ.get("GRANTS_V14", os.path.join(os.path.dirname(KIT), "S243_DARPAN_TILE", "tile_grants.json"))
GRANTS_V15 = os.path.join(KIT, "tile_grants.json")
PORTAL_PIN = "06f1b378608fbc97c54bc1f546d7985c"
G14_PIN = "0efad736e71de7199e7c596a5b3d0c2e"
G15_PIN = "932f7bd05f4bf19b1f53deb9a2f35d22"
T = "Staff Register"
GAINS = ("shavez", "shivani", "alisha")
OTHERS = ("darpan", "amir", "awdhesh", "sukhveer", "surendra", "parvesh", "sandeep", "vikky")

PASSED, FAILED = [], []
def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label, ("   [%s]" % (detail,)) if (detail and not cond) else ""))

def md5f(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()

def load_portal(modname, folder):
    os.environ["TILE_GRANTS_FILE"] = os.path.join(folder, "tile_grants.json")
    os.environ.setdefault("PORTAL_PIN_SALT", "walk")
    os.environ.setdefault("PORTAL_TOKEN_SEED", "walk")
    spec = importlib.util.spec_from_file_location(modname, os.path.join(folder, "portal.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(mod)
    return mod

def sections(mod, user, role="staff", pc=False):
    return [(g, [t["name"] for t in items]) for g, items in mod._visible_sections(role, pc, user)]

def names(mod, user, role="staff", pc=False):
    return [n for _g, items in sections(mod, user, role, pc) for n in items]

print("S250_STAFF_REGISTER_TILE -- live-shape walk")
print("portal.py : %s" % PORTAL_PY)

for p, pin, what in ((PORTAL_PY, PORTAL_PIN, "portal.py"), (GRANTS_V14, G14_PIN, "grants v14"), (GRANTS_V15, G15_PIN, "grants v15")):
    if not os.path.exists(p):
        sys.exit("REFUSING: %s not found (%s)" % (p, what))
    ck("%s is the declared pin %s" % (what, pin[:8]), md5f(p) == pin, md5f(p))

tmp = tempfile.mkdtemp(prefix="s250walk_")
A, B, C = (os.path.join(tmp, d) for d in ("v14", "v15", "nogrants"))
for d, g in ((A, GRANTS_V14), (B, GRANTS_V15), (C, None)):
    os.makedirs(d)
    shutil.copy2(PORTAL_PY, os.path.join(d, "portal.py"))
    if g:
        shutil.copy2(g, os.path.join(d, "tile_grants.json"))

m14 = load_portal("portal_v14", A)          # its own import-time assert: every tile is grouped
m15 = load_portal("portal_v15", B)
m00 = load_portal("portal_nogrants", C)
ck("portal.py imports under all three grant states", True)

hits = [t for t in m15.TILES if t["name"] == T]
ck("exactly one '%s' tile in portal.py" % T, len(hits) == 1, str(len(hits)))
if hits:
    t = hits[0]
    ck("its url is /register/review", t.get("url") == "/register/review", str(t.get("url")))
    ck("its roles are doctor/manager/staff (so lifting the mask is the whole change)",
       set(t.get("roles", [])) == {"doctor", "manager", "staff"}, str(t.get("roles")))
ck("'%s' is grouped under Staff" % T, m15._TILE_GROUP.get(T) == "Staff", str(m15._TILE_GROUP.get(T)))
ck("no name-grant was used: '%s' is in nobody's extra in v15" % T,
   not any(T in u.get("extra", []) for u in json.load(open(GRANTS_V15, encoding="utf-8"))["users"].values()))

print("\nTHE THREE WHO GAIN IT")
for u in GAINS:
    for role in (("staff", "manager") if u == "shavez" else ("staff",)):
        before, after = names(m14, u, role), names(m15, u, role)
        gained = [n for n in after if n not in before]
        lost = [n for n in before if n not in after]
        ck("%s (%s): gains exactly ['%s']" % (u, role, T), gained == [T], str(gained))
        ck("%s (%s): loses nothing" % (u, role), lost == [], str(lost))
        ck("%s (%s): Attendance still NOT shown" % (u, role), "Attendance" not in after)
        ck("%s (%s): it lands in the Staff section" % (u, role),
           any(g == "Staff" and T in items for g, items in sections(m15, u, role)))
        ck("%s (%s): every other tile keeps its place" % (u, role),
           [n for n in after if n != T] == before, "%s -> %s" % (before, after))

print("\nEVERYBODY ELSE -- tile for tile, section for section")
for u in OTHERS:
    ck("%s: unchanged" % u, sections(m14, u) == sections(m15, u))
    ck("%s: still does NOT see '%s'" % (u, T), T not in names(m15, u))
for u in ("manoj", "bhawna"):
    ck("%s (doctor): unchanged" % u, sections(m14, u, "doctor") == sections(m15, u, "doctor"))
    ck("%s (doctor): still sees '%s'" % (u, T), T in names(m15, u, "doctor"))
ck("a staff login with no grants row: unchanged",
   sections(m14, "nobody_x") == sections(m15, "nobody_x"))
ck("the owner's PC-tools view is unchanged",
   sections(m14, "manoj", "doctor", True) == sections(m15, "manoj", "doctor", True))

print("\nFAIL CLOSED -- no grants file at all")
for u in GAINS:
    ck("%s: with no grants file '%s' is still shown -- it sits on the staff role, so this kit can never take it away" % (u, T),
       T in names(m00, u))
    ck("%s: with no grants file the screen is the code-only screen (no extra, no mask)" % u,
       sections(m00, u) == sections(m00, u))
ck("the doctor keeps '%s' with no grants file" % T, T in names(m00, "manoj", "doctor"))
ck("the money tiles granted by name are the ones that fall away with no grants file (fail closed, unchanged)",
   all(n not in names(m00, "shavez") for n in ("Docterz Revenue", "Vaapsi Desk", "Call Tracker")))

print("\nTHE DIFF v14 -> v15, measured")
a = json.load(open(GRANTS_V14, encoding="utf-8"))
b = json.load(open(GRANTS_V15, encoding="utf-8"))
ck("version 14 -> 15", (a["version"], b["version"]) == (14, 15))
ck("the v14 note is carried whole, only appended to", b["_note"].startswith(a["_note"]))
ck("same set of logins", set(a["users"]) == set(b["users"]))
changed = [u for u in a["users"] if a["users"][u] != b["users"][u]]
ck("exactly three logins change", sorted(changed) == sorted(GAINS), str(sorted(changed)))
for u in GAINS:
    ck("%s: only the mask changes, and only by removing '%s'" % (u, T),
       a["users"][u].get("extra") == b["users"][u].get("extra")
       and [x for x in a["users"][u]["mask"] if x != T] == b["users"][u]["mask"]
       and b["users"][u]["mask"] == ["Attendance"], str(b["users"][u]))
ck("section order block untouched", a["defaults"] == b["defaults"])

print("\n%d passed, %d failed" % (len(PASSED), len(FAILED)))
if FAILED:
    for f in FAILED:
        print("  FAILED: %s" % f)
sys.exit(1 if FAILED else 0)
