"""make_s666.py -- kit S666_INBOX_RETRY (the parent, session 358, 27-Oct-2026). The owner (12:23 IST): the retry "ready
beforehand" for the 15:30 IST MyOperator technical call (ticket 691386).
Since 21-Oct, 11 of 19 free-text replies from his WhatsApp Inbox were refused by MyOperator with HTTP 500
{"message":null} and x-amzn-ErrorType: AuthorizerConfigurationException -- their API Gateway's authorizer, before the
message service. The same customer, text and key are accepted minutes later. This kit keeps such a send and lets the
server try again; any other failure is shown at once exactly as before and is never retried.
  /root/portal/portal_inbox.py   e25bed25 -> TO   7 counted edits:
    E1 db(): a table retry_q (the queue; additive)
    E2 gateway_refusal(trace) -- true ONLY for HTTP 500 + x-amzn-ErrorType AuthorizerConfigurationException; RETRY_GAP_MIN 2,
       RETRY_FOR_MIN 60; run_retries(cfg_get) -- one pass over the queue (window re-checked before every try; a try that is
       refused the same way waits 2 minutes more, up to 60 minutes from the first; anything else gives up at once; a job
       left 'busy' by a crash is given up, never sent again); _mail_gaveup -- one mail when it stops
    E3 log_send: a retry's own lines carry quiet=True and send no "[WA send refused]" mail each (the first refusal still does)
    E4 queue_retry() beside out_row: the chat shows the message as "retrying"; the page is told it is queued
    E5 the text send and E6 the photo/PDF/voice send: that refusal goes to queue_retry instead of an error
    E7 the page: the status word "MyOperator busy — retrying", the toast on a queued send; health says kit S666
  /root/portal/inbox_retry.py    NEW -- the cron runner (every 2 minutes, under flock), calls run_retries
Usage: python make_s666.py <root holding portal/portal_inbox.py at e25bed25> <out dir>"""
import hashlib, os, sys

FROM = {"portal/portal_inbox.py": "e25bed25d025d84b57180f388c653a8b"}
src, out = sys.argv[1], sys.argv[2]
T = {}
for r, h in FROM.items():
    b = open(os.path.join(src, r), "rb").read()
    assert hashlib.md5(b).hexdigest() == h, "the live %s is not %s" % (r, h[:8])
    T[r] = b.decode("utf-8")
P = "portal/portal_inbox.py"
N = [0]


def rep(old, new):
    assert T[P].count(old) == 1, "anchor not found exactly once: %r" % old[:90]
    T[P] = T[P].replace(old, new, 1)
    N[0] += 1


# E1 -- the queue table
rep('''    CREATE TABLE IF NOT EXISTS shapes(sig TEXT PRIMARY KEY, n INTEGER NOT NULL);
    """)''', '''    CREATE TABLE IF NOT EXISTS shapes(sig TEXT PRIMARY KEY, n INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS retry_q(id INTEGER PRIMARY KEY AUTOINCREMENT, mid TEXT NOT NULL, phone TEXT NOT NULL,
        kind TEXT NOT NULL, data TEXT NOT NULL, text TEXT, fname TEXT, mime TEXT, by_user TEXT, first_ts TEXT NOT NULL,
        next_at TEXT NOT NULL, tries INTEGER NOT NULL DEFAULT 1, state TEXT NOT NULL DEFAULT 'waiting', last_err TEXT);
    """)''')

