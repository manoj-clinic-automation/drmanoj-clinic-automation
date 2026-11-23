#!/usr/bin/env python3
"""walk_s935.py -- kit S935: the call hook keeps outgoing calls dialled from a staff member's MyOperator app, and the
console counts them as Out. Made-up payloads shaped as the live ones read on 23-Nov (field names only; numbers built
here at run time, F-185). The hook is loaded with gspread blocked (no Sheet) and its log folders in a temp dir.
    python3 walk_s935.py <call_hook_capture.py> <portal_console.py>        last line: WALK n/m"""
import importlib.util, os, sqlite3, sys, tempfile
hook_path, pc_path = sys.argv[1], sys.argv[2]
tmp = tempfile.mkdtemp(prefix="w935_")
os.environ["CALLHOOK_RAW_LOG_DIR"] = os.path.join(tmp, "raw")
os.environ["CALLHOOK_REJECT_DIR"] = os.path.join(tmp, "rej")
sys.modules["gspread"] = None                      # import gspread -> ImportError -> no Sheet connect
sys.path.insert(0, os.path.dirname(os.path.abspath(pc_path)))

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

ok = bad = 0
def check(name, cond):
    global ok, bad
    if cond: ok += 1
    else:
        bad += 1; print("RED  " + name)

try:
    H = load("chc_s935", hook_path)
    P = load("pc_s935", pc_path)
except Exception as e:
    print("could not load: %r" % (e,)); print("WALK 0/1"); sys.exit(1)

d = "9" + "1" * 8 + "7"                    # a made-up 10-digit number
cust = "+91" + d
agent_ph = "+91" + "8" * 10

def ow(ev, status, sid, with_cust=True, direction="outgoing", rec=True, end="2026-11-23T04:44:10.123456789Z"):
    legs = [{"type": "agent", "result": "connected", "phone_number": agent_ph},
            {"type": "customer", "result": "answered" if status == "bridged" else "not_answered",
             "phone_number": cust, "talk_duration": 40 if status == "bridged" else 0, "ring_duration": 8}]
    p = {"category": "oneway", "direction": direction, "status": status, "id": sid, "duration": 55,
         "ended_at": end, "legs": legs, "did": "+91" + "7" * 10}
    if with_cust: p["customer_number"] = cust
    if rec and status == "bridged": p["recording_filename"] = "rec_" + sid.replace(".", "_") + ".mp3"
    return {"event_type": ev, "session_id": sid, "payload": p}

r1 = H.extract_record(ow("call.summary", "bridged", "15.1763872450.101"), "call.summary")
check("W1 oneway outgoing kept", isinstance(r1, dict))
r1 = r1 or {}
check("W2 key OUT-<session>", r1.get("client_ref_id") == "OUT-15.1763872450.101")
check("W3 phone10 = the patient's last 10", r1.get("phone10") == d)
check("W4 category oneway, status bridged", r1.get("category") == "oneway" and r1.get("status") == "bridged")
check("W5 recording filename kept", (r1.get("recording_filename") or "").startswith("rec_15_"))
check("W6 ended_at in IST", str(r1.get("ended_at_ist", "")).startswith("2026-11-23T10:14:10"))
check("W7 talk from the customer leg", str(r1.get("customer_talk_duration")) == "40")
r2 = H.extract_record(ow("call.end", "bridged", "15.1763872450.101"), "call.end")
check("W8 call.end and call.summary share the key", (r2 or {}).get("client_ref_id") == r1.get("client_ref_id"))
r3 = H.extract_record(ow("call.end", "missed", "15.1763872450.102", end="2026-11-23T04:47:02Z"), "call.end")
check("W9 a missed app call kept, status missed", (r3 or {}).get("status") == "missed" and (r3 or {}).get("phone10") == d)
r4 = H.extract_record(ow("call.summary", "bridged", "15.1763872450.103", with_cust=False), "call.summary")
check("W10 no customer_number -> the customer leg's number", (r4 or {}).get("phone10") == d)
b5 = ow("call.summary", "bridged", ""); b5["session_id"] = ""
check("W11 no session id -> not kept", H.extract_record(b5, "call.summary") is None)
check("W12 oneway incoming -> not kept", H.extract_record(ow("call.end", "bridged", "15.9.1", direction="incoming"), "call.end") is None)
check("W13 oneway with no direction -> not kept", H.extract_record({"payload": {"category": "oneway", "id": "15.9.2"}}) is None)
check("W14 callback -> not kept", H.extract_record({"payload": {"category": "callback", "direction": "outgoing", "id": "15.9.3"}}) is None)
inc = {"event_type": "call.summary", "session_id": "15.9.4",
       "payload": {"category": "incoming", "direction": "incoming", "status": "bridged", "id": "15.9.4",
                   "customer_number": cust, "legs": [{"type": "customer", "result": "connected", "phone_number": cust}]}}
ri = H.extract_record(inc, "call.summary") or {}
check("W15 incoming unchanged (IN- key, phone)", ri.get("client_ref_id") == "IN-15.9.4" and ri.get("phone10") == d)
obd = {"payload": {"category": "obd", "client_ref_id": d + "-1763872450", "status": "bridged", "id": "15.9.5"}}
ro = H.extract_record(obd, "call.summary") or {}
check("W16 OBD unchanged (its own ref, no phone)", ro.get("client_ref_id") == d + "-1763872450" and ro.get("phone10") == "")
check("W17 a row has the tab's width", len(H.record_to_row(r1)) == len(H.HEADER))

check("W18 console: oneway -> Out", P.derive_direction("oneway") == "Out")
check("W19 console: obd Out, incoming In, other ?", P.derive_direction("obd") == "Out" and P.derive_direction("incoming") == "In" and P.derive_direction("callback") == "?")
conn = sqlite3.connect(":memory:")
P.create_schema(conn)
rows = [dict(r1, total_duration=55), dict(r2 or {}, total_duration=55), dict(r3 or {}), dict(ri)]
st = P.load_calls(conn, rows, {})
got = conn.execute("SELECT direction, answered, phone10 FROM calls WHERE client_ref_id LIKE 'OUT-%' ORDER BY client_ref_id").fetchall()
check("W20 the console loads two app calls (the pair folded) as Out", [g[0] for g in got] == ["Out", "Out"])
check("W21 answered from the status (bridged 1, missed 0)", [g[1] for g in got] == [1, 0])
check("W22 the patient's number on the console row", all(g[2] == d for g in got))
check("W23 the incoming row still In", conn.execute("SELECT direction FROM calls WHERE client_ref_id='IN-15.9.4'").fetchone() == ("In",))
print("WALK %d/%d" % (ok, ok + bad))
