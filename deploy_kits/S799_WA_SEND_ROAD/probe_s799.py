#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_s799.py -- kit S799_WA_SEND_ROAD (S437, 12-Nov-2026, the parent). SENDS NOTHING.

The owner, 11:25 IST: the Callback Tracker's WhatsApp section sends through the API while his Inbox fails (F-1031). The tracker
sends through the server's relay (wa_send.py: Python's http.client); the Inbox and the portal's template sender go to the SAME
address with the same headers through urllib. On the wire the two differ only in what urllib adds by itself.

This asks MyOperator's gateway the same question four ways, three rounds each, with two keys:
  * a MADE-UP key   -- the right answer is "not authorised" (401/403); F-1031's signature is HTTP 500 from their authorizer;
  * the REAL key    -- with an EMPTY number and EMPTY text: nothing can be delivered; the right answer is a validation error.
No patient number, no message text, no template is in any request. The key is read on the box and never printed.

  probe_s799.py              the table and a VERDICT line
  probe_s799.py --installed  three tries through the INSTALLED Inbox sender (real key, empty number, empty text): refused or not

VERDICT: DECISIVE-UA      urllib's own way is refused and the same call with a plain User-Agent is not  -> the kit's one-line fix fits
         DECISIVE-CLIENT  urllib is refused even with a plain User-Agent, http.client is not             -> no automatic fix
         NOT-DECISIVE     anything else                                                                  -> nothing is changed
