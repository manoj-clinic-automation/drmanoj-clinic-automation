#!/usr/bin/python3
# make_s804.py -- kit S804_WABA_SEND_HEADERS (S439, 12-Nov-2026, the parent). Usage: make_s804.py <live waba.py> <out dir>
# F-1294 (F-1031's cause, shown by S802 on MyOperator's live gateway). urllib re-cases header names on the wire --
# "X-MYOP-COMPANY-ID" leaves as "X-Myop-Company-Id" -- and MyOperator's gateway refuses that form at its authorizer (HTTP 500)
# unless a properly-cased request with the same key has just been let through. http.client sends header names exactly as written.
# waba.send_template's ONE request per try is moved from urllib to http.client; nothing else changes (the same result dict, the
# same fatal codes, the same one retry on a 5xx or when the request could not be connected or sent; a failure AFTER the request
# went out is raised after ONE request, as before -- never sent twice).
# The replaced block is cut between two anchors that must occur once and is checked against its md5 before it is replaced.
import hashlib, os, sys
pw, out = sys.argv[1], sys.argv[2]
BLOCK_MD5 = "6b5cad3fc3b317ea32b1efe6a1418c69"
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

Wt = load(pw, "031b4642")
Wt = rp(Wt, "import urllib.request\nimport urllib.error\nfrom pathlib import Path\n",
        "import urllib.request\nimport urllib.error\nimport http.client                                       # S804\nfrom urllib.parse import urlparse                        # S804\nfrom pathlib import Path\n")
Wt = cut(Wt, '    for attempt in range(retries + 1):\n        req = urllib.request.Request(url, data=payload, headers=_headers(), method="POST")\n',
         '    return {"ok": False, "status_code": 0, "message_id": "", "conversation_id": "",\n            "code": "NETWORK", "message": f"Network error: {last_exc}", "raw": ""}\n',
         BLOCK_MD5, '''    for attempt in range(retries + 1):
        # S804 (F-1294, F-1031): sent through http.client, the header names EXACTLY as written. urllib re-cases them on the
        # wire ("X-MYOP-COMPANY-ID" leaves as "X-Myop-Company-Id") and MyOperator's gateway refuses that form at its authorizer
        # (HTTP 500 {"message":null}) unless a properly-cased request with the same key has just been let through.
        conn = None
        try:
            try:
                u = urlparse(url)
                conn = (http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection)(u.netloc, timeout=timeout)
                conn.request("POST", (u.path or "/") + (("?" + u.query) if u.query else ""), payload, _headers())
            except OSError as e:
                # The request could not be connected or sent (what urllib raised as URLError): the ONE retry, as before.
                last_exc = e
                if attempt < retries:
                    time.sleep(3)
                    continue
                return {"ok": False, "status_code": 0, "message_id": "",
                        "conversation_id": "", "code": "NETWORK",
                        "message": f"Network error: {e}", "raw": ""}
            # Once the request has gone out it is NEVER sent again by this function: a late answer, a dropped connection
            # or a cut-short body is raised to the caller, exactly as before (MyOperator may already have accepted it).
            resp = conn.getresponse()
            status = resp.status
            body = resp.read().decode("utf-8", "replace")
        finally:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
        if 200 <= status < 300:
            return _parse_response(status, body)
        result = _parse_response(status, body)
        # Fatal conditions: stop the batch.
        if result.get("code") in FATAL_CODES:
            raise WabaFatalError(result["code"], FATAL_CODES[result["code"]])
        # Transient server errors (5xx): ONE retry, as before (S177).
        if 500 <= status < 600 and attempt < retries:
            time.sleep(3)
            continue
        return result
''')
os.makedirs(os.path.join(out, "wa"), exist_ok=True)
with open(os.path.join(out, "wa", "waba.py"), "wb") as fh:
    fh.write(Wt.encode("utf-8"))
print("waba.py", hashlib.md5(Wt.encode("utf-8")).hexdigest())
