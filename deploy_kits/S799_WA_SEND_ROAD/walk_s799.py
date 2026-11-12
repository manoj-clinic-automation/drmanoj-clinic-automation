#!/usr/bin/python3
# walk_s799.py -- kit S799_WA_SEND_ROAD. Usage: walk_s799.py <dir holding portal/portal_inbox.py and portal/portal_wa.py> <dir holding probe_s799.py> [--control]
# Everything is MADE UP: a stand-in gateway runs on this machine (127.0.0.1) and answers the way MyOperator's does in F-1031 --
# HTTP 500 with x-amzn-ErrorType AuthorizerConfigurationException to urllib's own User-Agent. Nothing leaves this machine; the key
# is the word "real-key"; the one number is built from a counter (F-185). Prints ok/BAD only.
# The last line is "WALK OK n/n" or "WALK RED k of n"; with --control, "CONTROL: red ..." when it is red as it must be.
import http.server, importlib, json, os, shutil, subprocess, sys, tempfile, threading
K, PK = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
CONTROL = "--control" in sys.argv
T = tempfile.mkdtemp(prefix="s799w.")
RES = []
def ck(name, ok, why=""):
    RES.append(bool(ok)); print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + str(why)) if (why and not ok) else ""))
STATE = {"mode": "ua", "seen": []}
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0); body = self.rfile.read(n)
        ua = self.headers.get("User-Agent") or ""; key = (self.headers.get("Authorization") or "").replace("Bearer ", "")
        STATE["seen"].append({"ua": ua, "conn": (self.headers.get("Connection") or "").lower(), "body": body})
        m = STATE["mode"]
        bad = (m == "all500") or (m == "ua" and ua.startswith("Python-urllib")) or (m == "client" and (self.headers.get("Connection") or "").lower() == "close")
        if bad:
            self.send_response(500); self.send_header("x-amzn-ErrorType", "AuthorizerConfigurationException"); self.send_header("Content-Type", "application/json")
            out = b'{"message":null}'
        elif key != "real-key":
            self.send_response(403); self.send_header("Content-Type", "application/json"); out = b'{"message":"Forbidden"}'
        else:
            self.send_response(400); self.send_header("Content-Type", "application/json"); out = b'{"status":"error","message":"customer_number is required"}'
        self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/chat/messages" % srv.server_address[1]
ENV = dict(os.environ, S799_API_URL=URL, S799_TOKEN="real-key", S799_COMPANY="walk-company", S799_PNID="walk-pnid", S799_ROUNDS="3", S799_GAP="0",
           S799_PORTAL_DIR=os.path.join(K, "portal"), INBOX_STORE=os.path.join(T, "inbox"), INBOX_RAW_DIR=os.path.join(T, "raw"), PORTAL_WA_DIR=os.path.join(T, "wa"))