# E2 -- the rule, the pass, the give-up mail
rep('''# --------------------------------------------------------------------------- S608: the send log
''', '''# --------------------------------------------------------------------------- S666: the retry of a gateway refusal
# MyOperator's API Gateway sometimes refuses a send at its authorizer (HTTP 500, x-amzn-ErrorType:
# AuthorizerConfigurationException) -- before their message service, so nothing was sent. The same send is accepted a few
# minutes later (ticket 691386, 21-27 Oct). Only that refusal is kept and tried again; every other failure is shown at once,
# never retried, so a retry can never deliver a message twice.
RETRY_GAP_MIN = 2
RETRY_FOR_MIN = 60
RETRY_STUCK_MIN = 10


def gateway_refusal(trace):
    tr = trace or {}
    if str(tr.get("status", "")) != "500":
        return False
    for k, v in (tr.get("headers") or {}).items():
        if str(k).lower() == "x-amzn-errortype" and str(v).split(":")[0].strip() == "AuthorizerConfigurationException":
            return True
    return False


def run_retries(cfg_get, send=None):
    """One pass over the queue; inbox_retry.py calls it every 2 minutes from cron, under flock. Returns a one-line summary,
    '' when nothing was due. A job is claimed (waiting -> busy) and marked 'sent' the moment MyOperator accepts it, before any
    other bookkeeping; a job older than RETRY_FOR_MIN is given up BEFORE any call; a job found 'busy' (a crash mid-try) or a try
    whose outcome is unknown is marked 'unsure' -- never tried again, and named in the mail as 'may have gone'."""
    send = send or myop_send
    now = now_ist()
    try:
        ingest(force=True)                      # the patient's latest message counts for the window
    except Exception:                                                   # noqa: BLE001
        pass
    c = db()
    sent, gave, unsure, waiting, due = [], [], [], 0, []

    def mark_unsure(j, why):
        c.execute("UPDATE msgs SET status='unsure' WHERE mid=?", (j["mid"],))
        c.execute("UPDATE retry_q SET state='unsure', last_err=? WHERE id=?", (why[:300], j["id"]))
        e = attempt_entry(j["by_user"], j["phone"], j["kind"], j["text"] or "", {}, False, "", why,
                          fname=j["fname"] or "", mime=j["mime"] or "", route="inbox-retry")
        e["quiet"] = True
        log_send(e)
        unsure.append(e)
    try:
        stuck = iso(now - datetime.timedelta(minutes=RETRY_STUCK_MIN + RETRY_GAP_MIN))
        for j in c.execute("SELECT * FROM retry_q WHERE state='busy' AND next_at<?", (stuck,)).fetchall():
            mark_unsure(j, "the server stopped in the middle of a try -- the message MAY have gone; check before sending again")
        c.execute("UPDATE msgs SET status='sent' WHERE status='retrying' AND mid IN (SELECT mid FROM retry_q WHERE state='sent')")
        c.commit()                              # a chat row that lagged behind an accepted retry catches up
        due = c.execute("SELECT * FROM retry_q WHERE state='waiting' AND next_at<=? ORDER BY id", (iso(now),)).fetchall()
        token = _token(cfg_get) if due else ""
        for j in due:
            if c.execute("UPDATE retry_q SET state='busy' WHERE id=? AND state='waiting'", (j["id"],)).rowcount != 1:
                continue
            c.commit()
            w = window(c, j["phone"])
            first = parse_ts(j["first_ts"])
            tr = {}
            if not first or now - first >= datetime.timedelta(minutes=RETRY_FOR_MIN):
                ok, mid, err = False, "", "an hour of retrying is over"
            elif not w["open"]:
                ok, mid, err = False, "", "the patient's 24-hour window closed before MyOperator accepted it"
            elif not token:
                ok, mid, err = False, "", "the WhatsApp send key is not set on the server"
            else:
                try:
                    ok, mid, err = send(token, j["phone"], json.loads(j["data"]), trace=tr)
                except Exception as ex:                                 # noqa: BLE001 -- the outcome is unknown
                    mark_unsure(j, "the try ended in an error (%s) -- the message MAY have gone; check before sending again"
                                % type(ex).__name__)
                    c.commit()
                    continue
            e = attempt_entry(j["by_user"], j["phone"], j["kind"], j["text"] or "", tr, ok, mid, err,
                              fname=j["fname"] or "", mime=j["mime"] or "", route="inbox-retry")
            e["quiet"] = True
            e["retry_try"] = j["tries"] + 1
            if ok:
                c.execute("UPDATE retry_q SET state='sent', tries=tries+1, last_err='' WHERE id=?", (j["id"],))
                c.commit()                      # accepted is recorded first: nothing below can make it go again
                log_send(e)
                try:
                    if mid and c.execute("SELECT 1 FROM msgs WHERE mid=?", (mid,)).fetchone():   # MyOperator's echo came first
                        c.execute("UPDATE msgs SET local_path=COALESCE(NULLIF(local_path,''),?), mime=COALESCE(NULLIF(mime,''),?), "
                                  "fname=COALESCE(NULLIF(fname,''),?), sent_by=COALESCE(NULLIF(sent_by,''),?) WHERE mid=?",
                                  ("", j["mime"] or "", j["fname"] or "", j["by_user"] or "", mid))
                        old = c.execute("SELECT local_path FROM msgs WHERE mid=?", (j["mid"],)).fetchone()
                        if old and old["local_path"]:
                            c.execute("UPDATE msgs SET local_path=? WHERE mid=? AND COALESCE(local_path,'')=''", (old["local_path"], mid))
                        c.execute("DELETE FROM msgs WHERE mid=?", (j["mid"],))
                    else:
                        c.execute("UPDATE msgs SET mid=?, status='sent' WHERE mid=?", (mid or j["mid"], j["mid"]))
                    if mid:
                        _apply_pending(c, mid)
                    c.commit()
                except Exception:                                       # noqa: BLE001 -- the send stands; only the chat row lags
                    try:
                        c.rollback()
                    except Exception:                                   # noqa: BLE001
                        pass
                sent.append(j["phone"])
                continue
            if w["open"] and token and gateway_refusal(tr) and first and now - first < datetime.timedelta(minutes=RETRY_FOR_MIN):
                log_send(e)
                c.execute("UPDATE retry_q SET state='waiting', tries=tries+1, next_at=?, last_err=? WHERE id=?",
                          (iso(now + datetime.timedelta(minutes=RETRY_GAP_MIN)), (err or "")[:300], j["id"]))
                waiting += 1
            else:
                e["error"] = (err or "refused") + " -- stopped after %d tries" % (j["tries"] + (1 if tr else 0))
                log_send(e)
                c.execute("UPDATE msgs SET status='failed' WHERE mid=?", (j["mid"],))
                c.execute("UPDATE retry_q SET state='gaveup', tries=tries+1, last_err=? WHERE id=?", ((err or "")[:300], j["id"]))
                gave.append(e)
            c.commit()
    finally:
        c.close()
    if gave or unsure:
        _mail_gaveup(gave, unsure)
    if not due and not unsure:
        return ""
    return "%s retry pass: %d due, %d sent, %d still retrying, %d gave up, %d unsure" % (
        iso(now), len(due), len(sent), waiting, len(gave), len(unsure))


def _mail_gaveup(gave, unsure=()):
    """One mail to the clinic Gmail when the server stops: NOT delivered, and 'may have gone' (check before re-sending)."""
    try:
        env = read_env()
        allx = list(gave) + list(unsure)
        first = allx[0]
        subj = "[WA send %s] %s · ••••%s%s" % (
            "NOT delivered" if gave else "may have gone -- check", str(first.get("ts", ""))[:16].replace("T", " "),
            str(first.get("customer", ""))[-4:], (" (+%d more)" % (len(allx) - 1)) if len(allx) > 1 else "")
        body = ("The server stopped retrying WhatsApp message(s) from the clinic inbox. MyOperator ticket %s.\\n"
                "The full log: https://followup.dr-manoj.in/portal/inbox/sendlog\\n\\n" % MYOP_TICKET_DEFAULT)
        if gave:
            body += ("NOT DELIVERED (%d) -- marked so in the chat; send again or use a template:\\n\\n" % len(gave)
                     + "\\n".join(entry_text(e) for e in gave) + "\\n")
        if unsure:
            body += ("MAY HAVE GONE (%d) -- the server could not tell; open the patient's chat and check before sending "
                     "again:\\n\\n" % len(unsure) + "\\n".join(entry_text(e) for e in unsure))
        smtp_send([env.get("WATCHDOG_SMTP_USER", "")], subj, body)
    except Exception:                                                   # noqa: BLE001
        pass


# --------------------------------------------------------------------------- S608: the send log
''')