"""
import http.client
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

API_URL = os.environ.get("S799_API_URL", "https://publicapi.myoperator.co/chat/messages")
PORTAL_DIR = os.environ.get("S799_PORTAL_DIR", "/root/portal")
ROUNDS = int(os.environ.get("S799_ROUNDS", "3"))
GAP = float(os.environ.get("S799_GAP", "1.5"))
UA_PLAIN = "clinic-portal/1.0"
UA_URLLIB = "Python-urllib/%d.%d" % sys.version_info[:2]
MADE_UP = "made-up-key-for-the-S799-probe"


def ids_and_key():
    """(company_id, phone_number_id, real key or '') -- the way inbox_retry.py gets them; a test may give S799_TOKEN."""
    company = os.environ.get("S799_COMPANY", "")
    pnid = os.environ.get("S799_PNID", "")
    tok = os.environ.get("S799_TOKEN", "")
    try:
        if PORTAL_DIR not in sys.path:
            sys.path.insert(0, PORTAL_DIR)
        try:
            import portal_config as _cfg
        except Exception:                                              # noqa: BLE001
            _cfg = None

        def cfg_get(name, default=""):
            v = getattr(_cfg, name, None) if _cfg is not None else None
            return v if v else os.environ.get(name, default)
        import portal_inbox
        company = company or portal_inbox.COMPANY_ID
        pnid = pnid or portal_inbox.PHONE_NUMBER_ID
        tok = tok or portal_inbox._token(cfg_get)
        return company, pnid, tok, portal_inbox
    except Exception as e:                                             # noqa: BLE001
        return company, pnid, tok, None


def body_empty(pnid):
    return json.dumps({"phone_number_id": pnid, "customer_country_code": "91", "customer_number": "",
                       "data": {"type": "text", "context": {"body": ""}}, "reply_to": None, "myop_ref_id": None}).encode("utf-8")


def _headers(token, company, ua):
    h = {"Authorization": "Bearer " + token, "X-MYOP-COMPANY-ID": company, "Content-Type": "application/json", "Accept": "application/json"}
    if ua:
        h["User-Agent"] = ua
    return h


def via_urllib(token, company, body, ua=None):
    req = urllib.request.Request(API_URL, data=body, method="POST")
    for k, v in _headers(token, company, ua).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.headers.get("x-amzn-ErrorType", "") or "", r.read(300).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            raw = e.read(300).decode("utf-8", "replace")
        except Exception:                                              # noqa: BLE001
            raw = ""
        return e.code, (e.headers.get("x-amzn-ErrorType", "") if e.headers else "") or "", raw
    except Exception as e:                                             # noqa: BLE001
        return 0, type(e).__name__, ""


def via_httpclient(token, company, body, ua=None):
    u = urlparse(API_URL)
    C = http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection
    conn = C(u.netloc, timeout=30)
    try:
        conn.request("POST", u.path or "/", body, _headers(token, company, ua))
        r = conn.getresponse()
        return r.status, r.getheader("x-amzn-ErrorType", "") or "", r.read(300).decode("utf-8", "replace")
    except Exception as e:                                             # noqa: BLE001
        return 0, type(e).__name__, ""
    finally:
        try:
            conn.close()
        except Exception:                                              # noqa: BLE001
            pass


def refused(ans):
    """F-1031's signature: HTTP 500 from the gateway's authorizer (or its bare {"message":null})."""
    status, etype, raw = ans
    return status == 500 and ("AuthorizerConfigurationException" in (etype or "") or re.sub(r"\s", "", raw or "") == '{"message":null}')


def cell(ans):
    return "500A" if refused(ans) else (str(ans[0]) if ans[0] else "none")


WAYS = [
    ("1 urllib, as the Inbox sends today      ", via_urllib, None),
    ("2 urllib + a plain User-Agent           ", via_urllib, UA_PLAIN),
    ("3 http.client, as the tracker's relay   ", via_httpclient, None),
    ("4 http.client + urllib's own User-Agent ", via_httpclient, UA_URLLIB),
]


def run():
    company, pnid, tok, _pi = ids_and_key()
    if not company or not pnid:
        print("the Inbox's own settings could not be read (portal_inbox not importable)")
        print("VERDICT: NOT-DECISIVE")
        return
    body = body_empty(pnid)
    res = {}
    for rnd in range(ROUNDS):
        for i, (_label, fn, ua) in enumerate(WAYS):
            res.setdefault((i, "made-up"), []).append(fn(MADE_UP, company, body, ua))
            if tok:
                res.setdefault((i, "real"), []).append(fn(tok, company, body, ua))
            time.sleep(GAP / 4.0)
        time.sleep(GAP)
    print("the gateway asked %d times each way -- NOTHING SENT (500A = HTTP 500 from their authorizer, F-1031's signature)" % ROUNDS)
    print("  way                                       a made-up key      the real key, empty number and text")
    for i, (label, _fn, _ua) in enumerate(WAYS):
        a = " ".join(cell(x) for x in res.get((i, "made-up"), []))
        b = " ".join(cell(x) for x in res.get((i, "real"), [])) if tok else "(no key on the box)"
        print("  %s  %-18s %s" % (label, a, b))
    key = "real" if tok else "made-up"
    r = lambda i: sum(1 for x in res.get((i, key), []) if refused(x))  # noqa: E731
    ok = lambda i: all((not refused(x)) and 0 < x[0] < 500 for x in res.get((i, key), []))  # noqa: E731
    need = max(2, ROUNDS - 1)
    if r(0) >= need and ok(1):
        v = "DECISIVE-UA"
    elif r(0) >= need and r(1) >= 1 and ok(2):
        v = "DECISIVE-CLIENT"
    else:
        v = "NOT-DECISIVE"
    print("judged on the %s key: way 1 refused %d of %d, way 2 refused %d, way 3 refused %d, way 4 refused %d" % (key, r(0), ROUNDS, r(1), r(2), r(3)))
    print("VERDICT: " + v)


def installed():
    """Three tries through the INSTALLED Inbox sender: the real key, an empty number, empty text. Nothing can be delivered."""
    company, pnid, tok, pi = ids_and_key()
    if pi is None or not tok:
        print("INSTALLED: could not load the Inbox sender or its key")
        return 2
    if os.environ.get("S799_API_URL"):
        pi.API_URL = os.environ["S799_API_URL"]
    bad = 0
    out = []
    for _ in range(ROUNDS):
        tr = {}
        pi.myop_send(tok, "", {"type": "text", "context": {"body": ""}}, trace=tr)
        ref = pi.gateway_refusal(tr) or (str(tr.get("status")) == "500")
        bad += 1 if ref else 0
        out.append("500A" if ref else str(tr.get("status") or "none"))
        time.sleep(GAP)
    print("INSTALLED: the Inbox sender, %d tries, nothing sent: %s -> %s" % (ROUNDS, " ".join(out), "REFUSED" if bad else "not refused"))
    return 1 if bad else 0


if __name__ == "__main__":
    if "--installed" in sys.argv:
        sys.exit(installed())
    run()
