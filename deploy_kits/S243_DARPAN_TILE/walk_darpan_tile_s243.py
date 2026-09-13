#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walk_darpan_tile_s243.py -- LIVE-SHAPE walk of kit S243_DARPAN_TILE.

Not a reading of the JSON.  portal.py itself is patched IN MEMORY (the kit's own patcher, on a copy;
the live file is never written), imported (its own "every tile is grouped" assert is the first
check), and portal's own _visible_sections is asked what each person is shown -- with tile_grants
v14 beside it, and again with v13 + the unpatched file as the BASELINE, so "unchanged" is a
comparison, not a claim.

    PORTAL_PY=<portal.py> python3 -B walk_darpan_tile_s243.py          (offline, on a copy)
    /root/wa/venv/bin/python3 -B walk_darpan_tile_s243.py             (on the box: reads /root/portal/portal.py, writes nothing)

Exit 0 when every check passes, 1 otherwise.
"""
import hashlib
import importlib.util
import io
import json
import os
import py_compile
import shutil
import sys
import tempfile

KIT = os.path.dirname(os.path.abspath(__file__))
PORTAL_PY = os.environ.get("PORTAL_PY", "/root/portal/portal.py")
GRANTS_V13 = os.environ.get("GRANTS_V13", os.path.join(os.path.dirname(KIT), "S243_REPORTS_TILE", "tile_grants.json"))
FROM_PIN = "4bb6bde0e2e07033ac0e0f5d7a7daaf6"
TO_PIN = "06f1b378608fbc97c54bc1f546d7985c"
G13_PIN = "c9ee95c39bb805086b79d95327b2b626"
G14_PIN = "0efad736e71de7199e7c596a5b3d0c2e"
NEW = "Kal ka hisaab"
NEW_URL = "/finance/darpan/kal"

sys.path.insert(0, KIT)
import patch_portal_darpan_tile_s243 as PPATCH                          # noqa: E402

PASSED, FAILED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label, ("   [%s]" % (detail,)) if (detail and not cond) else ""))


def md5b(b):
    return hashlib.md5(b).hexdigest()


def load_portal(modname, folder):
    """Import <folder>/portal.py under a private module name, grants file beside it."""
    os.environ["TILE_GRANTS_FILE"] = os.path.join(folder, "tile_grants.json")
    os.environ.setdefault("PORTAL_PIN_SALT", "walk")
    os.environ.setdefault("PORTAL_TOKEN_SEED", "walk")
    spec = importlib.util.spec_from_file_location(modname, os.path.join(folder, "portal.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(mod)
    return mod


def tiles(mod, user, role="staff", pc=False):
    return [t["name"] for _g, items in mod._visible_sections(role, pc, user) for t in items]


def sections(mod, user, role="staff", pc=False):
    return [(g, [t["name"] for t in items]) for g, items in mod._visible_sections(role, pc, user)]


def tile(mod, name):
    hits = [t for t in mod.TILES if t["name"] == name]
    return hits[0] if len(hits) == 1 else None


if not os.path.exists(PORTAL_PY):
    sys.exit("REFUSING: %s not found (set PORTAL_PY)" % PORTAL_PY)
if not os.path.exists(GRANTS_V13):
    sys.exit("REFUSING: v13 grants not found at %s (set GRANTS_V13)" % GRANTS_V13)

TMP = tempfile.mkdtemp(prefix="walk_darpan_tile_")
BASE = os.path.join(TMP, "base")
PATCHED = os.path.join(TMP, "patched")
os.makedirs(BASE)
os.makedirs(PATCHED)

print("WALK S243_DARPAN_TILE  portal.py=%s" % PORTAL_PY)

# ---- 0 the file, the patch, the pins ------------------------------------------------
raw = io.open(PORTAL_PY, "rb").read()
src = raw.decode("utf-8")
live_pin = md5b(raw)
print("  live portal.py %s" % live_pin)
ck("the live portal.py is the pin this kit was built on (%s)" % FROM_PIN[:8], live_pin == FROM_PIN, live_pin)
new, st = PPATCH.patch_text(src)
ck("the patcher patches it (%s)" % st, st == "patched", st)
new_bytes = new.encode("utf-8")
print("  patched  %s" % md5b(new_bytes))
ck("the patched bytes are the predicted to-pin %s" % TO_PIN[:8], md5b(new_bytes) == TO_PIN, md5b(new_bytes))
ck("second pass is a no-op ('already')", PPATCH.patch_text(new)[1] == "already")
def _subsequence(short, long_):
    it = iter(long_)
    return all(any(x == y for y in it) for x in short)


ck("only additions: every original line is still present, in order", _subsequence(src.splitlines(), new.splitlines()))
ck("exactly 11 lines added (10 for the tile, 1 for the group row)",
   len(new.splitlines()) - len(src.splitlines()) == 11, len(new.splitlines()) - len(src.splitlines()))
ck("LF only", b"\r" not in new_bytes)

io.open(os.path.join(BASE, "portal.py"), "wb").write(raw)
io.open(os.path.join(PATCHED, "portal.py"), "wb").write(new_bytes)
g13 = io.open(GRANTS_V13, "rb").read()
g14 = io.open(os.path.join(KIT, "tile_grants.json"), "rb").read()
ck("v13 grants beside the walk are %s" % G13_PIN[:8], md5b(g13) == G13_PIN, md5b(g13))
ck("the kit's tile_grants.json is v14 %s" % G14_PIN[:8], md5b(g14) == G14_PIN, md5b(g14))
io.open(os.path.join(BASE, "tile_grants.json"), "wb").write(g13)
io.open(os.path.join(PATCHED, "tile_grants.json"), "wb").write(g14)
try:
    py_compile.compile(os.path.join(PATCHED, "portal.py"), cfile=os.path.join(TMP, "p.pyc"), doraise=True)
    ck("py_compile of the patched copy", True)
except Exception as ex:                                                  # noqa: BLE001
    ck("py_compile of the patched copy", False, ex)

# ---- 1 the grants file, v13 -> v14: only darpan.extra, the version and the note --------
d13, d14 = json.loads(g13.decode("utf-8")), json.loads(g14.decode("utf-8"))
ck("v14: version field 13 -> 14", d13["version"] == 13 and d14["version"] == 14)
ck("v14: the note grew by one S243 v14 paragraph and lost nothing",
   d14["_note"].startswith(d13["_note"]) and "S243 v14" in d14["_note"] and "S243 v14" not in d13["_note"])
ck("v14: darpan.extra = [Kal ka hisaab, Daily Sale, Vaapsi Desk]",
   d14["users"]["darpan"]["extra"] == [NEW, "Daily Sale", "Vaapsi Desk"], d14["users"]["darpan"]["extra"])
ck("v14: darpan.mask unchanged", d14["users"]["darpan"].get("mask") == d13["users"]["darpan"].get("mask"))
others_same = all(d13["users"][u] == d14["users"][u] for u in d13["users"] if u != "darpan") and set(d13["users"]) == set(d14["users"])
ck("v14: every other login's grants are byte-equal to v13 (%d logins)" % (len(d13["users"]) - 1), others_same)
ck("v14: defaults (section order) unchanged", d13["defaults"] == d14["defaults"])
ck("'Corrections' is granted by name to NOBODY in v13 and in v14 (the CA ruling: nothing to withdraw)",
   all("Corrections" not in (u.get("extra") or []) for u in d13["users"].values())
   and all("Corrections" not in (u.get("extra") or []) for u in d14["users"].values()))

# ---- 2 import both: the portal's own grouping assert is the gate --------------------
try:
    base = load_portal("portal_base_s243", BASE)
    ck("BASELINE portal.py (live bytes) imports with v13", base._tile_grants().get("version") == 13)
except Exception as ex:                                                  # noqa: BLE001
    ck("BASELINE portal.py imports", False, ex)
    base = None
try:
    pat = load_portal("portal_patched_s243", PATCHED)
    ck("PATCHED portal.py imports: every tile is grouped (its own assert)", True)
    ck("grants file in use is v14", pat._tile_grants().get("version") == 14)
except Exception as ex:                                                  # noqa: BLE001
    ck("PATCHED portal.py imports", False, ex)
    pat = None

if base is not None and pat is not None:
    # ---- 3 the tile ------------------------------------------------------------------
    t = tile(pat, NEW)
    ck("the tile exists exactly once", t is not None)
    ck("it opens %s" % NEW_URL, t is not None and t["url"] == NEW_URL and t.get("live") is True)
    ck("it carries roles ['doctor'] only (fail closed) and sits in Money & Accounts",
       t is not None and t["roles"] == ["doctor"] and t["group"] == "Money & Accounts")
    ck("it is NOT in the baseline", tile(base, NEW) is None)
    names_p = [x["name"] for x in pat.TILES]
    names_b = [x["name"] for x in base.TILES]
    ck("it sits immediately before Daily Sale", names_p.index(NEW) + 1 == names_p.index("Daily Sale"))
    ck("every other tile is in the same order as before", [n for n in names_p if n != NEW] == names_b)
    ck("every other tile is byte-for-byte what it was (icon, desc, url, roles, group, flags)",
       all(tile(pat, n) == tile(base, n) for n in names_b))
    ck("Daily Sale is untouched: /finance/daily, roles ['doctor'], its to-do counter flag",
       tile(pat, "Daily Sale") == tile(base, "Daily Sale") and tile(pat, "Daily Sale")["url"] == "/finance/daily"
       and tile(pat, "Daily Sale")["roles"] == ["doctor"] and tile(pat, "Daily Sale").get("daily_sale_counts") is True)
    ck("Corrections is untouched: still defined, /finance/darpan/corrections, roles ['doctor']",
       tile(pat, "Corrections") == tile(base, "Corrections") and tile(pat, "Corrections")["url"] == "/finance/darpan/corrections"
       and tile(pat, "Corrections")["roles"] == ["doctor"])
    ck("GROUP_ORDER unchanged", pat.GROUP_ORDER == base.GROUP_ORDER)

    # ---- 4 who is shown what -- portal's own _visible_sections ------------------------
    dp = tiles(pat, "darpan")
    ck("darpan IS shown '%s'" % NEW, NEW in dp, dp)
    ck("darpan is NOT shown 'Corrections' (after)", "Corrections" not in dp)
    ck("darpan was NOT shown 'Corrections' before either (nothing to withdraw)", "Corrections" not in tiles(base, "darpan"))
    ck("darpan's tiles are exactly the old ones plus the new one", [n for n in dp if n != NEW] == tiles(base, "darpan"), (dp, tiles(base, "darpan")))
    ck("darpan's Money & Accounts reads: Kal ka hisaab, Daily Sale, Vaapsi Desk",
       dict(sections(pat, "darpan")).get("Money & Accounts") == [NEW, "Daily Sale", "Vaapsi Desk"], sections(pat, "darpan"))
    ck("darpan's section order is unchanged (Clinic, then Money & Accounts)",
       [g for g, _ in sections(pat, "darpan")] == [g for g, _ in sections(base, "darpan")] == ["Clinic", "Money & Accounts"])

    mj = tiles(pat, "manoj", role="doctor")
    ck("manoj (doctor) is shown '%s' by role" % NEW, NEW in mj)
    ck("manoj still sees Corrections, Daily Sale, Aaj ki reports, Amir ka kaam, Manage Users",
       all(n in mj for n in ("Corrections", "Daily Sale", "Aaj ki reports", "Amir ka kaam", "Manage Users")))
    ck("manoj sees everything he saw before, plus the one new tile, in the same order",
       [n for n in mj if n != NEW] == tiles(base, "manoj", role="doctor"))
    ck("manoj (doctor, on the clinic PC) likewise", [n for n in tiles(pat, "manoj", "doctor", True) if n != NEW] == tiles(base, "manoj", "doctor", True))

    for user, role in (("shavez", "manager"), ("amir", "staff"), ("alisha", "staff"), ("shivani", "staff"),
                       ("bhawna", "doctor"), ("nobody", "staff"), ("parvesh", "staff")):
        before, after = sections(base, user, role), sections(pat, user, role)
        if role == "doctor":
            after = [(g, [n for n in ns if n != NEW]) for g, ns in after]
        ck("%s (%s) unchanged, tile for tile and section for section%s" % (user, role, " (bar the doctor-role tile)" if role == "doctor" else ""),
           before == after, (before, after))
    ck("shavez is NOT shown '%s'" % NEW, NEW not in tiles(pat, "shavez", "manager"))
    ck("amir is still shown exactly ['Amir ka kaam', 'Aaj ki reports']", tiles(pat, "amir") == ["Amir ka kaam", "Aaj ki reports"], tiles(pat, "amir"))
    ck("bhawna (doctor) is shown it by role -- the page shows her the owner view", NEW in tiles(pat, "bhawna", "doctor"))

    # ---- 5 fail closed ---------------------------------------------------------------
    pat.TILE_GRANTS_FILE = os.path.join(PATCHED, "no_such_grants.json")
    pat._GRANTS_CACHE["mtime"] = None
    pat._GRANTS_CACHE["data"] = None
    ck("FAIL CLOSED: no grants file -> darpan loses the tile (and Daily Sale, as before), the doctor keeps both",
       NEW not in tiles(pat, "darpan") and "Daily Sale" not in tiles(pat, "darpan")
       and NEW in tiles(pat, "manoj", "doctor") and "Daily Sale" in tiles(pat, "manoj", "doctor"))
    io.open(os.path.join(PATCHED, "bad.json"), "w").write("{ not json")
    pat.TILE_GRANTS_FILE = os.path.join(PATCHED, "bad.json")
    pat._GRANTS_CACHE["mtime"] = None
    pat._GRANTS_CACHE["data"] = None
    ck("FAIL CLOSED: malformed grants file -> same", NEW not in tiles(pat, "darpan") and NEW in tiles(pat, "manoj", "doctor"))

print()
print("WALK: %d passed, %d failed" % (len(PASSED), len(FAILED)))
for f in FAILED:
    print("  FAILED:", f)
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(0 if not FAILED else 1)
