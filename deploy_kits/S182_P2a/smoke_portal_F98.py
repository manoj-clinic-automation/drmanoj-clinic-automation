#!/usr/bin/env python3
"""F-98 gate — identity is proven, never assumed; plus SERVED-HTML tile checks.

Two blocks the S182_P1a gate did not have:

  [C] THE IDENTITY MATRIX. Every combination of (broker ready?, SSO user?) is
      asserted against _is_doctor(). The regression this guards is the one found
      at S182: a browser holding the legacy PIN-era device cookie, with NO SSO
      session, was treated as the doctor and reached every @doctor_required
      surface. D264 is guarded too - when broker mode is unavailable the legacy
      behaviour must be UNCHANGED, so a config failure cannot lock the owner out.

  [D] SERVED HTML (D307c). The portal page is actually rendered for each named
      person and the tiles are counted in the HTML they would receive. When the
      owner reported "my new tiles are missing", nothing in the previous gate
      could answer it, because every check ran against Python objects rather
      than the page. This block answers it directly - including the ABSENCE
      checks, which is where the S171 CSS regression (F-79) hid.

Usage:  python3 smoke_portal_F98.py <candidate.py> <live-baseline.py>
"""
import sys, os, importlib.util, importlib.machinery, types

CAND = sys.argv[1] if len(sys.argv) > 1 else "portal_p2.py"
BASE = sys.argv[2] if len(sys.argv) > 2 else "portal_live2.py"
passed, failed = [], []


def check(label, cond, saw):
    (passed if cond else failed).append(label)
    print("  %s  %-54s | saw: %s" % ("OK  " if cond else "FAIL", label, saw))


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
print("S182_P2 - F-98 IDENTITY GATE + SERVED-HTML TILE CHECKS")
print("=" * 76)

print("\n[A] IMPORT")
try:
    new = load(CAND, "p2_cand")
    check("candidate imports cleanly", True, "%d tiles" % len(new.TILES))
except Exception as e:
    check("candidate imports cleanly", False, "%s: %s" % (type(e).__name__, e))
    sys.exit(1)
old = load(BASE, "p2_base")

print("\n[B] REGRESSION - this kit changes AUTH ONLY, no tile may move")
nn = [t["name"] for t in new.TILES]
on = [t["name"] for t in old.TILES]
check("tile set byte-identical to live", nn == on,
      "%d tiles, %s" % (len(nn), "identical" if nn == on else "CHANGED"))
for t in ("Daily Sale", "Sanjeevni Medicos", "Daily Collection", "Clinic", "Manage Users"):
    check("'%s' still present" % t, t in nn, "present" if t in nn else "MISSING")

print("\n[C] IDENTITY MATRIX - _is_doctor() must never assume")


class Req:
    def __init__(self):
        self.cookies = {}


def matrix(ready, who):
    new._sso_ready = lambda: ready
    new._sso_user = lambda req: who
    return new._is_doctor(Req())


check("broker READY + no SSO user  -> NOT doctor  (the F-98 fix)",
      matrix(True, None) is False, repr(matrix(True, None)))
check("broker READY + role=doctor  -> doctor",
      matrix(True, {"user": "manoj", "role": "doctor"}) is True, "True")
check("broker READY + role=staff   -> NOT doctor",
      matrix(True, {"user": "darpan", "role": "staff"}) is False, "False")
check("broker READY + role=manager -> NOT doctor",
      matrix(True, {"user": "shavez", "role": "manager"}) is False, "False")
check("broker DOWN  + no SSO user  -> doctor  (D264: access not removed)",
      matrix(False, None) is True, repr(matrix(False, None)))
check("broker DOWN  + role=staff   -> NOT doctor",
      matrix(False, {"user": "darpan", "role": "staff"}) is False, "False")

print("\n[D] SERVED HTML - render the real page and read the tiles out of it")
new._usable = lambda: True
new._is_trusted = lambda req: True          # legacy device cookie present
new._is_clinic_pc = lambda req: False
new._sso_ready = lambda: True
client = new.app.test_client()


def page_for(user, role):
    new._sso_user = lambda req: ({"user": user, "role": role} if user else None)
    r = client.get("/portal", follow_redirects=False)
    return r


r = page_for(None, None)
loc = r.headers.get("Location", "")
check("trusted device, NO SSO -> redirected to login (not a doctor portal)",
      r.status_code in (301, 302) and "/portal/login" in loc,
      "%s %s" % (r.status_code, loc or "-"))

EXPECT = {
    "manoj":   {"Clinic": True,  "Daily Collection": False, "Manage Users": True,
                "Sanjeevni Medicos": True},
    "bhawna":  {"Clinic": True,  "Daily Collection": False, "Manage Users": False,
                "Sanjeevni Medicos": False},
    "shavez":  {"Clinic": True,  "Daily Collection": True,  "Manage Users": False,
                "Sanjeevni Medicos": False},
    "alisha":  {"Clinic": False, "Daily Collection": True,  "Manage Users": False,
                "Sanjeevni Medicos": False},
    "shivani": {"Clinic": False, "Daily Collection": True,  "Manage Users": False,
                "Sanjeevni Medicos": False},
    # darpan is role=staff and Sanjeevni Medicos is roles:["doctor"], so he does
    # NOT see it. His medical tile is "Daily Sale". The earlier expectation here
    # was simply wrong; the code was right.
    "darpan":  {"Clinic": False, "Daily Collection": False, "Manage Users": False,
                "Sanjeevni Medicos": False, "Daily Sale": True},
}
ROLE = {"manoj": "doctor", "bhawna": "doctor", "shavez": "manager",
        "alisha": "manager", "shivani": "staff", "darpan": "staff"}

for user, want in EXPECT.items():
    r = page_for(user, ROLE[user])
    html = r.get_data(as_text=True)
    ok_page = r.status_code == 200
    check("%-8s page renders 200" % user, ok_page, str(r.status_code))
    if not ok_page:
        continue
    for tile, should in want.items():
        # Must match the tile NAME div specifically. A bare ">Clinic<" also
        # matches the SECTION header <div class="sec">Clinic</div>, which made
        # this gate report a leak that did not exist (caught in rehearsal).
        got = ('<div class="nm">' + tile + '</div>') in html
        check("%-8s %-18s in SERVED html = %-5s" % (user, tile, should),
              got == should, "yes" if got else "no")

r = page_for("manoj", "doctor")
html = r.get_data(as_text=True)
check("retired sheet tile absent from served html",
      "Daily Collections" not in html and "1AnJWDJsAwtgkfFCQNwLzi6" not in html, "absent")
check("hydration script present in served html",
      "/finance/clinic/api/tile-meta" in html and "data-clinic-tile" in html, "present")
check("signed-in identity shown in header (not the anonymous line)",
      "Signed in as" in html, "present")

print("\n" + "=" * 76)
print("RESULT: %d passed, %d failed" % (len(passed), len(failed)))
if failed:
    print("FAILED: " + ", ".join(failed))
print("=" * 76)
sys.exit(1 if failed else 0)
