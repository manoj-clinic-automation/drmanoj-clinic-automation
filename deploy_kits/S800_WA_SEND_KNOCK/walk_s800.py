#!/usr/bin/python3
# walk_s800.py -- kit S800_WA_SEND_KNOCK. Usage: walk_s800.py <dir holding portal/portal_inbox.py and portal/portal_wa.py> <dir holding prove_s800.py> [--control]
# Everything is MADE UP: a stand-in gateway on this machine (127.0.0.1) behaves as MyOperator's does in F-1031 -- after it has been
# idle it REFUSES (HTTP 500, x-amzn-ErrorType AuthorizerConfigurationException, {"message":null}) for a short while from the first
# request, then accepts. Nothing leaves this machine; the key is the word "real-key"; the one number is built from a counter (F-185).
# The last line is "WALK OK n/n" or "WALK RED k of n"; with --control, "CONTROL: red ..." when it is red as it must be.
import http.server, importlib, json, os, shutil, subprocess, sys, tempfile, threading, time
K, PK = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
CONTROL = "--control" in sys.argv
T = tempfile.mkdtemp(prefix="s800w.")
RES = []
def ck(name, ok, why=""):
    RES.append(bool(ok)); print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + str(why)) if (why and not ok) else ""))
COLD_FOR, IDLE_AFTER = 0.5, 1.5            # the stand-in: refuses for 0.5 s from the first request after 1.5 s of silence
S = {"mode": "cold", "last": 0.0, "burst": 0.0, "n": 0, "bodies": []}
LOCK = threading.Lock()
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        key = (self.headers.get("Authorization") or "").replace("Bearer ", "")
        with LOCK:
            now = time.time()
            if now - S["last"] > IDLE_AFTER:
                S["burst"] = now
            S["last"] = now; S["n"] += 1; S["bodies"].append(body)
            cold = (now - S["burst"]) < COLD_FOR
            m = S["mode"]
        if m == "drop":                                                # no answer at all: the outcome is unknown
            try:
                self.connection.close()
            except Exception:
                pass
            return
        if m == "backend500":                                          # the same words, but NOT from the gateway's authorizer (no header)
            self.send_response(500); out = b'{"message":null}'
        elif m == "all500" or (m == "cold" and cold):
            self.send_response(500); self.send_header("x-amzn-ErrorType", "AuthorizerConfigurationException"); out = b'{"message":null}'
        elif m == "accept":
            self.send_response(200); out = b'{"status":"success","data":{"message_id":"walk-mid-1","conversation_id":"walk-c"}}'
        elif key != "real-key":
            self.send_response(403); out = b'{"message":"Forbidden"}'
        else:
            self.send_response(400); out = b'{"status":"error","message":"customer_number is required"}'
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/chat/messages" % srv.server_address[1]
def reset(mode):
    time.sleep(IDLE_AFTER + 0.3)           # let the stand-in go idle
    with LOCK:
        S.update({"mode": mode, "n": 0, "bodies": []})
os.environ.update({"INBOX_STORE": os.path.join(T, "inbox"), "INBOX_RAW_DIR": os.path.join(T, "raw"), "PORTAL_WA_DIR": os.path.join(T, "wa")})
sys.path.insert(0, os.path.join(K, "portal"))
M = "9" + "%09d" % 79902                                               # a made-up mobile
TXT = {"type": "text", "context": {"body": "walk"}}

