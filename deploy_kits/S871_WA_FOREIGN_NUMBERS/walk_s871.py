#!/usr/bin/env python3
"""walk_s871.py -- the walk for kit S871_WA_FOREIGN_NUMBERS, on a MADE-UP root (no real number, no real store).

Usage: python walk_s871.py INBOX_PY CONSOLE_PY [--deps DIR]
  INBOX_PY / CONSOLE_PY: the portal_inbox.py / calls_console.py to judge (the kit's TO files: green; the FROM: red).
  --deps: a folder with the portal's other modules (for calls_console's imports); never the kit's own folder.
Every made-up number below is invented (555 / 0000 patterns). Prints one line per check and 'WALK n/m'.
"""
import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != HERE]          # F-1441: never import the kit's own copy

args = [a for a in sys.argv[1:]]
deps = None
if "--deps" in args:
    i = args.index("--deps")
    deps = args[i + 1]
    del args[i:i + 2]
INBOX, CONSOLE = os.path.abspath(args[0]), os.path.abspath(args[1])
if deps:
    sys.path.insert(0, os.path.abspath(deps))

ROOT = tempfile.mkdtemp(prefix="walk871_")
RAW = os.path.join(ROOT, "raw")
STORE = os.path.join(ROOT, "store")
os.makedirs(RAW)
os.environ.update({"INBOX_RAW_DIR": RAW, "INBOX_STORE": STORE, "INBOX_WA_ENV": os.path.join(ROOT, "no.env"),
                   "INBOX_API_URL": "http://127.0.0.1:9/chat/messages", "INBOX_CALL_URL": "http://127.0.0.1:9/call"})

N = {"ok": 0, "all": 0}


def check(name, cond, info=""):
    N["all"] += 1
    if cond:
        N["ok"] += 1
    print("%s  %s%s" % ("ok  " if cond else "RED ", name, ("  [" + str(info)[:160] + "]") if (info and not cond) else ""))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


US = "15550100000"            # +1 555 010 0000 -- invented
US_CUT = "5550100000"
UK = "445550100001"            # +44 ...  invented
IN = "9555" + "000001"          # an invented Indian-shaped number (built in two pieces: the number gate)
US9 = "1" + IN                  # an invented US-shaped number whose last 10 equal IN
IN_H = IN[:5] + " " + IN[5:]    # how the screens group it


def push(phone, mid, body="hello", ts="2026-11-18T06:15:00Z"):
    return {"event_type": "message.received", "timestamp": ts, "customer_identifier": phone, "direction": "incoming",
            "payload": {"id": mid, "status": "received", "data": {"type": "text", "context": {"body": body}}}}


try:
    pi = load("portal_inbox_w871", INBOX)
except Exception as e:                                                  # noqa: BLE001
    print("RED  portal_inbox could not be loaded: %s" % e)
    sys.exit(1)

# ---- A. the chat key -------------------------------------------------------------------------------------------
lk = pi.last10
check("A1 a US sender keeps its whole number", lk(US) == US, lk(US))
check("A2 '+1 555-010-0000' typed form -> the same key", lk("+1 555-010-0000") == US, lk("+1 555-010-0000"))
check("A3 91 + 10 digits -> 10 digits (as before)", lk("91" + IN) == IN, lk("91" + IN))
check("A4 0 + 10 digits -> 10 digits", lk("0" + IN) == IN)
check("A5 10 digits unchanged", lk(IN) == IN)
check("A6 00 44 ... -> the whole number", lk("00" + UK) == UK, lk("00" + UK))
check("A7 too short -> empty", lk("12345") == "")
check("A8 every key comes back unchanged (idempotent)", all(lk(lk(x)) == lk(x) for x in (US, "91" + IN, UK, IN, "0" + IN)))
check("A9 0091 + 10 digits -> 10 digits", lk("0091" + IN) == IN)

