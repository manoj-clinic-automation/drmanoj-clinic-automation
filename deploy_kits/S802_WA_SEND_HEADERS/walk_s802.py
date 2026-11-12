#!/usr/bin/python3
# walk_s802.py -- kit S802_WA_SEND_HEADERS. Usage: walk_s802.py <dir holding portal/portal_inbox.py and portal/portal_wa.py> <dir holding prove_s802.py> [--control]
# Everything is MADE UP: a stand-in gateway on this machine (127.0.0.1) behaves the way both of today's live runs fit --
#   * its "authorizer" fails (HTTP 500, x-amzn-ErrorType AuthorizerConfigurationException, {"message":null}) unless the company
#     header arrives named exactly "X-MYOP-COMPANY-ID" (or all lower-case);
#   * an authorisation, once given or denied, is kept per key for a short while and the authorizer is not asked again.
# Nothing leaves this machine; the real key is the word "real-key"; the one number is built from a counter (F-185).
# The last line is "WALK OK n/n" or "WALK RED k of n"; with --control, "CONTROL: red ..." when it is red as it must be.
import http.server, importlib, json, os, shutil, subprocess, sys, tempfile, threading, time
K, PK = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
CONTROL = "--control" in sys.argv
T = tempfile.mkdtemp(prefix="s802w.")
RES = []
def ck(name, ok, why=""):
    RES.append(bool(ok)); print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + str(why)) if (why and not ok) else ""))
TTL = 1.5
S = {"mode": "validate", "cache": {}, "n": 0, "names": [], "auths": []}
LOCK = threading.Lock()
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        names = list(self.headers.keys()); tok = self.headers.get("Authorization") or ""
        with LOCK:
            S["n"] += 1; S["names"].append(names); m = S["mode"]; now = time.time()
            hit = S["cache"].get(tok); hit = hit if (hit and now - hit[1] < TTL) else None
        if m == "drop":
            try:
                self.connection.close()
            except Exception:
                pass
            return
        verdict = hit[0] if hit else None
        if verdict is None:                                            # the authorizer is asked
            cased_ok = ("X-MYOP-COMPANY-ID" in names) or ("x-myop-company-id" in names) or m == "lenient"
            if m == "crash" or not cased_ok:
                out = b'{"message":null}'
                self.send_response(500); self.send_header("x-amzn-ErrorType", "AuthorizerConfigurationException")
                self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)
                return
            verdict = "allow" if tok == "Bearer real-key" else "deny"
            with LOCK:
                S["cache"][tok] = (verdict, time.time())
        if verdict == "deny":
            self.send_response(403); out = b'{"message":"Forbidden"}'
        elif m == "accept":
            self.send_response(200); out = b'{"status":"success","data":{"message_id":"walk-mid-1","conversation_id":"walk-c"}}'
        else:
            self.send_response(400); out = b'{"status":"error","message":"customer_number is required"}'
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/chat/messages" % srv.server_address[1]
def reset(mode):
    with LOCK:
        S.update({"mode": mode, "cache": {}, "n": 0, "names": []})
os.environ.update({"INBOX_STORE": os.path.join(T, "inbox"), "INBOX_RAW_DIR": os.path.join(T, "raw"), "PORTAL_WA_DIR": os.path.join(T, "wa")})
sys.path.insert(0, os.path.join(K, "portal"))
M = "9" + "%09d" % 79903                                               # a made-up mobile
TXT = {"type": "text", "context": {"body": "walk"}}

