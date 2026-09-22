#!/usr/bin/env python3
"""walk_s369.py -- the S369 walk (portal side): the card reports, the doctor reads, staff cannot; the S366 portal.py is
the negative control. Usage: python walk_s369.py <app dir: portal.py portal_push.py ring_common.py portal_sw.js
clinic_sso.py clinic_users.py tracker_pass.py> <tile_grants.json> [<S366 portal.py>]"""
import importlib.util, json, os, sys, tempfile
app_dir, grants = [os.path.abspath(a) for a in sys.argv[1:3]]
neg = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else ""
tmp = tempfile.mkdtemp(prefix="s369walk_")
os.environ.update({"RING_PORTAL_DIR": app_dir, "RING_HOOK_ENV": os.path.join(tmp, "ring_hook.env"), "PUSH_SUBS_FILE": os.path.join(tmp, "subs.json"),
                   "RING_AGENTS_FILE": os.path.join(tmp, "agents.json"), "PUSH_DIAG_FILE": os.path.join(tmp, "diag.json"),
                   "CLINIC_USERS_FILE": os.path.join(tmp, "users.json"), "CLINIC_SSO_SECRET": "walk-sso-secret", "TILE_GRANTS_FILE": grants, "PORTAL_TOKEN_SEED": "walk-seed"})
open(os.environ["RING_HOOK_ENV"], "w").write("RING_HOOK_SECRET=h\nRING_INTERNAL_KEY=i\nRING_HOOK_PORT=8110\nVAPID_PUBLIC=BPUB\nVAPID_SUBJECT=mailto:x@y.z\n")
json.dump({"agents": {"5800000011": {"user": "shivani", "name": "Shivani"}}}, open(os.environ["RING_AGENTS_FILE"], "w"))
sys.path.insert(0, app_dir); os.chdir(tmp)
import clinic_users, clinic_sso
n = 0
def ok(c, l):
    global n
    if not c: print("WALK RED: " + l); sys.exit(1)
    n += 1
st = os.environ["CLINIC_USERS_FILE"]; clinic_users.add_role(st, "staff")
for u, r in [("manoj", "doctor"), ("shivani", "staff")]: clinic_users.add_user(st, u, r, "pw-" + u + "-12345")
def load(p, name):
    s = importlib.util.spec_from_file_location(name, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
P = load(os.path.join(app_dir, "portal.py"), "portal_walk")
ok(P.SSO_SECRET == "walk-sso-secret" and P._PORTAL_PUSH, "scratch portal, push loaded")
c = P.app.test_client()
def as_user(u, role): c.set_cookie(clinic_sso.COOKIE_NAME, clinic_sso.make_token(u, role, clinic_users.get_epoch(st), "walk-sso-secret"), domain="localhost")
ok(c.post("/portal/push/diag", json={"step": "tap"}).status_code == 302, "diag needs a login")
as_user("shivani", "staff")
h = c.get("/portal").get_data(as_text=True)
ok('id="pushState"' in h and "_pushDiag('tap')" in h and "permission-timeout" in h and "DENIED_TXT" in h, "home carries the S369 card: state line, reporting, timeout")
ok(c.post("/portal/push/diag", json={"step": "tap", "perm": "default", "standalone": True}).get_json()["ok"], "staff report accepted")
ok(c.post("/portal/push/diag", json={"step": "error", "perm": "denied", "error": "x" * 500}).get_json()["ok"], "long error clipped, accepted")
ok(c.get("/portal/push/diag").status_code == 403, "staff cannot read the diag")
as_user("manoj", "doctor")
d = c.get("/portal/push/diag").get_json()
ok(d["ok"] and len(d["attempts"]["shivani"]) == 2 and d["attempts"]["shivani"][0]["step"] == "tap" and d["attempts"]["shivani"][0]["standalone"] is True
   and len(d["attempts"]["shivani"][1]["error"]) == 200 and "ua" in d["attempts"]["shivani"][1] and "when_ist" in d["attempts"]["shivani"][1], "doctor reads shivani's attempts, clipped, timed")
for i in range(15): c.post("/portal/push/diag", json={"step": "tap%d" % i})
ok(len(c.get("/portal/push/diag").get_json()["attempts"]["manoj"]) == 12, "kept to the last 12 per login")
ok(oct(os.stat(os.environ["PUSH_DIAG_FILE"]).st_mode)[-3:] == "600", "diag file 0600")
ok(c.get("/portal/sw.js").status_code == 200 and c.get("/portal/push/key").get_json()["key"] == "BPUB", "S366 routes still there")
if neg:
    N = load(neg, "portal_neg")
    ok(len({r.rule for r in N.app.url_map.iter_rules()}) == len({r.rule for r in P.app.url_map.iter_rules()}), "route table unchanged in portal.py itself (the +1 lives in portal_push.py)")
    ok(N.TILES == P.TILES, "every tile identical")
    nc = N.app.test_client(); nc.set_cookie(clinic_sso.COOKIE_NAME, clinic_sso.make_token("shivani", "staff", clinic_users.get_epoch(st), "walk-sso-secret"), domain="localhost")
    ok('id="pushState"' not in nc.get("/portal").get_data(as_text=True), "negative control: the S366 page has no state line")
print("WALK OK %d/%d checks" % (n, n))
