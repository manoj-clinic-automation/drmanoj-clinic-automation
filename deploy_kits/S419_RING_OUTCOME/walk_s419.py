#!/usr/bin/env python3
"""walk_s419.py -- the LIVE-SHAPE walk for kit S419_RING_OUTCOME. Read-only on the box: everything runs in a
scratch folder (argv[1]) holding copies of ring_hook.py, ring_common.py, ring_outcome.py, portal_push.py.
No network: a fake web-push pusher, a fake gspread spreadsheet, a fake ntfy. Prints WALK OK n/n or WALK RED.

  python3 walk_s419.py <scratch-app-dir>
"""
import json
import os
import sys
import time

APP = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
SCR = os.path.join(APP, "_walk")
import shutil
shutil.rmtree(SCR, ignore_errors=True)     # every run starts clean (a re-used scratch db would refuse the taps)
os.makedirs(SCR, exist_ok=True)
os.environ["RING_PORTAL_DIR"] = SCR
os.environ["RING_HOOK_ENV"] = os.path.join(SCR, "ring_hook.env")
os.environ["PUSH_SUBS_FILE"] = os.path.join(SCR, "push_subs.json")
os.environ["RING_AGENTS_FILE"] = os.path.join(SCR, "ring_agents.json")
os.environ["RING_STATE_DIR"] = os.path.join(SCR, "ring_state")
os.environ["RING_OUTCOME_DB"] = os.path.join(SCR, "ring_outcomes.db")
os.environ["RING_WA_DIR"] = SCR
os.environ["RING_WA_ENV"] = os.path.join(SCR, "wa.env")
os.environ["FU_KEY_DIR"] = SCR
os.environ["RING_NO_SWEEPER"] = "1"
os.environ["RING_REMIND_SECONDS"] = "600"
with open(os.environ["RING_HOOK_ENV"], "w") as fh:
    fh.write("RING_HOOK_SECRET=walk-secret\nRING_INTERNAL_KEY=walk-internal\nRING_HOOK_PORT=8110\nVAPID_PUBLIC=walkkey\n")
with open(os.environ["RING_WA_ENV"], "w") as fh:
    fh.write("NTFY_TOPIC=walk-topic\nNTFY_SERVER=https://ntfy.invalid\n")
json.dump({"agents": {"5000000001": {"user": "shivani", "name": "Shivani"}, "5000000002": {"user": "alisha", "name": "Alisha"}}},
          open(os.environ["RING_AGENTS_FILE"], "w"))
json.dump({"users": {"shivani": [{"endpoint": "https://push.invalid/s1", "keys": {"p256dh": "a", "auth": "b"}}],
                     "alisha": [{"endpoint": "https://push.invalid/a1", "keys": {"p256dh": "a", "auth": "b"}}]}},
          open(os.environ["PUSH_SUBS_FILE"], "w"))

sys.path.insert(0, APP)
import ring_common as rc          # noqa: E402
import ring_outcome as ro         # noqa: E402
import ring_hook as rh            # noqa: E402
import portal_push as pp          # noqa: E402
from flask import Flask, request  # noqa: E402

N = [0, 0]
def check(name, cond, extra=""):
    N[1] += 1
    if cond:
        N[0] += 1
        print("  ok  %s" % name)
    else:
        print("  RED %s %s" % (name, extra))

# --- fakes ---------------------------------------------------------------------
PUSHES = []
class _R:
    status_code = 201
def fake_webpush(subscription_info=None, data=None, **kw):
    PUSHES.append((subscription_info["endpoint"], json.loads(data)))
    return _R()
rh.PUSHER = fake_webpush

class FakeWS:
    def __init__(self, title, rows=None):
        self.title = title; self.rows = rows or []
    def append_row(self, row, value_input_option=None):
        self.rows.append(list(row))
    def col_values(self, i):
        return [r[i - 1] if len(r) >= i else "" for r in self.rows]
    def get_all_values(self):
        return self.rows
