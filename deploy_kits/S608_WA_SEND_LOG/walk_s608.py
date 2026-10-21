#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""walk_s608.py -- the send-log walk (kit S608, S331). Everything stand-in: a stand-in MyOperator on 127.0.0.1
(answers 200 for one made-up customer, 500 {"message":null} for another, each with an x-amzn-requestid), a stand-in
mail server, a scratch inbox store. Nothing real is sent, nothing live is read or written.

    python3 walk_s608.py --code DIR --scratch DIR
Exit 0 = GREEN. Run against the S599 portal_inbox.py it must go RED (the negative control).
"""
import argparse
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

ap = argparse.ArgumentParser()
ap.add_argument("--code", required=True)
ap.add_argument("--scratch", required=True)
a = ap.parse_args()
S = os.path.abspath(a.scratch)
if S.startswith("/root/wa") or S.startswith("/root/portal"):
    print("RED: refusing to walk in a live folder")
    sys.exit(1)
os.makedirs(os.path.join(S, "store"), exist_ok=True)
os.makedirs(os.path.join(S, "raw"), exist_ok=True)
GOOD = "9" * 9 + "1"          # made up, built at run time (F-185)
BAD = "9" * 9 + "2"
TOKEN = "walk-key-" + "x" * 12
with open(os.path.join(S, "wa.env"), "w") as fh:
    fh.write("MYOP_AUTH_TOKEN=%s\nWATCHDOG_SMTP_USER=clinic@example.test\nWATCHDOG_SMTP_PASS=walkpass\n" % TOKEN)

SEEN = []


class MyOp(BaseHTTPRequestHandler):
    def log_message(self, *x):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        SEEN.append({"auth": self.headers.get("Authorization"), "body": body})
        if body.get("customer_number") == GOOD:
            out, code, rid = {"status": "success", "data": {"message_id": "wamid.walk1"}}, 200, "req-ok-1"
        else:
            out, code, rid = {"message": None}, 500, "req-bad-1"
        data = json.dumps(out).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("x-amzn-RequestId", rid)
        self.send_header("Set-Cookie", "secret=1")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


srv = HTTPServer(("127.0.0.1", 0), MyOp)
threading.Thread(target=srv.serve_forever, daemon=True).start()

os.environ["INBOX_STORE"] = os.path.join(S, "store")
os.environ["INBOX_RAW_DIR"] = os.path.join(S, "raw")
os.environ["INBOX_WA_ENV"] = os.path.join(S, "wa.env")
os.environ["INBOX_API_URL"] = "http://127.0.0.1:%d/chat/messages" % srv.server_port
sys.path.insert(0, os.path.abspath(a.code))
sys.dont_write_bytecode = True
import portal_inbox as P  # noqa: E402

MAILS = []


class FakeSMTP:
    def __init__(self, host, port, timeout=30):
        pass

    def starttls(self):
        pass

    def login(self, u, p):
        pass

    def send_message(self, m):
        MAILS.append(m)

    def quit(self):
        pass


if hasattr(P, "SMTP_CLASS"):
    P.SMTP_CLASS = FakeSMTP
    P.NOTE_GAP_S = 0

from flask import Flask  # noqa: E402

app = Flask("walk")
P.register(app, lambda f: f, lambda: "manoj", lambda k, d="": d)
C = app.test_client()
H = {"X-Inbox": "1"}
passed, failed = [], []


def check(cond, label):
    (passed if cond else failed).append(label)
    print(("  ok   " if cond else "  FAIL ") + label)
    return cond


# open both chats' 24-hour windows with a made-up inbound message
c = P.db()
for ph in (GOOD, BAD):
    c.execute("INSERT INTO msgs(mid,phone,dir,ts,mtype,body,status) VALUES(?,?,?,?,?,?,?)",
              ("in-" + ph, ph, "in", P.iso(P.now_ist()), "image", "", "received"))
c.commit()
c.close()

print("[a] the pages")
r = C.get("/portal/inbox/sendlog")
if not check(r.status_code == 200 and b"WhatsApp send log" in r.data, "the send-log page is there"):
    print("RED: no send-log page (%s)" % r.status_code)
    sys.exit(1)
check(b"/portal/inbox/sendlog" in C.get("/portal/inbox").data, "the inbox header links to it")
check(C.get("/portal/inbox/health").get_json().get("kit") == "S608", "the health line names S608")

print("[b] a text that goes, and one that MyOperator refuses")
r = C.post("/portal/inbox/api/send", json={"phone": GOOD, "kind": "text", "text": "walk test one"}, headers=H)
check(r.status_code == 200 and r.get_json().get("ok"), "the good send is sent")
r = C.post("/portal/inbox/api/send", json={"phone": BAD, "kind": "text", "text": "walk test two"}, headers=H)
check(r.status_code == 502 and "HTTP 500" in r.get_json().get("error", ""), "the refused send shows HTTP 500, as before")
check(SEEN and SEEN[-1]["auth"] == "Bearer " + TOKEN, "the request itself is unchanged (same key header)")
rows = P.read_log(7, False)
check(len(rows) == 2, "both attempts are in the log (%d)" % len(rows))
bad = [e for e in rows if not e["ok"]]
good = [e for e in rows if e["ok"]]
check(bad and bad[0]["http_status"] == 500 and bad[0]["myoperator_reply"] == '{"message": null}',
      "the refusal keeps MyOperator's status and full reply")
check(bad and bad[0]["request_id"] == "req-bad-1" and good and good[0]["request_id"] == "req-ok-1",
      "the x-amzn-requestid of each answer is kept")
check(bad and bad[0]["customer"] == BAD and bad[0]["text"] == "walk test two" and bad[0]["by"] == "manoj",
      "who, to whom and what")
check(bad and json.loads(bad[0]["request_json"])["customer_number"] == BAD, "the exact request body is kept")
raw = open(P.SEND_LOG, encoding="utf-8").read()
check(TOKEN not in raw and "walkpass" not in raw, "the key and the mail password are never in the log")
check("Set-Cookie" not in raw and "set-cookie" not in raw.lower(), "cookies are not kept")
check(oct(os.stat(P.SEND_LOG).st_mode & 0o777) == "0o600", "the log file is private (600)")

print("[c] the refused send reaches the clinic Gmail by itself")
import time  # noqa: E402
for _ in range(50):
    if MAILS:
        break
    time.sleep(0.1)
check(len(MAILS) == 1 and MAILS[0]["Subject"].startswith("[WA send refused]") and MAILS[0]["To"] == "clinic@example.test",
      "one mail to the clinic Gmail: %s" % (MAILS[0]["Subject"] if MAILS else "-"))
check(MAILS and "req-bad-1" in MAILS[0].get_content(), "the mail carries the request id")

print("[d] the page's data, the CSV, the mail to MyOperator")
j = C.get("/portal/inbox/api/sendlog?days=7").get_json()
check(j["ok"] and j["total"] == 2 and j["refused"] == 1, "the page counts 2 sends, 1 refused")
j = C.get("/portal/inbox/api/sendlog?days=7&only=refused").get_json()
check(len(j["rows"]) == 1 and not j["rows"][0]["ok"], "'refused only' shows only the refusal")
r = C.get("/portal/inbox/sendlog.csv?days=7")
body = r.data.decode()
check(r.status_code == 200 and "attachment" in r.headers.get("Content-Disposition", "") and "REFUSED" in body
      and "req-bad-1" in body and ("91" + BAD) in body, "the CSV downloads with the refusal, the id and the full number")
n0 = len(MAILS)
r = C.post("/portal/inbox/api/sendlog/email?days=7&only=refused", json={"note": "Please check."}, headers=H)
check(r.status_code == 200 and r.get_json().get("ok"), "Email to MyOperator: sent")
m = MAILS[-1] if len(MAILS) > n0 else None
check(m is not None and "support@myoperator.com" in m["To"] and "khushi.jain@myoperator.co" in m["To"],
      "addressed to MyOperator support and Khushi")
check(m is not None and "[## 691386 ##]" in m["Subject"], "on ticket 691386")
atts = list(m.iter_attachments()) if m is not None else []
check(len(atts) == 1 and atts[0].get_filename().endswith(".csv"), "with the log attached as CSV")
check(m is not None and TOKEN not in m.as_string(), "the key is not in the mail")
r = C.post("/portal/inbox/api/sendlog/email", json={}, headers={})
check(r.status_code == 403, "the mail button refuses a request not from the page")

print("")
print("WALK S608: %d passed, %d failed" % (len(passed), len(failed)))
print("GREEN" if not failed else "RED")
srv.shutdown()
sys.exit(0 if not failed else 1)
