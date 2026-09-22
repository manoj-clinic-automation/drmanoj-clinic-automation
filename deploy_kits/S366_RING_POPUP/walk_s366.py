#!/usr/bin/env python3
"""
walk_s366.py -- the S366 walk, offline. Loads ring_hook + the S366 portal.py into a scratch world (own env
file, own subs/agents files, a scratch finance.db with the real fingerprint code and a test salt, a FAKE webpush
that records instead of sending) and walks: ring -> answered -> end, missed, unknown caller, family phone,
unmapped agent, the gate, the test push, the portal's push routes, the service worker text, the card, and a
negative control (the live portal.py has none of the new routes).
Usage: python walk_s366.py <dir with ring_hook.py ring_common.py portal_push.py portal_sw.js portal.py
                             clinic_sso.py clinic_users.py tracker_pass.py> <finance dir with finance_patient_match.py>
                             <tile_grants.json> [<negative-control portal.py>]
"""
import hashlib, importlib.util, json, os, sqlite3, sys, tempfile, time

app_dir, fin_dir, grants = [os.path.abspath(a) for a in sys.argv[1:4]]
neg = os.path.abspath(sys.argv[4]) if len(sys.argv) > 4 else ""
tmp = tempfile.mkdtemp(prefix="s366walk_")
SALT = "walk-salt-not-real"
os.environ.update({
    "RING_PORTAL_DIR": app_dir, "RING_HOOK_ENV": os.path.join(tmp, "ring_hook.env"),
    "PUSH_SUBS_FILE": os.path.join(tmp, "push_subs.json"), "RING_AGENTS_FILE": os.path.join(tmp, "ring_agents.json"),
    "FINANCE_DB": os.path.join(tmp, "f.db"), "FINANCE_DIR": fin_dir, "PATIENT_FP_SALT": SALT,
    "RING_STATE_DIR": os.path.join(tmp, "state"), "CLINIC_USERS_FILE": os.path.join(tmp, "users.json"),
    "CLINIC_SSO_SECRET": "walk-sso-secret", "TILE_GRANTS_FILE": grants, "PORTAL_TOKEN_SEED": "walk-seed",
})
open(os.environ["RING_HOOK_ENV"], "w").write("RING_HOOK_SECRET=hookkey-walk\nRING_INTERNAL_KEY=internal-walk\nRING_HOOK_PORT=8110\n"
                                             "VAPID_PUBLIC=BPUBLICKEYwalk\nVAPID_SUBJECT=mailto:walk@example.invalid\n")
sys.path.insert(0, app_dir); sys.path.insert(0, fin_dir)
os.chdir(tmp)
import finance_patient_match as fpm
import ring_common as rc

n = 0
def ok(c, label):
    global n
    if not c:
        print("WALK RED: " + label); sys.exit(1)
    n += 1

# --- the scratch finance.db: two known patients on one number (family), one solo, one old id ---
con = sqlite3.connect(os.environ["FINANCE_DB"])
con.executescript("""
CREATE TABLE patient_ref(id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT, phone_last4 TEXT, first_seen TEXT, merged_into INTEGER,
  note TEXT, mobile_fp TEXT, patient_uid TEXT, last_seen TEXT, mobile_dup_count INTEGER, admin_cc_p INTEGER, admin_pd_pct INTEGER,
  admin_bid_pct INTEGER, is_vip INTEGER, concession_scheme TEXT, mobile TEXT);
CREATE TABLE patient_visit(visit_id TEXT, visit_date TEXT, clinic_id TEXT, patient_uid TEXT, mobile_fp TEXT, had_procedure TEXT);
""")
FAM, SOLO, UNK = "5811100001", "5811100002", "5811100003"
fp_f, fp_s = fpm.fingerprint(FAM, SALT), fpm.fingerprint(SOLO, SALT)
con.executemany("INSERT INTO patient_ref(clinic_id,name,mobile_fp,patient_uid,last_seen,mobile_dup_count) VALUES(?,?,?,?,?,?)", [
    ("1201", "RAM KUMAR", fp_f, "u1", "2026-08-12", 2), ("1202", "SITA DEVI", fp_f, "u2", "2026-07-03", 2),
    ("1305", "MOHAN LAL", fp_s, "u3", "2026-09-01", 1)])
