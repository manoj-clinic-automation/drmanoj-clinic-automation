#!/usr/bin/env python3
"""walk_s949.py -- kit S949 (F1a): the call hook writes the server table first and the Sheet second; the nightly compare
proves table = Sheet; the health leg reads it. Made-up payloads shaped like the live ones (numbers built here at run time,
F-185). The hook is loaded from a temp copy beside the kit's call_log_db.py, gspread blocked (no Sheet: a fake tab),
its raw log, reject log, pipeline queue and table all in a temp dir -- nothing live is touched.
    python3 walk_s949.py <call_hook_capture.py> <kit dir> [--control]        last line: WALK n/m
    --control: the legs file is LEGS_FROM (the live one) -- run with the FROM hook, the walk must go red."""
import contextlib, importlib.util, io, json, os, re, shutil, sys, tempfile, time

hook_src, KIT = sys.argv[1], sys.argv[2]
CONTROL = "--control" in sys.argv
LEGS = os.environ.get("LEGS_FROM") if CONTROL and os.environ.get("LEGS_FROM") else os.path.join(KIT, "freshness_legs.json")
FROM_LEGS = os.path.join(KIT, "from", "freshness_legs.json")
tmp = tempfile.mkdtemp(prefix="w949_")
H_DIR = os.path.join(tmp, "h")
os.makedirs(H_DIR)
shutil.copy(hook_src, os.path.join(H_DIR, "call_hook_capture.py"))
shutil.copy(os.path.join(KIT, "call_log_db.py"), os.path.join(H_DIR, "call_log_db.py"))
shutil.copy(os.path.join(KIT, "call_log_compare.py"), os.path.join(H_DIR, "call_log_compare.py"))
RAW, QUEUE, DB = os.path.join(tmp, "raw"), os.path.join(tmp, "queue"), os.path.join(tmp, "calls.db")
os.environ.update({"CALLHOOK_RAW_LOG_DIR": RAW, "CALLHOOK_REJECT_DIR": os.path.join(tmp, "rej"),
                   "CALLHOOK_QUEUE_DIR": QUEUE, "CALLHOOK_DB": DB, "CALLHOOK_SECRET": "Walk@Key949",
                   "CALLHOOK_SECRET_PREV": "", "CALL_LOG_COMPARE_STATE": os.path.join(tmp, "cmp.json")})
sys.modules["gspread"] = None                       # import gspread -> ImportError -> no Sheet connect, ever
sys.path.insert(0, H_DIR)

ok = bad = 0
def check(name, cond):
    global ok, bad
    if cond:
        ok += 1
    else:
        bad += 1
        print("RED  " + name)

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

out = io.StringIO()
try:
    with contextlib.redirect_stdout(out):
        H = load("chc_w949", os.path.join(H_DIR, "call_hook_capture.py"))     # runs _startup_connect() at import
except Exception as e:
    print("could not load the hook: %r" % (e,)); print("WALK 0/1"); sys.exit(1)
boot = out.getvalue()
check("W1 the startup says receiver v3.4 and names the table with its row count",
      "receiver v3.4" in boot and ("call log table: %s -- 0 rows since" % DB) in boot)
check("W2 the table file exists, owner-only", os.path.exists(DB) and (os.stat(DB).st_mode & 0o777) == 0o600)

class FakeWS:
    def __init__(self, header):
        self.rows = [list(header)]
    def col_values(self, c):
        o = [(r[c - 1] if len(r) >= c else "") for r in self.rows]
        while o and o[-1] == "":
            o.pop()
        return o
    def get(self, rng):
        r = int(re.sub(r"\D", "", rng.split(":")[0]))
        return [self.rows[r - 1][:2]] if r <= len(self.rows) else [[]]
    def batch_update(self, body, value_input_option=None):
        r = int(body[0]["range"][1:])
        self.rows[r - 1] = [("" if v is None else v) for v in body[0]["values"][0]]
    def append_row(self, row, value_input_option=None):
        self.rows.append([("" if v is None else v) for v in row])
        n = len(self.rows)
        return {"updates": {"updatedRange": "'Call_Durations'!A%d:N%d" % (n, n)}}
    def as_values(self):                                  # what get_all_values gives: strings
        return [["" if v is None else str(v) for v in r] for r in self.rows]

ws = FakeWS(H.HEADER)
H._store.update({"ws": ws, "index": {}, "refs": {}})
c = H.app.test_client()
num = "6" + "2" * 8 + "4"                      # a made-up ten-digit number
posted = []

def post(body):
    posted.append(body)
    o = io.StringIO()
    with contextlib.redirect_stdout(o):
        r = c.post("/mo-callhook?key=Walk@Key949", json=body)
    post.log += o.getvalue()
    return r.status_code, (r.get_json() or {})
post.log = ""