def probe(mode, *args):
    STATE["mode"] = mode
    r = subprocess.run([sys.executable, "-B", os.path.join(PK, "probe_s799.py")] + list(args), env=ENV, capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout

# ---- A. the probe judges a stand-in gateway rightly, four ways
try:
    rc, out = probe("ua")
    ck("A1 urllib's own User-Agent refused, a plain one accepted -> DECISIVE-UA", "VERDICT: DECISIVE-UA" in out, out[-300:])
    ck("A2 the table shows way 1 as 500A and way 2 as 400 on the real key", "500A 500A 500A" in out and "400 400 400" in out)
    ck("A3 the probe prints no key", "real-key" not in out and "made-up-key" not in out)
    rc, out = probe("client")
    ck("A4 urllib refused even with a plain User-Agent, http.client accepted -> DECISIVE-CLIENT (no automatic fix)", "VERDICT: DECISIVE-CLIENT" in out, out[-300:])
    rc, out = probe("all500")
    ck("A5 every way refused -> NOT-DECISIVE", "VERDICT: NOT-DECISIVE" in out, out[-200:])
    rc, out = probe("ok")
    ck("A6 nothing refused -> NOT-DECISIVE", "VERDICT: NOT-DECISIVE" in out, out[-200:])
    ck("A7 every probe request carried an empty number and empty text", STATE["seen"] and all(
        json.loads(s["body"]).get("customer_number") == "" and json.loads(s["body"])["data"]["context"].get("body") == "" for s in STATE["seen"]))
except Exception as e:  # noqa: BLE001
    ck("A the probe", False, repr(e)[:160])

# ---- B. the two senders of the given folder, against the gateway that refuses urllib's own User-Agent
os.environ.update({"INBOX_STORE": os.path.join(T, "inbox"), "INBOX_RAW_DIR": os.path.join(T, "raw"), "PORTAL_WA_DIR": os.path.join(T, "wa")})
sys.path.insert(0, os.path.join(K, "portal"))
M = "9" + "%09d" % 79901                                               # a made-up mobile
try:
    pi = importlib.import_module("portal_inbox")
    ck("B1 portal_inbox imports from the given folder", os.path.dirname(os.path.abspath(pi.__file__)) == os.path.join(K, "portal"))
    pi.API_URL = URL; STATE["mode"] = "ua"; STATE["seen"] = []
    tr = {}
    ok, mid, err = pi.myop_send("real-key", M, {"type": "text", "context": {"body": "walk"}}, trace=tr)
    ck("B2 the Inbox sender is NOT refused at the gateway (HTTP 400 from the stand-in, not 500)", str(tr.get("status")) == "400" and not pi.gateway_refusal(tr), tr.get("status"))
    ck("B3 it named the plain User-Agent", STATE["seen"] and STATE["seen"][-1]["ua"] == "clinic-portal/1.0", STATE["seen"][-1]["ua"] if STATE["seen"] else "")
    STATE["mode"] = "all500"; tr = {}
    pi.myop_send("real-key", M, {"type": "text", "context": {"body": "walk"}}, trace=tr)
    ck("B4 a real refusal is still seen as one (the retry rule stands)", pi.gateway_refusal(tr))
except Exception as e:  # noqa: BLE001
    ck("B the Inbox sender", False, repr(e)[:160])
try:
    pw = importlib.import_module("portal_wa")
    pw.BASE = URL.rsplit("/chat/messages", 1)[0]; STATE["mode"] = "ua"; STATE["seen"] = []
    r = pw.send(M, "drmanoj_post_visit", {"1": "Walk"}, "walk", "real-key", dry_run=False)
    ck("C1 the template sender is NOT refused at the gateway (HTTP 400, not 500)", (not r["ok"]) and "HTTP 400" in r.get("error", ""), r.get("error", "")[:80])
    ck("C2 it named the plain User-Agent", STATE["seen"] and STATE["seen"][-1]["ua"] == "clinic-portal/1.0")
    r = pw.send(M, "drmanoj_post_visit", {"1": "Walk"}, "walk", "real-key", dry_run=True)
    ck("C3 test mode still sends nothing", r["mode"] == "DRY" and len(STATE["seen"]) == 1)
except Exception as e:  # noqa: BLE001
    ck("C the template sender", False, repr(e)[:160])

# ---- D. the files
try:
    for name in ("portal_inbox.py", "portal_wa.py"):
        t = open(os.path.join(K, "portal", name), encoding="utf-8").read()
        ck("D %s: the one new line, once" % name, t.count('req.add_header("User-Agent", "clinic-portal/1.0")') == 1)
        import py_compile
        py_compile.compile(os.path.join(K, "portal", name), cfile=os.path.join(T, name + "c"), doraise=True)
    ck("D both files compile", True)
except Exception as e:  # noqa: BLE001
    ck("D the files", False, repr(e)[:160])

srv.shutdown(); shutil.rmtree(T, ignore_errors=True)
bad = RES.count(False)
if CONTROL:
    print("CONTROL: red (%d of %d)" % (bad, len(RES)) if bad else "CONTROL: GREEN -- the control did not go red")
else:
    print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))