con.executemany("INSERT INTO patient_visit VALUES(?,?,?,?,?,?)", [
    ("v1", "2026-08-12", "1201", "u1", fp_f, "1"), ("v2", "2026-05-02", "1201", "u1", fp_f, "0"),
    ("v3", "2026-07-03", "1202", "u2", fp_f, "0"), ("v4", "2026-09-01", "1305", "u3", fp_s, "0")])
con.commit(); con.close()

# --- ring_common ---
ok(rc.mobile10("+915811100001") == FAM and rc.mobile10("05811100001") == FAM and rc.mobile10("12345") == "", "mobile10")
info = rc.lookup_caller("+91" + FAM)
ok(info["fp_ok"] and [p["name"] for p in info["patients"]] == ["RAM KUMAR", "SITA DEVI"], "family lookup newest first")
ok(info["patients"][0]["last_visit"] == "2026-08-12" and info["patients"][0]["visits"] == 2 and info["patients"][0]["procedure"], "visit facts")
t, b = rc.caller_card(info)
ok(FAM in t and "2 मरीज़" in t and "RAM KUMAR (ID 1201, 12 Aug 2026)" in b, "family card shows the FULL number and both names")
t, b = rc.caller_card(rc.lookup_caller(SOLO))
ok(t == "\U0001F4DE MOHAN LAL · " + SOLO and "ID 1305" in b and "1 Sep 2026" in b, "solo card")
t, b = rc.caller_card(rc.lookup_caller(UNK))
ok("नया नंबर" in t and UNK in t, "unknown -> naya number with the full number")
ok(rc.caller_card(rc.lookup_caller("garbage"))[0].endswith("garbage"), "unparseable number never raises")
# subs
S1 = {"endpoint": "https://push.example/a1", "keys": {"p256dh": "k1", "auth": "a1"}}
S2 = {"endpoint": "https://push.example/a2", "keys": {"p256dh": "k2", "auth": "a2"}}
ok(rc.add_sub("shavez", S1, "ua") and rc.add_sub("shavez", S1, "ua") and len(rc.subs_for("shavez")) == 1, "same endpoint twice = one")
ok(rc.add_sub("shavez", S2) and len(rc.subs_for("shavez")) == 2 and rc.add_sub("alisha", S1), "two phones for shavez, one for alisha")
ok(not rc.add_sub("x", {"endpoint": "e"}), "bad subscription refused")
ok(oct(os.stat(os.environ["PUSH_SUBS_FILE"]).st_mode)[-3:] == "600", "subs file 0600")
json.dump({"agents": {"5800000011": {"user": "shavez", "name": "Shavez Ahmed"}, "5800000014": {"user": "alisha", "name": "Alisha Khan"}}},
          open(os.environ["RING_AGENTS_FILE"], "w"))
ok(rc.agent_for("+915800000011")["user"] == "shavez" and rc.agent_for("+915899999999") is None, "agent map")

# --- fake webpush ---
SENT = []
DEAD = {"https://push.example/a2"}
def fake_webpush(subscription_info, data, vapid_private_key, vapid_claims, ttl, timeout, headers):
    ep = subscription_info["endpoint"]
    if ep in DEAD:
        class R: status_code = 410
        e = Exception("gone"); e.response = R(); raise e
    SENT.append((ep, json.loads(data), ttl, headers.get("Urgency")))
    class R2: status_code = 201
    return R2()
sent, failed = rc.push_user("shavez", {"kind": "x", "ttl": 30}, pusher=fake_webpush)
ok(sent == 1 and failed == 1 and len(rc.subs_for("shavez")) == 1, "dead subscription (410) dropped, live one sent")
ok(SENT[-1][2] == 30 and SENT[-1][3] == "high", "ttl and urgency carried")
SENT.clear()

# --- ring_hook ---
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
RH = load(os.path.join(app_dir, "ring_hook.py"), "ring_hook_walk")
RH.PUSHER = fake_webpush
c = RH.app.test_client()
def settle():
    for _ in range(60):
        time.sleep(0.02)
    return SENT
def ev(event_type, sid, legs, status=None, cust="+91" + FAM, key="hookkey-walk"):
    body = {"event_type": event_type, "session_id": sid, "direction": "incoming", "customer_identifier": cust,
            "timestamp": "2026-09-22T05:00:00.000Z", "payload": {"legs": legs}}
    if status: body["payload"]["status"] = status
    return c.post("/ring-hook?key=" + key, json=body)