# E3 -- a retry's own lines send no mail each
rep('''        if not entry.get("ok") and entry.get("kind") != "log-mail":
            _note_refused(entry)''', '''        if not entry.get("ok") and entry.get("kind") != "log-mail" and not entry.get("quiet"):   # S666: retries are quiet
            _note_refused(entry)''')

# E4 -- queue_retry beside out_row; health names the kit
rep('''    @app.route("/portal/inbox/health")
    def inbox_health():                                                 # the installer's proof the module is in; carries nothing
        return jsonify({"inbox": "ok", "kit": "S608"})''', '''    def queue_retry(c, ph, kind, data, body, local_path="", mime="", fname=""):
        """S666: MyOperator's gateway refused this send at its authorizer -- nothing went. Keep it, show it as 'retrying';
        inbox_retry.py tries again every RETRY_GAP_MIN minutes for RETRY_FOR_MIN minutes."""
        mid = "retry-" + uuid.uuid4().hex
        out_row(c, ph, kind, body, mid, "retrying", local_path=local_path, mime=mime, fname=fname)
        now = now_ist()
        c.execute("INSERT INTO retry_q(mid,phone,kind,data,text,fname,mime,by_user,first_ts,next_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (mid, ph, kind, json.dumps(data, ensure_ascii=False), body or "", fname or "", mime or "",
                   (get_user() or "doctor"), iso(now), iso(now + datetime.timedelta(minutes=RETRY_GAP_MIN))))
        c.commit()
        return jsonify({"ok": True, "queued": True,
                        "note": "MyOperator is refusing for the moment. The server will try again every %d minutes "
                                "for up to %d minutes." % (RETRY_GAP_MIN, RETRY_FOR_MIN)})

    @app.route("/portal/inbox/health")
    def inbox_health():                                                 # the installer's proof the module is in; carries nothing
        return jsonify({"inbox": "ok", "kit": "S666"})''')