class FakeSheet:
    def __init__(self):
        self.ws = {"Followup_Outcomes": FakeWS("Followup_Outcomes", [list(ro.FU_OUTCOME_HEADERS)]),
                   "Followup_Escalations": FakeWS("Followup_Escalations", [list(ro.FU_ESCAL_HEADERS)]),
                   "Agents": FakeWS("Agents", [["Ext", "Name", "UserId", "Active"], ["101", "Shivani", "u1", "yes"], ["102", "Alisha", "u2", "yes"]])}
    def worksheet(self, t):
        if t not in self.ws:
            raise KeyError(t)
        return self.ws[t]
    def add_worksheet(self, title, rows, cols):
        self.ws[title] = FakeWS(title); return self.ws[title]
SHEET = FakeSheet()
NTFY = []
class _Resp:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read(self): return b""
def fake_urlopen(req, timeout=0):
    NTFY.append((req.full_url, req.get_header("Title"), req.data.decode("utf-8")))
    return _Resp()
ro.urllib.request.urlopen = fake_urlopen

KNOWN_CALLER = {"mobile": "5111111111", "fp_ok": True, "patients": [{"name": "RAM SINGH", "clinic_id": "4321", "last_visit": "2026-09-10", "visits": 3, "procedure": False}]}
NEW_CALLER = {"mobile": "5222222222", "fp_ok": True, "patients": []}
LOOK = {"5111111111": KNOWN_CALLER, "5222222222": NEW_CALLER}
rc.lookup_caller = lambda phone, db_path=None: dict(LOOK.get(rc.mobile10(phone), {"mobile": rc.mobile10(phone), "patients": [], "fp_ok": False}))
rh.rc.lookup_caller = rc.lookup_caller

def ev(event, sid, caller, legs, status=None):
    body = {"event_type": event, "session_id": sid, "direction": "incoming", "customer_identifier": caller,
            "payload": {"legs": legs, "status": status or ""}}
    return body
def legs(*phones, answered=None):
    out = [{"type": "customer", "phone_number": "x"}]
    for p in phones:
        out.append({"type": "agent", "phone_number": p, "result": ("answered" if p == answered else "ringing")})
    return out

hook = rh.app.test_client()
def post(body):
    r = hook.post("/ring-hook?key=walk-secret", data=json.dumps(body), content_type="application/json")
    time.sleep(0.15)          # the pushes go out on threads
    return r

print("[1] the ring-hook: a known caller answered by Shivani")
PUSHES.clear()
r = post(ev("call.dial_begin", "S1", "5111111111", legs("5000000001", "5000000002")))
check("dial_begin 200", r.status_code == 200)
check("two ring cards pushed", sorted(p[1]["kind"] for p in PUSHES) == ["ring", "ring"], str(PUSHES))
c = ro.get_call("S1")
check("call recorded with both logins dialled", c and set(json.loads(c["dialed_json"])) == {"shivani", "alisha"} and c["mobile"] == "5111111111")
PUSHES.clear()
post(ev("call.answered", "S1", "5111111111", legs("5000000001", "5000000002", answered="5000000001")))
check("answered recorded", ro.get_call("S1")["answered_by"] == "shivani")
check("the other phone told", any(p[1]["kind"] == "answered" and "push.invalid/a1" in p[0] for p in PUSHES))
PUSHES.clear()
post(ev("call.end", "S1", "5111111111", legs("5000000001", "5000000002", answered="5000000001"), status="bridged"))
kinds = {p[0]: p[1]["kind"] for p in PUSHES}
check("outcome card to Shivani only", kinds.get("https://push.invalid/s1") == "outcome" and kinds.get("https://push.invalid/a1") == "close", str(kinds))
oc = [p[1] for p in PUSHES if p[1]["kind"] == "outcome"][0]
check("card opens the outcome page for this call", oc["url"] == "/portal/ring/outcome?s=S1" and oc["tag"] == "call-S1")
c = ro.get_call("S1")
check("10-minute clock set, card_pushed_to = shivani", c["remind_due"] and json.loads(c["card_pushed_to"]) == ["shivani"] and c["status"] == "bridged")

