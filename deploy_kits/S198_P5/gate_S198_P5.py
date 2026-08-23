#!/usr/bin/env python3
"""S198_P5 gate. Run: python3 gate_S198_P5.py <cand.py> --baseline <live.py>"""
import importlib.util, sys
PASS = FAIL = 0
def check(label, ok):
    global PASS, FAIL
    if ok: PASS += 1
    else:
        FAIL += 1; print("FAIL: " + label)
def load(p, n):
    s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
cand = load(sys.argv[1], "c5"); base = load(sys.argv[sys.argv.index("--baseline")+1], "b5")
bt = {t["name"]: (t["url"], t["live"], tuple(t["roles"])) for t in base.TILES}
ct = {t["name"]: (t["url"], t["live"], tuple(t["roles"])) for t in cand.TILES}
check("exactly the Payment Register tile removed",
      set(bt) - set(ct) == {"Payment Register"} and not set(ct) - set(bt))
changed = {n for n in ct if ct[n] != bt[n]}
check("only the Janitor desc changed otherwise (urls/live/roles equal)", changed == set())
check("Payment Register out of the group map", "Payment Register" not in cand._TILE_GROUP)
check("config still readable (later surfaces)", hasattr(cand, "PAYMENT_REGISTER_URL"))
cand._usable = lambda: True; cand._authed = lambda r: True; cand._sso_ready = lambda: True
cand._sso_user = lambda r: {"user": "manoj", "role": "doctor"}
cand._is_clinic_pc = lambda r: False
with cand.app.test_client() as c:
    h = c.get("/portal").get_data(as_text=True)
check("home: no Payment Register tile; Janitor + Renewals still there",
      'nm">Payment Register</div>' not in h and 'nm">Inbox Janitor</div>' in h
      and 'nm">Renewals</div>' in h)
check("PWA manifest still served", cand.app.test_client().get("/portal/manifest.webmanifest").status_code == 200)
print("GATE %d/%d %s" % (PASS, PASS+FAIL, "GREEN" if FAIL == 0 else "RED"))
sys.exit(0 if FAIL == 0 else 1)
