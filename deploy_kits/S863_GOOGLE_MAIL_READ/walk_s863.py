#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s863.py -- kit S863_GOOGLE_MAIL_READ (S480, 18-Nov-2026). A walk against a MADE-UP Google (a local web server that
answers like Google's token and Gmail endpoints), a made-up client file and made-up mails.
    python3 walk_s863.py <dir with google_mail_read.py> <work_dir> [<finance dir with S862's patients_part2.py>]
Last line "WALK n/m"."""
import base64
import importlib
import json
import os
import shutil
import stat
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

CODE, WORK = sys.argv[1:3]
P2DIR = sys.argv[3] if len(sys.argv) > 3 else ""
try:
    _ME = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _ME = None
sys.path[:] = [p for p in sys.path if not _ME or os.path.abspath(p or ".") != _ME]     # F-1441
sys.path[:0] = [CODE]
if os.path.isdir(WORK):
    shutil.rmtree(WORK)
os.makedirs(WORK)
RES = []


def ok(name, cond, extra=""):
    RES.append(bool(cond))
    print("%s  %s%s" % ("PASS" if cond else "FAIL", name, ("  -- " + str(extra)[:300]) if extra else ""))


def mail_text(month, n):
    return ("Your business performance for %s 2026: %d interactions\n\nYour performance at a glance\n\n%d\n\ncalls\n\n-1%%\n\n%d\n\nchat clicks\n\n"
            "+1%%\n\n%d\n\npeople asked for directions\n-6%%\n\n%d\n\nwebsite visits from profile\n\n+6%%\n\n%s\n\nprofile views\n\n-8%%\n\n"
            "%s\n\nsearches\n\n-8%%\n\nTop search terms\n\n1\n\nwalk doctor town\n\n%d\n\n2\n\nbest walk doctor\n\n9\n\nTake the next step"
            % (month, n * 4, n, n, n, n, "{:,}".format(n * 30), "{:,}".format(n * 7), n))


def b64(s):
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")


MAILS = {
    "m10": ("businessprofile-noreply@google.com", "Dr Walk, your performance report for October 2026", mail_text("October", 100), 1794018933000),
    "m09": ("businessprofile-noreply@google.com", "Dr Walk, your performance report for September 2026", mail_text("September", 90), 1791511905000),
    "bad": ("businessprofile-noreply@google.com", "Dr Walk, your performance report for August 2026", "nothing to read here", 1790192371000),
    "fake": ("someone@else.example", "your performance report for July 2026", mail_text("July", 1), 1787000000000),
    "lab": ("businessprofile-noreply@google.com", "NK Walk Lab, your performance report for October 2026", mail_text("October", 7), 1794100000000),
}
MODE = {"api": "ok", "refresh": "ok", "exchange": "ok", "email": "drmka.ortho@gmail.com"}
SEEN = {"auth": []}


class G(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        body = parse_qs(self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode())
        gt = body.get("grant_type", [""])[0]
        if gt == "refresh_token":
            if MODE["refresh"] != "ok" or body.get("refresh_token", [""])[0] != "walk-refresh":
                return self._send(400, dict(error="invalid_grant", error_description="Token has been expired or revoked."))
            return self._send(200, dict(access_token="walk-access", expires_in=3600))
        if gt == "authorization_code":
            if body.get("code", [""])[0] != "walk-code" or body.get("client_secret", [""])[0] != "walk-secret":
                return self._send(400, dict(error="invalid_grant"))
            if MODE["exchange"] == "norefresh":
                return self._send(200, dict(access_token="walk-access"))
            return self._send(200, dict(access_token="walk-access", refresh_token="walk-refresh", scope="https://www.googleapis.com/auth/gmail.readonly"))
        return self._send(400, dict(error="unsupported"))

    def do_GET(self):
        SEEN["auth"].append(self.headers.get("Authorization", ""))
        if MODE["api"] == "off":
            return self._send(403, dict(error=dict(code=403, message="Gmail API has not been used in project 123 before or it is disabled. Enable it by visiting "
                                                   "https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project=123 then retry.")))
        u = urlparse(self.path)
        if MODE["api"] == "garbage":
            b = b"<html>not json"
            self.send_response(200)
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            return self.wfile.write(b)
        if u.path.endswith("/profile"):
            return self._send(200, dict(emailAddress=MODE["email"]))
        if u.path.endswith("/messages"):
            q = parse_qs(u.query).get("q", [""])[0]
            SEEN["q"] = q
            return self._send(200, dict(messages=[dict(id=k) for k in MAILS]))
        mid = u.path.rsplit("/", 1)[-1]
        if mid not in MAILS:
            return self._send(404, dict(error=dict(code=404, message="not found")))
        frm, subj, text, ts = MAILS[mid]
        return self._send(200, dict(id=mid, internalDate=str(ts), payload=dict(mimeType="multipart/alternative", headers=[
            dict(name="From", value="Google <%s>" % frm), dict(name="Subject", value=subj)],
            parts=[dict(mimeType="text/plain", body=dict(data=b64(text))), dict(mimeType="text/html", body=dict(data=b64("<p>x</p>")))])))


srv = HTTPServer(("127.0.0.1", 0), G)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = "http://127.0.0.1:%d" % srv.server_port
DRIVE = os.path.join(WORK, "drive_token.json")
json.dump(dict(client_id="walk-client", client_secret="walk-secret", refresh_token="drive-walk", token_uri=BASE + "/token"), open(DRIVE, "w"))
os.environ.update(DRIVE_TOKEN_FILE=DRIVE, GMR_TOKEN=os.path.join(WORK, "rec", "gmail_token.json"), GMR_OUT=os.path.join(WORK, "patients_google_mail.json"),
                  GMR_STATE=os.path.join(WORK, "state.json"), GMR_TOKEN_URI=BASE + "/token", GMR_API=BASE + "/gmail/v1/users/me",
                  GMR_BUSINESS=r"dr\.?\s*walk")
import google_mail_read as g                                            # noqa: E402
ST = lambda: json.load(open(os.environ["GMR_STATE"]))                   # noqa: E731

rc = g.run()
ok("not connected: exit 2, the state says so, last_ok_iso present and empty (the leg reads 'never')", rc == 2 and ST()["ok"] is False and
   "not connected" in ST()["why"] and ST()["last_ok_iso"] == "" and not os.path.exists(os.environ["GMR_OUT"]), ST())
lines = []
rc = g.connect(inp=lambda _p: "http://localhost/?state=x&scope=y", out=lines.append)
ok("connect: a paste without a code saves nothing (exit 1)", rc == 1 and not os.path.exists(os.environ["GMR_TOKEN"]))
link = [x for x in lines if x.startswith("https://accounts.google.com/")]
ok("connect prints Google's Allow link: the clinic's client, read-only Gmail, offline, his account, localhost",
   len(link) == 1 and "client_id=walk-client" in link[0] and "gmail.readonly" in link[0] and "access_type=offline" in link[0]
   and "login_hint=drmka.ortho%40gmail.com" in link[0] and "redirect_uri=http%3A%2F%2Flocalhost" in link[0] and "walk-secret" not in link[0], link)
MODE["exchange"] = "norefresh"
rc = g.connect(inp=lambda _p: "http://localhost/?code=walk-code&scope=x", out=lambda *_a: None)
ok("connect: Google gives no lasting permission -> nothing saved (exit 3)", rc == 3 and not os.path.exists(os.environ["GMR_TOKEN"]))
MODE["exchange"] = "ok"
MODE["email"] = "someone.else@gmail.com"
lines = []
rc = g.connect(inp=lambda _p: "http://localhost/?code=walk-code&scope=https://www.googleapis.com/auth/gmail.readonly", out=lines.append)
ok("connect: another Google account signed in -> refused, nothing saved", rc == 3 and not os.path.exists(os.environ["GMR_TOKEN"])
   and any("another Google account" in x for x in lines), lines[-1:])
MODE["email"] = "drmka.ortho@gmail.com"
lines = []
rc = g.connect(inp=lambda _p: "http://localhost/?code=walk-code&scope=https://www.googleapis.com/auth/gmail.readonly", out=lines.append)
tk = os.environ["GMR_TOKEN"]
ok("connect: saved (mode 600, refresh token only, no secret) and read at once", rc == 0 and os.path.exists(tk) and
   stat.S_IMODE(os.stat(tk).st_mode) == 0o600 and json.load(open(tk)).get("refresh_token") == "walk-refresh"
   and "walk-secret" not in open(tk).read() and any("CONNECTED" in x for x in lines), lines[-2:])
ok("nothing printed carries the code or a token", not any(("walk-code" in x or "walk-refresh" in x or "walk-access" in x) for x in lines))
ok("the API was asked with the access token and the mail query", all(a == "Bearer walk-access" for a in SEEN["auth"]) and
   "businessprofile-noreply@google.com" in SEEN.get("q", "") and "performance report for" in SEEN.get("q", ""))
o = json.load(open(os.environ["GMR_OUT"]))
mo = o.get("months", {})
ok("two months read (Oct, Sep); the unreadable mail, the stranger's mail and another listing's report (later, same month) left out",
   sorted(mo) == ["2026-09", "2026-10"] and mo["2026-10"]["calls"] == 100 and ST()["other_listings"] == 1, (sorted(mo), ST().get("other_listings")))
ok("October's seven counts as the mail gives them", {k: mo["2026-10"][k] for k in ("calls", "chats", "directions", "website", "views", "searches", "interactions")}
   == dict(calls=100, chats=100, directions=100, website=100, views=3000, searches=700, interactions=400), mo.get("2026-10"))
ok("top search terms kept, mail_day in IST", mo["2026-10"]["top"][:2] == [["walk doctor town", 100], ["best walk doctor", 9]] and mo["2026-10"]["mail_day"] == "2026-11-07"
   and o.get("mail_day") == "2026-11-07", (mo["2026-10"].get("top"), mo["2026-10"].get("mail_day")))
s = ST()
ok("state ok: last_ok_iso written, months 2", s["ok"] is True and s["last_ok_iso"] and s["months_read"] == 2 and s["changed"] == ["2026-09", "2026-10"], s)
before = open(os.environ["GMR_OUT"]).read()
rc = g.run()
ok("a second run: exit 0, nothing changed", rc == 0 and ST()["changed"] == [] and json.load(open(os.environ["GMR_OUT"]))["months"] == json.loads(before)["months"])
o = json.load(open(os.environ["GMR_OUT"]))
o["months"]["2026-06"] = dict(calls=1, chats=1, directions=1, website=1, views=1, searches=1, interactions=4, top=[], mail_day="2026-07-05")
json.dump(o, open(os.environ["GMR_OUT"], "w"))
g.run()
ok("a month read earlier and no longer in the 400-day list is kept", "2026-06" in json.load(open(os.environ["GMR_OUT"]))["months"])
MODE["api"] = "off"
keep = open(os.environ["GMR_OUT"]).read()
rc = g.run()
ok("Gmail API switched off: exit 3, the state carries Google's own switch-on link, the months file untouched",
   rc == 3 and "console.developers.google.com/apis/api/gmail.googleapis.com/overview?project=123" in ST()["why"] and open(os.environ["GMR_OUT"]).read() == keep, ST()["why"])
ok("a failure keeps last_ok_iso and writes last_failure_iso", ST()["last_ok_iso"] and ST()["last_failure_iso"] >= ST()["last_ok_iso"])
MODE["api"] = "ok"
MODE["refresh"] = "revoked"
rc = g.run()
ok("permission withdrawn by Google: exit 3, the state says Google answered 400", rc == 3 and "400" in ST()["why"], ST()["why"])
MODE["refresh"] = "ok"
os.environ["DRIVE_TOKEN_FILE"] = os.path.join(WORK, "missing.json")
rc = g.run()
ok("no client file: exit 3, said plainly", rc == 3 and "client" in ST()["why"], ST()["why"])
os.environ["DRIVE_TOKEN_FILE"] = DRIVE
ok("the parser refuses a mail that lacks a count", g.parse("x, your performance report for May 2026", "Your business performance for May 2026: 4 interactions 1 calls") is None)
ok("the parser refuses a subject that is not a monthly report", g.parse("Puran left a review", mail_text("May", 5)) is None)
one = mail_text("May", 1).replace("1\n\npeople asked", "1\n\nperson asked").replace("chat clicks", "chat click").replace("website visits", "website visit").replace("1\n\ncalls", "1\n\ncall")
r1 = g.parse("Dr Walk, your performance report for May 2026", one)
ok("a month with 1 call / 1 chat click / 1 person / 1 website visit is read (review 2)", r1 is not None and (r1["calls"], r1["chats"], r1["directions"], r1["website"]) == (1, 1, 1, 1), r1)
keep_m = dict(MAILS)
for k in list(MAILS):
    MAILS.pop(k)
MAILS["m10"] = ("businessprofile-noreply@google.com", "Dr Walk, your performance report for October 2026", "the wording changed", 1794018933000)
open(os.environ["GMR_OUT"], "w").write(json.dumps(dict(months={})))
rc = g.run()
ok("mails found but none readable: exit 4, the state says the wording may have changed (the leg goes red)", rc == 4 and ST()["ok"] is False and "wording" in ST()["why"], ST()["why"])
MAILS.clear()
MAILS["old"] = ("businessprofile-noreply@google.com", "Dr Walk, your performance report for January 2025", mail_text("January", 3), 1738000000000)
rc = g.run()
ok("only an old month on record: exit 4, 'no monthly report newer than' (review 4)", rc == 4 and "no monthly report newer than 2025-01" in ST()["why"], ST()["why"])
MAILS.clear()
MAILS.update(keep_m)
MODE["api"] = "garbage"
rc = g.run()
ok("a reply that is not JSON: exit 1, the state says the run stopped (review 6)", rc == 1 and "stopped" in ST()["why"], ST()["why"])
MODE["api"] = "ok"
rc = g.run()
ok("and the next good run is OK again", rc == 0 and ST()["ok"] is True, ST()["why"])
MAILS["n11"] = ("businessprofile-noreply@google.com", "Dr. Walk -Best, your performance report for November 2026", "wording changed", 1796600000000)
rc = g.run()
ok("the newest report unreadable while older ones read: exit 4, says so (second look 5); 'Dr. Walk' with a full stop still the clinic's",
   rc == 4 and "newest report (2026-11)" in ST()["why"] and ST()["other_listings"] == 1, ST()["why"])
MAILS.pop("n11")
keep2 = dict(MAILS)
MAILS.clear()
MAILS["lab"] = keep2["lab"]
open(os.environ["GMR_OUT"], "w").write(json.dumps(dict(months={})))
rc = g.run()
ok("only another listing's reports: exit 4, 'none for the clinic's listing' (second look 2)", rc == 4 and "none for the clinic's listing" in ST()["why"], ST()["why"])
MAILS.clear()
MAILS.update(keep2)
rc = g.run()
if P2DIR:
    sys.path[:0] = [P2DIR]
    os.environ["PATIENTS_GOOGLE_MAIL"] = os.environ["GMR_OUT"]
    gj = os.path.join(WORK, "patients_google.json")
    json.dump(dict(months={"2026-10": dict(searches=1, views=1, calls=1, directions=1, chats=1, website=1, interactions=4, yoy=dict(calls=3.0))},
                   top_terms="walk", closed_days="walk"), open(gj, "w"))
    os.environ["PATIENTS_GOOGLE"] = gj
    import patients_part2 as p2                                         # noqa: E402
    importlib.reload(p2)
    rd = dict(rows=[dict(ym="2026-10", new=5, partial=False)], months=[dict(ym="2026-10")])
    gb = p2.google_block(rd, {})
    rows = {r["ym"]: r for r in gb.get("rows") or []}
    ok("S862's page reads this file: Sep and Oct from the mail, Oct's year-on-year from the session file, 'read by the server'",
       gb.get("read_by") == "server" and rows.get("2026-10", {}).get("calls") == 100 and rows["2026-10"]["yoy"] == dict(calls=3.0) and "2026-09" in rows, gb)
srv.shutdown()
print("WALK %d/%d" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