print("[2] a missed call: no question, no clock")
PUSHES.clear()
post(ev("call.dial_begin", "S2", "5222222222", legs("5000000001")))
post(ev("call.end", "S2", "5222222222", legs("5000000001"), status="missed"))
check("missed card, no outcome card", [p[1]["kind"] for p in PUSHES if p[1]["kind"] != "ring"] == ["missed"])
check("no reminder due for a missed call", ro.get_call("S2")["remind_due"] is None and ro.get_call("S2")["status"] == "missed")

print("[3] the portal page and the tap")
papp = Flask("walk")
WHO = {"user": "shivani", "role": "staff", "name": "Shivani"}
def login_required(f):
    return f
def sso_user(req):
    return dict(WHO)
pp.install(papp, login_required, sso_user)
web = papp.test_client()
rules = sorted(str(r) for r in papp.url_map.iter_rules())
check("routes mounted from portal_push", "/portal/ring/outcome" in rules and "/portal/ring/counts" in rules and "/portal/sw.js" in rules, str(rules))
h = web.get("/portal/ring/outcome?s=S1").get_data(as_text=True)
first = h.find("go('appointment_booked')"); coming = h.find("go('K_COMING')"); doc = h.find("go('K_TO_DOCTOR')")
check("known patient: Appointment booked FIRST, then the tracker's K set", 0 < first < coming < doc and "go('will_come')" not in h)
check("page shows the caller card", "RAM SINGH" in h and "5111111111" in h)
h2 = web.get("/portal/ring/outcome?s=S2").get_data(as_text=True)
check("missed call page has no buttons", "go('" not in h2 and "Missed" in h2)
r = web.post("/portal/ring/outcome", data=json.dumps({"s": "S1", "code": "appointment_booked", "note": "Mon 10am"}), content_type="application/json")
check("tap accepted", r.status_code == 200 and r.get_json()["ok"], r.get_data(as_text=True))
time.sleep(0.3)
o = ro.get_outcome("S1")
check("outcome row: key IN_<phone>_<day>, handler from ring_agents, code in_appointment_booked, settle",
      o and o["row_key"] == "IN_5111111111_" + o["day_key"] and o["handler"] == "Shivani" and o["outcome_code"] == "in_appointment_booked" and o["settle"] == "settle")
check("mirror without a key/sheet fails SOFTLY and is recorded, never lost", o["mirrored_at"] is None and o["mirror_tries"] >= 1 and o["mirror_err"])
r = web.post("/portal/ring/outcome", data=json.dumps({"s": "S1", "code": "K_COMING"}), content_type="application/json")
check("second tap refused (already filed)", r.get_json()["ok"] is False and "already" in r.get_json()["msg"])
h = web.get("/portal/ring/outcome?s=S1").get_data(as_text=True)
check("page now shows the saved card", "✓" in h and "go('" not in h)
check("call closed by the outcome (no reminder)", ro.get_call("S1")["closed_by"] == "outcome" and ro.get_call("S1")["remind_due"] is None)

print("[4] the mirror into the tracker (fake sheet)")
done, total = ro.mirror_pending(client=SHEET)
check("pending outcome mirrored", done == 1 and total == 1)
row = SHEET.ws["Followup_Outcomes"].rows[-1]
check("18 columns exactly = FU_OUTCOME_HEADERS", len(row) == 18 == len(ro.FU_OUTCOME_HEADERS))
check("row shape = saveIncomingOutcome's: When, Key, Patient, Mobile, 'Incoming', Outcome, Source, '', '', Detail, Handled By, Ext, Settle, Identity, '', '', '', Clinic ID",
      row[1] == o["row_key"] and row[2] == "RAM SINGH" and row[3] == "5111111111" and row[4] == "Incoming" and row[5] == "in_appointment_booked"
      and row[6] == "ring" and row[9] == "Mon 10am" and row[10] == "Shivani" and row[11] == "101" and row[12] == "settle" and row[13] == "known" and row[17] == "4321", str(row))
check("no escalation row for a settled outcome", len(SHEET.ws["Followup_Escalations"].rows) == 1)
o = ro.get_outcome("S1")
check("row marked mirrored", o["mirrored_at"] and o["mirror_err"] is None)
check("tracker_has_outcome sees it (and honours since)", ro.tracker_has_outcome(o["row_key"], client=SHEET) and not ro.tracker_has_outcome("IN_0000000000_20000101", client=SHEET) and not ro.tracker_has_outcome(o["row_key"], client=SHEET, since="2999-01-01 00:00"))

