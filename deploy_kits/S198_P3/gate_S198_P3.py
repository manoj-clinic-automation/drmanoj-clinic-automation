#!/usr/bin/env python3
"""S198_P3 gate — the Renewals tile. Run: python3 gate_S198_P3.py <cand.py> --baseline <live.py>"""
import importlib.util
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


def serve(mod, user, role):
    mod._usable = lambda: True
    mod._authed = lambda req: True
    mod._sso_ready = lambda: True
    mod._sso_user = lambda req: {"user": user, "role": role}
    mod._is_clinic_pc = lambda req: False
    with mod.app.test_client() as c:
        return c.get("/portal").get_data(as_text=True)


RURL = "https://docs.google.com/spreadsheets/d/1OB70_Mapuugc33zkfFevwnrS0e8s1NdWzsrzJDqO38E"

cand = load(sys.argv[1], "cand_p3")
base = load(sys.argv[sys.argv.index("--baseline") + 1], "base_p3")

burl = {t["name"]: t["url"] for t in base.TILES}
curl = {t["name"]: t["url"] for t in cand.TILES}
check("exactly one tile added, nothing else moved",
      set(curl) - set(burl) == {"Renewals"}
      and all(curl[n] == burl[n] for n in burl))
rt = next(t for t in cand.TILES if t["name"] == "Renewals")
check("Renewals tile: live, the Master v2 sheet, doctor-only",
      rt["live"] and rt["url"] == RURL and rt["roles"] == ["doctor"])
check("grouped Personal & Health",
      cand._TILE_GROUP.get("Renewals") == "Personal & Health")

h = serve(cand, "manoj", "doctor")
check("manoj sees the Renewals tile", 'nm">Renewals</div>' in h and RURL in h)
h = serve(cand, "alisha", "staff")
check("staff does not", 'nm">Renewals</div>' not in h)
h = serve(cand, "shavez", "manager")
check("manager does not", 'nm">Renewals</div>' not in h)
h = serve(cand, "bhawna", "doctor")
check("bhawna (doctor) sees it", 'nm">Renewals</div>' in h)

print("GATE %d/%d %s" % (PASS, PASS + FAIL, "GREEN" if FAIL == 0 else "RED"))
sys.exit(0 if FAIL == 0 else 1)