# ---- B. the split for MyOperator -------------------------------------------------------------------------------
sc = getattr(pi, "split_cc", None)
check("B1 split exists", sc is not None)
if sc:
    check("B2 US -> ('1', 10 digits)", sc(US) == ("1", US_CUT), sc(US))
    check("B3 UK -> ('44', rest)", sc(UK) == ("44", UK[2:]), sc(UK))
    check("B4 UAE-shaped 971... -> 3-digit code", sc("971555000000")[0] == "971", sc("971555000000"))
    check("B5 Indian key -> ('91', key)", sc(IN) == ("91", IN))


# ---- C. the send body -------------------------------------------------------------------------------------------
def sent_body(key):
    tr = {}
    pi.myop_send("x" * 32, key, {"type": "text", "context": {"body": "t"}}, timeout=2, trace=tr)
    try:
        return json.loads(tr.get("request_json") or "{}")
    except ValueError:
        return {}


b = sent_body(US)
check("C1 a reply to the US chat goes with code 1", b.get("customer_country_code") == "1", b.get("customer_country_code"))
check("C2 ... and the 10-digit number", b.get("customer_number") == US_CUT, b.get("customer_number"))
b = sent_body(IN)
check("C3 an Indian reply unchanged (91 + 10 digits)", (b.get("customer_country_code"), b.get("customer_number")) == ("91", IN))

# ---- D. ingest of a push from abroad ------------------------------------------------------------------------
with open(os.path.join(RAW, "2026-11-18.jsonl"), "w") as fh:
    fh.write(json.dumps({"body": push(US, "mid-us-new", "Is the clinic open?")}) + "\n")
    fh.write(json.dumps({"body": push("91" + IN, "mid-in-1", "namaste")}) + "\n")
pi.ingest(force=True)
c = sqlite3.connect(pi.DB_PATH)
ph = dict(c.execute("SELECT mid, phone FROM msgs").fetchall())
check("D1 the US message stored under the whole number", ph.get("mid-us-new") == US, ph.get("mid-us-new"))
check("D2 an Indian message still under 10 digits", ph.get("mid-in-1") == IN, ph.get("mid-in-1"))
c.close()

# ---- E. the once-only move of chats already cut ---------------------------------------------------------------
shutil.rmtree(STORE)
for f in os.listdir(RAW):
    os.remove(os.path.join(RAW, f))
with open(os.path.join(RAW, "2026-11-13.jsonl"), "w") as fh:
    fh.write(json.dumps({"body": push(US, "mid-us-1")}) + "\n")
    fh.write(json.dumps({"body": push(US9, "mid-us9-1")}) + "\n")
    fh.write(json.dumps({"body": push("15550100009", "mid-a")}) + "\n")      # two numbers abroad, one cut key
    fh.write(json.dumps({"body": push("445550100009", "mid-b")}) + "\n")
c = pi.db()
rows = [("mid-us-1", US_CUT, "in"), ("out-1", US_CUT, "out"),                   # the old cut chat (in + our failed reply)
        ("mid-us9-1", IN, "in"), ("in-own", IN, "in"), ("out-own", IN, "out"),  # an Indian-shaped cut key: only its own
        ("mid-a", "5550100009", "in"), ("mid-b", "5550100009", "in")]
for mid, p, d in rows:
    c.execute("INSERT INTO msgs(mid,phone,dir,ts,mtype,body,status,src) VALUES(?,?,?,?,?,?,?,?)",
              (mid, p, d, "2026-11-13T14:13:00+05:30", "text", "x", "received", "log"))
c.execute("INSERT INTO reads(phone,ts) VALUES(?,?)", (US_CUT, "2026-11-13T15:00:00+05:30"))
# the raw lines above count as already read (as on the server): only the once-only move may touch them
c.execute("INSERT INTO offsets(fname,pos) VALUES(?,?)", ("2026-11-13.jsonl", os.path.getsize(os.path.join(RAW, "2026-11-13.jsonl"))))
c.commit()
c.close()
if hasattr(pi, "_S871"):
    pi._S871["done"] = False                                             # a new made-up store in the same process
