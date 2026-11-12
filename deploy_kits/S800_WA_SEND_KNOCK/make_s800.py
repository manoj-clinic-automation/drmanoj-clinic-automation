#!/usr/bin/python3
# make_s800.py -- kit S800_WA_SEND_KNOCK (S437, 12-Nov-2026, the parent). Usage: make_s800.py <live portal_inbox.py> <live portal_wa.py> <out dir>
# F-1031: MyOperator's gateway refuses the FIRST request after idle (HTTP 500 from its authorizer, before their message service --
# nothing sent) and accepts the same request about two seconds later (S799's probe on the box, 12:05 IST 12-Nov). The two senders
# try a refused request again at once, five tries at most. Exact replacements on the live bytes (portal_inbox.py 06e2c28e -- S793;
# portal_wa.py 34994b23); every anchor must occur once.
import hashlib, os, sys
pi, pw, out = sys.argv[1], sys.argv[2], sys.argv[3]
def load(p, want):
    b = open(p, "rb").read()
    assert hashlib.md5(b).hexdigest().startswith(want), "not the live %s (%s)" % (os.path.basename(p), want)
    return b.decode("utf-8")
def rp(t, a, n):
    assert t.count(a) == 1, "anchor not once: " + a[:70]
    return t.replace(a, n)

# ---- the Inbox's sender
I = load(pi, "06e2c28e")
I = rp(I, '''def myop_send(token, phone, data, timeout=30, trace=None):
    """POST one session message. Returns (ok, message_id, error). Never raises.
''', '''def _myop_send_once(token, phone, data, timeout=30, trace=None):
    """POST one session message, ONE try (S800: myop_send below tries a gateway refusal again). Returns (ok, message_id, error). Never raises.
''')
I = rp(I, '''# --------------------------------------------------------------------------- S666: the retry of a gateway refusal
''', '''# --------------------------------------------------------------------------- S800: a refused try is followed at once
# MyOperator's gateway refuses the FIRST request after it has been idle (HTTP 500 from its authorizer, in about a tenth of a
# second, before their message service -- nothing was sent); the same request about two seconds later is accepted (S799's probe on
# the box, 12-Nov-2026: the first four of 24 requests refused, the twenty after them accepted; the send log: a try 10-60 s after
# another accepted about half the time, a try minutes after another almost never). So a refusal is tried again here, at once. It
# can never deliver a message twice, for the same reason the S666 retry cannot: the refusal comes before their message service.
# What is still refused after the last try goes to the S666 queue exactly as before.
S800_WAITS = (2.5, 3.0, 4.0, 6.0)        # seconds before the 2nd, 3rd, 4th and 5th try


def myop_send(token, phone, data, timeout=30, trace=None):
    """POST one session message; a gateway refusal is tried again after a short wait (S800). Returns (ok, message_id, error).
    Never raises. `trace` carries the LAST try, plus "attempts": what each try got ("500A" = refused at the gateway)."""
    tr = trace if trace is not None else {}
    attempts = []
    res = (False, "", "not tried")
    for i in range(len(S800_WAITS) + 1):
        one = {}
        res = _myop_send_once(token, phone, data, timeout=(timeout if i == 0 else min(timeout, 10)), trace=one)
        refused = gateway_refusal(one)
        attempts.append("500A" if refused else str(one.get("status") or "none"))
        tr.clear()                                 # the LAST try only: never one try's status beside another's headers
        tr.update(one)
        if not refused or i == len(S800_WAITS):
            break
        time.sleep(S800_WAITS[i])
    tr["attempts"] = attempts
    return res


# --------------------------------------------------------------------------- S666: the retry of a gateway refusal
''')

# ---- the portal's template sender
Wt = load(pw, "34994b23")
Wt = rp(Wt, "import os, csv, json, re, ssl, urllib.request, urllib.error\n", "import os, csv, json, re, ssl, time, urllib.request, urllib.error\n")
a0 = "    try:\n        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:\n"
a1 = '''    _log({"ts_ist": now, "sent_by": sent_by, "phone": ph, "template": template_name,
          "values_json": json.dumps(values or {}), "mode": "LIVE",
          "ok": "1" if r["ok"] else "0", "message_id": r.get("message_id", ""),
'''
assert Wt.count(a0) == 1 and Wt.count(a1) == 1, "portal_wa.py: the send block's ends not once"
i, j = Wt.index(a0), Wt.index(a1)
block = Wt[i:j]
assert block.rstrip("\n").endswith('"error": "send failed: %s" % e}') and block.count("urlopen(") == 1 and "\ndef " not in block, "portal_wa.py: the send block is not the expected one"
h0 = '''        r = {"ok": False, "message_id": "", "conversation_id": "", "mode": "LIVE",
             "error": "HTTP %s: %s" % (e.code, body_err or e.reason)}
'''
assert block.count(h0) == 1, "portal_wa.py: the HTTP-error branch is not the expected one"
block2 = block.replace(h0, h0 + '''        try:                                               # S800: their authorizer's header marks the gateway's own refusal
            r["_gateway_refused"] = (e.code == 500 and "AuthorizerConfigurationException" in str(e.headers.get("x-amzn-ErrorType", "") if e.headers else ""))
        except Exception:
            r["_gateway_refused"] = False
''')
Wt = Wt[:i] + '''    r = _s800_once(req, timeout, ctx)
    tries = 1
    for _w in S800_WAITS:                                  # S800: refused at the gateway -> the same request again, at once
        if not _s800_refused(r):
            break
        time.sleep(_w)
        r = _s800_once(req, timeout, ctx)
        tries += 1
    r.pop("_gateway_refused", None)
    if tries > 1:
        r["tries"] = tries

''' + Wt[j:]
Wt = rp(Wt, '''# --------------------------- the sender ------------------------------------- #
''', '''# --------------------------- S800: one try, and when it is tried again ------- #
# MyOperator's gateway refuses the FIRST request after idle (HTTP 500 {"message":null} from its authorizer, before their message
# service -- nothing sent) and accepts the same request about two seconds later (S799's probe, 12-Nov-2026). A refused try is tried
# again at once, five tries at most; it can never deliver a template twice.
S800_WAITS = (2.5, 3.0, 4.0, 6.0)


def _s800_refused(r):
    """True only for the gateway's own refusal: HTTP 500 WITH x-amzn-ErrorType AuthorizerConfigurationException (the Inbox's rule)."""
    return (not (r or {}).get("ok")) and bool((r or {}).get("_gateway_refused"))


def _s800_once(req, timeout, ctx):
''' + block2.rstrip("\n") + '''
    return r


# --------------------------- the sender ------------------------------------- #
''')
os.makedirs(os.path.join(out, "portal"), exist_ok=True)
for name, t in (("portal_inbox.py", I), ("portal_wa.py", Wt)):
    with open(os.path.join(out, "portal", name), "wb") as fh:
        fh.write(t.encode("utf-8"))
    print(name, hashlib.md5(t.encode("utf-8")).hexdigest())
