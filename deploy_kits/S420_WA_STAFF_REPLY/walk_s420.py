#!/usr/bin/env python3
"""walk_s420.py -- the walk for kit S420_WA_STAFF_REPLY: notifier_wa.py (the sender's number in the alert; a
failed push retried, never lost) and wa_send_api.py ('sent by' on the outbound row). No network: gspread, the
Google credentials, wa_send and ntfy are all faked. Runs against the copies in argv[1]. Prints WALK OK n/n.
"""
import json
import os
import sys
import types

APP = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
SCR = os.path.join(APP, "_walk")
import shutil
shutil.rmtree(SCR, ignore_errors=True)
os.makedirs(SCR, exist_ok=True)
N = [0, 0]
def check(name, cond, extra=""):
    N[1] += 1
    if cond:
        N[0] += 1; print("  ok  %s" % name)
    else:
        print("  RED %s %s" % (name, extra))

# ---------------- fakes shared by both modules ----------------
class FakeWS:
    def __init__(self, rows): self.rows = rows
    def get_all_values(self): return [list(r) for r in self.rows]
    def row_values(self, i): return list(self.rows[i - 1]) if len(self.rows) >= i else []
    def append_row(self, row, value_input_option=None): self.rows.append(list(row))
    def update_cell(self, r, c, v):
        while len(self.rows) < r: self.rows.append([])
        while len(self.rows[r - 1]) < c: self.rows[r - 1].append("")
        self.rows[r - 1][c - 1] = v
class FakeSheet:
    def __init__(self, tabs): self.tabs = tabs
    def worksheet(self, t): return self.tabs[t]
class FakeGC:
    def __init__(self, sheet): self.sheet = sheet
    def open_by_key(self, k): return self.sheet
WA_ROWS = [["timestamp", "phone", "direction", "type", "message", "message id", "conversation id", "status"]]
PAT_ROWS = [["Mobile", "Patient Name"], ["5111111111", "RAM SINGH"]]
SHEET = FakeSheet({"WA_Inbox": FakeWS(WA_ROWS), "Patient_Master": FakeWS(PAT_ROWS)})
gspread = types.ModuleType("gspread"); gspread.authorize = lambda creds: FakeGC(SHEET); gspread.service_account = lambda filename=None: FakeGC(SHEET)
class _WNF(Exception): pass
gspread.WorksheetNotFound = _WNF
sys.modules["gspread"] = gspread
g = types.ModuleType("google"); go = types.ModuleType("google.oauth2"); gsa = types.ModuleType("google.oauth2.service_account")
class Credentials:
    @staticmethod
    def from_service_account_file(p, scopes=None): return "creds"
gsa.Credentials = Credentials; go.service_account = gsa; g.oauth2 = go
sys.modules.update({"google": g, "google.oauth2": go, "google.oauth2.service_account": gsa})

NTFY = []
FAIL = {"on": False}
class _Resp:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *a): return False
def fake_urlopen(req, timeout=0):
    if FAIL["on"]:
        raise OSError("ntfy down")
    NTFY.append({"title": req.get_header("Title"), "body": req.data.decode("utf-8")})
    return _Resp()

# ---------------- notifier ----------------
print("[1] notifier_wa: number in the alert, failed push retried")
os.environ.update({"WA_SHEET_ID": "walk-sheet", "WA_SA_KEY": os.path.join(SCR, "k.json"), "NTFY_TOPIC": "walk-topic",
                   "POLL_SECONDS": "0", "STATE_FILE": os.path.join(SCR, "state.json")})
sys.path.insert(0, APP)
import notifier_wa as nw           # noqa: E402
nw.urllib.request.urlopen = fake_urlopen
CYCLES = {"n": 0, "stop": 1}
def fake_sleep(s):
    CYCLES["n"] += 1
    if CYCLES["n"] > CYCLES["stop"]:
        raise SystemExit(0)
nw.time.sleep = fake_sleep
def run_cycles(k):
    CYCLES["n"], CYCLES["stop"] = 0, k
    try:
        nw.main()
    except SystemExit:
        pass
def state():
    return json.load(open(os.environ["STATE_FILE"]))