# ---- A. the Inbox's sender against a gateway that is cold after idle
try:
    pi = importlib.import_module("portal_inbox")
    ck("A1 portal_inbox imports from the given folder", os.path.dirname(os.path.abspath(pi.__file__)) == os.path.join(K, "portal"))
    pi.API_URL = URL
    if hasattr(pi, "S800_WAITS"):
        pi.S800_WAITS = (0.7, 0.7, 0.7, 0.7)
    reset("cold"); tr = {}
    ok, mid, err = pi.myop_send("real-key", M, TXT, trace=tr)
    ck("A2 from cold: the first try is refused, the second is not (the stand-in's HTTP 400)", tr.get("attempts") == ["500A", "400"] and not pi.gateway_refusal(tr), tr.get("attempts") or tr.get("status"))
    tr = {}
    pi.myop_send("real-key", M, TXT, trace=tr)
    ck("A3 warm: one try only", tr.get("attempts") == ["400"] and S["n"] == 3, (tr.get("attempts"), S["n"]))
    reset("all500"); tr = {}; t0 = time.time()
    ok, mid, err = pi.myop_send("real-key", M, TXT, trace=tr)
    ck("A4 refused every time: five tries, then it is still a gateway refusal (so the S666 queue takes it as before)",
       tr.get("attempts") == ["500A"] * 5 and pi.gateway_refusal(tr) and not ok and S["n"] == 5 and time.time() - t0 >= 2.7, (tr.get("attempts"), S["n"]))
    reset("accept"); tr = {}
    ok, mid, err = pi.myop_send("real-key", M, TXT, trace=tr)
    ck("A5 accepted: sent ONCE -- never a second request after an acceptance", ok and mid == "walk-mid-1" and S["n"] == 1 and tr.get("attempts") == ["200"], (ok, S["n"]))
    reset("cold")
    with LOCK:
        S["mode"] = "cold-then-accept"
    # cold first, then a real acceptance: exactly one accepted request
    S["mode"] = "cold"; tr = {}
    def flip():
        time.sleep(COLD_FOR + 0.05)
        with LOCK:
            S["mode"] = "accept"
    threading.Thread(target=flip, daemon=True).start()
    ok, mid, err = pi.myop_send("real-key", M, TXT, trace=tr)
    ck("A6 refused then accepted: the message goes once (two requests, the second the only one accepted)", ok and tr.get("attempts") == ["500A", "200"] and S["n"] == 2, (tr.get("attempts"), S["n"]))
    reset("backend500"); tr = {}
    ok, mid, err = pi.myop_send("real-key", M, TXT, trace=tr)
    ck("A6b an HTTP 500 that is NOT the gateway's (no authorizer header) is not tried again", (not ok) and tr.get("attempts") == ["500"] and S["n"] == 1 and not pi.gateway_refusal(tr), (tr.get("attempts"), S["n"]))
    reset("cold"); tr = {}
    def drop():
        time.sleep(COLD_FOR + 0.05)
        with LOCK:
            S["mode"] = "drop"
    threading.Thread(target=drop, daemon=True).start()
    ok, mid, err = pi.myop_send("real-key", M, TXT, timeout=3, trace=tr)
    ck("A6c refused, then NO ANSWER on the next try: the caller is told 'unknown', not 'refused' (so the queue never sends it again)",
       (not ok) and tr.get("attempts") == ["500A", "none"] and not pi.gateway_refusal(tr) and S["n"] == 2, (tr.get("attempts"), tr.get("status"), S["n"]))
    pi.API_URL = "http://127.0.0.1:9/chat/messages"; tr = {}
    ok, mid, err = pi.myop_send("real-key", M, TXT, timeout=3, trace=tr)
    ck("A7 no answer at all is NOT tried again (its outcome is unknown)", (not ok) and tr.get("attempts") == ["none"], tr.get("attempts"))
    pi.API_URL = URL
    ck("A8 the retry queue's own sender is the new one", pi.run_retries.__defaults__ == (None,) and "myop_send" in pi.run_retries.__code__.co_names)
except Exception as e:  # noqa: BLE001
    ck("A the Inbox sender", False, repr(e)[:170])

