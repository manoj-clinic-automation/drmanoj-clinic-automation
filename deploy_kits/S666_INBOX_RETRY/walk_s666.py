#!/usr/bin/env python3
"""walk_s666.py -- kit S666_INBOX_RETRY's walk. Nothing real is read or written: a temp store, made-up numbers, and a
stand-in MyOperator on 127.0.0.1 that refuses exactly as theirs does (HTTP 500 {"message":null},
x-amzn-ErrorType: AuthorizerConfigurationException), refuses otherwise, or accepts -- as each step orders.
  python3 walk_s666.py <dir holding portal/portal_inbox.py (+ inbox_retry.py) under test> [--old]
--old: the control on the live file -- every S666 check red, every older check green."""
import datetime, http.server, importlib.util, io, json, os, shutil, sqlite3, subprocess, sys, tempfile, threading, time, warnings
warnings.filterwarnings("ignore")
OLD = "--old" in sys.argv
SRC = os.path.abspath([a for a in sys.argv[1:] if not a.startswith("--")][0])
TMP = tempfile.mkdtemp(prefix="s666walk.")
STORE, RAW = os.path.join(TMP, "store"), os.path.join(TMP, "raw")
os.makedirs(RAW)
open(os.path.join(TMP, ".env"), "w").write("MYOP_AUTH_TOKEN=walk-not-a-key\nWATCHDOG_SMTP_USER=clinic@example.invalid\nWATCHDOG_SMTP_PASS=x\n")
PLAN, CALLS = [], []


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        CALLS.append(json.loads(self.rfile.read(n) or b"{}"))
        mode = PLAN.pop(0) if PLAN else "ok"
        if mode == "authz2":                                            # the same refusal, header in lower case with a suffix
            body, code, hd = b'{"message":null}', 500, {"x-amzn-errortype": "AuthorizerConfigurationException:http://internal/",
                                                         "x-amzn-RequestId": "walk-%d" % len(CALLS)}
        elif mode == "authz":
            body, code, hd = b'{"message":null}', 500, {"x-amzn-ErrorType": "AuthorizerConfigurationException",
                                                         "x-amzn-RequestId": "walk-%d" % len(CALLS)}
        elif mode == "other":
            body, code, hd = b'{"message":"Internal server error"}', 500, {}
        else:
            body, code, hd = json.dumps({"status": "success", "code": "200", "message": "Accepted",
                                         "data": {"message_id": "mid-%d" % len(CALLS)}}).encode(), 200, {}
        self.send_response(code)
        for k, v in hd.items():
            self.send_header(k, v)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
os.environ.update({"INBOX_STORE": STORE, "INBOX_RAW_DIR": RAW, "INBOX_WA_ENV": os.path.join(TMP, ".env"),
                   "INBOX_API_URL": "http://127.0.0.1:%d/chat/messages" % srv.server_address[1],
                   "INBOX_PORTAL_LOG": os.path.join(TMP, "none.csv"), "INBOX_PORTAL_DIR": os.path.join(SRC, "portal")})
sys.path.insert(0, os.path.join(SRC, "portal"))
spec = importlib.util.spec_from_file_location("portal_inbox", os.path.join(SRC, "portal", "portal_inbox.py"))
PI = importlib.util.module_from_spec(spec)
sys.modules["portal_inbox"] = PI
spec.loader.exec_module(PI)
MAILS = []


class FakeSMTP:
    def __init__(self, *a, **k):
        pass

    def starttls(self):
        pass

    def login(self, *a):
        pass

    def send_message(self, m):
        MAILS.append(str(m["Subject"]))

    def quit(self):
        pass

    def close(self):
        pass


PI.SMTP_CLASS = FakeSMTP
PI.NOTE_GAP_S = 0
NOW = [datetime.datetime(2026, 10, 27, 8, 2, 0, tzinfo=PI.IST)]
PI.now_ist = lambda: NOW[0]
from flask import Flask                                                 # noqa: E402
app = Flask("walk")
app.testing = True
PI.register(app, lambda f: f, lambda: "manoj", lambda n, d="": d, base_url="https://walk.invalid")
C = app.test_client()
RES = []


