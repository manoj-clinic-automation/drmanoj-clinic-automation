#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""edits_s608.py -- kit S608 (session S331, 21-Oct-2026): the exact, counted edits that turn the live
/root/portal/portal_inbox.py (S599, 7bb6e0d7) into the S608 file.  Used two ways:
    python3 edits_s608.py LIVE_FILE OUT_FILE          -> writes the rebuilt file (refuses on any anchor count != 1)
    python3 edits_s608.py LIVE_FILE OUT_FILE KIT_FILE -> also compares with the kit's copy; exit 0 only if identical
READ ONLY on the live file.

THE OWNER, 21-Oct-2026 10:57 IST: "maintain a detailed log, which I can share with myoperator team as needed,
without needing you."  The inbox kept no record when MyOperator refused a message, so nobody could give them times.
"""
import hashlib
import sys

EDITS = []

# ---- 1. myop_send: the same request, now with a trace of what MyOperator answered ------------------------------
EDITS.append(('''def myop_send(token, phone, data, timeout=30):
    """POST one session message. Returns (ok, message_id, error). Never raises."""
    payload = {"phone_number_id": PHONE_NUMBER_ID, "customer_country_code": "91", "customer_number": phone,
               "data": data, "reply_to": None, "myop_ref_id": None}
    req = urllib.request.Request(API_URL, data=json.dumps(payload).encode("utf-8"), method="POST")
    req.add_header("Authorization", "Bearer " + token)                 # capital B required
    req.add_header("X-MYOP-COMPANY-ID", COMPANY_ID)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            status = resp.status
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8", "replace")
        except Exception:                                               # noqa: BLE001
            raw = ""
        status = e.code
    except Exception as e:                                              # noqa: BLE001
        return False, "", "could not reach MyOperator (%s)" % type(e).__name__
''', '''def myop_send(token, phone, data, timeout=30, trace=None):
    """POST one session message. Returns (ok, message_id, error). Never raises.

    S608: when `trace` (a dict) is passed it is filled with what was sent (never the key) and everything MyOperator
    answered -- status, body, headers (x-amzn-requestid is the id their tech team asks for), time taken."""
    payload = {"phone_number_id": PHONE_NUMBER_ID, "customer_country_code": "91", "customer_number": phone,
               "data": data, "reply_to": None, "myop_ref_id": None}
    req = urllib.request.Request(API_URL, data=json.dumps(payload).encode("utf-8"), method="POST")
    req.add_header("Authorization", "Bearer " + token)                 # capital B required
    req.add_header("X-MYOP-COMPANY-ID", COMPANY_ID)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    t0 = time.time()
    hdrs = {}
    if trace is not None:
        trace.update({"endpoint": API_URL, "request_json": json.dumps(payload), "status": 0, "raw": "", "headers": {},
                      "ms": 0})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            status = resp.status
            hdrs = dict(resp.headers.items())
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8", "replace")
        except Exception:                                               # noqa: BLE001
            raw = ""
        status = e.code
        try:
            hdrs = dict(e.headers.items()) if e.headers else {}
        except Exception:                                               # noqa: BLE001
            hdrs = {}
    except Exception as e:                                              # noqa: BLE001
        if trace is not None:
            trace.update({"ms": int((time.time() - t0) * 1000), "raw": "no answer: %s" % type(e).__name__})
        return False, "", "could not reach MyOperator (%s)" % type(e).__name__
    if trace is not None:
        trace.update({"status": status, "raw": raw[:4000], "ms": int((time.time() - t0) * 1000),
                      "headers": {k: v for k, v in hdrs.items() if k.lower() not in ("set-cookie", "authorization")}})
'''))

# ---- 2. the log itself, the refused-send mail, the CSV and the mail to MyOperator ------------------------------
EDITS.append(('''def safe_name(name, fallback):''', '''# --------------------------------------------------------------------------- S608: the send log
# Every send the inbox makes is written here, one JSON line each, whatever the answer. Full numbers and texts: it is
# the clinic's own record, on the clinic's own server, shown only on the owner's page, and it is what MyOperator's
# team needs to find a request in their logs. It never holds the key.
SEND_LOG = os.path.join(STORE, "send_log.jsonl")
SMTP_CLASS = None                       # the walk puts a stand-in here; None = smtplib.SMTP
MYOP_TICKET_DEFAULT = "691386"
MYOP_MAIL_TO_DEFAULT = "support@myoperator.com,khushi.jain@myoperator.co"
_NOTE_LOCK = threading.Lock()
_NOTE = {"last": 0.0, "pending": [], "busy": False}
NOTE_GAP_S = 120


def _reqid(headers):
    for k, v in (headers or {}).items():
        if k.lower() in ("x-amzn-requestid", "x-request-id", "x-amz-apigw-id", "x-amzn-trace-id"):
            return str(v)
    return ""


def log_send(entry):
    """Append one attempt. Never raises -- a log must not stop a message."""
    try:
        os.makedirs(STORE, mode=0o700, exist_ok=True)
        entry = dict(entry)
        entry.setdefault("ts", iso(now_ist()))
        entry.setdefault("id", uuid.uuid4().hex[:12])
        old = os.umask(0o077)
        try:
            with open(SEND_LOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\\n")
        finally:
            os.umask(old)
        if not entry.get("ok") and entry.get("kind") != "log-mail":
            _note_refused(entry)
    except Exception:                                                   # noqa: BLE001
        pass


def attempt_entry(user, phone, kind, text, trace, ok, mid, err, fname="", mime="", route="inbox"):
    tr = trace or {}
    return {"by": user or "doctor", "customer": phone, "kind": kind, "text": (text or "")[:1000],
            "file": fname or "", "mime": mime or "", "route": route, "ok": bool(ok), "message_id": mid or "",
            "error": err or "", "http_status": tr.get("status", ""), "myoperator_reply": tr.get("raw", ""),
            "request_id": _reqid(tr.get("headers")), "response_headers": tr.get("headers") or {},
            "ms": tr.get("ms", ""), "endpoint": tr.get("endpoint", ""), "request_json": tr.get("request_json", "")}


def read_log(days=7, only_refused=False, limit=2000):
    floor = iso(now_ist() - datetime.timedelta(days=days)) if days else ""
    out = []
    try:
        with open(SEND_LOG, encoding="utf-8") as fh:
            for line in fh:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if floor and str(e.get("ts", "")) < floor:
                    continue
                if only_refused and e.get("ok"):
                    continue
                out.append(e)
    except OSError:
        pass
    out.sort(key=lambda e: e.get("ts", ""), reverse=True)
    return out[:limit]


CSV_COLS = ("ts", "by", "customer", "kind", "text", "file", "route", "ok", "http_status", "message_id", "error",
            "myoperator_reply", "request_id", "ms", "endpoint", "request_json", "response_headers")


def log_csv(rows):
    import csv as _csv
    import io as _io
    buf = _io.StringIO()
    w = _csv.writer(buf)
    w.writerow(["time_ist", "sent_by", "customer_number", "kind", "text", "file", "route", "result", "http_status",
                "message_id", "error", "myoperator_reply", "x_amzn_requestid", "elapsed_ms", "endpoint",
                "request_json_without_key", "response_headers"])
    for e in rows:
        w.writerow([e.get("ts", ""), e.get("by", ""), ("91" + e["customer"]) if e.get("customer") else "",
                    e.get("kind", ""), e.get("text", ""), e.get("file", ""), e.get("route", ""),
                    "sent" if e.get("ok") else "REFUSED", e.get("http_status", ""), e.get("message_id", ""),
                    e.get("error", ""), e.get("myoperator_reply", ""), e.get("request_id", ""), e.get("ms", ""),
                    e.get("endpoint", ""), e.get("request_json", ""), json.dumps(e.get("response_headers") or {})])
    return buf.getvalue()


def entry_text(e):
    return ("Time (IST): %s\\nSent by: %s\\nCustomer: +91 %s\\nKind: %s\\nText: %s\\nResult: %s\\nHTTP status: %s\\n"
            "MyOperator reply: %s\\nx-amzn-requestid: %s\\nTime taken: %s ms\\nEndpoint: %s\\n"
            "Request (key not shown): %s\\nResponse headers: %s\\n"
            % (e.get("ts", ""), e.get("by", ""), e.get("customer", ""), e.get("kind", ""), e.get("text", "") or e.get("file", ""),
               "sent" if e.get("ok") else "REFUSED", e.get("http_status", ""), e.get("myoperator_reply", ""),
               e.get("request_id", "") or "(none in the answer)", e.get("ms", ""), e.get("endpoint", ""),
               e.get("request_json", ""), json.dumps(e.get("response_headers") or {})))


def smtp_send(to_list, subject, body, cc_list=(), attach_csv=None, attach_name="whatsapp_send_log.csv"):
    """Send from the clinic Gmail (the watchdog's own SMTP settings in /root/wa/.env). Returns (ok, why)."""
    import smtplib
    from email.message import EmailMessage
    env = read_env()
    host = env.get("WATCHDOG_SMTP_HOST", "smtp.gmail.com")
    port = int(env.get("WATCHDOG_SMTP_PORT", "587") or 587)
    user = env.get("WATCHDOG_SMTP_USER", "")
    pw = env.get("WATCHDOG_SMTP_PASS", "")
    if not user or not pw:
        return False, "the clinic mail settings are not on the server"
    m = EmailMessage()
    m["From"] = user
    m["To"] = ", ".join([t for t in to_list if t] or [user])
    if cc_list:
        m["Cc"] = ", ".join(cc_list)
    m["Subject"] = subject
    m.set_content(body)
    if attach_csv is not None:
        m.add_attachment(attach_csv.encode("utf-8"), maintype="text", subtype="csv", filename=attach_name)
    try:
        cls = SMTP_CLASS or smtplib.SMTP
        s = cls(host, port, timeout=30)
        try:
            s.starttls()
            s.login(user, pw)
            s.send_message(m)
        finally:
            try:
                s.quit()
            except Exception:                                           # noqa: BLE001
                pass
        return True, user
    except Exception as ex:                                             # noqa: BLE001
        return False, "the mail did not go (%s)" % type(ex).__name__


def _note_refused(entry):
    """A refused send is mailed to the clinic Gmail itself, at most one mail every two minutes (batched), so the
    record is in the mailbox, ready to forward, without anyone opening the server."""
    with _NOTE_LOCK:
        _NOTE["pending"].append(entry)
        if _NOTE["busy"]:
            return
        _NOTE["busy"] = True
    threading.Thread(target=_note_worker, daemon=True).start()


def _note_worker():
    try:
        while True:
            with _NOTE_LOCK:
                wait = _NOTE["last"] + NOTE_GAP_S - time.time()
            if wait > 0:
                time.sleep(min(wait, NOTE_GAP_S))
                continue
            with _NOTE_LOCK:
                batch, _NOTE["pending"] = _NOTE["pending"], []
                if not batch:
                    _NOTE["busy"] = False
                    return
                _NOTE["last"] = time.time()
            env = read_env()
            first = batch[0]
            subj = "[WA send refused] %s · ••••%s · HTTP %s%s" % (
                str(first.get("ts", ""))[:16].replace("T", " "), str(first.get("customer", ""))[-4:],
                first.get("http_status", "") or "no answer", (" (+%d more)" % (len(batch) - 1)) if len(batch) > 1 else "")
            body = ("MyOperator refused %d WhatsApp message(s) sent from the clinic inbox.\\n"
                    "This is the server's own record, for MyOperator's team if they ask (ticket %s).\\n"
                    "The full log: https://followup.dr-manoj.in/portal/inbox/sendlog\\n\\n" % (len(batch), MYOP_TICKET_DEFAULT)
                    + "\\n".join(entry_text(e) for e in batch))
            smtp_send([env.get("WATCHDOG_SMTP_USER", "")], subj, body)
    except Exception:                                                   # noqa: BLE001
        with _NOTE_LOCK:
            _NOTE["busy"] = False


def safe_name(name, fallback):'''))

# ---- 3. the text send: traced and logged ---------------------------------------------------------------------
EDITS.append(('''                ok, mid, err = myop_send(token, ph, {"type": "text", "context": {"body": text[:4000], "preview_url": False}})
                if not ok:
                    return fail(err, 502)''', '''                tr = {}
                ok, mid, err = myop_send(token, ph, {"type": "text", "context": {"body": text[:4000], "preview_url": False}},
                                         trace=tr)
                log_send(attempt_entry(get_user(), ph, "text", text[:4000], tr, ok, mid, err))
                if not ok:
                    return fail(err, 502)'''))

# ---- 4. the media send: traced and logged --------------------------------------------------------------------
EDITS.append(('''            ok, mid, err = myop_send(token, ph, {"type": kind, "context": ctx})
            if not ok:
                return fail(err, 502)''', '''            tr = {}
            ok, mid, err = myop_send(token, ph, {"type": kind, "context": ctx}, trace=tr)
            log_send(attempt_entry(get_user(), ph, kind, text if kind != "audio" else "", tr, ok, mid, err,
                                   fname=fname, mime=mime))
            if not ok:
                return fail(err, 502)'''))

# ---- 5. the template send (portal_wa): its result logged ------------------------------------------------------
EDITS.append(('''        except Exception as e:                                          # noqa: BLE001
            return fail("the template sender could not run (%s)" % type(e).__name__, 500)
        if not r.get("ok"):
            return fail(r.get("error") or "not sent", 502)''', '''        except Exception as e:                                          # noqa: BLE001
            return fail("the template sender could not run (%s)" % type(e).__name__, 500)
        if r.get("mode") != "DRY":
            log_send({"by": get_user() or "doctor", "customer": ph, "kind": "template", "text": b.get("template", ""),
                      "route": "inbox-template", "ok": bool(r.get("ok")), "message_id": r.get("message_id", ""),
                      "error": r.get("error", ""), "http_status": r.get("http_status", r.get("status", "")),
                      "myoperator_reply": str(r.get("raw") or r.get("response") or "")[:4000], "request_id": "",
                      "response_headers": {}, "ms": "", "endpoint": "portal_wa.send", "request_json": ""})
        if not r.get("ok"):
            return fail(r.get("error") or "not sent", 502)'''))

# ---- 6. the health line names this kit; the log's routes ------------------------------------------------------
EDITS.append(('''    @app.route("/portal/inbox/health")
    def inbox_health():                                                 # the installer's proof the module is in; carries nothing
        return jsonify({"inbox": "ok", "kit": "S599"})
''', '''    @app.route("/portal/inbox/health")
    def inbox_health():                                                 # the installer's proof the module is in; carries nothing
        return jsonify({"inbox": "ok", "kit": "S608"})

    # ---- S608: the send log -- the owner's page, its CSV, and the mail to MyOperator ----------------------------
    def _log_args():
        try:
            days = int(request.args.get("days") or (request.get_json(silent=True) or {}).get("days") or 7)
        except (TypeError, ValueError):
            days = 7
        only = str(request.args.get("only") or (request.get_json(silent=True) or {}).get("only") or "") == "refused"
        return max(1, min(days, 365)), only

    @app.route("/portal/inbox/sendlog")
    @guard
    def inbox_sendlog_page():
        return Response(LOG_PAGE, mimetype="text/html; charset=utf-8")

    @app.route("/portal/inbox/api/sendlog")
    @guard
    def inbox_sendlog_api():
        days, only = _log_args()
        rows = read_log(days, only)
        allr = read_log(days, False)
        pats = {}
        try:
            pats = patients()
        except Exception:                                               # noqa: BLE001
            pass
        for e in rows:
            e["name"] = (pats.get(e.get("customer", ""), ("", ""))[0] or "")
        sends = [e for e in allr if e.get("kind") != "log-mail"]
        return jsonify({"ok": True, "rows": rows, "total": len(sends), "refused": sum(1 for e in sends if not e.get("ok")),
                        "ticket": cfg_get("INBOX_MYOP_TICKET", "") or MYOP_TICKET_DEFAULT,
                        "mail_to": cfg_get("INBOX_MYOP_MAIL_TO", "") or MYOP_MAIL_TO_DEFAULT})

    @app.route("/portal/inbox/sendlog.csv")
    @guard
    def inbox_sendlog_csv():
        days, only = _log_args()
        name = "whatsapp_send_log_%s_%dd%s.csv" % (now_ist().strftime("%Y%m%d"), days, "_refused" if only else "")
        return Response(log_csv(read_log(days, only, limit=100000)), mimetype="text/csv; charset=utf-8",
                        headers={"Content-Disposition": "attachment; filename=%s" % name})

    @app.route("/portal/inbox/api/sendlog/email", methods=["POST"])
    @guard
    def inbox_sendlog_email():
        if not xhr_ok():
            abort(403)
        b = request.get_json(silent=True) or {}
        days, only = _log_args()
        rows = [e for e in read_log(days, only, limit=100000) if e.get("kind") != "log-mail"]
        if not rows:
            return fail("nothing in the log for that choice")
        ticket = cfg_get("INBOX_MYOP_TICKET", "") or MYOP_TICKET_DEFAULT
        to = [t.strip() for t in (cfg_get("INBOX_MYOP_MAIL_TO", "") or MYOP_MAIL_TO_DEFAULT).split(",") if t.strip()]
        cc = [t.strip() for t in (cfg_get("INBOX_MYOP_MAIL_CC", "") or "").split(",") if t.strip()]
        note = str(b.get("note") or "").strip()[:2000]
        refused = [e for e in rows if not e.get("ok")]
        body = ("Hi MyOperator team,\\n\\n"
                + ((note + "\\n\\n") if note else "")
                + "Attached is our server's log of WhatsApp sends through your public API for the last %d day(s)%s: "
                  "%d attempt(s), %d refused.\\n"
                  "Company ID %s · phone_number_id %s · endpoint %s.\\n"
                  "Each row has the time (IST), the customer, what we sent (the key is never logged), your HTTP "
                  "status, your full reply and the x-amzn-requestid header from your answer.\\n\\n"
                  % (days, " (refused only)" if only else "", len(rows), len(refused), COMPANY_ID, PHONE_NUMBER_ID, API_URL)
                + ("The refused ones:\\n\\n" + "\\n".join(entry_text(e) for e in refused[:50]) if refused else "")
                + "\\nRegards,\\nDr Manoj Agarwal Clinic, Bareilly\\n")
        subj = "Re:[## %s ##] WhatsApp send log from our server -- %s" % (ticket, now_ist().strftime("%d-%b-%Y %H:%M IST"))
        ok, why = smtp_send(to, subj, body, cc_list=cc, attach_csv=log_csv(rows),
                            attach_name="whatsapp_send_log_%s.csv" % now_ist().strftime("%Y%m%d_%H%M"))
        log_send({"by": get_user() or "doctor", "customer": "", "kind": "log-mail", "text": "%d rows to %s" % (len(rows), ", ".join(to)),
                  "route": "sendlog-email", "ok": ok, "message_id": "", "error": "" if ok else why, "http_status": "",
                  "myoperator_reply": "", "request_id": "", "response_headers": {}, "ms": "", "endpoint": "smtp",
                  "request_json": ""})
        if not ok:
            return fail(why, 502)
        return jsonify({"ok": True, "to": to, "rows": len(rows)})
'''))

# ---- 7. a "Send log" link on the inbox's own header -----------------------------------------------------------
EDITS.append(('''      <a href="/portal">Portal</a></div>''',
              '''      <span><a href="/portal/inbox/sendlog">Send log</a> · <a href="/portal">Portal</a></span></div>'''))

# ---- 8. the log page itself (English, the owner's) ------------------------------------------------------------
EDITS.append(('''PAGE = r"""<!doctype html>''', '''LOG_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WhatsApp send log</title>
<style>
:root{--ink:#16211D;--muted:#5B6B66;--line:#DDE2DE;--bg:#ECEEE9;--card:#fff;--head:#0F4F45;--acc:#0F6B5C;--bad:#9B2C1F;--badbg:#FCEDEA}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
header{background:var(--head);color:#fff;padding:14px 16px}header h1{margin:0;font-size:19px}header .sub{font-size:13px;color:#CFE5DF}
header a{color:#CFE5DF}.wrap{max-width:1000px;margin:0 auto;padding:12px 16px 60px}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:8px 0}
select,button,textarea{font:inherit}select{padding:8px;border-radius:8px;border:1px solid #bbb;background:#fff}
.btn{padding:9px 14px;border-radius:9px;border:1px solid #bbb;background:#fff;cursor:pointer;color:var(--ink);text-decoration:none;display:inline-block}
.btn.p{background:var(--acc);border-color:var(--acc);color:#fff}
.sum{font-size:14px;color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:8px 0}
.card.bad{border-color:#E8B4AC;background:var(--badbg)}
.r1{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}.r1 b{font-size:15px}
.k{color:var(--muted);font-size:13px}.ok{color:var(--acc);font-weight:600}.no{color:var(--bad);font-weight:600}
pre{white-space:pre-wrap;word-break:break-word;background:#F6F7F5;border-radius:6px;padding:6px 8px;font-size:12px;margin:6px 0 0}
details summary{cursor:pointer;color:var(--muted);font-size:13px;margin-top:4px}
#mailbox{display:none}textarea{width:100%;min-height:70px;border:1px solid #bbb;border-radius:8px;padding:8px}
#toast{position:fixed;left:0;right:0;bottom:0;background:#16211D;color:#fff;padding:12px 16px;display:none;white-space:pre-wrap}
</style></head><body>
<header><h1>WhatsApp send log</h1><div class="sub">Every message the inbox sent, and what MyOperator answered · <a href="/portal/inbox">back to the inbox</a></div></header>
<div class="wrap">
 <div class="bar">
  <select id="days"><option value="1">Today and yesterday</option><option value="7" selected>Last 7 days</option><option value="30">Last 30 days</option><option value="365">Last year</option></select>
  <select id="only"><option value="">All sends</option><option value="refused">Refused only</option></select>
  <a class="btn" id="csv" href="#">Download CSV</a>
  <button class="btn p" onclick="mailOpen()">Email to MyOperator</button>
 </div>
 <div class="sum" id="sum">Loading…</div>
 <div class="card" id="mailbox">
  <div><b>Email this log to MyOperator</b> <span class="k" id="mailto"></span></div>
  <div class="k">Goes from the clinic Gmail on ticket <span id="tk"></span>, with the log attached as a spreadsheet (CSV). Add a line if you like:</div>
  <textarea id="note" placeholder="e.g. Please check the refused messages to this customer."></textarea>
  <div class="bar"><button class="btn p" onclick="mailSend()">Send now</button><button class="btn" onclick="mailClose()">Cancel</button></div>
 </div>
 <div id="rows"></div>
</div>
<div id="toast"></div>
<script>
var $=function(i){return document.getElementById(i)};
function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})}
function toast(t){var m=$("toast");m.textContent=t;m.style.display="block";clearTimeout(toast.t);toast.t=setTimeout(function(){m.style.display="none"},5000)}
function q(){return "days="+$("days").value+"&only="+$("only").value}
function fmt(ts){ts=String(ts||"");return ts.slice(8,10)+"-"+ts.slice(5,7)+"-"+ts.slice(0,4)+" "+ts.slice(11,16)}
function load(){
 $("csv").href="/portal/inbox/sendlog.csv?"+q();
 fetch("/portal/inbox/api/sendlog?"+q(),{headers:{"X-Inbox":"1"}}).then(function(r){return r.json()}).then(function(j){
  if(!j.ok){$("sum").textContent=j.error||"could not read the log";return}
  $("tk").textContent=j.ticket;$("mailto").textContent="· to "+j.mail_to;
  $("sum").textContent=j.total+" send(s) in this period · "+j.refused+" refused by MyOperator";
  var h="";
  j.rows.forEach(function(e){
   var who=(e.name?e.name+" · ":"")+(e.customer?"+91 "+e.customer:"");
   h+='<div class="card'+(e.ok?'':' bad')+'"><div class="r1"><b>'+esc(fmt(e.ts))+' · '+esc(who||e.kind)+'</b>'+
    (e.ok?'<span class="ok">✓ sent</span>':'<span class="no">✗ refused · HTTP '+esc(e.http_status||"no answer")+'</span>')+'</div>'+
    '<div class="k">'+esc(e.kind)+' · by '+esc(e.by)+(e.ms!==""?' · '+esc(e.ms)+' ms':'')+(e.request_id?' · request id '+esc(e.request_id):'')+'</div>'+
    (e.text||e.file?'<div>'+esc(e.text||e.file)+'</div>':'')+
    (e.ok?'':'<div class="no" style="font-weight:400">'+esc(e.error)+'</div>')+
    '<details><summary>Technical details for MyOperator</summary><pre>Their reply: '+esc(e.myoperator_reply)+'\\nRequest (key not shown): '+esc(e.request_json)+'\\nResponse headers: '+esc(JSON.stringify(e.response_headers||{}))+'</pre></details></div>';
  });
  $("rows").innerHTML=h||'<div class="card">Nothing logged in this period yet. Every send from now on is recorded here.</div>';
 }).catch(function(){$("sum").textContent="could not read the log"});
}
function mailOpen(){$("mailbox").style.display="block";$("note").focus()}
function mailClose(){$("mailbox").style.display="none"}
function mailSend(){
 fetch("/portal/inbox/api/sendlog/email?"+q(),{method:"POST",headers:{"X-Inbox":"1","Content-Type":"application/json"},
  body:JSON.stringify({days:$("days").value,only:$("only").value,note:$("note").value})})
 .then(function(r){return r.json()}).then(function(j){ if(j.ok){toast("Sent to "+j.to.join(", ")+" ("+j.rows+" rows).");mailClose();$("note").value=""}else toast(j.error||"not sent")})
 .catch(function(){toast("not sent")});
}
$("days").onchange=load;$("only").onchange=load;load();
</script></body></html>"""


PAGE = r"""<!doctype html>'''))


def main():
    live, out = sys.argv[1], sys.argv[2]
    kit = sys.argv[3] if len(sys.argv) > 3 else None
    s = open(live, encoding="utf-8").read()
    for i, (old, new) in enumerate(EDITS, 1):
        n = s.count(old)
        if n != 1:
            print("  REFUSED: edit %d's anchor occurs %d times (expected 1)" % (i, n))
            return 1
        s = s.replace(old, new)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    a = hashlib.md5(open(out, "rb").read()).hexdigest()
    print("  %d edits applied · rebuilt %s" % (len(EDITS), a[:8]))
    if kit:
        b = hashlib.md5(open(kit, "rb").read()).hexdigest()
        print("  kit %s  %s" % (b[:8], "same" if a == b else "DIFFERENT"))
        return 0 if a == b else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