def inc(ev, sid, status="bridged", talk=40):
    return {"event_type": ev, "session_id": sid, "customer_identifier": "+91" + num,
            "payload": {"id": sid, "category": "incoming", "direction": "incoming", "status": status,
                        "customer_number": "+91" + num, "duration": talk + 10, "ended_at": "2026-11-24T15:00:01.5Z",
                        "ref_id": "u-" + sid, "recording_filename": ("r-%s.mp3" % sid) if status == "bridged" else "",
                        "legs": [{"type": "customer", "result": "connected", "talk_duration": talk, "ring_duration": 6}]}}

s, j = post(inc("call.end", "15.17.1"))
check("W3 incoming call.end: 200, db=inserted, sheet=inserted", s == 200 and j.get("db") == "inserted" and j.get("sheet") == "inserted")
s, j = post(inc("call.summary", "15.17.1"))
check("W4 its call.summary: db=updated, sheet=updated", j.get("db") == "updated" and j.get("sheet") == "updated")
ow = {"event_type": "call.summary", "payload": {"id": "15.17.2", "category": "oneway", "direction": "outgoing",
      "status": "missed", "customer_number": "+91" + num, "ref_id": "u-2",
      "legs": [{"type": "customer", "result": "not_answered", "talk_duration": 0, "ring_duration": 22}]}}
s, j = post(ow)
check("W5 an app-dialled outgoing call (S935) lands in both", j.get("db") == "inserted" and j.get("sheet") == "inserted")
obd_ref = num + "_" + "20261124" + "150500"
s, j = post({"event_type": "call.end", "payload": {"category": "obd", "client_ref_id": obd_ref, "status": "answered",
             "duration": 30, "ref_id": "u-3", "legs": [{"type": "customer", "talk_duration": 25, "result": "answered"}]}})
check("W6 a dialler (OBD) call lands in both", j.get("db") == "inserted" and j.get("sheet") == "inserted")
s, j = post({"event_type": "call.end", "payload": {"category": "obd", "client_ref_id": "PROBE-WRITEPATH", "status": "probe"}})
check("W7 the write probe's call: sheet= still inserted/updated (the probe reads that key)", j.get("sheet") in ("inserted", "updated") and "row" in j)
s, j = post({"event_type": "call.end", "payload": {"category": "webcall"}})
check("W8 a call the hook does not keep: sheet=skipped, the table not written", j.get("sheet") == "skipped" and "db" not in j)

import call_log_db as cldb
try:
    trows = cldb.rows(DB)
except Exception as ex:
    trows = []
    check("W9 the table readable (%s)" % type(ex).__name__, False)
check("W9 the table holds the four kept calls, one row each", len(trows) == 4 and len(ws.rows) == 5)
sheet_by = {r[0]: r for r in ws.as_values()[1:]}
same = all([("" if t[h] is None else str(t[h])) for h in H.HEADER] == sheet_by.get(t["client_ref_id"]) for t in trows)
check("W10 every table row equals its Sheet row, all 14 fields", same)
raw_lines = sum(1 for f in os.listdir(RAW) for _ in open(os.path.join(RAW, f))) if os.path.isdir(RAW) else 0
check("W11 the raw log still keeps every event first (6 posted, 6 lines)", raw_lines == len(posted) == 6)
check("W12 the pipeline kicks unchanged (every end/summary event kicked)", os.path.isdir(QUEUE) and len(os.listdir(QUEUE)) == 6)

real_db = cldb.DB_PATH
cldb.DB_PATH = os.path.join(tmp, "no_such_dir", "calls.db")
s, j = post(inc("call.end", "15.17.9", status="missed", talk=0))
check("W13 the table cannot be written: db=deferred, the Sheet still written, 200", s == 200 and j.get("db") == "deferred"
      and j.get("sheet") == "inserted" and len(ws.rows) == 6)
check("W14 the failure is one log line naming the table, no number in it",
      "call log table write failed" in post.log and num not in post.log)
cldb.DB_PATH = real_db
try:
    import sqlite3 as _sq
    _c = _sq.connect(DB); _c.execute("ALTER TABLE call_log_raw RENAME TO moved_aside"); _c.commit(); _c.close()
    s, j = post(inc("call.end", "15.17.8", status="missed", talk=0))
    _c = _sq.connect(DB); n_new = _c.execute("SELECT COUNT(*) FROM call_log_raw").fetchone()[0]
    _c.execute("INSERT INTO call_log_raw SELECT * FROM moved_aside"); _c.execute("DROP TABLE moved_aside")
    _c.execute("DELETE FROM call_log_raw WHERE client_ref_id='IN-15.17.8'"); _c.commit(); _c.close()
    ws.rows = [r for r in ws.rows if r[0] != "IN-15.17.8"]
    check("W27 the table missing (a failed startup init): made once, the write retried -> db=inserted",
          j.get("db") == "inserted" and n_new == 1)
except Exception as ex:
    check("W27 the missing-table retry (%s)" % type(ex).__name__, False)
check("W15 no full number in any line the hook printed", num not in post.log and num not in boot)

os.environ["CALLHOOK_DB"] = "off"
o = io.StringIO()
with contextlib.redirect_stdout(o):
    H2 = load("chc_w949_off", os.path.join(H_DIR, "call_hook_capture.py"))