def check(tag, name, fn):
    try:
        ok, note = fn()
    except Exception as e:                                              # noqa: BLE001
        ok, note = False, "%s: %s" % (type(e).__name__, e)
    RES.append((tag, bool(ok)))
    print("%s  [%s] %s%s" % ("GREEN" if ok else "RED  ", tag, name, ("  -- " + str(note)[:220]) if (note and not ok) else ""))


def phone(i):
    return str(9 * 10 ** 9 + i)


def wrote(ph, hours_ago):
    c = PI.db()
    c.execute("INSERT INTO msgs(mid,phone,dir,ts,mtype,body,status,src) VALUES(?,?,?,?,?,?,?,?)",
              ("in-%s-%s" % (ph, hours_ago), ph, "in", PI.iso(NOW[0] - datetime.timedelta(hours=hours_ago)), "text", "hello", "received", "log"))
    c.commit(); c.close()


def send(ph, text="Please call", plan=("ok",)):
    PLAN[:] = list(plan)
    r = C.post("/portal/inbox/api/send", json={"phone": ph, "kind": "text", "text": text}, headers={"X-Inbox": "1"})
    return r.status_code, r.get_json(silent=True) or {}


def row(ph):
    c = PI.db()
    try:
        return dict(c.execute("SELECT * FROM msgs WHERE phone=? AND dir='out' ORDER BY rid DESC LIMIT 1", (ph,)).fetchone() or {})
    finally:
        c.close()


def job(ph):
    c = PI.db()
    try:
        return dict(c.execute("SELECT * FROM retry_q WHERE phone=? ORDER BY id DESC LIMIT 1", (ph,)).fetchone() or {})
    finally:
        c.close()


def job_safe(ph):
    try:
        return job(ph)
    except Exception:                                                   # noqa: BLE001 -- the old store has no queue
        return {}


def settle():
    time.sleep(0.4)


def later(minutes, plan=()):
    NOW[0] = NOW[0] + datetime.timedelta(minutes=minutes)
    PLAN[:] = list(plan)
    try:
        return PI.run_retries(lambda n, d="": d)
    except Exception as e:                                              # noqa: BLE001 -- the old file has no retry
        return "no retry (%s)" % type(e).__name__


T = "S666"
A, B_, Cc, D, E, F, G = (phone(i) for i in range(1, 8))
for p in (A, B_, Cc, D, E, F, G):
    wrote(p, 1)
# ---- older behaviour
check("older", "an accepted send is sent at once, nothing queued", lambda: (send(A)[1].get("ok") is True and row(A).get("status") == "sent"
                                                                             and not job_safe(A), row(A)))



check("older", "any OTHER refusal (500 without the authorizer header) fails at once with the error, nothing queued",
      lambda: (lambda st, j: (st == 502 and j.get("ok") is False and not job_safe(B_), (st, j)))(*send(B_, plan=("other",))))
# ---- the authorizer refusal is kept
settle()
n0 = len(MAILS)
st, j = send(Cc, plan=("authz",))
settle()
check(T, "the authorizer refusal is kept: 200 {queued}, the chat shows 'retrying', one job waiting",
      lambda: (st == 200 and j.get("queued") is True and row(Cc).get("status") == "retrying" and job(Cc).get("state") == "waiting", (st, j, row(Cc))))
