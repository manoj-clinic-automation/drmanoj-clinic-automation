#!/usr/bin/env python3
"""S182 portal-tiles smoke suite.

Runs OFFLINE against the candidate portal.py by importing it and interrogating
the real TILES / _TILE_GROUP / USER_TILE_EXTRA / _visible_sections objects - not
by grepping strings. Every check PRINTS WHAT IT SAW (F-95), so a pass is
readable evidence rather than a bare tick.

The single most important block is REGRESSION: it asserts that every tile that
existed on the live box BEFORE this change still exists after it, which is the
guard F-97 was raised for. The S179 finance tiles were absent from git for two
sessions; nothing would have noticed them disappearing.

Usage:  python3 smoke_portal_S182.py <candidate.py> <live-baseline.py>
"""
import sys, os, importlib.util, importlib.machinery, types

CAND = sys.argv[1] if len(sys.argv) > 1 else "portal_new.py"
BASE = sys.argv[2] if len(sys.argv) > 2 else "portal_live.py"

passed = []
failed = []


def check(label, cond, saw):
    (passed if cond else failed).append(label)
    print("  %s  %-52s | saw: %s" % ("OK  " if cond else "FAIL", label, saw))


def load(path, name):
    """Import a portal.py in isolation.

    portal_config / clinic_sso / clinic_users sit beside the LIVE portal.py, so
    the baseline's directory goes on sys.path and the REAL modules are used when
    they are there - on the VPS all three are present, which makes this gate a
    test of the actual environment rather than of a synthetic one (F-95). Only a
    module that genuinely cannot be imported is stubbed, and never one that can.
    """
    live_dir = os.path.dirname(os.path.abspath(BASE)) or "."
    if live_dir not in sys.path:
        sys.path.insert(0, live_dir)
    for mod in ("portal_config", "clinic_sso", "clinic_users"):
        try:
            __import__(mod)
        except Exception:
            sys.modules.setdefault(mod, types.ModuleType(mod))
    # An explicit SourceFileLoader is required: the candidate arrives as
    # "portal.py.new", and importlib cannot infer a loader from that suffix.
    # Without this the gate fails with an obscure AttributeError and reports a
    # FALSE red on a perfectly good kit (caught in offline rehearsal, F-94).
    loader = importlib.machinery.SourceFileLoader(name, path)
    spec = importlib.util.spec_from_file_location(name, path, loader=loader)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


print("=" * 74)
print("S182 PORTAL TILES - OFFLINE SMOKE")
print("=" * 74)

print("\n[1] IMPORT (the ungrouped-tile assert at import time is itself a gate)")
try:
    new = load(CAND, "portal_new_mod")
    check("candidate imports cleanly", True, "%d tiles" % len(new.TILES))
except Exception as e:
    check("candidate imports cleanly", False, "%s: %s" % (type(e).__name__, e))
    print("\nABORT - cannot continue without an import.")
    sys.exit(1)

old = load(BASE, "portal_live_mod")
new_names = [t["name"] for t in new.TILES]
old_names = [t["name"] for t in old.TILES]

print("\n[2] REGRESSION - nothing on the live box may vanish (the F-97 guard)")
RETIRED = {"Daily Collections"}          # deliberate, owner ruling S182
lost = [n for n in old_names if n not in new_names and n not in RETIRED]
check("no unintended tile lost", not lost, "lost=%s" % (lost or "none"))
check("S179 'Daily Sale' still present", "Daily Sale" in new_names,
      "present" if "Daily Sale" in new_names else "MISSING")
check("S179 'Sanjeevni Medicos' still present", "Sanjeevni Medicos" in new_names,
      "present" if "Sanjeevni Medicos" in new_names else "MISSING")
for t in new.TILES:
    if t["name"] == "Daily Sale":
        check("'Daily Sale' url unchanged", t["url"] == "/finance/entry", t["url"])
    if t["name"] == "Sanjeevni Medicos":
        check("'Sanjeevni Medicos' url unchanged", t["url"] == "/finance/review", t["url"])
check("tile count moved by exactly +2-1", len(new_names) - len(old_names) == 1,
      "%d -> %d" % (len(old_names), len(new_names)))

print("\n[3] RETIREMENT - the legacy Google-Sheet tile is gone, cleanly")
check("'Daily Collections' removed from TILES", "Daily Collections" not in new_names,
      "absent" if "Daily Collections" not in new_names else "STILL PRESENT")