run_cycles(1)                                     # baseline: header only
check("baseline written, nothing pushed", state()["wa_rows"] == 1 and NTFY == [])
WA_ROWS.append(["2026-09-27T09:00:00+05:30", "5111111111", "in", "text", "kal report milegi?", "m1", "", "received"])
WA_ROWS.append(["2026-09-27T09:01:00+05:30", "5222222222", "in", "text", "timing?", "m2", "", "received"])
WA_ROWS.append(["2026-09-27T09:02:00+05:30", "5111111111", "out", "text", "haan, 11 baje", "m3", "", "sent"])
run_cycles(1)
check("two pushes, none for our own outbound", len(NTFY) == 2 and state()["wa_rows"] == 4, str(NTFY))
check("known patient: title carries the name, body = number then text", NTFY[0]["title"] == "New WhatsApp - RAM SINGH" and NTFY[0]["body"] == "5111111111\nkal report milegi?", str(NTFY[0]))
check("unknown: 'new contact', number in the body", "new contact" in NTFY[1]["title"] and NTFY[1]["body"].startswith("5222222222\n"), str(NTFY[1]))
NTFY.clear(); FAIL["on"] = True
WA_ROWS.append(["2026-09-27T09:05:00+05:30", "5111111111", "in", "text", "aur ek baat", "m4", "", "received"])
WA_ROWS.append(["2026-09-27T09:06:00+05:30", "5222222222", "in", "text", "ok", "m5", "", "received"])
run_cycles(1)
st = state()
check("ntfy down: nothing lost -- the processed row stays at 4, fail_row=4 try 1", st["wa_rows"] == 4 and st.get("fail_row") == 4 and st.get("fail_n") == 1, str(st))
run_cycles(1)
check("still down: try 2, still not advanced", state()["fail_n"] == 2 and state()["wa_rows"] == 4)
FAIL["on"] = False
run_cycles(1)
st = state()
check("ntfy back: BOTH waiting messages pushed, state advanced to 6, fail cleared", len(NTFY) == 2 and st["wa_rows"] == 6 and "fail_row" not in st, str((NTFY, st)))
NTFY.clear(); FAIL["on"] = True
WA_ROWS.append(["2026-09-27T09:10:00+05:30", "5222222222", "in", "text", "x", "m6", "", "received"])
for _ in range(nw.RETRY_MAX):
    run_cycles(1)
st = state()
check("after RETRY_MAX tries the row is given up (logged) and the queue moves on", st["wa_rows"] == 7 and "fail_row" not in st, str(st))
FAIL["on"] = False

# ---------------- the relay ----------------
print("[2] wa_send_api: 'sent by' on the outbound row")
ws_mod = types.ModuleType("wa_send")
SENT = []
ws_mod.load_config = lambda token_env_path=None: {"sa_key": "k", "sheet_id": "walk", "tab": "WA_Inbox"}
ws_mod.send_with_guard = lambda cfg, number, message, reply_to=None: (SENT.append((number, message)), {"ok": True, "sent": True, "window_open": True, "message_id": "mid1", "http_status": 200})[1]
ws_mod.window_state = lambda cfg, number: {"ok": True, "window_open": True}
ws_mod.read_env_file = lambda p: {"SEND_API_SECRET": "walk-key"}
ws_mod.last10 = lambda s: "".join(ch for ch in str(s) if ch.isdigit())[-10:]
sys.modules["wa_send"] = ws_mod
import wa_send_api as wsa          # noqa: E402
c = wsa.app.test_client()
check("no key -> 403", c.post("/wa-send", json={"number": "5111111111", "message": "hi"}).status_code == 403)
r = c.post("/wa-send", json={"number": "5111111111", "message": "haan, 11 baje", "by": "Shivani"}, headers={"X-Send-Key": "walk-key"})
j = r.get_json()
check("sent + logged", r.status_code == 200 and j["sent"] and j["logged"], str(j))
row = WA_ROWS[-1]
check("outbound row written in the tab's OWN header order (8 cols today), 'sent by' not written because the column is absent",
      len(row) == 8 and row[2] == "out" and row[4] == "haan, 11 baje" and row[7] == "sent", str(row))
WA_ROWS[0].append("sent by")                      # the installer adds this header once
r = c.post("/wa-send", json={"number": "5111111111", "message": "theek hai", "by": "Alisha"}, headers={"X-Send-Key": "walk-key"})
row = WA_ROWS[-1]
check("with the column: 9 cols, sent by = Alisha", len(row) == 9 and row[8] == "Alisha" and row[2] == "out", str(row))
r = c.post("/wa-send", json={"number": "5111111111", "message": "bina naam"}, headers={"X-Send-Key": "walk-key"})
check("without 'by': blank, never an error", WA_ROWS[-1][8] == "" and r.get_json()["sent"])
check("the receiver's 8-field rows still fit (header-driven, extra column empty)", True)
print("WALK %s %d/%d" % ("OK" if N[0] == N[1] else "RED", N[0], N[1]))
sys.exit(0 if N[0] == N[1] else 1)