# ---- B. the portal's template sender
try:
    pw = importlib.import_module("portal_wa")
    pw.BASE = URL.rsplit("/chat/messages", 1)[0]
    if hasattr(pw, "S800_WAITS"):
        pw.S800_WAITS = (0.7, 0.7, 0.7, 0.7)
    reset("cold")
    r = pw.send(M, "drmanoj_post_visit", {"1": "Walk"}, "walk", "real-key", dry_run=False)
    ck("B1 from cold: refused, then not (HTTP 400 from the stand-in on the second try)", (not r["ok"]) and "HTTP 400" in r.get("error", "") and r.get("tries") == 2 and S["n"] == 2, (r.get("error", "")[:60], r.get("tries"), S["n"]))
    reset("all500")
    r = pw.send(M, "drmanoj_post_visit", {"1": "Walk"}, "walk", "real-key", dry_run=False)
    ck("B2 refused every time: five tries, the refusal is reported", (not r["ok"]) and r.get("error", "").startswith("HTTP 500") and r.get("tries") == 5 and S["n"] == 5, (r.get("tries"), S["n"]))
    reset("accept")
    r = pw.send(M, "drmanoj_post_visit", {"1": "Walk"}, "walk", "real-key", dry_run=False)
    ck("B3 accepted: sent ONCE", r["ok"] and r.get("message_id") == "walk-mid-1" and S["n"] == 1 and "tries" not in r, (r.get("ok"), S["n"]))
    reset("backend500")
    r = pw.send(M, "drmanoj_post_visit", {"1": "Walk"}, "walk", "real-key", dry_run=False)
    ck("B3b an HTTP 500 {\"message\":null} WITHOUT the authorizer's header is not tried again", (not r["ok"]) and S["n"] == 1 and "tries" not in r, (S["n"], r.get("tries")))
    ck("B3c what the caller gets back carries no private key of the kit", "_gateway_refused" not in r and set(r) <= {"ok", "message_id", "conversation_id", "mode", "error", "tries"}, sorted(r))
    reset("cold")
    r = pw.send(M, "drmanoj_post_visit", {"1": "Walk"}, "walk", "real-key", dry_run=True)
    ck("B4 test mode still sends nothing", r["mode"] == "DRY" and S["n"] == 0)
    body = json.loads(S["bodies"][0]) if S["bodies"] else None
    ck("B5 the template sender's log has one row per send (not one per try)", sum(1 for _ in open(pw.LOG, encoding="utf-8")) == 1 + 5, "rows")
except Exception as e:  # noqa: BLE001
    ck("B the template sender", False, repr(e)[:170])

# ---- C. the proof the installer runs, against the stand-in
ENV = dict(os.environ, S800_API_URL=URL, S800_TOKEN="real-key", S800_WAITS="0.7,0.7,0.7,0.7", S800_IDLE="2", S800_CYCLES="3")
def prove(mode, *args):
    reset(mode)
    r = subprocess.run([sys.executable, "-B", os.path.join(PK, "prove_s800.py"), os.path.join(K, "portal")] + list(args), env=ENV, capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]
try:
    rc, last = prove("cold");   ck("C1 a cold gateway: PROVEN", rc == 0 and last.startswith("PROVE: PROVEN"), last)
    rc, last = prove("all500"); ck("C2 a gateway that refuses every try: FAILED", rc == 1 and last.startswith("PROVE: FAILED"), last)
    rc, last = prove("warm");   ck("C3 a gateway that never refuses: WARM after three calls", rc == 3 and last.startswith("PROVE: WARM"), last)
    rc, last = prove("backend500"); ck("C3b an answer that is not the proper 400 is never taken for proof", rc == 1 and last.startswith("PROVE: FAILED"), last)
    rc, last = prove("cold", "--installed"); ck("C4 the installed check: not refused at the end", rc == 0 and "not refused" in last, last)
    ck("C5 every request of the proof carried an empty number and empty text", S["bodies"] and all(
        json.loads(b).get("customer_number") == "" and json.loads(b)["data"]["context"].get("body") == "" for b in S["bodies"]))
    ck("C6 the proof prints no key", "real-key" not in last)
except Exception as e:  # noqa: BLE001
    ck("C the proof", False, repr(e)[:170])

# ---- D. the files
try:
    ti = open(os.path.join(K, "portal", "portal_inbox.py"), encoding="utf-8").read()
    tw = open(os.path.join(K, "portal", "portal_wa.py"), encoding="utf-8").read()
    ck("D1 portal_inbox.py: one sender for the callers, one single try beneath it", ti.count("def myop_send(") == 1 and ti.count("def _myop_send_once(") == 1 and ti.count("S800_WAITS = (2.5, 3.0, 4.0, 6.0)") == 1)
    ck("D2 portal_wa.py: the one request moved whole, tried again only on a refusal", tw.count("urlopen(") == 1 and tw.count("def _s800_once(") == 1 and tw.count("S800_WAITS = (2.5, 3.0, 4.0, 6.0)") == 1)
    import py_compile
    for n in ("portal_inbox.py", "portal_wa.py"):
        py_compile.compile(os.path.join(K, "portal", n), cfile=os.path.join(T, n + "c"), doraise=True)
    ck("D3 both files compile", True)
except Exception as e:  # noqa: BLE001
    ck("D the files", False, repr(e)[:170])

srv.shutdown(); shutil.rmtree(T, ignore_errors=True)
bad = RES.count(False)
if CONTROL:
    print("CONTROL: red (%d of %d)" % (bad, len(RES)) if bad else "CONTROL: GREEN -- the control did not go red")
else:
    print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))