check("older", "a refusal that is not kept still mails '[WA send refused]'", lambda: (any(m.startswith("[WA send refused] ") for m in MAILS[:n0]), MAILS[:n0]))
check(T, "the kept refusal's mail says '[WA send refused -- being retried]'", lambda: (len(MAILS) == n0 + 1 and "being retried" in MAILS[-1], MAILS[n0:]))
k1 = len(CALLS)
check(T, "the SAME text sent again by hand while it is retrying is refused, MyOperator not called", lambda: (lambda st, j: (st == 400 and "already being retried" in (j.get("error") or "") and len(CALLS) == k1, (st, j)))(*send(Cc)))
check("older", "a DIFFERENT text to the same patient still goes", lambda: (send(Cc, text="another line")[1].get("ok") is True, ""))
k0 = len(CALLS)
check(T, "a pass before 2 minutes does nothing", lambda: (later(1) == "" and len(CALLS) == k0, len(CALLS)))
n1 = len(MAILS)
s = later(1, ("authz",))
settle()
check(T, "2 minutes on, refused the same way again: still retrying (try 2), no mail for the retry",
      lambda: ("1 still retrying" in s and job(Cc).get("tries") == 2 and job(Cc).get("state") == "waiting" and len(MAILS) == n1, (s, job(Cc), MAILS[n1:])))
s = later(2, ("ok",))
check(T, "4 minutes on, accepted: the chat row is 'sent' with MyOperator's message id; the job is done",
      lambda: ("1 sent" in s and row(Cc).get("status") == "sent" and str(row(Cc).get("mid", "")).startswith("mid-") and job(Cc).get("state") == "sent", (s, row(Cc))))
check(T, "every try is in the send log: the first, the different text, and the two retries (route inbox-retry)",
      lambda: (lambda L: (sum(1 for e in L if e.get("customer") == Cc) == 4 and sum(1 for e in L if e.get("customer") == Cc and e.get("route") == "inbox-retry") == 2, len(L)))(PI.read_log(days=0)))
# ---- give up on anything else
send(D, plan=("authz",)); settle()
n2 = len(MAILS)
s = later(2, ("other",)); settle()
check(T, "a retry that meets ANY OTHER error gives up at once: NOT delivered, one '[WA send NOT delivered]' mail",
      lambda: ("1 gave up" in s and row(D).get("status") == "failed" and job(D).get("state") == "gaveup" and any("NOT delivered" in m for m in MAILS[n2:]), (s, MAILS[n2:])))
send(E, plan=("authz",)); settle()
for _ in range(29):
    later(2, ("authz",))
s = later(4, ("authz",))
check(T, "after 60 minutes of the same refusal the server stops: NOT delivered", lambda: (job(E).get("state") == "gaveup" and row(E).get("status") == "failed", (s, job(E))))
# ---- a stale job is never sent late (the runner was down for hours)
H1 = phone(8)
wrote(H1, 1)
send(H1, plan=("authz",)); settle()
k = len(CALLS)
s = later(300, ("ok",))
check(T, "a job 5 hours old is given up WITHOUT a call (never sent late)", lambda: (job(H1).get("state") == "gaveup" and len(CALLS) == k, (s, job(H1))))
# ---- MyOperator's echo of the real id arrives before the runner's bookkeeping
H2 = phone(9)
wrote(H2, 0.2)
send(H2, plan=("authz",)); settle()
c = PI.db(); c.execute("INSERT INTO msgs(mid,phone,dir,ts,mtype,body,status,src) VALUES(?,?,?,?,?,?,?,?)",
                       ("mid-%d" % (len(CALLS) + 1), H2, "out", PI.iso(NOW[0]), "text", "Please call", "delivered", "log")); c.commit(); c.close()
s = later(2, ("ok",))


def rows_of(ph):
    c = PI.db()
    try:
        return [dict(r) for r in c.execute("SELECT mid, status FROM msgs WHERE phone=? AND dir='out'", (ph,))]
    finally:
        c.close()


check(T, "the echo came first: the job is 'sent', ONE row left (the delivered one), no 'retry-' row, nothing 'failed'",
      lambda: (job(H2).get("state") == "sent" and len(rows_of(H2)) == 1 and rows_of(H2)[0]["status"] == "delivered", (s, rows_of(H2))))
# ---- a try that raises: the outcome is unknown
H3 = phone(10)
wrote(H3, 0.2)
send(H3, plan=("authz",)); settle()
NOW[0] = NOW[0] + datetime.timedelta(minutes=2)
n3 = len(MAILS)