# ---- A. the Inbox's sender
try:
    pi = importlib.import_module("portal_inbox")
    ck("A1 portal_inbox imports from the given folder", os.path.dirname(os.path.abspath(pi.__file__)) == os.path.join(K, "portal"))
    pi.API_URL = URL
    reset("validate"); tr = {}
    ok, mid, err = pi.myop_send("real-key", M, TXT, trace=tr)
    ck("A2 the real key, nothing kept at the gateway: let through at the first try (the stand-in's HTTP 400, not 500)", str(tr.get("status")) == "400" and not pi.gateway_refusal(tr) and S["n"] == 1, (tr.get("status"), S["n"]))
    ck("A3 the company header left exactly as written", "X-MYOP-COMPANY-ID" in S["names"][-1] and "X-Myop-Company-Id" not in S["names"][-1], S["names"][-1])
    ck("A4 the caller's trace is whole and carries no key", all(k in tr for k in ("status", "raw", "headers", "ms", "endpoint", "request_json")) and "real-key" not in json.dumps(tr), sorted(tr))
    reset("validate"); tr = {}
    pi.myop_send("walk-made-up-key", M, TXT, trace=tr)
    ck("A5 a made-up key gets the proper 'not authorised' (403), not 500", str(tr.get("status")) == "403", tr.get("status"))
    reset("accept"); tr = {}
    ok, mid, err = pi.myop_send("real-key", M, TXT, trace=tr)
    ck("A6 accepted: sent ONCE, the message id returned", ok and mid == "walk-mid-1" and S["n"] == 1, (ok, mid, S["n"]))
    reset("crash"); tr = {}
    ok, mid, err = pi.myop_send("real-key", M, TXT, trace=tr)
    ck("A7 a refusal at the gateway is still seen as one -- ONE try, then the S666 queue's rule holds", (not ok) and pi.gateway_refusal(tr) and S["n"] == 1, (tr.get("status"), S["n"]))
    reset("drop"); tr = {}
    ok, mid, err = pi.myop_send("real-key", M, TXT, timeout=3, trace=tr)
    ck("A8 no answer at all: 'could not reach', one try, not a refusal", (not ok) and "could not reach" in err and S["n"] == 1 and not pi.gateway_refusal(tr) and str(tr.get("raw", "")).startswith("no answer"), (err, S["n"]))
    pi.API_URL = "http://127.0.0.1:9/chat/messages"; tr = {}
    ok, mid, err = pi.myop_send("real-key", M, TXT, timeout=3, trace=tr)
    ck("A9 nobody listening: 'could not reach'", (not ok) and "could not reach" in err, err)
    pi.API_URL = URL
except Exception as e:  # noqa: BLE001
    ck("A the Inbox sender", False, repr(e)[:170])

# ---- B. the portal's template sender
try:
    pw = importlib.import_module("portal_wa")
    pw.BASE = URL.rsplit("/chat/messages", 1)[0]
    reset("validate")
    r = pw.send(M, "drmanoj_post_visit", {"1": "Walk"}, "walk", "real-key", dry_run=False)
    ck("B1 the real key, nothing kept at the gateway: let through at the first try (HTTP 400 from the stand-in)", (not r["ok"]) and r.get("error", "").startswith("HTTP 400") and S["n"] == 1, (r.get("error", "")[:50], S["n"]))
    ck("B2 the company header left exactly as written", "X-MYOP-COMPANY-ID" in S["names"][-1], S["names"][-1])
    reset("accept")
    r = pw.send(M, "drmanoj_post_visit", {"1": "Walk"}, "walk", "real-key", dry_run=False)
    ck("B3 accepted: sent ONCE, the ids returned", r["ok"] and r.get("message_id") == "walk-mid-1" and r.get("conversation_id") == "walk-c" and S["n"] == 1, (r, S["n"]))
    reset("crash")
    r = pw.send(M, "drmanoj_post_visit", {"1": "Walk"}, "walk", "real-key", dry_run=False)
    ck("B4 a refusal is reported in the same words as before, after ONE try", (not r["ok"]) and r.get("error") == 'HTTP 500: {"message":null}' and S["n"] == 1, (r.get("error"), S["n"]))
    reset("validate")
    r = pw.send(M, "drmanoj_post_visit", {"1": "Walk"}, "walk", "real-key", dry_run=True)
    ck("B5 test mode still sends nothing", r["mode"] == "DRY" and S["n"] == 0)
    ck("B6 what the caller gets back has the same keys as before", set(r) == {"ok", "message_id", "conversation_id", "mode", "error"}, sorted(r))
    ck("B7 the log has one row per send", sum(1 for _ in open(pw.LOG, encoding="utf-8")) == 1 + 4)
    reset("drop")
    r = pw.send(M, "drmanoj_post_visit", {"1": "Walk"}, "walk", "real-key", dry_run=False, timeout=3)
    ck("B8 no answer at all: 'send failed', one try", (not r["ok"]) and r.get("error", "").startswith("send failed") and S["n"] == 1, (r.get("error", "")[:40], S["n"]))