pi.ingest(force=True)
c = sqlite3.connect(pi.DB_PATH)
ph = dict(c.execute("SELECT mid, phone FROM msgs").fetchall())
check("E1 the cut US chat moved to the whole number (its message)", ph.get("mid-us-1") == US, ph.get("mid-us-1"))
check("E2 ... with our earlier reply", ph.get("out-1") == US, ph.get("out-1"))
check("E3 ... and the read mark", [r[0] for r in c.execute("SELECT phone FROM reads")] == [US])
check("E4 an Indian-shaped cut key: only the abroad sender's message moved", ph.get("mid-us9-1") == US9, ph.get("mid-us9-1"))
check("E5 ... the Indian chat's own messages stay", ph.get("in-own") == IN and ph.get("out-own") == IN)
check("E6 a cut key two numbers share is left alone", ph.get("mid-a") == ph.get("mid-b") == "5550100009")
check("E7 the move ran once (its mark is kept)", c.execute("SELECT 1 FROM offsets WHERE fname='s871:rekey'").fetchone() is not None)
c.execute("UPDATE msgs SET phone=? WHERE mid='out-1'", (US_CUT,))                # a row put back by hand ...
c.commit()
c.close()
pi.ingest(force=True)
c = sqlite3.connect(pi.DB_PATH)
check("E8 ... and never again", c.execute("SELECT phone FROM msgs WHERE mid='out-1'").fetchone()[0] == US_CUT)
c.close()

# ---- F. the pages' doors ------------------------------------------------------------------------------------------
try:
    import flask
    app = flask.Flask("w871")
    app.secret_key = "w"
    pi.register(app, lambda f: f, lambda: "manoj", lambda k, d=None: d)
    cl = app.test_client()
    H = {"X-Inbox": "1"}                                                 # the page's own header (xhr_ok)
    r = cl.post("/portal/inbox/api/call", json={"phone": US}, headers=H)
    j = r.get_json(silent=True) or {}
    check("F1 Call refused for a number abroad, in plain words", (not j.get("ok")) and "abroad" in str(j.get("error", "")),
          "%s %s" % (r.status_code, j))
    r = cl.post("/portal/inbox/api/template", json={"phone": US, "template": "x"}, headers=H)
    j = r.get_json(silent=True) or {}
    check("F2 a template refused for a number abroad", (not j.get("ok")) and "abroad" in str(j.get("error", "")),
          "%s %s" % (r.status_code, j))
    r = cl.get("/portal/inbox/api/chat?phone=" + US)
    j = r.get_json(silent=True) or {}
    check("F3 the chat opens under the whole number", j.get("phone") == US and len(j.get("msgs") or []) >= 1, "%s %s" % (r.status_code, str(j)[:120]))
    r = cl.get("/portal/inbox/health")
    j = r.get_json(silent=True) or {}
    check("F4 health unchanged (S859's three keys, no number)", set(j) == {"inbox", "kit", "no_file_30d"} and US not in r.get_data(as_text=True), j)
    check("F4b the count of chats abroad (2 here) -- a count only", pi.abroad_count() == 2, pi.abroad_count())
    r = cl.get("/portal/inbox")
    check("F5 the inbox page opens", r.status_code == 200, r.status_code)
    page = r.get_data(as_text=True)
except Exception as e:                                                   # noqa: BLE001
    check("F0 the pages could be opened", False, "%s: %s" % (type(e).__name__, e))
    page = ""

