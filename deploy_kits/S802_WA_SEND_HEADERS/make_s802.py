#!/usr/bin/python3
# make_s802.py -- kit S802_WA_SEND_HEADERS (S437, 12-Nov-2026, the parent). Usage: make_s802.py <live portal_inbox.py> <live portal_wa.py> <out dir>
# F-1031. urllib re-cases header names on the wire -- "X-MYOP-COMPANY-ID" leaves as "X-Myop-Company-Id" -- and MyOperator's gateway
# refuses that form at its authorizer (HTTP 500) unless a properly-cased request with the same key has just been let through.
# http.client sends header names exactly as written (the tracker's relay, wa_send.py, has always sent that way). The two senders'
# ONE request is moved from urllib to http.client; nothing else changes (one try; the S666 queue as it is).
# Each replaced block is cut between two anchors that must occur once and is checked against its md5 before it is replaced.
import hashlib, os, sys
pi, pw, out = sys.argv[1], sys.argv[2], sys.argv[3]
def load(p, want):
    b = open(p, "rb").read()
    assert hashlib.md5(b).hexdigest().startswith(want), "not the live %s (%s)" % (os.path.basename(p), want)
    return b.decode("utf-8")
def rp(t, a, n):
    assert t.count(a) == 1, "anchor not once: " + a[:70]
    return t.replace(a, n)
def cut(t, a0, a1, want_md5, new):
    assert t.count(a0) == 1 and t.count(a1) == 1, "the block's ends are not once each: " + a0[:50]
    i, j = t.index(a0), t.index(a1)
    assert i < j, "the block's ends are in the wrong order"
    got = hashlib.md5(t[i:j].encode("utf-8")).hexdigest()
    assert got == want_md5 or want_md5 == "PRINT", "the block is not the expected one (%s)" % got
    if want_md5 == "PRINT":
        print("block md5", got)
    return t[:i] + new + t[j:]

# ---- the Inbox's sender
I = load(pi, "06e2c28e")
I = rp(I, "import os, re, json, time, uuid, sqlite3, secrets, hashlib, threading, mimetypes, datetime, urllib.request, urllib.error\n",
       "import os, re, json, time, uuid, sqlite3, secrets, hashlib, threading, mimetypes, datetime, urllib.request, urllib.error\nimport http.client                                                     # S802\n")
I = cut(I, '    req = urllib.request.Request(API_URL, data=json.dumps(payload).encode("utf-8"), method="POST")\n',
        '    if trace is not None:\n        trace.update({"status": status, "raw": raw[:4000], "ms": int((time.time() - t0) * 1000),\n',
        "66723df575a40afe6173d8537b423a87", '''    # S802 (F-1031): sent through http.client, the header names EXACTLY as written. urllib re-cases them on the wire
    # ("X-MYOP-COMPANY-ID" leaves as "X-Myop-Company-Id") and MyOperator's gateway refuses that form at its authorizer
    # (HTTP 500, AuthorizerConfigurationException) unless a properly-cased request with the same key has just been let through.
    body = json.dumps(payload).encode("utf-8")
    send_headers = {"Authorization": "Bearer " + token,                # capital B required
                    "X-MYOP-COMPANY-ID": COMPANY_ID, "Content-Type": "application/json", "Accept": "application/json"}
    t0 = time.time()
    hdrs = {}
    if trace is not None:
        trace.update({"endpoint": API_URL, "request_json": json.dumps(payload), "status": 0, "raw": "", "headers": {},
                      "ms": 0})
    conn = None
    try:
        u = urlparse(API_URL)
        conn = (http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection)(u.netloc, timeout=timeout)
        conn.request("POST", u.path or "/", body, send_headers)
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8", "replace")
        status = resp.status
        hdrs = dict(resp.getheaders())
    except Exception as e:                                              # noqa: BLE001
        if trace is not None:
            trace.update({"ms": int((time.time() - t0) * 1000), "raw": "no answer: %s" % type(e).__name__})
        return False, "", "could not reach MyOperator (%s)" % type(e).__name__
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:                                               # noqa: BLE001
            pass
''')

# ---- the portal's template sender
Wt = load(pw, "34994b23")
Wt = rp(Wt, "import os, csv, json, re, ssl, urllib.request, urllib.error\n",
        "import os, csv, json, re, ssl, urllib.request, urllib.error\nimport http.client                                       # S802\nfrom urllib.parse import urlparse                        # S802\n")
Wt = cut(Wt, '    data = json.dumps(payload).encode("utf-8")\n    req = urllib.request.Request(BASE + SEND_PATH, data=data, method="POST")\n',
         '    _log({"ts_ist": now, "sent_by": sent_by, "phone": ph, "template": template_name,\n          "values_json": json.dumps(values or {}), "mode": "LIVE",\n          "ok": "1" if r["ok"] else "0", "message_id": r.get("message_id", ""),\n',
         "6062e0cc690107a99eb7fbf2fed74e96", '''    data = json.dumps(payload).encode("utf-8")
    # S802 (F-1031): sent through http.client, the header names EXACTLY as written. urllib re-cases them on the wire
    # ("X-MYOP-COMPANY-ID" leaves as "X-Myop-Company-Id") and MyOperator's gateway refuses that form at its authorizer.
    conn = None
    try:
        u = urlparse(BASE + SEND_PATH)
        conn = (http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection)(u.netloc, timeout=timeout)
        conn.request("POST", u.path or "/", data, {"Authorization": "Bearer " + token,   # capital B required
                                                   "X-MYOP-COMPANY-ID": COMPANY_ID, "Content-Type": "application/json"})
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8", "replace")
        if resp.status >= 300:
            r = {"ok": False, "message_id": "", "conversation_id": "", "mode": "LIVE",
                 "error": "HTTP %s: %s" % (resp.status, raw[:200] or resp.reason)}
        else:
            j = json.loads(raw) if raw else {}
            d = j.get("data") or {}
            mid = d.get("message_id", "")
            cid = d.get("conversation_id") or d.get("conversaton_id") or ""  # misspelling seen in webhooks
            ok = (j.get("status") == "success") or bool(mid)
            r = {"ok": ok, "message_id": mid, "conversation_id": cid, "mode": "LIVE",
                 "error": "" if ok else ("unexpected response: " + raw[:200])}
    except Exception as e:
        r = {"ok": False, "message_id": "", "conversation_id": "", "mode": "LIVE",
             "error": "send failed: %s" % e}
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass

''')
os.makedirs(os.path.join(out, "portal"), exist_ok=True)
for name, t in (("portal_inbox.py", I), ("portal_wa.py", Wt)):
    with open(os.path.join(out, "portal", name), "wb") as fh:
        fh.write(t.encode("utf-8"))
    print(name, hashlib.md5(t.encode("utf-8")).hexdigest())
