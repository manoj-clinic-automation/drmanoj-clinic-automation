#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prove_s802.py -- kit S802_WA_SEND_HEADERS (S437, 12-Nov-2026, the parent). SENDS NOTHING.

F-1031. MyOperator's gateway seems to keep an authorisation per key for a while, so a test with the real key can be helped by
an earlier request. A FRESH made-up key has no such help: its proper answer is "not authorised" (401/403), and F-1031's
signature is HTTP 500 from their authorizer ("500A"). Every made-up key here is new and used once. The real key is used only
with an EMPTY number and EMPTY text (nothing can be delivered; the proper answer is HTTP 400). No key is ever printed.

  prove_s802.py <dir of the changed portal_inbox.py>     the table, two rounds, and a last line:
      PROVE: PROVEN     the old road (urllib) is refused, the same request with header names as written is answered properly,
                        and the changed Inbox sender is answered properly with a fresh made-up key AND with the real key
      PROVE: NOT-SHOWN  the old road is not being refused right now -- nothing to prove, nothing is changed
      PROVE: FAILED     anything else
  prove_s802.py <installed portal dir> --installed        the installed sender, the real key, an empty number: 400 or not
"""
import http.client
import json
import os
import re
import secrets
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

PORTAL_DIR = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "/root/portal"
ROUNDS = int(os.environ.get("S802_ROUNDS", "2"))
GAP = float(os.environ.get("S802_GAP", "1.0"))


def load():
    if PORTAL_DIR not in sys.path:
        sys.path.insert(0, PORTAL_DIR)
    cfgdir = os.environ.get("S802_CONFIG_DIR", "/root/portal")         # the portal's own settings stay where they are (never copied)
    if cfgdir not in sys.path:
        sys.path.append(cfgdir)
    try:
        import portal_config as _cfg
    except Exception:                                                  # noqa: BLE001
        _cfg = None

    def cfg_get(name, default=""):
        v = getattr(_cfg, name, None) if _cfg is not None else None
        return v if v else os.environ.get(name, default)
    import portal_inbox as pi
    if os.path.dirname(os.path.abspath(pi.__file__)) != PORTAL_DIR:
        raise RuntimeError("portal_inbox came from another folder")
    tok = os.environ.get("S802_TOKEN") or pi._token(cfg_get)
    if os.environ.get("S802_API_URL"):
        pi.API_URL = os.environ["S802_API_URL"]
    return pi, tok


def fresh():
    return "s802-made-up-" + secrets.token_hex(8)


def is_refusal(status, etype, raw):
    return status == 500 and ("AuthorizerConfigurationException" in (etype or "") or re.sub(r"\s", "", raw or "") == '{"message":null}')


def cell(ans):
    return "500A" if is_refusal(*ans) else (str(ans[0]) if ans[0] else "none")


def via_urllib(url, token, company, body):
    req = urllib.request.Request(url, data=body, method="POST")
    for k, v in (("Authorization", "Bearer " + token), ("X-MYOP-COMPANY-ID", company), ("Content-Type", "application/json"), ("Accept", "application/json")):
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


def via_httpclient(url, token, company, body, company_header="X-MYOP-COMPANY-ID", extra=None):
    u = urlparse(url)
    conn = (http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection)(u.netloc, timeout=30)
    h = {"Authorization": "Bearer " + token, company_header: company, "Content-Type": "application/json", "Accept": "application/json"}
    h.update(extra or {})
    try:
        conn.request("POST", u.path or "/", body, h)
        r = conn.getresponse()
        return r.status, r.getheader("x-amzn-ErrorType", "") or "", r.read(300).decode("utf-8", "replace")
    except Exception as e:                                             # noqa: BLE001
        return 0, type(e).__name__, ""
    finally:
        try:
            conn.close()
        except Exception:                                              # noqa: BLE001
            pass


def changed_sender(pi, token):
    tr = {}
    pi.myop_send(token, "", {"type": "text", "context": {"body": ""}}, trace=tr)   # an empty number, empty text: nothing can go
    return "500A" if pi.gateway_refusal(tr) else str(tr.get("status") or "none")


def main():
    try:
        pi, tok = load()
    except Exception as e:                                             # noqa: BLE001
        print("PROVE: ERROR the Inbox sender could not be loaded (%s: %s)" % (type(e).__name__, str(e)[:80]))
        return 2
    if not tok:
        print("PROVE: ERROR no key on the box")
        return 2
    if "--installed" in sys.argv:
        got = changed_sender(pi, tok)
        print("INSTALLED: the Inbox sender, the real key, an empty number, nothing sent: %s -- %s" % (got, "let through" if got == "400" else "NOT A PROPER ANSWER"))
        return 0 if got == "400" else 1
    url, company = pi.API_URL, pi.COMPANY_ID
    body = json.dumps({"phone_number_id": pi.PHONE_NUMBER_ID, "customer_country_code": "91", "customer_number": "",
                       "data": {"type": "text", "context": {"body": ""}}, "reply_to": None, "myop_ref_id": None}).encode("utf-8")
    ways = [
        ("1 urllib -- the Inbox's road today (header names re-cased on the wire)", lambda: via_urllib(url, fresh(), company, body)),
        ("2 http.client, the header names exactly as written                   ", lambda: via_httpclient(url, fresh(), company, body)),
        ("3 http.client, but the company header named as urllib sends it       ", lambda: via_httpclient(url, fresh(), company, body, company_header="X-Myop-Company-Id")),
        ("4 http.client as written, with urllib's 'Connection: close'          ", lambda: via_httpclient(url, fresh(), company, body, extra={"Connection": "close"})),
    ]
    res = [[] for _ in ways]
    for _ in range(ROUNDS):
        for i, (_label, fn) in enumerate(ways):
            res[i].append(cell(fn()))
            time.sleep(GAP / 2.0)
        time.sleep(GAP)
    b_made = [changed_sender(pi, fresh()) for _ in range(ROUNDS)]
    b_real = changed_sender(pi, tok)
    print("each request with a FRESH made-up key, used once -- NOTHING SENT (500A = HTTP 500 from their authorizer; 401/403 = the proper answer)")
    for (label, _fn), r in zip(ways, res):
        print("  %s  %s" % (label, " ".join(r)))
    print("  5 the CHANGED Inbox sender, fresh made-up keys                         %s" % " ".join(b_made))
    print("  6 the CHANGED Inbox sender, the real key, empty number and text        %s   (400 = let through; the empty number is refused by the service)" % b_real)
    proper = ("401", "403")
    old_refused = all(x == "500A" for x in res[0])
    if not old_refused and all(x in proper for x in res[0]):
        print("PROVE: NOT-SHOWN the old road is answered properly right now (%s) -- nothing to prove" % " ".join(res[0]))
        return 3
    if old_refused and all(x in proper for x in res[1]) and all(x in proper for x in b_made) and b_real == "400":
        which = "the company header's name is what decides" if all(x == "500A" for x in res[2]) else "the company header's name alone does not decide it"
        print("PROVE: PROVEN the old road is refused; with the header names as written the gateway answers properly (%s)" % which)
        return 0
    print("PROVE: FAILED the table above does not show it")
    return 1


if __name__ == "__main__":
    sys.exit(main())
