#!/usr/bin/env python3
"""S187_P1a gate — the Sanjeevni tile moves to the approvals hub and gains a
live pending summary; EVERYTHING ELSE about the portal must be untouched.

Adapted from the F-98 harness (S182_P2a): candidate + live baseline are both
imported, pages are rendered per named person, and the assertions run on the
SERVED HTML — including the absence checks, where regressions hide (F-79).

Usage:  python3 smoke_portal_P1a.py <candidate.py> <live-baseline.py>
"""
import sys, os, importlib.util, importlib.machinery, types

CAND = sys.argv[1] if len(sys.argv) > 1 else "portal_P1a.py"
BASE = sys.argv[2] if len(sys.argv) > 2 else "portal_live.py"
passed, failed = [], []


def check(label, cond, saw):
    (passed if cond else failed).append(label)
    print("  %s  %-58s | saw: %s" % ("OK  " if cond else "FAIL", label, saw))


def load(path, name):
    live_dir = os.path.dirname(os.path.abspath(BASE)) or "."
    if live_dir not in sys.path:
        sys.path.insert(0, live_dir)
    for mod in ("portal_config", "clinic_sso", "clinic_users"):
        try:
            __import__(mod)
        except Exception:
            sys.modules.setdefault(mod, types.ModuleType(mod))
    loader = importlib.machinery.SourceFileLoader(name, path)
    spec = importlib.util.spec_from_file_location(name, path, loader=loader)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


print("=" * 76)
print("S187_P2a - DAILY SALE + CLINIC TILE COUNTS GATE")
print("=" * 76)

print("\n[A] IMPORT + TILE SET")
try:
    new = load(CAND, "p1a_cand")
    old = load(BASE, "p1a_live")
    check("candidate imports cleanly", True, "%d tiles" % len(new.TILES))
except Exception as e:
    check("candidate imports cleanly", False, "%s: %s" % (type(e).__name__, e))
    print("\nRESULT: RED — cannot continue"); sys.exit(1)

nn = sorted(t["name"] for t in new.TILES)
on = sorted(t["name"] for t in old.TILES)
check("tile NAMES identical to live (nothing added or dropped)", nn == on,
      "same %d names" % len(nn) if nn == on else "DIFFER: %s" % set(nn) ^ set(on))

sj_new = [t for t in new.TILES if t["name"] == "Sanjeevni Medicos"]
sj_old = [t for t in old.TILES if t["name"] == "Sanjeevni Medicos"]
check("exactly one Sanjeevni tile", len(sj_new) == 1, str(len(sj_new)))
sj = sj_new[0]
check("Sanjeevni tile now lands on /finance/approvals",
      sj.get("url") == "/finance/approvals", sj.get("url"))
check("Sanjeevni tile carries the live-counts flag",
      sj.get("sanjeevni_counts") is True, str(sj.get("sanjeevni_counts")))
check("Sanjeevni tile roles unchanged (doctor only)",
      sj.get("roles") == sj_old[0].get("roles"), str(sj.get("roles")))

others_new = {t["name"]: (t.get("url"), tuple(t.get("roles") or []))
              for t in new.TILES if t["name"] != "Sanjeevni Medicos"}
others_old = {t["name"]: (t.get("url"), tuple(t.get("roles") or []))
              for t in old.TILES if t["name"] != "Sanjeevni Medicos"}
check("every OTHER tile's url+roles byte-identical to live",
      others_new == others_old,
      "identical" if others_new == others_old else
      "DIFFER: %s" % [k for k in others_new if others_new[k] != others_old.get(k)])

print("\n[B] SERVED HTML")
new._usable = lambda: True
new._is_trusted = lambda req: True
new._is_clinic_pc = lambda req: False
new._sso_ready = lambda: True
client = new.app.test_client()


def page_for(user, role):
    new._sso_user = lambda req: ({"user": user, "role": role} if user else None)
    return client.get("/portal", follow_redirects=False)


r = page_for("manoj", "doctor")
html = r.get_data(as_text=True)
check("manoj page renders 200", r.status_code == 200, str(r.status_code))
check("Sanjeevni tile href is the approvals hub in SERVED html",
      'href="/finance/approvals"' in html, "present" if 'href="/finance/approvals"' in html else "MISSING")
check("the review dead-end href is GONE from the tile",
      'href="/finance/review"' not in html, "absent" if 'href="/finance/review"' not in html else "STILL PRESENT")
check("data-sanjeevni-counts attribute served",
      "data-sanjeevni-counts" in html, "present" if "data-sanjeevni-counts" in html else "MISSING")
check("tile-summary fetch script served",
      "/finance/api/tile-summary" in html, "present" if "/finance/api/tile-summary" in html else "MISSING")
check("staff-register counts script INTACT",
      "/portal/review-counts" in html and "data-review-counts" in html, "intact")
check("gist summary script INTACT",
      "/portal/gist-data" in html and "data-gist-summary" in html, "intact")
check("clinic tile hydration INTACT",
      "/finance/clinic/api/tile-meta" in html and "data-clinic-tile" in html, "intact")

r = page_for("bhawna", "doctor")
html_b = r.get_data(as_text=True)
check("bhawna: Sanjeevni tile still MASKED (served html)",
      '<div class="nm">Sanjeevni Medicos</div>' not in html_b, "masked")
# the SCRIPT (served to all) contains the selector string; the check must
# target the rendered tile ATTRIBUTE, not the page text (F-106 in a test,
# caught by this gate's own first run)
check("bhawna: no tile ELEMENT carries the counts attribute",
      ' data-sanjeevni-counts>' not in html_b, "absent")

r = page_for("darpan", "staff")
html_d = r.get_data(as_text=True)
check("darpan: Daily Sale present, Sanjeevni absent",
      '<div class="nm">Daily Sale</div>' in html_d and
      '<div class="nm">Sanjeevni Medicos</div>' not in html_d, "correct")


r = page_for("darpan", "staff")
html_d2 = r.get_data(as_text=True)
check("darpan: Daily Sale tile carries the counts attribute",
      " data-daily-sale-counts>" in html_d2, "present" if " data-daily-sale-counts>" in html_d2 else "MISSING")
check("my-day-summary fetch script served",
      "/finance/api/my-day-summary" in html_d2, "present")
r = page_for("manoj", "doctor")
html_m2 = r.get_data(as_text=True)
check("manoj: no Daily Sale tile, so no daily-sale attr on an element",
      " data-daily-sale-counts>" not in html_m2, "absent")
ds_new = [t for t in new.TILES if t["name"] == "Daily Sale"][0]
ds_old = [t for t in old.TILES if t["name"] == "Daily Sale"][0]
check("Daily Sale url+roles unchanged",
      ds_new.get("url") == ds_old.get("url") and ds_new.get("roles") == ds_old.get("roles"),
      str(ds_new.get("url")))

print("\n" + "=" * 76)
print("RESULT: %d passed, %d failed" % (len(passed), len(failed)))
if failed:
    for f in failed:
        print("  FAIL:", f)
    print("GATE RED — do not install."); sys.exit(1)
print("GATE GREEN")