# ---- G. the inbox page's own words (run in node) ----------------------------------------------------------------
js_ok = False
if page and shutil.which("node"):
    import re as _re
    want = [n for n in ("CC2", "ccLen", "MYOP_CHAT", "myopUrl", "fmtNum") if n in page]
    lines = [ln for ln in page.split("\n") if _re.match(r"^\s*(var (CC2|MYOP_CHAT)=|function (ccLen|myopUrl|fmtNum)\()", ln)]
    prog = "\n".join(lines) + "\nconsole.log(JSON.stringify([fmtNum(%r), fmtNum(%r), myopUrl(%r), myopUrl(%r)]));" % (US, IN, US, IN)
    try:
        out = subprocess.run(["node", "-e", prog], capture_output=True, text=True, timeout=20).stdout.strip()
        v = json.loads(out)
        js_ok = True
        check("G1 the inbox shows '+1 55501 00000 · abroad'", v[0] == "+1 55501 00000 · abroad", v[0])
        check("G2 an Indian number still '+91 ' and its two groups", v[1] == "+91 " + IN_H, v[1])
        check("G3 the MyOperator link uses /1/<number>", v[2].endswith("/1/" + US_CUT) and "/91/" not in v[2], v[2])
        check("G4 an Indian link unchanged (/91/<number>)", v[3].endswith("/91/" + IN), v[3])
    except Exception as e:                                               # noqa: BLE001
        check("G0 the page's script ran", False, "%s %s" % (type(e).__name__, e))
elif page:
    print("note  G1-G4 not run: no node on this machine (the walk in the build ran them)")
if page:
    check("G5 no Call button drawn for a number abroad", 'String(j.phone).length>10?document.createTextNode("")' in page)
    check("G6 the send log shows a number abroad with its own code", '"+"+e.customer+" (abroad)"' in (pi.LOG_PAGE if hasattr(pi, "LOG_PAGE") else ""))
check("G7 the send log CSV writes the whole number abroad",
      hasattr(pi, "full_number") and pi.full_number(US) == US and pi.full_number(IN) == "91" + IN)

# ---- H. the Call Console ----------------------------------------------------------------------------------------
try:
    cc = load("calls_console_w871", CONSOLE)
except Exception as e:                                                  # noqa: BLE001
    check("H0 calls_console could be loaded", False, "%s: %s" % (type(e).__name__, e))
    cc = None