AG = lambda ph, res, ans=None: {"type": "agent", "phone_number": ph, "result": res, "answered_at": ans}
CU = {"type": "customer", "phone_number": "+91" + FAM, "result": "connected"}
ok(c.get("/ring-hook/health").status_code == 200 and c.get("/ring-hook/health").get_json()["agents_mapped"] == 2, "health")
ok(ev("call.dial_begin", "s0", [CU], key="wrong").status_code == 403, "wrong key -> 403, counted")
ok(c.get("/ring-hook?key=hookkey-walk&challenge=abc").get_data(as_text=True) == "abc", "challenge echoed")
# ring: shavez dialled
r = ev("call.dial_begin", "s1", [CU, AG("+915800000011", "dialing")]); ok(r.status_code == 200 and r.get_json()["ok"], "dial_begin 200 at once")
settle()
ok(len(SENT) == 1 and SENT[0][1]["kind"] == "ring" and SENT[0][1]["tag"] == "call-s1" and "RAM KUMAR" in SENT[0][1]["body"] and FAM in SENT[0][1]["title"], "shavez's phone gets the ring pop-up with the full number")
ok(SENT[0][1]["requireInteraction"] is True and SENT[0][1]["url"] == "/portal/go/call-tracker", "ring stays until tapped; tap opens the Tracker signed in")
# hunt moves on: alisha dialled, shavez not answered -- shavez is NOT notified twice
ev("call.dial_begin", "s1", [CU, AG("+915800000011", "not_answered"), AG("+915800000014", "dialing")]); settle()
ok(len(SENT) == 2 and SENT[1][0] == S1["endpoint"] and SENT[1][1]["kind"] == "ring", "alisha gets hers, shavez not repeated")
# alisha answers -> shavez sees 'answered by'
ev("call.answered", "s1", [CU, AG("+915800000011", "not_answered"), AG("+915800000014", "answered", "2026-09-22T05:00:09Z")]); settle()
ok(len(SENT) == 3 and SENT[2][1]["kind"] == "answered" and "Alisha Khan" in SENT[2][1]["body"] and SENT[2][1]["tag"] == "call-s1", "shavez's pop-up becomes 'Alisha Khan ne utha liya'")
ok(all(s[1]["kind"] != "answered" for s in SENT if s[0] == S1["endpoint"] and s[1]["tag"] == "call-s1" and s[1]["kind"] == "ring") , "answerer keeps hers")
# end bridged -> close on both
ev("call.end", "s1", [CU, AG("+915800000011", "not_answered"), AG("+915800000014", "answered")], status="bridged"); settle()
closes = [s for s in SENT if s[1]["kind"] == "close" and s[1]["tag"] == "call-s1"]
ok(len(closes) == 2, "call end (bridged) closes both pop-ups")
ok("s1" not in RH._sessions, "session forgotten after end")
SENT.clear()
# missed call, unknown caller
ev("call.dial_begin", "s2", [{"type": "customer", "phone_number": "+91" + UNK, "result": "connected"}, AG("+915800000011", "dialing")], cust="+91" + UNK); settle()
ok(len(SENT) == 1 and "नया नंबर" in SENT[0][1]["title"] and UNK in SENT[0][1]["title"], "unknown caller -> naya number + full number")
ev("call.end", "s2", [AG("+915800000011", "not_answered")], status="missed", cust="+91" + UNK); settle()
ok(len(SENT) == 2 and SENT[1][1]["kind"] == "missed" and SENT[1][1]["requireInteraction"] and "Missed" in SENT[1][1]["title"], "missed -> stays on the phone")
SENT.clear()
# unmapped agent -> nothing sent, counted
r = ev("call.dial_begin", "s3", [CU, AG("+915899999999", "dialing")]); settle()
ok(len(SENT) == 0 and r.status_code == 200, "unmapped agent phone: no pop-up, still 200")
# garbage body
ok(c.post("/ring-hook?key=hookkey-walk", data="not json", content_type="text/plain").status_code == 200, "garbage body -> 200, logged")
# test push
ok(c.post("/ring-hook/test", json={"user": "shavez"}).status_code == 403, "test without internal key refused")
r = c.post("/ring-hook/test", json={"user": "shavez"}, headers={"X-Internal-Key": "internal-walk"}).get_json()
ok(r["ok"] and r["sent"] == 1 and SENT[-1][1]["kind"] == "test", "test push reaches shavez")
r = c.post("/ring-hook/test", json={"user": "nobody"}, headers={"X-Internal-Key": "internal-walk"}).get_json()
ok(r["ok"] is False and r["sent"] == 0, "test to a login with no phone -> ok:false")
logs = [json.loads(l) for l in open(os.path.join(os.environ["RING_STATE_DIR"], sorted(os.listdir(os.environ["RING_STATE_DIR"]))[0]))]
ok(any(l["type"] == "reject" for l in logs) and any(l["type"] == "event" and l.get("body", {}).get("session_id") == "s1" for l in logs)
   and any(l["type"] == "push" and "took_ms" in l for l in logs), "raw log: rejects, whole bodies, push timings")