# E5 -- the text send
rep('''                tr = {}
                ok, mid, err = myop_send(token, ph, {"type": "text", "context": {"body": text[:4000], "preview_url": False}},
                                         trace=tr)
                log_send(attempt_entry(get_user(), ph, "text", text[:4000], tr, ok, mid, err))
                if not ok:
                    return fail(err, 502)''', '''                if c.execute("SELECT 1 FROM retry_q WHERE phone=? AND kind='text' AND text=? AND state IN ('waiting','busy')",
                             (ph, text[:4000])).fetchone():                 # S666: never the same message twice
                    return fail("This same message is already being retried by the server (MyOperator busy) -- it shows "
                                "'retrying' in the chat. Wait for it; do not send it again.")
                tr = {}
                dat = {"type": "text", "context": {"body": text[:4000], "preview_url": False}}
                ok, mid, err = myop_send(token, ph, dat, trace=tr)
                e0 = attempt_entry(get_user(), ph, "text", text[:4000], tr, ok, mid, err)
                kept = (not ok) and gateway_refusal(tr)
                if kept:
                    e0["retrying"] = True
                log_send(e0)
                if kept:                                                # S666: kept and tried again
                    return queue_retry(c, ph, "text", dat, text[:4000])
                if not ok:
                    return fail(err, 502)''')

# E6 -- the photo / PDF / voice send
rep('''            if not f:
                return fail("no file came with the message")''', '''            if not f:
                return fail("no file came with the message")
            if c.execute("SELECT 1 FROM retry_q WHERE phone=? AND kind=? AND state IN ('waiting','busy')", (ph, kind)).fetchone():
                return fail("A %s to this patient is already being retried by the server (MyOperator busy) -- wait for it; "
                            "do not send it again." % {"image": "photo", "document": "PDF", "audio": "voice note"}[kind])''')
rep('''            log_send(attempt_entry(get_user(), ph, kind, text if kind != "audio" else "", tr, ok, mid, err,
                                   fname=fname, mime=mime))
            if not ok:
                return fail(err, 502)''', '''            e0 = attempt_entry(get_user(), ph, kind, text if kind != "audio" else "", tr, ok, mid, err, fname=fname, mime=mime)
            kept = (not ok) and gateway_refusal(tr)
            if kept:
                e0["retrying"] = True
            log_send(e0)
            if kept:                                                    # S666: kept and tried again
                return queue_retry(c, ph, kind, {"type": kind, "context": ctx}, text if kind != "audio" else "",
                                   local_path=path, mime=mime, fname=fname)
            if not ok:
                return fail(err, 502)''')
# E6b -- the first refusal's mail says it is being retried
rep('''            subj = "[WA send refused] %s · ••••%s · HTTP %s%s" % (''', '''            subj = ("[WA send refused -- being retried] " if first.get("retrying") else "[WA send refused] ") + "%s · ••••%s · HTTP %s%s" % (''')

# E7 -- the page: the status word and the toast
rep('''failed:"NOT delivered",pending:"Test mode — not sent",''', '''failed:"NOT delivered",retrying:"MyOperator busy — retrying",unsure:"May have gone — check before sending again",pending:"Test mode — not sent",''')
rep('''    toast("Sent.");S.pending=null;S.lastSig="";if(t)t.value="";drawComposer();loadChat(true);loadChats();});''',
    '''    toast(j.queued?(j.note||"MyOperator busy — the server will try again."):"Sent.",j.queued?8000:0);S.pending=null;S.lastSig="";if(t)t.value="";drawComposer();loadChat(true);loadChats();});''')
assert N[0] == 10, N[0]         # E1..E5, E6 (two), E6b and the two halves of E7

RUNNER = '''#!/usr/bin/env python3
"""inbox_retry.py -- kit S666_INBOX_RETRY (the parent, S358, 27-Oct-2026). Run by cron every 2 minutes under flock:
tries again the WhatsApp Inbox sends MyOperator's gateway refused at its authorizer (portal_inbox.run_retries).
Prints one line only when something was due. Never prints a key."""
import os, sys
HERE = os.environ.get("INBOX_PORTAL_DIR", os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    import portal_config as _cfg                # the portal's own settings (VPS-only, chmod 600)
except Exception:                                                       # noqa: BLE001
    _cfg = None


def cfg_get(name, default=""):
    v = getattr(_cfg, name, None) if _cfg is not None else None
    return v if v else os.environ.get(name, default)


import portal_inbox                             # noqa: E402

if __name__ == "__main__":
    line = portal_inbox.run_retries(cfg_get)
    if line:
        print(line, flush=True)
'''
os.makedirs(os.path.join(out, "portal"), exist_ok=True)
for r, s in list(T.items()) + [("portal/inbox_retry.py", RUNNER)]:
    open(os.path.join(out, r), "wb").write(s.encode("utf-8"))
    print(r, hashlib.md5(s.encode("utf-8")).hexdigest())
