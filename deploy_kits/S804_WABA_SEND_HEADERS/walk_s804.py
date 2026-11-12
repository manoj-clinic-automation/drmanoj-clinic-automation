#!/usr/bin/python3
# walk_s804.py -- kit S804_WABA_SEND_HEADERS. Usage: walk_s804.py <dir holding wa/waba.py> <dir holding prove_s804.py> [--control]
# Everything is MADE UP: a stand-in gateway on this machine (127.0.0.1) behaves the way MyOperator's did in S802's proof --
#   * its "authorizer" fails (HTTP 500, x-amzn-ErrorType AuthorizerConfigurationException, {"message":null}) unless the company
#     header arrives named exactly "X-MYOP-COMPANY-ID" (or all lower-case);
#   * an authorisation, once given or denied, is kept per key for a short while and the authorizer is not asked again.
# Nothing leaves this machine; the real key is the word "real-key"; the one number is built from a counter (F-185).
# The last line is "WALK OK n/n" or "WALK RED k of n"; with --control, "CONTROL: red ..." when it is red as it must be.
import http.server, importlib, json, os, shutil, subprocess, sys, tempfile, threading, time, types
K, PK = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
CONTROL = "--control" in sys.argv
T = tempfile.mkdtemp(prefix="s804w.")
RES = []
def ck(name, ok, why=""):
    RES.append(bool(ok)); print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + str(why)) if (why and not ok) else ""))
TTL = 1.5
S = {"mode": "validate", "cache": {}, "n": 0, "names": [], "paths": [], "bodies": []}
LOCK = threading.Lock()
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        got = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        names = list(self.headers.keys()); tok = self.headers.get("Authorization") or ""
        with LOCK:
            S["n"] += 1; S["names"].append(names); S["paths"].append(self.path); S["bodies"].append(got); m = S["mode"]; now = time.time()
            hit = S["cache"].get(tok); hit = hit if (hit and now - hit[1] < TTL) else None
        if m == "drop":
            try:
                self.connection.close()
            except Exception:
                pass
            return
        if m == "late":                                                # accepted, but the answer comes after the caller's patience
            time.sleep(2.5)
            m = "accept"
        if m == "cut":                                                 # accepted, the answer's body cut short
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", "500"); self.end_headers()
            self.wfile.write(b'{"status":"succ'); self.wfile.flush()
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
        elif m == "wallet":
            self.send_response(400); out = b'{"status":"error","code":"CHAT_4001","message":"Insufficient wallet balance"}'
        elif m == "busy":
            self.send_response(503); out = b'{"status":"error","message":"try later"}'
        else:
            self.send_response(400); out = b'{"status":"error","message":"customer_number is required"}'
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = "http://127.0.0.1:%d" % srv.server_address[1]
URL = BASE + "/chat/messages"
def reset(mode):
    with LOCK:
        S.update({"mode": mode, "cache": {}, "n": 0, "names": [], "paths": [], "bodies": []})
os.environ.update({"MYOP_BASE_URL": BASE, "MYOP_COMPANY_ID": "walk-co", "MYOP_PHONE_NUMBER_ID": "walk-pn", "MYOP_AUTH_TOKEN": "real-key"})
sys.path.insert(0, os.path.join(K, "wa"))
M = "9" + "%09d" % 79903                                               # a made-up mobile
KEYSET = {"ok", "status_code", "message_id", "conversation_id", "code", "message", "raw"}

