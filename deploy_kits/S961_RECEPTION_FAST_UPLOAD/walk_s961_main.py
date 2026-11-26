#!/usr/bin/env python3
"""S961 live-shape: the agent's real main() loop (tick 0.2 s) against a made-up server; a report saved while it runs
must arrive by the fast lane, and agent.log must hold no FAILED line. Usage: python walk_s961_main.py <reception_agent.py>"""
import http.server as hs, importlib.util, json, os, shutil, sys, tempfile, threading, time
AGENT = os.path.abspath(sys.argv[1]); fails = []
root = tempfile.mkdtemp(prefix="w961m_"); shutil.copy(AGENT, os.path.join(root, "reception_agent.py"))
spec = importlib.util.spec_from_file_location("ra961m", os.path.join(root, "reception_agent.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
home = os.path.join(root, "home"); os.makedirs(os.path.join(home, "Downloads")); os.environ["USERPROFILE"] = home
drive = os.path.join(root, "G", "My Drive"); ex = os.path.join(drive, "Clinic Records", "Docterz exports"); os.makedirs(ex)
m.find_my_drive = lambda: drive
m.windows_state = lambda force=False: None
GOT = []
class H(hs.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        if not self.path.endswith("/heartbeat"): GOT.append((time.time(), self.headers.get("X-Rx-Name")))
        raw = b'{"ok": true, "status": "TAKEN", "day": "2031-01-07"}'
        self.send_response(200); self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)
srv = hs.HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
json.dump({"server_url": "http://127.0.0.1:%d" % srv.server_address[1], "tick_seconds": 0.2, "server_jobs": False,
           "repair_drive": False, "repair_chrome_download": False, "keep_claude_running": False}, open(os.path.join(root, "config.json"), "w"))
threading.Thread(target=m.main, daemon=True).start()
time.sleep(2.0)
p = os.path.join(ex, "consultation_report_2031-01-07.csv")
open(p, "w").write("Patient Name,Consultation Date,Mode Of Payment,Amount\nW961 TEST A,07-01-2031,Cash,100\n")
saved = time.time(); t = saved - 19; os.utime(p, (t, t))      # stands still in ~1 s from now
deadline = time.time() + 15
while time.time() < deadline and not GOT: time.sleep(0.1)
log = open(os.path.join(root, "agent.log"), encoding="utf-8").read()
ok1 = len(GOT) == 1 and GOT[0][1] == "consultation_report_2031-01-07.csv"
print(("ok  " if ok1 else "FAIL"), " the real loop posts a new report at once (%s s after it was written)" % (round(GOT[0][0] - saved, 1) if GOT else "-"))
ok2 = "FAILED" not in log and "Traceback" not in log
print(("ok  " if ok2 else "FAIL"), " agent.log holds no FAILED line")
ok3 = "(at once)" in log
print(("ok  " if ok3 else "FAIL"), " agent.log says it went at once")
n = sum([ok1, ok2, ok3]); print("\n%d passed, %d failed" % (n, 3 - n)); sys.exit(0 if n == 3 else 1)