def boom(*a, **k):
    raise ValueError("walk")


try:
    s = PI.run_retries(lambda n, d="": d, send=boom)
except Exception as e:                                                  # noqa: BLE001
    s = "no retry (%s)" % type(e).__name__
settle()
check(T, "a try that ends in an error is 'unsure' (may have gone), never tried again, and mailed", lambda: (job(H3).get("state") == "unsure" and row(H3).get("status") == "unsure"
      and any("may have gone" in m for m in MAILS[n3:]), (s, job(H3), MAILS[n3:])))
# ---- the 24-hour window
c = PI.db(); c.execute("DELETE FROM msgs WHERE phone=? AND dir='in'", (F,)); c.commit(); c.close()
wrote(F, 23.95)
send(F, plan=("authz",)); settle()
k = len(CALLS)
s = later(5, ("ok",))
check(T, "the 24-hour window closes while waiting: given up WITHOUT another call to MyOperator", lambda: (job(F).get("state") == "gaveup" and len(CALLS) == k, (s, len(CALLS) - k)))
# ---- a photo
PLAN[:] = ["authz"]
r = C.post("/portal/inbox/api/send", data={"phone": G, "kind": "image", "text": "x-ray", "file": (io.BytesIO(b"\xff\xd8\xff\xe0walkjpeg"), "p.jpg", "image/jpeg")},
           headers={"X-Inbox": "1"}, content_type="multipart/form-data")
settle()
check(T, "a photo refused the same way is kept with its file", lambda: ((r.get_json() or {}).get("queued") is True and row(G).get("local_path") and job(G).get("kind") == "image", r.get_json()))
s = later(2, ("ok",))
check(T, "...and sent on the retry, with the same link", lambda: (row(G).get("status") == "sent" and CALLS[-1]["data"]["type"] == "image" and CALLS[-1]["data"]["context"]["link"].startswith("https://walk.invalid/portal/inbox/f/"), CALLS[-1]))
# ---- a crash mid-try is never sent again
send(A, plan=("authz",)); settle()
try:
    c = PI.db(); c.execute("UPDATE retry_q SET state='busy' WHERE phone=? AND state='waiting'", (A,)); c.commit(); c.close()
except Exception:                                                       # noqa: BLE001 -- the old store has no queue
    pass
k = len(CALLS)
s = later(15, ("ok",))
check(T, "a job left 'busy' by a crash is 'unsure' (may have gone), never sent again", lambda: (job(A).get("state") == "unsure" and len(CALLS) == k and row(A).get("status") == "unsure", (s, job(A))))
# ---- the header in another spelling
H4 = phone(11)
wrote(H4, 0.2)
check(T, "the same refusal with the header in lower case and a suffix is kept too", lambda: (send(H4, text="z", plan=("authz2",))[1].get("queued") is True, job_safe(H4)))
# ---- the runner and the page
check(T, "inbox_retry.py runs on its own (exit 0)", lambda: (lambda p: (p.returncode == 0, p.stderr[-300:]))(
    subprocess.run([sys.executable, "-B", os.path.join(SRC, "portal", "inbox_retry.py")], capture_output=True, text=True, timeout=60)))
page = C.get("/portal/inbox").get_data(as_text=True)
check(T, "the page: 'MyOperator busy — retrying' and the queued toast; health names S666",
      lambda: ('retrying:"MyOperator busy — retrying"' in page and 'unsure:"May have gone' in page and "j.queued?" in page and C.get("/portal/inbox/health").get_json().get("kit") == "S666", ""))
srv.shutdown()
shutil.rmtree(TMP, ignore_errors=True)
s6 = sum(1 for t, ok in RES if t == T and not ok)
older = sum(1 for t, ok in RES if t != T and not ok)
g = sum(1 for _t, ok in RES if ok)
print("%d S666 check(s) red · %d older red · %d green" % (s6, older, g) if OLD else "%d of %d green" % (g, len(RES)))