os.environ["CALLHOOK_DB"] = DB
H2._store.update({"ws": FakeWS(H2.HEADER), "index": {}, "refs": {}})
with contextlib.redirect_stdout(io.StringIO()):
    r2 = H2.app.test_client().post("/mo-callhook?key=Walk@Key949", json=inc("call.end", "15.17.5"))
j2 = r2.get_json() or {}
check("W16 CALLHOOK_DB=off: db=off, the Sheet written, the startup says so",
      j2.get("db") == "off" and j2.get("sheet") == "inserted" and "call log table: off" in o.getvalue())

C = load("clc_w949", os.path.join(H_DIR, "call_log_compare.py"))
C.cldb.DB_PATH = DB
far = time.time() + 3600
started = ""
cmp3 = cmp4 = {}
try:
  rows_t, started = C.read_table()
  cmp_eq = C.compare(ws.as_values(), rows_t, started, far)
  check("W17 the compare sees the deferred call as only-sheet 1 (window 5) -> DIFFER",
        cmp_eq["sheet_window"] == 5 and cmp_eq["only_sheet"] == 1 and C.verdict_of(cmp_eq) == "DIFFER")
  cldb.upsert(H.extract_record(inc("call.end", "15.17.9", status="missed", talk=0), "call.end"), DB)
  vals = ws.as_values()
  rows_t, started = C.read_table()
  cmp2 = C.compare(vals, rows_t, started, far)
  check("W18 once the table has the call: only sheet 0 (fields may differ by the capture second only)",
        cmp2["only_sheet"] == 0 and set(cmp2["differ_fields"]) <= {"captured_at_ist"})
  vals2 = [list(r) for r in ws.as_values()]
  for t in cldb.rows(DB):
      for r in vals2:
          if r[0] == t["client_ref_id"]:
              r[:] = [("" if t[h] is None else str(t[h])) for h in H.HEADER]
  cmp3 = C.compare(vals2, C.read_table()[0], started, far)
  check("W19 table = Sheet row for row -> EQUAL", C.verdict_of(cmp3) == "EQUAL" and cmp3["both"] == 5)
  vals2[2][H.HEADER.index("status")] = "changed"
  cmp4 = C.compare(vals2, C.read_table()[0], started, far)
  check("W20 one field changed on the Sheet -> DIFFER, named by field", C.verdict_of(cmp4) == "DIFFER" and cmp4["differ_fields"] == {"status": 1})
except Exception as ex:
  check("W17-20 the compare on the hook's table (%s)" % type(ex).__name__, False)

sys.path.insert(0, os.path.join(KIT, "from"))
try:
    import freshness as fr
    legs = fr.load_legs(LEGS, {"STATE_FILE": os.path.join(tmp, "fs.json")})
    byname = {l["name"]: l for l in legs}
    leg = byname.get("call log table = sheet")
    check("W21 the legs file declares 'call log table = sheet' (state_json, fail_field, 26 h)",
          bool(leg) and leg["kind"] == "state_json" and leg.get("fail_field") == "last_fail_iso" and leg["max_age_h"] == 26
          and leg["target"] == "/root/wa/call-hook/call_log_compare.state.json")
    sp = os.path.join(tmp, "cmp_state.json")
    lg = dict(leg or {"name": "x", "kind": "state_json", "max_age_h": 26, "fail_field": "last_fail_iso"}, target=sp)
    now = time.time()
    check("W22 before the first compare the leg reads NEVER (not an error)", fr.check_leg(lg, now)["verdict"] == fr.NEVER)
    C.record("EQUAL", cmp3, started, path=sp)
    r_ok = fr.check_leg(lg, time.time())
    time.sleep(1.1)
    C.record("DIFFER", cmp4, started, path=sp)
    r_bad = fr.check_leg(lg, time.time())
    check("W23 the leg: green after EQUAL, red at once after DIFFER", r_ok["verdict"] == fr.OK
          and cmp3 and r_bad["verdict"] == fr.STALE and "newest build FAILED" in r_bad["age_words"])
    st = json.load(open(sp))
    check("W24 the state file holds counts only (no key, no number)", "IN-" not in json.dumps(st) and num not in json.dumps(st))
except Exception as ex:
    check("W21-24 freshness import/judge (%s)" % ex, False)

try:
    a = json.load(open(FROM_LEGS, encoding="utf-8"))["legs"]
    b = json.load(open(LEGS, encoding="utf-8"))["legs"]
    raw_b = open(LEGS, encoding="utf-8").read()
    check("W25 the legs file: the 44 legs before it byte-equal, one appended (45)",
          len(b) == len(a) + 1 == 45 and b[:44] == a and not raw_b.endswith("\n"))
    check("W26 no six-digit run in the new leg", not re.search(r"\d{6}", json.dumps(b[-1])))
except Exception as ex:
    check("W25-26 legs (%s)" % ex, False)

shutil.rmtree(tmp, ignore_errors=True)
print("WALK %d/%d" % (ok, ok + bad))
sys.exit(0 if bad == 0 else 1)