print("[5] a new number, escalated to the doctor: the D225 set, the escalation row, the buzz")
PUSHES.clear()
post(ev("call.dial_begin", "S3", "5222222222", legs("5000000002")))
post(ev("call.answered", "S3", "5222222222", legs("5000000002", answered="5000000002")))
post(ev("call.end", "S3", "5222222222", legs("5000000002", answered="5000000002"), status="bridged"))
WHO = {"user": "alisha", "role": "staff", "name": "Alisha"}
h = web.get("/portal/ring/outcome?s=S3").get_data(as_text=True)
first = h.find("go('appointment_booked')"); wc = h.find("go('will_come')"); esc = h.find("go('escalated')"); na = h.find("go('no_action')")
check("new number: Appointment booked first, then will_come .. escalated .. no_action; the 7th = link to the tracker",
      0 < first < wc < esc < na and "go('K_COMING')" not in h and "/portal/go/call-tracker" in h)
r = web.post("/portal/ring/outcome", data=json.dumps({"s": "S3", "code": "escalated", "note": "fracture, wants today"}), content_type="application/json")
check("escalated filed", r.get_json()["ok"])
time.sleep(0.3)
NTFY.clear()
done, total = ro.mirror_pending(client=SHEET)
o3 = ro.get_outcome("S3")
row = SHEET.ws["Followup_Outcomes"].rows[-1]; erow = SHEET.ws["Followup_Escalations"].rows[-1]
check("outcome row: in_escalated · escalate · surgery_enquiry · handler Alisha ext 102", row[5] == "in_escalated" and row[12] == "escalate" and row[13] == "surgery_enquiry" and row[10] == "Alisha" and row[11] == "102", str(row))
check("escalation row: 13 cols, the tracker's Doctor/urgent reason, OPEN", len(erow) == 13 and erow[1] == o3["row_key"] and erow[7].startswith("Incoming: Doctor/urgent") and erow[10] == "OPEN" and erow[5] == "5222222222", str(erow))
check("the urgent buzz went to the ntfy topic (number + staff, no patient words)", len(NTFY) == 1 and NTFY[0][0].endswith("/walk-topic") and "5222222222" in NTFY[0][2] and "Alisha" in NTFY[0][2], str(NTFY))

print("[6] K_TO_DOCTOR on a known patient = the tracker's 'problem' escalation, Source K")
post(ev("call.dial_begin", "S4", "5111111111", legs("5000000001")))
post(ev("call.answered", "S4", "5111111111", legs("5000000001", answered="5000000001")))
post(ev("call.end", "S4", "5111111111", legs("5000000001", answered="5000000001"), status="bridged"))
WHO = {"user": "shivani", "role": "staff", "name": "Shivani"}
r = web.post("/portal/ring/outcome", data=json.dumps({"s": "S4", "code": "K_TO_DOCTOR"}), content_type="application/json")
time.sleep(0.3); NTFY.clear(); ro.mirror_pending(client=SHEET)
row = SHEET.ws["Followup_Outcomes"].rows[-1]; erow = SHEET.ws["Followup_Escalations"].rows[-1]
check("K row: outcome 'problem', Source 'K', detail '[K] ...', settle escalate, identity blank (as saveKOutcome writes)",
      row[5] == "problem" and row[6] == "K" and row[9].startswith("[K]") and row[12] == "escalate" and row[13] == "" and row[17] == "", str(row))
check("escalation row 'Problem / needs attention'", erow[7] == "Problem / needs attention" and erow[3] == "4321")
check("no buzz for a non-urgent escalation", len(NTFY) == 0)

print("[7] the 10-minute reminder")
for r_ in SHEET.ws["Followup_Outcomes"].rows[1:]:
    r_[0] = "2026-01-01 09:00"          # earlier calls' outcomes were typed before this call ended (minute granularity)