# ---- A. waba.send_template
try:
    w = importlib.import_module("waba")
    ck("A1 waba imports from the given folder", os.path.dirname(os.path.abspath(w.__file__)) == os.path.join(K, "wa"))
    w.BASE_URL, w.AUTH_TOKEN, w.COMPANY_ID, w.PHONE_NUMBER_ID = BASE, "real-key", "walk-co", "walk-pn"
    w.time = types.SimpleNamespace(sleep=lambda s: None, time=time.time)   # the 3-second wait before a retry is not waited here
    reset("validate")
    r = w.send_template(M, "drmanoj_post_visit", ["Walk"])
    ck("A2 the real key, nothing kept at the gateway: let through at the first try (the stand-in's HTTP 400, not 500)", r["status_code"] == 400 and S["n"] == 1 and not r["ok"], (r["status_code"], S["n"]))
    ck("A3 the company header left exactly as written", "X-MYOP-COMPANY-ID" in S["names"][-1] and "X-Myop-Company-Id" not in S["names"][-1], S["names"][-1])
    b2 = json.loads(S["bodies"][-1].decode("utf-8"))
    ck("A3b it went to /chat/messages with the template request as its body", S["paths"][-1] == "/chat/messages" and b2.get("customer_number") == M and b2.get("phone_number_id") == "walk-pn" and b2["data"]["context"]["template_name"] == "drmanoj_post_visit" and b2["data"]["context"]["body"] == {"1": "Walk"}, (S["paths"][-1], sorted(b2)))
    ck("A4 what the caller gets back has the same keys as before, and no key in it", set(r) == KEYSET and "real-key" not in json.dumps(r), sorted(r))
    reset("validate"); setattr(w, "AUTH_TOKEN", "-".join(("walk", "made", "up", "key")))     # a made-up word, not a key (the number gate reads literals)
    r = w.send_template(M, "drmanoj_post_visit", ["Walk"]); setattr(w, "AUTH_TOKEN", "real-key")
    ck("A5 a made-up key gets the proper 'not authorised' (403), not 500", r["status_code"] == 403 and not r["ok"], r["status_code"])
    reset("accept")
    r = w.send_template(M, "drmanoj_post_visit", ["Walk"])
    ck("A6 accepted: sent ONCE, the ids returned", r["ok"] and r["message_id"] == "walk-mid-1" and r["conversation_id"] == "walk-c" and S["n"] == 1, (r, S["n"]))
    reset("crash")
    r = w.send_template(M, "drmanoj_post_visit", ["Walk"])
    ck("A7 a 500 from the gateway: reported as before, after the SAME one retry as before (2 requests)", (not r["ok"]) and r["status_code"] == 500 and r["raw"] == '{"message":null}' and S["n"] == 2, (r["status_code"], S["n"]))
    reset("crash")
    r = w.send_template(M, "drmanoj_post_visit", ["Walk"], retries=0)
    ck("A8 ... and ONE request when the caller asks for no retry", (not r["ok"]) and S["n"] == 1, S["n"])
    reset("busy")
    r = w.send_template(M, "drmanoj_post_visit", ["Walk"])
    ck("A9 another 5xx: the same one retry, the status passed on", r["status_code"] == 503 and S["n"] == 2, (r["status_code"], S["n"]))
    reset("wallet")
    try:
        w.send_template(M, "drmanoj_post_visit", ["Walk"]); got = "no stop"
    except w.WabaFatalError as fe:
        got = fe.code
    ck("A10 an empty wallet still STOPS the batch (WabaFatalError), after one request", got == "CHAT_4001" and S["n"] == 1, (got, S["n"]))
    def once(mode, **kw):
        reset(mode)
        try:
            w.send_template(M, "drmanoj_post_visit", ["Walk"], **kw); how = "returned"
        except w.WabaFatalError:
            how = "fatal"
        except Exception as ex:  # noqa: BLE001
            how = "raised " + type(ex).__name__
        return how, S["n"]
    how, n = once("drop", timeout=3)
    ck("A11 the request went out and the line dropped: raised to the caller after ONE request -- never sent again", how.startswith("raised") and n == 1, (how, n))
    how, n = once("late", timeout=1)
    ck("A11b accepted but the answer is late: raised after ONE request -- never sent again (no second message to a patient)", how.startswith("raised") and n == 1, (how, n))
    time.sleep(2.0)
    how, n = once("cut", timeout=3)
    ck("A11c accepted but the answer is cut short: raised after ONE request -- never sent again", how.startswith("raised") and n == 1, (how, n))
    w.BASE_URL = "http://127.0.0.1:9"
    r = w.send_template(M, "drmanoj_post_visit", ["Walk"], timeout=3)
    ck("A12 nobody listening (the request could not be sent): code NETWORK, status 0, the same keys", r["code"] == "NETWORK" and r["status_code"] == 0 and not r["ok"] and set(r) == KEYSET, r)
    tried = []
    real_conn = w.http.client.HTTPConnection
    class Counting(real_conn):
        def connect(self):
            tried.append(1); return real_conn.connect(self)
    w.http.client.HTTPConnection = Counting
    try:
        w.send_template(M, "drmanoj_post_visit", ["Walk"], timeout=3); a12 = len(tried)
        tried.clear(); w.send_template(M, "drmanoj_post_visit", ["Walk"], timeout=3, retries=0); a12b = len(tried)
    finally:
        w.http.client.HTTPConnection = real_conn
    ck("A12b ... tried twice (the one retry, as before), once when the caller asks for no retry", (a12, a12b) == (2, 1), (a12, a12b))
    w.BASE_URL = BASE
    ck("A13 every name the approve page and the diagnosis script use is still there", all(hasattr(w, n) for n in ("normalize_mobile", "check_config", "send_template", "build_payload", "WabaFatalError", "WabaConfigError", "AUTH_TOKEN", "COMPANY_ID", "BASE_URL", "SEND_PATH", "PHONE_NUMBER_ID", "BODY_FORMAT", "FATAL_CODES")))
    p = w.build_payload(M, "drmanoj_post_visit", ["Walk"], myop_ref_id="walk-ref")
    ck("A14 the request body is built as before", p["customer_number"] == M and p["data"] == {"type": "template", "context": {"template_name": "drmanoj_post_visit", "language": "en", "body": {"1": "Walk"}}} and p["myop_ref_id"] == "walk-ref", p)
except Exception as e:  # noqa: BLE001
    ck("A waba.send_template", False, repr(e)[:170])

