#!/usr/bin/env python3
"""S961 walk -- the fast report lane of the reception agent, offline, on made-up
files and a made-up server on this machine. Usage: python walk_s961.py <reception_agent.py>
Run against S456.1 it must go RED (the control); against S961.1 every check green."""
import http.server as hs, importlib.util, json, os, shutil, socket, sys, tempfile, threading, time
AGENT = os.path.abspath(sys.argv[1])
PASS, FAIL = [], []
def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("%s  %s%s" % ("ok  " if cond else "FAIL", name, ("  -- " + str(detail)) if detail and not cond else ""))
def put(path, text, age=10):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    t = time.time() - age
    os.utime(path, (t, t))

root = tempfile.mkdtemp(prefix="w961_")
shutil.copy(AGENT, os.path.join(root, "reception_agent.py"))
spec = importlib.util.spec_from_file_location("ra961", os.path.join(root, "reception_agent.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
home = os.path.join(root, "home"); dl = os.path.join(home, "Downloads"); os.makedirs(dl)
os.environ["USERPROFILE"] = home
drive = os.path.join(root, "G", "My Drive"); ex = os.path.join(drive, "Clinic Records", "Docterz exports")
os.makedirs(ex); os.makedirs(os.path.join(drive, "Clinic Data Archive"))
m.find_my_drive = lambda: drive
m.ensure_dirs()

GOT = {"beats": 0, "reports": [], "down": False, "rdown": False}
class H(hs.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        if GOT["down"] or (GOT["rdown"] and not self.path.endswith("/heartbeat")):
            out, code = {"ok": False, "status": "NOT_READY"}, 503
        elif self.path.endswith("/heartbeat"):
            GOT["beats"] += 1; out, code = {"ok": True, "status": "KEPT"}, 200
        else:
            GOT["reports"].append(self.headers.get("X-Rx-Name")); out, code = {"ok": True, "status": "TAKEN", "day": "2031-01-07"}, 200
        raw = json.dumps(out).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)
srv = hs.HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
json.dump({"server_url": "http://127.0.0.1:%d" % srv.server_address[1]}, open(os.path.join(root, "config.json"), "w"))
cfg = m.load_config()
CONS = "Patient Name,Consultation Date,Mode Of Payment,Amount\nW961 TEST A,07-01-2031,Cash,100\n"
FOLL = "Appointment ID,Patient Name,Mobile No,Due Date\nW1,W961 TEST B,x,09-01-2031\n"
put(os.path.join(ex, "consultation_report_2031-01-06.csv"), CONS, age=3600)

st = m.new_state()
try:
    # 1. nothing before the server has answered a heartbeat
    m.fast_pass(st, cfg); m.fast_pass(st, cfg)
    check("1 no fast post before the server has answered a heartbeat", GOT["reports"] == [] and GOT["beats"] == 0)
    # 2. the heartbeat's own pass still sends (the fallback), then the first look only learns
    beat, _ = m.build_beat(st, cfg); st["my_drive"] = beat.get("my_drive"); m.direct_pass(st, cfg, beat)
    check("2 the heartbeat pass sends the waiting report (the fallback road kept)", GOT["beats"] == 1 and len(GOT["reports"]) == 1)
    m.fast_pass(st, cfg)
    check("3 the first look after a start posts nothing and learns the folders", len(GOT["reports"]) == 1 and st["fast"]["sig"] is not None)
    # 3. a new export: settling first, then at once
    p = os.path.join(ex, "consultation_report_2031-01-07.csv"); put(p, CONS + "W961 TEST C,07-01-2031,UPI,200\n", age=3)
    m.fast_pass(st, cfg)
    check("4 a report saved 3 s ago is not posted yet (still settling)", len(GOT["reports"]) == 1 and st["fast"]["again"])
    t = time.time() - 30; os.utime(p, (t, t))
    m.fast_pass(st, cfg)
    check("5 once it has stood still it is posted at once, on the next tick", GOT["reports"][-1:] == ["consultation_report_2031-01-07.csv"] and len(GOT["reports"]) == 2, GOT["reports"])
    check("6 the counters say it went at once, and how long after it was saved", st["upload"]["fast_sent"] == 1 and 25 <= (st["upload"]["fast_last_after_save_s"] or 0) <= 60)
    m.fast_pass(st, cfg); m.fast_pass(st, cfg)
    check("7 a quiet folder posts nothing more", len(GOT["reports"]) == 2)
    # 4. other files: never posted
    put(os.path.join(dl, "RAMKALI DEVI report.csv"), CONS, age=60); put(os.path.join(dl, "notes.txt"), "x", age=60)
    m.fast_pass(st, cfg)
    check("8 a file that is not a Docterz report by name is not posted", len(GOT["reports"]) == 2)
    check("9 ... and the tick's look never opened it", not any("RAMKALI" in k[0] for k in st["upload_cache"]))
    # 5. Downloads too, and the cap of two per pass
    for i in (1, 2, 3):
        put(os.path.join(dl, "followup_logs (%d).csv" % i), FOLL + "W%d,W961 TEST F%d,x,09-01-2031\n" % (i, i), age=40)
    m.fast_pass(st, cfg)
    check("10 three new exports: two in this tick (the cap) and it looks again", len(GOT["reports"]) == 4 and st["fast"]["again"], GOT["reports"])
    m.fast_pass(st, cfg)
    check("11 the third goes on the very next tick", len(GOT["reports"]) == 5)
    # 6. a re-save of the same name with new rows is a new export
    put(p, CONS + "W961 TEST C,07-01-2031,UPI,200\nW961 TEST D,07-01-2031,Cash,300\n", age=30)
    m.fast_pass(st, cfg)
    check("12 the same file saved again with more rows is posted again", len(GOT["reports"]) == 6)
    # 7. the server refuses: hold a minute, then try again
    GOT["down"] = True
    put(os.path.join(ex, "consultation_report_2031-01-08.csv"), CONS + "W961 TEST E,08-01-2031,Cash,1\n", age=30)
    m.fast_pass(st, cfg)
    n_down = len(GOT["reports"])
    check("13 a refused post sets a hold and keeps the report waiting", st["fast"]["hold_until"] > time.time() + 50 and st["upload"]["fast_sent"] == 5)
    GOT["down"] = False
    m.fast_pass(st, cfg); m.fast_pass(st, cfg)
    check("14 during the hold nothing is tried", len(GOT["reports"]) == n_down)
    st["fast"]["hold_until"] = 0
    m.fast_pass(st, cfg)
    check("15 after the hold it is posted", GOT["reports"][-1] == "consultation_report_2031-01-08.csv" and st["upload"]["fast_sent"] == 6)
    # 8. a failed heartbeat stops the fast lane until the next good one
    st["upload"]["fail_streak"] = 2
    put(os.path.join(ex, "consultation_report_2031-01-09.csv"), CONS + "W961 TEST G,09-01-2031,Cash,1\n", age=30)
    n = len(GOT["reports"]); m.fast_pass(st, cfg)
    check("16 while heartbeats fail the fast lane waits for the 5-minute pass", len(GOT["reports"]) == n)
    st["upload"]["fail_streak"] = 0; m.fast_pass(st, cfg)
    check("17 ... and sends once the server answers again", len(GOT["reports"]) == n + 1)
    # 9. switched off in config
    json.dump({"server_url": "http://127.0.0.1:%d" % srv.server_address[1], "fast_upload": False}, open(os.path.join(root, "config.json"), "w"))
    cfg2 = m.load_config()
    put(os.path.join(ex, "consultation_report_2031-01-10.csv"), CONS + "W961 TEST H,10-01-2031,Cash,1\n", age=30)
    n = len(GOT["reports"]); m.fast_pass(st, cfg2)
    check("18 fast_upload false in config.json: nothing at once", len(GOT["reports"]) == n)
    # 10. the next heartbeat pass does not send any of them twice; the beat says it all without names
    beat, _ = m.build_beat(st, cfg); m.direct_pass(st, cfg, beat)
    check("19 the heartbeat pass sends only what the fast lane had not (one), nothing twice", len(GOT["reports"]) == n + 1 and len(set(GOT["reports"])) == len(GOT["reports"]) - 1, GOT["reports"])
    du = beat["direct_upload"]
    check("20 the heartbeat carries the fast-lane counts", du.get("at_once") is True and du.get("sent_at_once_since_start") == 7 and du.get("last_seconds_after_save") is not None)
    hb = json.dumps(beat)
    check("21 the heartbeat carries no file name and no patient text", "W961" not in hb and "consultation_report" not in hb and ".csv" not in hb)
    # 11. the main loop: fast_pass on every tick, skipped when switched off, before the update check
    src = open(AGENT, encoding="utf-8").read(); main = src[src.index("def main():"):src.index("def install_keys")]
    i_fast, i_upd = main.find("fast_pass(st, cfg)"), main.find("take_update()")
    check("22 the main loop calls the fast lane every tick, only when not switched off", 0 < i_fast < i_upd and main.rfind("if not off:", 0, i_fast) > main.rfind("time.sleep", 0, i_fast))
    check("23 the agent says S961.1", m.AGENT_VERSION == "S961.1")
    # 12. the cold review's SHOULDs (S528)
    json.dump({"server_url": "http://127.0.0.1:%d" % srv.server_address[1]}, open(os.path.join(root, "config.json"), "w"))
    cfg = m.load_config(); st["fast"]["hold_until"] = 0; st["fast"]["fails"] = 0
    m.fast_pass(st, cfg); m.fast_pass(st, cfg)
    q = os.path.join(ex, "consultation_report_2031-01-11.csv"); put(q, CONS + "W961 TEST J,11-01-2031,Cash,1\n", age=30)
    os.chmod(q, 0)
    n = len(GOT["reports"]); m.fast_pass(st, cfg)
    check("24 a report that cannot be read yet is not posted and is looked at again", len(GOT["reports"]) == n and st["fast"]["again"])
    os.chmod(q, 0o644); m.fast_pass(st, cfg)
    check("25 ... and goes on the next tick once it can be read", len(GOT["reports"]) == n + 1)
    GOT["rdown"] = True
    put(os.path.join(ex, "consultation_report_2031-01-12.csv"), CONS + "W961 TEST K,12-01-2031,Cash,1\n", age=30)
    beat, _ = m.build_beat(st, cfg); m.direct_pass(st, cfg, beat)
    check("26 a refused post in the heartbeat lane hands over to the fast lane", st["fast"]["again"] is True)
    GOT["rdown"] = False; st["fast"]["hold_until"] = 0
    n = len(GOT["reports"]); m.fast_pass(st, cfg)
    check("27 ... which posts it with no change in the folder", len(GOT["reports"]) == n + 1)
    calls = {"n": 0}; real = m.report_pass
    def counting(*a, **k):
        calls["n"] += 1; return real(*a, **k)
    m.report_pass = counting
    put(os.path.join(ex, "consultation_report_2031-01-13.csv"), CONS + "W961 TEST L,13-01-2031,Cash,1\n", age=-600)
    m.fast_pass(st, cfg); m.fast_pass(st, cfg); m.fast_pass(st, cfg)
    check("28 a file dated in the future is not waited on every tick", calls["n"] <= 1 and not st["fast"]["again"], calls)
    m.report_pass = real
    os.remove(os.path.join(ex, "consultation_report_2031-01-13.csv")); m.fast_pass(st, cfg)
    GOT["down"] = True
    put(os.path.join(ex, "consultation_report_2031-01-14.csv"), CONS + "W961 TEST M,14-01-2031,Cash,1\n", age=30)
    m.fast_pass(st, cfg); h1 = st["fast"]["hold_until"] - time.time()
    st["fast"]["hold_until"] = 0; m.fast_pass(st, cfg); h2 = st["fast"]["hold_until"] - time.time()
    check("29 repeated refusals wait longer each time", 50 < h1 < 70 and 110 < h2 < 130, (h1, h2))
    GOT["down"] = False; st["fast"]["hold_until"] = 0; m.fast_pass(st, cfg)
    check("30 ... and the wait resets after a success", st["fast"]["fails"] == 0)
    json.dump({"server_url": "http://127.0.0.1:%d" % srv.server_address[1], "upload_max_files": 1}, open(os.path.join(root, "config.json"), "w"))
    cfg1 = m.load_config(); real_w = m._sent_write; m._sent_write = lambda s: False
    put(os.path.join(ex, "consultation_report_2031-01-15.csv"), CONS + "W961 TEST N,15-01-2031,Cash,1\n", age=30)
    n = len(GOT["reports"])
    for _ in range(5):
        m.fast_pass(st, cfg1)
    check("31 a ledger that cannot be written does not post the same bytes on every tick", len(GOT["reports"]) == n + 1 and st["fast"]["hold_until"] > time.time())
    m._sent_write = real_w
except Exception as ex_:                                        # the control (S456.1) lands here
    check("the fast lane exists and runs", False, "%s: %s" % (ex_.__class__.__name__, ex_))
srv.shutdown()
print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
sys.exit(1 if FAIL else 0)
