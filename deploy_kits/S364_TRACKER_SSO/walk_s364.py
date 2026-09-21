#!/usr/bin/env python3
# walk_s364.py -- the S364 walk. Loads a portal.py into a scratch world (its own user store,
# its own test secret, the REAL tile_grants.json read-only) and walks the tile, the pass and
# the redeem. Touches no live store, no live secret, no service.
# Usage: python walk_s364.py <dir holding portal.py + tracker_pass.py + clinic_sso.py + clinic_users.py>
#                            <tile_grants.json> [<negative-control portal.py>]
import importlib.util, json, os, sys, tempfile, time, urllib.parse

app_dir, grants = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
neg = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else ""
tmp = tempfile.mkdtemp(prefix="s364walk_")
os.environ["CLINIC_USERS_FILE"] = os.path.join(tmp, "users.json")
os.environ["CLINIC_SSO_SECRET"] = "walk-secret-not-real"
os.environ["TILE_GRANTS_FILE"] = grants
os.environ.setdefault("PORTAL_TOKEN_SEED", "walk-seed")
sys.path.insert(0, app_dir)
os.chdir(tmp)                      # never pick up a real portal_config.py from the cwd
import clinic_users, clinic_sso, tracker_pass
S = os.environ["CLINIC_SSO_SECRET"]
st = os.environ["CLINIC_USERS_FILE"]
clinic_users.add_role(st, "staff")
for u, r in [("manoj", "doctor"), ("shavez", "staff"), ("alisha", "staff"), ("amir", "staff"), ("gone", "staff")]:
    clinic_users.add_user(st, u, r, "pw-" + u + "-12345")
clinic_users.set_active(st, "gone", False)

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

n = 0
def ok(c, label):
    global n
    if not c:
        print("WALK RED: " + label); sys.exit(1)
    n += 1

P = load(os.path.join(app_dir, "portal.py"), "portal_walk")
ok(P._TRACKER_PASS and P._sso_ready(), "broker mode + tracker_pass loaded")
c = P.app.test_client()
EXEC = P.TRACKER_URL
ok(EXEC.startswith("https://script.google.com/macros/s/AKfycbyo") and EXEC.endswith("/exec"), "Tracker address kept")

def as_user(u, role):
    ep = clinic_users.get_epoch(st)
    c.set_cookie(clinic_sso.COOKIE_NAME, clinic_sso.make_token(u, role, ep, S), domain="localhost")

def go():
    return c.get("/portal/go/call-tracker")

# not signed in -> the login page, nothing minted
c.delete_cookie(clinic_sso.COOKIE_NAME, domain="localhost")
r = go(); ok(r.status_code == 302 and "/portal/login" in r.headers["Location"], "no login -> /portal/login")

def pass_of(r):
    loc = r.headers["Location"]
    q = urllib.parse.parse_qs(urllib.parse.urlparse(loc).query)
    return loc, (q.get("sso") or [""])[0]

for u, role in [("shavez", "staff"), ("alisha", "staff"), ("manoj", "doctor")]:
    as_user(u, role)
    r = go(); loc, p = pass_of(r)
    ok(r.status_code == 302 and loc.startswith(EXEC + "?sso=") and p, u + ": tile -> Tracker with a pass")
    ok(r.headers.get("Cache-Control") == "no-store", u + ": no-store")
    ok(r.headers.get("Referrer-Policy") == "no-referrer", u + ": no-referrer")
    rr = c.post("/portal/sso/tracker-redeem", data={"p": p}).get_json()
    ok(rr == {"ok": True, "user": u, "role": role}, u + ": redeem names " + u)
    rj = c.post("/portal/sso/tracker-redeem", json={"p": p}).get_json()
    ok(rj.get("ok") and rj.get("user") == u, u + ": redeem also takes JSON")
    # the home page shows the tile pointing at the portal, never at Google directly
    h = c.get("/portal").get_data(as_text=True)
    ok('href="/portal/go/call-tracker"' in h, u + ": tile href is /portal/go/call-tracker")
    ok(EXEC not in h, u + ": Google address not in the page")

# a person NOT shown the tile gets the plain address (old behaviour), no pass
as_user("amir", "staff")
r = go(); loc, p = pass_of(r)
ok(r.status_code == 302 and loc == EXEC and not p, "amir (not granted): plain Tracker, no pass")

# redeem refusals
bad = lambda d: c.post("/portal/sso/tracker-redeem", data=d).get_json() == {"ok": False}
ok(bad({}), "empty redeem refused")
ok(bad({"p": "x.y"}), "garbage refused")
ck = clinic_sso.make_token("manoj", "doctor", clinic_users.get_epoch(st), S)
ok(bad({"p": ck}), "a login cookie is not a pass")
ok(c.get("/portal/sso/tracker-redeem").status_code == 405, "redeem is POST only")
p_gone = tracker_pass.mint("gone", "staff", clinic_users.get_epoch(st), S)
ok(bad({"p": p_gone}), "inactive user refused")
p_ghost = tracker_pass.mint("nobody", "doctor", clinic_users.get_epoch(st), S)
ok(bad({"p": p_ghost}), "unknown user refused")
p_old = tracker_pass.mint("shavez", "staff", clinic_users.get_epoch(st), S, now=int(time.time()) - 200)
ok(bad({"p": p_old}), "expired pass refused")
p_other = tracker_pass.mint("shavez", "staff", clinic_users.get_epoch(st), "another-secret")
ok(bad({"p": p_other}), "pass from another secret refused")
p_live = tracker_pass.mint("shavez", "staff", clinic_users.get_epoch(st), S)
clinic_users.set_role(st, "shavez", "doctor")
rr = c.post("/portal/sso/tracker-redeem", data={"p": p_live}).get_json()
ok(rr.get("role") == "doctor", "redeem answers the CURRENT role, not the pass's")
clinic_users.set_role(st, "shavez", "staff")
clinic_users.bump_epoch(st)
ok(bad({"p": p_live}), "sign out everywhere kills a live pass")

# a broken tracker_pass never breaks the tile: plain address
P._TRACKER_PASS = False
as_user("shavez", "staff")
r = go(); ok(r.status_code == 302 and r.headers["Location"] == EXEC, "tracker_pass missing -> plain Tracker")
ok(bad({"p": tracker_pass.mint("shavez", "staff", clinic_users.get_epoch(st), S)}), "tracker_pass missing -> redeem refuses")
P._TRACKER_PASS = True

# nothing else moved: the route table is the old one plus exactly two
if neg:
    N = load(neg, "portal_neg")
    old = {r.rule for r in N.app.url_map.iter_rules()}
    new = {r.rule for r in P.app.url_map.iter_rules()}
    ok(new - old == {"/portal/go/call-tracker", "/portal/sso/tracker-redeem"} and not (old - new),
       "routes: +2, none lost (%d -> %d)" % (len(old), len(new)))
    nc = N.app.test_client()
    ok(nc.get("/portal/go/call-tracker").status_code == 404, "negative control: live portal has no such route")
    ok([t["url"] for t in N.TILES if t["name"] == "Call Tracker"] == [EXEC], "negative control: live tile goes straight to Google")
    ok([t for t in N.TILES if t["name"] != "Call Tracker"] == [t for t in P.TILES if t["name"] != "Call Tracker"], "every other tile identical")
ok(c.get("/portal/health").status_code in (200, 503), "health answers")
print("WALK OK %d/%d checks" % (n, n))