except Exception as e:  # noqa: BLE001
    ck("B the template sender", False, repr(e)[:170])

# ---- C. the stand-in reproduces both of today's live runs (so the walk tests the right thing)
try:
    sys.path.insert(0, PK)
    pv = importlib.import_module("prove_s802")
    body = b'{"customer_number":""}'
    reset("validate")
    five = [pv.cell(pv.via_urllib(URL, "real-key", "c", body)) for _ in range(5)]
    ck("C1 12:37 IST: five urllib tries, no properly-cased request before them -> all refused", five == ["500A"] * 5, five)
    a = pv.cell(pv.via_httpclient(URL, "real-key", "c", body)); b = pv.cell(pv.via_urllib(URL, "real-key", "c", body))
    ck("C2 12:05 IST: after ONE properly-cased request is let through, urllib with the same key is accepted for a while", a == "400" and b == "400", (a, b))
    time.sleep(TTL + 0.3)
    ck("C3 ... and refused again when that while has passed", pv.cell(pv.via_urllib(URL, "real-key", "c", body)) == "500A")
except Exception as e:  # noqa: BLE001
    ck("C the stand-in", False, repr(e)[:170])

# ---- D. the proof the installer runs
ENV = dict(os.environ, S802_API_URL=URL, S802_TOKEN="real-key", S802_GAP="0", S802_CONFIG_DIR=os.path.join(T, "none"))
def prove(mode, *args):
    reset(mode)
    r = subprocess.run([sys.executable, "-B", os.path.join(PK, "prove_s802.py"), os.path.join(K, "portal")] + list(args), env=ENV, capture_output=True, text=True, timeout=180)
    return r.returncode, (r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]), r.stdout
try:
    rc, last, out = prove("validate"); ck("D1 the gateway as today: PROVEN, and it names the company header", rc == 0 and last.startswith("PROVE: PROVEN") and "name is what decides" in last, last)
    ck("D2 the proof prints no key", "real-key" not in out and "s802-made-up-" not in out)
    rc, last, out = prove("lenient");  ck("D3 a gateway that takes either casing: NOT-SHOWN (nothing would be changed)", rc == 3 and last.startswith("PROVE: NOT-SHOWN"), last)
    rc, last, out = prove("crash");    ck("D4 a gateway that refuses everything: FAILED", rc == 1 and last.startswith("PROVE: FAILED"), last)
    rc, last, out = prove("validate", "--installed"); ck("D5 the installed check: 400 = let through", rc == 0 and "let through" in last, last)
    rc, last, out = prove("crash", "--installed");    ck("D6 the installed check says so when it is not", rc == 1 and "NOT A PROPER ANSWER" in last, last)
except Exception as e:  # noqa: BLE001
    ck("D the proof", False, repr(e)[:170])

# ---- E. the files
try:
    ti = open(os.path.join(K, "portal", "portal_inbox.py"), encoding="utf-8").read()
    tw = open(os.path.join(K, "portal", "portal_wa.py"), encoding="utf-8").read()
    fi = ti[ti.index("def myop_send("):ti.index("# --------------------------------------------------------------------------- S666")]
    fw = tw[tw.index("def send(phone, template_name"):tw.index("def registry_public(")]
    ck("E1 portal_inbox.myop_send: one request, through http.client, none through urllib", fi.count("conn.request(") == 1 and "urlopen" not in fi and "urllib.request.Request" not in fi)
    ck("E2 portal_wa.send: one request, through http.client, none through urllib", fw.count("conn.request(") == 1 and "urlopen" not in fw and "urllib.request.Request" not in fw)
    import py_compile
    for n in ("portal_inbox.py", "portal_wa.py"):
        py_compile.compile(os.path.join(K, "portal", n), cfile=os.path.join(T, n + "c"), doraise=True)
    ck("E3 both files compile", True)
except Exception as e:  # noqa: BLE001
    ck("E the files", False, repr(e)[:170])

srv.shutdown(); shutil.rmtree(T, ignore_errors=True)
bad = RES.count(False)
if CONTROL:
    print("CONTROL: red (%d of %d)" % (bad, len(RES)) if bad else "CONTROL: GREEN -- the control did not go red")
else:
    print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))