check("'Daily Collections' removed from _TILE_GROUP",
      "Daily Collections" not in new._TILE_GROUP,
      "absent" if "Daily Collections" not in new._TILE_GROUP else "STILL PRESENT")
sheet_refs = sum(1 for t in new.TILES if "1AnJWDJsAwtgkfFCQNwLzi6lqPPAfGwd" in str(t.get("url", "")))
check("no tile still points at the old sheet", sheet_refs == 0, "%d refs" % sheet_refs)

print("\n[4] THE TWO NEW TILES")
by = {t["name"]: t for t in new.TILES}
for nm, url in (("Daily Collection", "/finance/clinic/entry"),
                ("Clinic", "/finance/clinic/review")):
    check("'%s' exists" % nm, nm in by, "yes" if nm in by else "MISSING")
    if nm in by:
        t = by[nm]
        check("'%s' url" % nm, t["url"] == url, t["url"])
        check("'%s' roles are EMPTY (grant-only)" % nm, t["roles"] == [], repr(t["roles"]))
        check("'%s' is live" % nm, t.get("live") is True, repr(t.get("live")))
        check("'%s' marked for hydration" % nm, t.get("clinic_meta") is True,
              repr(t.get("clinic_meta")))
        check("'%s' grouped Money & Accounts" % nm,
              new._TILE_GROUP.get(nm) == "Money & Accounts", new._TILE_GROUP.get(nm))

print("\n[5] WHO SEES WHAT - resolved through the real _visible_sections()")


def visible(user, role, pc=False):
    out = set()
    for _lab, items in new._visible_sections(role, pc, user):
        for t in items:
            out.add(t["name"])
    return out


EXPECT_ENTRY = {"shavez", "alisha", "shivani"}
EXPECT_REVIEW = {"manoj", "bhawna", "shavez"}
ROLE = {"manoj": "doctor", "bhawna": "doctor", "shavez": "manager",
        "alisha": "manager", "shivani": "staff", "darpan": "staff"}
for u in ("manoj", "bhawna", "shavez", "alisha", "shivani", "darpan"):
    v = visible(u, ROLE[u])
    want_e, want_r = u in EXPECT_ENTRY, u in EXPECT_REVIEW
    check("%-8s sees 'Daily Collection' = %-5s" % (u, want_e),
          ("Daily Collection" in v) == want_e,
          "yes" if "Daily Collection" in v else "no")
    check("%-8s sees 'Clinic'           = %-5s" % (u, want_r),
          ("Clinic" in v) == want_r,
          "yes" if "Clinic" in v else "no")

print("\n[6] NO LEAKAGE - grant-only tiles must not reach anyone else")
leak = []
for role in ("doctor", "staff", "manager"):
    v = visible("nobody_" + role, role)
    for nm in ("Daily Collection", "Clinic"):
        if nm in v:
            leak.append("%s via role=%s" % (nm, role))
check("ungranted user of any role sees neither tile", not leak, "leaks=%s" % (leak or "none"))

print("\n[7] MEDICAL UNCHANGED - the S179 masks still behave")
check("bhawna still masked from 'Sanjeevni Medicos'",
      "Sanjeevni Medicos" not in visible("bhawna", "doctor"), "masked")
check("darpan still sees 'Daily Sale'", "Daily Sale" in visible("darpan", "staff"), "yes")
check("darpan sees NEITHER clinic tile",
      not ({"Daily Collection", "Clinic"} & visible("darpan", "staff")), "none")

print("\n[8] HYDRATION WIRING")
src = open(CAND, encoding="utf-8").read()
check("template emits data-clinic-tile", "data-clinic-tile" in src,
      "%d occurrence(s)" % src.count("data-clinic-tile"))
check("fetch targets the clinic tile-meta route",
      "/finance/clinic/api/tile-meta" in src, "present")
check("fetch has a .catch (portal never breaks on finance)",
      src.count(".catch(function(){});") >= 3,
      "%d catch blocks" % src.count(".catch(function(){});"))
check("hydration matches on href, not tile order",
      "getAttribute('href')!==d.href" in src, "href-matched")

print("\n" + "=" * 74)
print("RESULT: %d passed, %d failed" % (len(passed), len(failed)))
if failed:
    print("FAILED: " + ", ".join(failed))
print("=" * 74)
sys.exit(1 if failed else 0)
