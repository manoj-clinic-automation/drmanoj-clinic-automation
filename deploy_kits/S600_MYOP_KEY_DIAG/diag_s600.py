#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""diag_s600.py -- kit S600_MYOP_KEY_DIAG (session S329, 19-Oct-2026). READ-ONLY. SENDS NOTHING.

The owner, 09:09 IST 19-Oct: "find out the cause and rectify it or escalate it to the MyOperator support team".
Since ~08:50 IST MyOperator answers the clinic's one WhatsApp key with HTTP 500 {"message":null} -- the same answer it gave
in June before the API was switched on for the account (MyOperator_API_Support_Report, 13-Jun). The same key delivered a
photo, a PDF and a voice note at 08:17 IST today.

What it reads, and only this:
  1. the key in /root/wa/.env (MYOP_AUTH_TOKEN): its length, its first 4 characters (the masked hint the reference
     already records), stray spaces or line ends, and when the file was last changed -- never the key;
  2. four read-only calls to MyOperator: the approved-template list with the key; the phone-number list with the key;
     the template list with the key sent as x-api-key (June: 401); the template list with a MADE-UP key (the control:
     what MyOperator answers for a key it does not know);
  3. the text/template sender's own journal for the last 48 hours: by hour, how many sends went and the HTTP answers
     (numbers are never printed).
Writes /root/finance/s600_myop_diag.json (no key, no number) for the escalation.
"""
import os, re, json, time, datetime, subprocess, urllib.request, urllib.error, collections

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
ENV = os.environ.get("S600_ENV", "/root/wa/.env")
BASE = os.environ.get("S600_BASE", "https://publicapi.myoperator.co")
COMPANY = "68384350414b9847"
OUT = os.environ.get("S600_OUT", "/root/finance/s600_myop_diag.json")


def now():
    return datetime.datetime.now(IST).strftime("%d-%b-%Y %H:%M:%S IST")


def mask(s):
    return re.sub(r"\d{7,}", lambda m: "••••" + m.group(0)[-4:], str(s))


def raw_key():
    for line in open(ENV, encoding="utf-8", errors="replace"):
        if line.startswith("MYOP_AUTH_TOKEN"):
            return line.split("=", 1)[1].rstrip("\n")
    return None


def call(path, headers):
    req = urllib.request.Request(BASE + path, method="GET")
    for k, v in headers.items():
        req.add_header(k, v)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read(400).decode("utf-8", "replace")
            st = r.status
            rid = r.headers.get("x-amzn-RequestId") or r.headers.get("x-amz-apigw-id") or ""
    except urllib.error.HTTPError as e:
        st = e.code
        try:
            body = e.read(400).decode("utf-8", "replace")
        except Exception:                                               # noqa: BLE001
            body = ""
        rid = e.headers.get("x-amzn-RequestId") or e.headers.get("x-amz-apigw-id") or ""
    except Exception as e:                                              # noqa: BLE001
        st, body, rid = "no answer (%s)" % type(e).__name__, "", ""
    return {"at": now(), "status": st, "body": mask(body.strip())[:200], "ms": int((time.time() - t0) * 1000), "request_id": rid}


def main():
    R = {"kit": "S600", "at": now()}
    k = raw_key()
    if k is None:
        print("!! /root/wa/.env has no MYOP_AUTH_TOKEN line")
        return
    clean = k.strip().strip('"').strip("'")
    st = os.stat(ENV)
    R["key"] = {"length": len(clean), "starts": clean[:4] + "…", "stray_spaces_or_quotes": clean != k,
                "carriage_return": "\r" in k, "env_file_changed": datetime.datetime.fromtimestamp(st.st_mtime, IST).strftime("%d-%b-%Y %H:%M IST")}
    print("[1] the key in /root/wa/.env: %d characters, starts %s · stray spaces/quotes: %s · line-end \\r: %s · file last changed %s"
          % (len(clean), clean[:4] + "…", "YES" if clean != k else "no", "YES" if "\r" in k else "no", R["key"]["env_file_changed"]))
    waba = "2101222617483538"
    h = {"Authorization": "Bearer " + clean, "X-MYOP-COMPANY-ID": COMPANY, "Accept": "application/json"}
    tests = [
        ("templates, Bearer (our key)", "/chat/templates?waba_id=%s&waba_template_status=approved&limit=1&offset=0" % waba, h),
        ("phone numbers, Bearer (our key)", "/chat/phonenumbers?limit=1&offset=0&waba_id=%s" % waba, h),
        ("templates, x-api-key (our key)", "/chat/templates?waba_id=%s&waba_template_status=approved&limit=1&offset=0" % waba,
         {"x-api-key": clean, "X-MYOP-COMPANY-ID": COMPANY, "Accept": "application/json"}),
        ("templates, Bearer (a MADE-UP key -- control)", "/chat/templates?waba_id=%s&waba_template_status=approved&limit=1&offset=0" % waba,
         {"Authorization": "Bearer " + "x" * len(clean), "X-MYOP-COMPANY-ID": COMPANY, "Accept": "application/json"}),
    ]
    R["calls"] = []
    print("[2] MyOperator, read-only:")
    for name, path, hh in tests:
        r = call(path, hh)
        r["what"] = name
        R["calls"].append(r)
        print("    %-46s HTTP %s  %s  (%s ms)%s" % (name, r["status"], r["body"][:90], r["ms"], ("  id " + r["request_id"]) if r["request_id"] else ""))
        time.sleep(1)
    # the sender's journal
    p = subprocess.run(["journalctl", "-u", "wa-send-api", "--since", "48 hours ago", "-o", "short-iso", "--no-pager"],
                       capture_output=True, text=True, timeout=60)
    hours = collections.OrderedDict()
    for line in p.stdout.splitlines():
        m = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}):\d{2}:\d{2}([+-]\d{2}:?\d{2})?\s", line)
        if not m or ("[wa_send_api] send" not in line and "[wa_send_api] template" not in line):
            continue
        sent = re.search(r"sent=(\w+)", line)
        http = re.search(r"http=(\w+)", line)
        hk = m.group(1)
        d = hours.setdefault(hk, collections.Counter())
        d["%s/%s" % ("sent" if (sent and sent.group(1) == "True") else "not-sent", http.group(1) if http else "?")] += 1
    R["sender_journal"] = {k2: dict(v) for k2, v in hours.items()}
    print("[3] the sender (call tracker replies) -- last 48 h, by hour (journal clock):")
    if not hours:
        print("    no sends in the last 48 hours")
    for hk, v in list(hours.items())[-12:]:
        print("    %s  %s" % (hk.replace("T", " ") + "h", ", ".join("%s x%d" % (a, b) for a, b in v.items())))
    old = os.umask(0o077)
    try:
        with open(OUT, "w") as fh:
            json.dump(R, fh, indent=1)
    finally:
        os.umask(old)
    print("DONE -- recorded in %s (no key, no number). Send a photo of this screen to Claude." % OUT)


if __name__ == "__main__":
    main()
