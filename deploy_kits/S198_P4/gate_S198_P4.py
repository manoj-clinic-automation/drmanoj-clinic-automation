#!/usr/bin/env python3
"""S198_P4 gate — portal PWA. Run: python3 gate_S198_P4.py <cand.py> --baseline <live.py>"""
import hashlib
import importlib.util
import json
import sys

PASS = FAIL = 0


def check(label, ok):
    global PASS, FAIL
    if ok:
        PASS += 1
    else:
        FAIL += 1
        print("FAIL: " + label)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cand = load(sys.argv[1], "cand_p4")
base = load(sys.argv[sys.argv.index("--baseline") + 1], "base_p4")

# icons byte-identical to the ATT2 shipment (one identity on every phone)
check("icon 192 = the ATT2 bytes",
      hashlib.md5(cand._PWA_ICON_192).hexdigest() == "5a4fef3887fe271190a9f778beb05d6a")
check("icon 512 = the ATT2 bytes",
      hashlib.md5(cand._PWA_ICON_512).hexdigest() == "83c6ec70a3989b16d41bbe5f5a44c09c")

with cand.app.test_client() as c:
    r = c.get("/portal/manifest.webmanifest")
    check("manifest public 200 + correct content-type",
          r.status_code == 200
          and r.headers["Content-Type"].startswith("application/manifest+json"))
    j = json.loads(r.get_data(as_text=True))
    check("manifest fields (name/start/scope/display/theme)",
          j["name"] == "Dr. Manoj Agarwal Clinic" and j["start_url"] == "/portal"
          and j["scope"] == "/" and j["display"] == "standalone"
          and j["theme_color"] == "#0f2233" and len(j["icons"]) == 2)
    r = c.get("/portal/pwa-icon-192.png")
    check("icon 192 serves as PNG, byte-exact",
          r.status_code == 200 and r.headers["Content-Type"] == "image/png"
          and r.data == cand._PWA_ICON_192)
    r = c.get("/portal/pwa-icon-512.png")
    check("icon 512 serves as PNG, byte-exact",
          r.status_code == 200 and r.data == cand._PWA_ICON_512)

# login page (unauthenticated path) advertises the install
cand._usable = lambda: True
cand._authed = lambda req: False
cand._sso_ready = lambda: True
with cand.app.test_client() as c:
    h = c.get("/portal/login").get_data(as_text=True)
    check("login page carries manifest + theme + touch icon",
          'rel="manifest"' in h and "theme-color" in h and "apple-touch-icon" in h)
    check("home still redirects the unauthenticated",
          c.get("/portal").status_code == 302)

# authed home carries the links too; tiles untouched
cand._authed = lambda req: True
cand._sso_user = lambda req: {"user": "alisha", "role": "staff"}
cand._is_clinic_pc = lambda req: False
with cand.app.test_client() as c:
    h = c.get("/portal").get_data(as_text=True)
    check("home page carries the manifest link", 'rel="manifest"' in h)

burl = {t["name"]: (t["url"], t["live"], tuple(t["roles"])) for t in base.TILES}
curl = {t["name"]: (t["url"], t["live"], tuple(t["roles"])) for t in cand.TILES}
check("ZERO tile changes (urls, live flags, roles all byte-equal)", burl == curl)

print("GATE %d/%d %s" % (PASS, PASS + FAIL, "GREEN" if FAIL == 0 else "RED"))
sys.exit(0 if FAIL == 0 else 1)