ok(oct(os.stat(os.environ["RING_STATE_DIR"]).st_mode)[-3:] == "700", "state dir 0700")

# --- portal side ---
import clinic_users, clinic_sso
st = os.environ["CLINIC_USERS_FILE"]
clinic_users.add_role(st, "staff")
for u, rl in [("manoj", "doctor"), ("shavez", "staff"), ("amir", "staff")]:
    clinic_users.add_user(st, u, rl, "pw-" + u + "-12345")
P = load(os.path.join(app_dir, "portal.py"), "portal_walk")
ok(P._PORTAL_PUSH and P._TRACKER_PASS and P._sso_ready(), "portal loads with push + tracker pass")
pc = P.app.test_client()
sw = pc.get("/portal/sw.js")
ok(sw.status_code == 200 and "javascript" in sw.content_type and b"notificationclick" in sw.data and sw.headers.get("Cache-Control") == "no-cache", "sw.js served without login")
ok(pc.get("/portal/push/key").get_json() == {"ok": True, "key": "BPUBLICKEYwalk"}, "public key served without login")
ok(pc.post("/portal/push/subscribe", json=S1).status_code == 302, "subscribe needs a login")
def as_user(u, role):
    pc.set_cookie(clinic_sso.COOKIE_NAME, clinic_sso.make_token(u, role, clinic_users.get_epoch(st), "walk-sso-secret"), domain="localhost")
as_user("shavez", "staff")
h = pc.get("/portal").get_data(as_text=True)
ok('id="pushCard"' in h and "pushEnable()" in h and "/portal/sw.js" in h and 'href="/portal/go/call-tracker"' in h, "home carries the card, the script and the S364 tile")
ok(pc.get("/portal/push/status").get_json()["agent"] is True, "shavez owns a ringing phone -> card will show")
r = pc.post("/portal/push/subscribe", json={"subscription": {"endpoint": "https://push.example/s3", "keys": {"p256dh": "p", "auth": "a"}}}).get_json()
ok(r["ok"] and r["subs"] == 2, "phone subscribed under shavez")
ok(pc.post("/portal/push/subscribe", json={"bad": 1}).status_code == 400, "bad subscription 400")
ok(pc.post("/portal/push/unsubscribe", json={"endpoint": "https://push.example/s3"}).get_json()["subs"] == 1, "unsubscribe")
as_user("manoj", "doctor")
ok(pc.get("/portal/push/status").get_json()["agent"] is False, "the doctor's phone is not in the call flow -> no card")
as_user("amir", "staff")
ok(pc.get("/portal/push/status").get_json()["agent"] is False, "a login without a ringing phone -> no card")
r = pc.post("/portal/push/test").get_json()
ok(r["ok"] is False, "test with ring-hook down answers ok:false, never 500")
if neg:
    N = load(neg, "portal_neg")
    old = {r.rule for r in N.app.url_map.iter_rules()}; new = {r.rule for r in P.app.url_map.iter_rules()}
    ok(new - old == {"/portal/sw.js", "/portal/push/key", "/portal/push/status", "/portal/push/subscribe", "/portal/push/unsubscribe", "/portal/push/test"}
       and not (old - new), "routes: +6, none lost (%d -> %d)" % (len(old), len(new)))
    ok(N.TILES == P.TILES, "every tile identical to the live portal")
    ok(N.app.test_client().get("/portal/sw.js").status_code == 404, "negative control: live portal has no service worker")
print("WALK OK %d/%d checks" % (n, n))