if cc:
    check("H1 a number abroad shown with its code", cc.fmt_num(US) == "+1 55501 00000 · abroad", cc.fmt_num(US))
    check("H2 an Indian number shown as before", cc.fmt_num(IN) == IN_H)
    check("H3 '91'+10 digits shown as before (not 'abroad')", "abroad" not in cc.fmt_num("91" + IN), cc.fmt_num("91" + IN))
    ok, msg, code = cc.ivr_call(US, "manoj", env_path=os.path.join(ROOT, "no.env"), post=lambda *a, **k: None)
    check("H4 the click-to-call refuses a number abroad", (not ok) and "abroad" in msg and code == 400, msg)
    ok, msg, code = cc.ivr_call(IN, "manoj", env_path=os.path.join(ROOT, "no.env"), post=lambda *a, **k: None)
    check("H5 an Indian number is not refused as abroad", "abroad" not in msg, msg)
    row = {"rid": 1, "mid": "m", "phone": US, "dir": "in", "ts": "2026-11-18T11:45:00+05:30", "mtype": "text",
           "body": "Is the clinic open?", "status": "received", "sent_by": "", "src": "log"}

    class R(dict):
        def keys(self):
            return list(super().keys())
    it = cc.wa_item(R(row))
    check("H6 a WhatsApp item keeps the whole number", it["phone"] == US, it["phone"])
    row["phone"] = IN
    check("H7 an Indian WhatsApp item unchanged", cc.wa_item(R(row))["phone"] == IN)
    src = open(CONSOLE, encoding="utf-8").read()
    check("H8 the awaiting card shows Call only for an Indian number",
          "{% if a.phone|length <= 10 %}<button type=\"button\" class=\"awb sec\" onclick=\"callBack('{{ a.phone }}',this)\">Call</button>{% endif %}" in src)
    try:
        import jinja2
        snip = src[src.index('<div class="awg">'):]
        snip = snip[:snip.index("</div>") + 6]
        env = jinja2.Environment()
        for a, want in (({"phone": US, "mid": ""}, False), ({"phone": IN, "mid": ""}, True)):
            html = env.from_string(snip).render(a=a)
            check("H9 card for %s: Call %s" % ("abroad" if want is False else "India", "shown" if want else "hidden"),
                  ("callBack(" in html) == want, html[:200])
    except Exception as e:                                               # noqa: BLE001
        check("H9 the card could be drawn", False, e)
    check("H10 every other Call button for a number abroad is hidden on the page",
          "button[onclick^=\"callBack(\"]" in src and "callBack[(]'([^']*)'" in src)
    check("H11 callBack itself refuses a number abroad", "replace(/[^0-9]/g,'').length>10){ toast('This number is from abroad" in src)
    # review MUST 1 and 2: the chat reaches the Console's lists, and Done / Not a patient work on it
    tdb = os.path.join(ROOT, "h_inbox.db")
    t = sqlite3.connect(tdb)
    t.execute("CREATE TABLE msgs(rid INTEGER PRIMARY KEY, mid TEXT, phone TEXT, dir TEXT, ts TEXT, mtype TEXT, body TEXT, status TEXT, "
              "sent_by TEXT, src TEXT)")
    for i, p in enumerate((US, IN), 1):
        t.execute("INSERT INTO msgs VALUES(?,?,?,?,?,?,?,?,?,?)", (i, "m%d" % i, p, "in", "2026-11-18T11:45:00+05:30", "text", "hi",
                                                                   "received", "", "log"))
    t.commit()
    t.close()
    try:
        items, ok = cc.wa_items(tdb, "2026-11-18", "2026-11-18", dz={"np": set(), "done_t": {}, "done": {}})
        ph = sorted(x["phone"] for x in items)
        check("H12 the Console's WhatsApp list carries the chat from abroad", ok and ph == sorted([US, IN]), ph)
    except Exception as e:                                               # noqa: BLE001
        check("H12 the Console's WhatsApp list could be read", False, "%s: %s" % (type(e).__name__, e))
    try:
        okw, words, code = cc.wz_write(os.path.join(ROOT, "h_wz.db"), US, "not_patient", "", "manoj")
        check("H13 'Not a patient' on a chat from abroad is saved", okw and code == 200, "%s %s %s" % (okw, words, code))
        okw, words, code = cc.wz_write(os.path.join(ROOT, "h_wz.db"), "12345", "not_patient", "", "manoj")
        check("H14 ... a bad number is still refused", (not okw) and code == 400, "%s %s" % (okw, code))
    except Exception as e:                                               # noqa: BLE001
        check("H13 the marks could be written", False, "%s: %s" % (type(e).__name__, e))
    check("H15 the page's own door for the marks takes a number abroad", 'if not re.match(r"\\d{10,15}\\Z", ph) or act not in WZ_ACTS' in src)

# ---- I. review SHOULD 3: a move that fails never stops the inbox --------------------------------------------------
if hasattr(pi, "s871_apply"):
    shutil.rmtree(STORE, ignore_errors=True)
    for f in os.listdir(RAW):
        os.remove(os.path.join(RAW, f))
    with open(os.path.join(RAW, "2026-11-18.jsonl"), "w") as fh:
        fh.write(json.dumps({"body": push(US, "mid-i1")}) + "\n")
    real = pi.s871_apply

    def boom(c, plan):
        c.execute("UPDATE msgs SET phone='x' WHERE 1")
        raise RuntimeError("made-up failure")
    pi.s871_apply = boom
    pi._S871["done"] = False                                             # a new made-up store in the same process
    pi.ingest(force=True)
    pi.s871_apply = real
    c = sqlite3.connect(pi.DB_PATH)
    check("I1 the move failed, yet the new message is in", c.execute("SELECT phone FROM msgs WHERE mid='mid-i1'").fetchone() == (US,))
    check("I2 ... its mark is written (never tried again in a loop)", c.execute("SELECT 1 FROM offsets WHERE fname='s871:rekey'").fetchone() is not None)
    c.close()
else:
    check("I1 the move is split from its reading (s871_plan / s871_apply)", False)

shutil.rmtree(ROOT, ignore_errors=True)
print("WALK %d/%d" % (N["ok"], N["all"]))
sys.exit(0 if N["ok"] == N["all"] else 1)
