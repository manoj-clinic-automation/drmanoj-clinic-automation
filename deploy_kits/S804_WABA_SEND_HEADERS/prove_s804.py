#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prove_s804.py -- kit S804_WABA_SEND_HEADERS (S439, 12-Nov-2026, the parent). SENDS NOTHING.

F-1294 (F-1031's cause, shown by S802 at 15:35 IST 12-Nov). MyOperator's gateway keeps an authorisation per key for a while, so
a test with the real key can be helped by an earlier request. A FRESH made-up key has no such help: its proper answer is "not
authorised" (401/403), and the fault's signature is HTTP 500 from their authorizer ("500A"). Every made-up key here is new and
used once. The real key is used only with an EMPTY number and EMPTY text -- the request S802 made on this box, answered HTTP 400:
nothing can be delivered. No key and no setting is ever printed; the account's settings are read by key from the box's own file.

  prove_s804.py <dir of the changed waba.py>          the table, two rounds, and a last line:
      PROVE: PROVEN     the old road (urllib) is refused, the same request with header names as written is answered properly,
                        and the changed waba.send_template is answered properly with a fresh made-up key AND with the real key
      PROVE: NOT-SHOWN  the old road is not being refused right now -- nothing to prove, nothing is changed
      PROVE: FAILED     anything else
  prove_s804.py <the installed /root/wa> --installed  the installed waba.send_template, the real key, an empty number: 400 or not
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

WA_DIR = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "/root/wa"
ROUNDS = int(os.environ.get("S804_ROUNDS", "2"))
GAP = float(os.environ.get("S804_GAP", "1.0"))
KEYS = ("MYOP_BASE_URL", "MYOP_COMPANY_ID", "MYOP_PHONE_NUMBER_ID", "MYOP_WABA_ID", "MYOP_AUTH_TOKEN", "MYOP_COUNTRY_CODE",
        "WABA_TEMPLATE_BODY_FORMAT")


def load():
    os.environ.pop("WABA_DEBUG", None)                                 # waba.py prints the request when this is set
    envf = os.environ.get("S804_ENV_FILE", "/root/wa/.env")           # waba.py's own settings stay where they are (never copied)
    if os.path.isfile(envf):
        for line in open(envf, encoding="utf-8").read().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k in KEYS and v and "PASTE_" not in v and "_HERE" not in v:
                os.environ[k] = v
    if os.environ.get("S804_API_BASE"):                                # the walk's stand-in gateway
        os.environ["MYOP_BASE_URL"] = os.environ["S804_API_BASE"]
    if os.environ.get("S804_TOKEN"):
        os.environ["MYOP_AUTH_TOKEN"] = os.environ["S804_TOKEN"]
    if WA_DIR not in sys.path:
        sys.path.insert(0, WA_DIR)
    import waba as w
    if os.path.dirname(os.path.abspath(w.__file__)) != WA_DIR:
        raise RuntimeError("waba came from another folder")
    if os.environ.get("S804_API_BASE"):
        w.BASE_URL = os.environ["S804_API_BASE"].rstrip("/")
    if os.environ.get("S804_TOKEN"):
        w.AUTH_TOKEN = os.environ["S804_TOKEN"]
    return w


def fresh():
    return "s804-made-up-" + secrets.token_hex(8)


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


def via_httpclient(url, token, company, body, company_header="X-MYOP-COMPANY-ID"):
    u = urlparse(url)
    conn = (http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection)(u.netloc, timeout=30)
    h = {"Authorization": "Bearer " + token, company_header: company, "Content-Type": "application/json", "Accept": "application/json"}
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


def probe_body(w):
    # an EMPTY number and EMPTY text: nothing can be delivered. The same body S802's proof sent on this box (answered HTTP 400).
    return {"phone_number_id": w.PHONE_NUMBER_ID, "customer_country_code": "91", "customer_number": "",
            "data": {"type": "text", "context": {"body": ""}}, "reply_to": None, "myop_ref_id": None}


def changed_sender(w, token):
    """waba.send_template itself (ONE try), with the given key and the empty probe body in place of a template."""
    old_tok, old_bp = w.AUTH_TOKEN, w.build_payload
    w.AUTH_TOKEN = token
    w.build_payload = lambda *a, **k: probe_body(w)
    try:
        r = w.send_template("", "s804_nothing", [], retries=0)
    except w.WabaFatalError:
        return "svc"                                                   # past the authorizer: the service itself answered with a stop code
    except Exception as e:                                             # noqa: BLE001
        return "err:" + type(e).__name__
    finally:
        w.AUTH_TOKEN, w.build_payload = old_tok, old_bp
    sc = r.get("status_code") or 0
    return "500A" if is_refusal(sc, "", r.get("raw", "")) else (str(sc) if sc else "none")


def main():
    try:
        w = load()
        w.check_config()
    except Exception as e:                                             # noqa: BLE001
        print("PROVE: ERROR waba.py could not be loaded with its settings (%s)" % type(e).__name__)
        return 2
    tok = w.AUTH_TOKEN
    if "--installed" in sys.argv:
        got = changed_sender(w, tok)
        good = got in ("400", "svc")
        print("INSTALLED: waba.send_template, the real key, an empty number, nothing sent: %s -- %s" % (got, "let through" if good else "NOT A PROPER ANSWER"))
        return 0 if good else 1
    url, company = w.BASE_URL + w.SEND_PATH, w.COMPANY_ID
    body = json.dumps(probe_body(w)).encode("utf-8")
    ways = [
        ("1 urllib -- waba.py's road today (header names re-cased on the wire)", lambda: via_urllib(url, fresh(), company, body)),
        ("2 http.client, the header names exactly as written                 ", lambda: via_httpclient(url, fresh(), company, body)),
        ("3 http.client, but the company header named as urllib sends it     ", lambda: via_httpclient(url, fresh(), company, body, company_header="X-Myop-Company-Id")),
    ]
    res = [[] for _ in ways]
    for _ in range(ROUNDS):
        for i, (_label, fn) in enumerate(ways):
            res[i].append(cell(fn()))
            time.sleep(GAP / 2.0)
        time.sleep(GAP)
    b_made = [changed_sender(w, fresh()) for _ in range(ROUNDS)]
    b_real = changed_sender(w, tok)
    print("each request with a FRESH made-up key, used once -- NOTHING SENT (500A = HTTP 500 from their authorizer; 401/403 = the proper answer)")
    for (label, _fn), r in zip(ways, res):
        print("  %s  %s" % (label, " ".join(r)))
    print("  4 the CHANGED waba.send_template, fresh made-up keys                 %s" % " ".join(b_made))
    print("  5 the CHANGED waba.send_template, the real key, empty number + text  %s   (400 = let through; the empty number is refused by the service)" % b_real)
    proper = ("401", "403")
    old_refused = all(x == "500A" for x in res[0])
    if not old_refused and all(x in proper for x in res[0]):
        print("PROVE: NOT-SHOWN the old road is answered properly right now (%s) -- nothing to prove" % " ".join(res[0]))
        return 3
    if old_refused and all(x in proper for x in res[1]) and all(x in proper for x in b_made) and b_real in ("400", "svc"):
        which = "the company header's name is what decides" if all(x == "500A" for x in res[2]) else "the company header's name alone does not decide it"
        print("PROVE: PROVEN the old road is refused; with the header names as written the gateway answers properly (%s)" % which)
        return 0
    print("PROVE: FAILED the table above does not show it")
    return 1


if __name__ == "__main__":
    sys.exit(main())