# ---- C. the stand-in reproduces the live gateway as S802's proof showed it (so the walk tests the right thing)
try:
    sys.path.insert(0, PK)
    pv = importlib.import_module("prove_s804")
    body = b'{"customer_number":""}'
    reset("validate")
    five = [pv.cell(pv.via_urllib(URL, "real-key", "c", body)) for _ in range(5)]
    ck("C1 five urllib tries, no properly-cased request before them -> all refused", five == ["500A"] * 5, five)
    a = pv.cell(pv.via_httpclient(URL, "real-key", "c", body)); b = pv.cell(pv.via_urllib(URL, "real-key", "c", body))
    ck("C2 after ONE properly-cased request is let through, urllib with the same key is accepted for a while", a == "400" and b == "400", (a, b))
    time.sleep(TTL + 0.3)
    ck("C3 ... and refused again when that while has passed", pv.cell(pv.via_urllib(URL, "real-key", "c", body)) == "500A")
except Exception as e:  # noqa: BLE001
    ck("C the stand-in", False, repr(e)[:170])

# ---- D. the proof the installer runs
ENV = dict(os.environ, S804_API_BASE=BASE, S804_TOKEN="real-key", S804_GAP="0", S804_ENV_FILE=os.path.join(T, "none"))
def prove(mode, *args):
    reset(mode)
    r = subprocess.run([sys.executable, "-B", os.path.join(PK, "prove_s804.py"), os.path.join(K, "wa")] + list(args), env=ENV, capture_output=True, text=True, timeout=180)
    return r.returncode, (r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]), r.stdout
try:
    rc, last, out = prove("validate"); ck("D1 the gateway as today: PROVEN, and it names the company header", rc == 0 and last.startswith("PROVE: PROVEN") and "name is what decides" in last, last)
    ck("D2 the proof prints no key and no setting", "real-key" not in out and "s804-made-up-" not in out and "walk-co" not in out and "walk-pn" not in out)
    rc, last, out = prove("lenient");  ck("D3 a gateway that takes either casing: NOT-SHOWN (nothing would be changed)", rc == 3 and last.startswith("PROVE: NOT-SHOWN"), last)
    rc, last, out = prove("crash");    ck("D4 a gateway that refuses everything: FAILED", rc == 1 and last.startswith("PROVE: FAILED"), last)
    rc, last, out = prove("validate", "--installed"); ck("D5 the installed check: 400 = let through", rc == 0 and "let through" in last, last)
    rc, last, out = prove("crash", "--installed");    ck("D6 the installed check says so when it is not", rc == 1 and "NOT A PROPER ANSWER" in last, last)
    rc, last, out = prove("wallet", "--installed");   ck("D7 a stop code from the service itself counts as let through (past the authorizer)", rc == 0 and "let through" in last, last)
    envf = os.path.join(T, "made-up.env")
    open(envf, "w").write("# made up\nMYOP_BASE_URL=%s\nMYOP_COMPANY_ID=walk-co\nMYOP_PHONE_NUMBER_ID=walk-pn\nMYOP_AUTH_TOKEN='real-key'\nOTHER_SECRET=never-read\n" % BASE)
    e2 = {k: v for k, v in os.environ.items() if not k.startswith("MYOP_")}; e2.update(S804_GAP="0", S804_ENV_FILE=envf)
    reset("validate")
    r2 = subprocess.run([sys.executable, "-B", os.path.join(PK, "prove_s804.py"), os.path.join(K, "wa")], env=e2, capture_output=True, text=True, timeout=180)
    last2 = r2.stdout.strip().splitlines()[-1] if r2.stdout.strip() else r2.stderr[-200:]
    ck("D8 the settings are read by key from the box's own file (a made-up one here), and nothing of it is printed", r2.returncode == 0 and last2.startswith("PROVE: PROVEN") and "real-key" not in r2.stdout and "never-read" not in r2.stdout, last2)
    e3 = dict(e2, S804_ENV_FILE=os.path.join(T, "none"))
    reset("validate")
    r3 = subprocess.run([sys.executable, "-B", os.path.join(PK, "prove_s804.py"), os.path.join(K, "wa")], env=e3, capture_output=True, text=True, timeout=60)
    ck("D9 no settings on the box: an ERROR line, nothing asked of the gateway", r3.returncode == 2 and "PROVE: ERROR" in r3.stdout and S["n"] == 0, r3.stdout[-120:])
except Exception as e:  # noqa: BLE001
    ck("D the proof", False, repr(e)[:170])

# ---- E. the file
try:
    tw = open(os.path.join(K, "wa", "waba.py"), encoding="utf-8").read()
    fw = tw[tw.index("def send_template("):tw.index("def _parse_response(")]
    ck("E1 waba.send_template: one request per try, through http.client, none through urllib", fw.count("conn.request(") == 1 and "urlopen" not in fw and "urllib.request.Request" not in fw)
    import py_compile
    py_compile.compile(os.path.join(K, "wa", "waba.py"), cfile=os.path.join(T, "waba.pyc"), doraise=True)
    ck("E2 the file compiles", True)
except Exception as e:  # noqa: BLE001
    ck("E the file", False, repr(e)[:170])

srv.shutdown(); shutil.rmtree(T, ignore_errors=True)
bad = RES.count(False)
if CONTROL:
    print("CONTROL: red (%d of %d)" % (bad, len(RES)) if bad else "CONTROL: GREEN -- the control did not go red")
else:
    print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))