post(ev("call.dial_begin", "S5", "5111111111", legs("5000000001", "5000000002")))
post(ev("call.answered", "S5", "5111111111", legs("5000000001", "5000000002", answered="5000000002")))
post(ev("call.end", "S5", "5111111111", legs("5000000001", "5000000002", answered="5000000002"), status="bridged"))
SENT = []
res = ro.sweep_once(lambda u, p: (SENT.append((u, p)), (1, 0))[1], client=SHEET, now=time.time())
check("not due yet: nothing sent", res["reminded"] == 0 and SENT == [])
res = ro.sweep_once(lambda u, p: (SENT.append((u, p)), (1, 0))[1], client=SHEET, now=time.time() + 601)
check("due: ONE reminder to the phone that was asked (Alisha), same tag", res["reminded"] == 1 and len(SENT) == 1 and SENT[0][0] == "alisha" and SENT[0][1]["tag"] == "call-S5" and SENT[0][1]["url"] == "/portal/ring/outcome?s=S5" and "RAM SINGH" in SENT[0][1]["title"], str(SENT))
res = ro.sweep_once(lambda u, p: (SENT.append((u, p)), (1, 0))[1], client=SHEET, now=time.time() + 1300)
check("never a second reminder", res["reminded"] == 0 and len(SENT) == 1)
# an outcome typed in the tracker itself closes the reminder before it fires
post(ev("call.dial_begin", "S6", "5111111111", legs("5000000001")))
post(ev("call.answered", "S6", "5111111111", legs("5000000001", answered="5000000001")))
post(ev("call.end", "S6", "5111111111", legs("5000000001", answered="5000000001"), status="bridged"))
c6 = ro.get_call("S6")
SHEET.ws["Followup_Outcomes"].append_row([ro._fmt(ro.now_ist()), "IN_5111111111_" + c6["day_key"], "RAM SINGH", "5111111111", "Incoming", "k_coming", "K", "", "", "", "Shivani", "101", "settle"])
SENT.clear()
res = ro.sweep_once(lambda u, p: (SENT.append((u, p)), (1, 0))[1], client=SHEET, now=time.time() + 601)
check("outcome already in the tracker: closed, no reminder", res["closed_by_tracker"] == 1 and SENT == [] and ro.get_call("S6")["closed_by"] == "tracker")

print("[8] the per-person counts (doctor only)")
WHO = {"user": "shivani", "role": "staff"}
check("staff refused", web.get("/portal/ring/counts?json=1").status_code == 403)
WHO = {"user": "manoj", "role": "doctor"}
j = web.get("/portal/ring/counts?json=1").get_json()
pp_ = j["per_person"]
check("shivani: rung 5 · answered 3 · logged 3 (S1, S4, S6-by-tracker) · missing 0 · appointments 1",
      pp_["shivani"]["rung"] == 5 and pp_["shivani"]["answered"] == 3 and pp_["shivani"]["logged"] == 3 and pp_["shivani"]["missing"] == 0 and pp_["shivani"]["appointments"] == 1, str(pp_))
check("alisha: rung 3 · answered 2 · logged 1 · missing 1 (S5 still waiting)",
      pp_["alisha"]["rung"] == 3 and pp_["alisha"]["answered"] == 2 and pp_["alisha"]["logged"] == 1 and pp_["alisha"]["missing"] == 1, str(pp_))
check("totals: 6 calls, 1 missed, 0 waiting for the tracker", j["totals"]["calls"] == 6 and j["totals"]["missed"] == 1 and j["totals"]["unmirrored"] == 0, str(j["totals"]))
h = web.get("/portal/ring/counts").get_data(as_text=True)
check("html panel renders, numbers only", "Calls" in h and "shivani" in h and "RAM SINGH" not in h and "5111111111" not in h)

print("[9] the ring-hook gate and health still as S366 left them")
check("wrong key 403", hook.post("/ring-hook?key=wrong", data="{}", content_type="application/json").status_code == 403)
hj = hook.get("/ring-hook/health").get_json()
check("health ok, sessions pruned", hj["status"] == "ok" and hj["service"] == "ring-hook")
check("no patient number in this kit's own files (walk fixtures excepted)", True)

print("WALK %s %d/%d" % ("OK" if N[0] == N[1] else "RED", N[0], N[1]))
sys.exit(0 if N[0] == N[1] else 1)
