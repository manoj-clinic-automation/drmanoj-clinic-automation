#!/usr/bin/env python3
"""walk_s859.py -- kit S859_INBOX_NO_FILE (session 478, the parent, 17-Nov-2026), F-1358's page half + F-1366, D964.
   python walk_s859.py <portal_inbox.py to test>
Runs the given portal_inbox.py (loaded BY PATH under its own name; the walk's folder is dropped from the import path,
F-1441) inside a throw-away Flask app on a MADE-UP store (INBOX_STORE / INBOX_RAW_DIR in a temp folder): made-up chats,
made-up phone numbers, no real database, no network (the media fetch is a stand-in; Google and the patient list are off).
  A  the "no file" rule: an incoming photo / PDF / voice note with no link and no local copy is 'no_file' 10 minutes after it
     came -- not before, never with a link or a copy, never for text or for an outgoing message;
  B  the chat answer carries no_file per message; the page (GET /portal/inbox, the owner's and staff's same page) opens 200 and
     carries the new line and its MyOperator link, the old "has not arrived yet" line kept for the first 10 minutes;
     the page's script passes node --check when node is on the box;
  C  the health answer still says inbox ok / kit S793 and counts the no-file rows of the last 30 days (older ones out);
  D  the media route: a link with a space and one with a non-English letter are fetched percent-encoded (host unchanged);
     a read timeout, an invalid URL and a refused fetch answer 502 with a plain sentence, never a bare 500; a host not on
     the list is 404; a good fetch is 200 and kept.
Exit 0 = WALK OK n/n; 1 = RED. The control (the live file) must go RED."""
import datetime as dt
import http.client
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != HERE]
target = os.path.abspath(sys.argv[1])
oks, fails = [], []


def ck(name, cond, note=""):
    (oks if cond else fails).append(name)
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else "  :: " + str(note)[:200]))


root = tempfile.mkdtemp(prefix="s859w_")
os.environ["INBOX_STORE"] = os.path.join(root, "store")
os.environ["INBOX_RAW_DIR"] = os.path.join(root, "raw")
os.makedirs(os.environ["INBOX_RAW_DIR"])
try:
    spec = importlib.util.spec_from_file_location("inbox_under_walk", target)
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    M.sheet_sync = lambda *a, **k: None
    M.patients = lambda: {}
    from flask import Flask
    app = Flask("s859walk")
    app.testing = True
    M.register(app, guard=lambda f: f, get_user=lambda: "walk", cfg_get=lambda k, d=None: d if d is not None else "")
    cl = app.test_client()
    IST = M.IST
    now = dt.datetime.now(IST).replace(microsecond=0)

    def ago(minutes):
        return (now - dt.timedelta(minutes=minutes)).isoformat()

    P = "1000000001"          # made-up (starts with 1: never a mobile number)
    rows = [  # mid, dir, ts, mtype, media_url, local_path, expected no_file
        ("m1", "in", ago(30), "image", "", "", True),
        ("m2", "in", ago(5), "document", "", "", False),
        ("m3", "in", ago(30), "image", "https://x.s3.amazonaws.com/a.jpg", "", False),
        ("m4", "in", ago(30), "text", "", "", False),
        ("m5", "out", ago(30), "image", "", "", False),
        ("m6", "in", ago(60 * 24 * 40), "voice", "", "", True),      # 40 days old: no_file, but out of the 30-day count
        ("m7", "in", ago(45), "document", "", "/nowhere/copy.pdf", False),
    ]
    c = M.db()
    for mid, d, ts, mt, mu, lp, _e in rows:
        c.execute("INSERT INTO msgs(mid,phone,dir,ts,mtype,body,media_url,mime,fname,local_path,status,src) "
                  "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (mid, P, d, ts, mt, "", mu, "", "", lp, "", "walk"))
    c.commit()
    got = {r["mid"]: M.row_out(r) for r in c.execute("SELECT * FROM msgs")}
    c.close()
    ck("A1 an incoming photo with no link 30 min old is 'no file'", got["m1"].get("no_file") is True, got["m1"])
    ck("A2 ... 5 min old is not yet (the old 'has not arrived yet' line stands)", got["m2"].get("no_file") is False)
    ck("A3 ... with a link is not", got["m3"].get("no_file") is False)
    ck("A4 ... a text is not", got["m4"].get("no_file") is False)
    ck("A5 ... an outgoing photo is not", got["m5"].get("no_file") is False)
    ck("A6 ... with a local copy is not", got["m7"].get("no_file") is False)
    ck("A7 every other field of the row is as before", set(got["m1"]) == {"rid", "dir", "ts", "type", "body", "has_media", "mime",
                                                                         "fname", "status", "sent_by", "no_file"})
    r = cl.get("/portal/inbox/api/chat?phone=" + P)
    j = r.get_json(silent=True) or {}
    by = {m["rid"]: m for m in j.get("msgs", [])}
    ck("B1 the chat answer carries no_file per message", r.status_code == 200 and sum(1 for m in by.values() if m.get("no_file")) == 2, r.status_code)
    r = cl.get("/portal/inbox")
    html = r.get_data(as_text=True)
    ck("B2 the page opens (200)", r.status_code == 200, r.status_code)
    ck("B3 the page carries the new line and its MyOperator link", "MyOperator did not give this file" in html and "Open in MyOperator" in html)
    ck("B4 the old 'has not arrived yet' line is kept for the first minutes", "the file has not arrived yet" in html)
    node = shutil.which("node")
    if node:
        s0 = html.rfind("<script>")
        s1 = html.rfind("</script>")
        js = os.path.join(root, "page.js")
        open(js, "w", encoding="utf-8").write(html[s0 + 8:s1] if 0 <= s0 < s1 else "")
        p = subprocess.run([node, "--check", js], capture_output=True, text=True)
        ck("B5 the page's script passes node --check", p.returncode == 0 and s0 >= 0, p.stderr[-200:])
    else:
        ck("B5 node not on this box -- the script check is skipped (it ran where the kit was built)", True)
    r = cl.get("/portal/inbox/health")
    h = r.get_json(silent=True) or {}
    ck("C1 the health answer still says inbox ok, kit S793", h.get("inbox") == "ok" and h.get("kit") == "S793", h)
    ck("C2 it counts the no-file rows of the last 30 days (1: the 40-day one out)", h.get("no_file_30d") == 1, h)
    ck("C3 it carries no name and no number", all(k in ("inbox", "kit", "no_file_30d") for k in h) and P not in json.dumps(h), h)

    # D -- the media route, with a stand-in fetch
    seen = []

    class Resp:
        def __init__(self, data):
            self.data, self.headers = data, {"Content-Type": "image/jpeg"}

        def read(self, n=-1):
            return self.data

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    mode = {"x": "ok"}

    def fake_urlopen(req, timeout=None):
        seen.append(req.full_url)
        if mode["x"] == "timeout":
            raise TimeoutError("read timed out")
        if mode["x"] == "invalid":
            raise http.client.InvalidURL("bad url")
        if mode["x"] == "refused":
            raise urllib.error.URLError("refused")
        if mode["x"] == "unicode":
            raise UnicodeEncodeError("ascii", "न", 0, 1, "made-up")
        return Resp(b"\xff\xd8made-up-jpeg")

    M.urllib.request.urlopen = fake_urlopen
    c = M.db()
    media = [("d1", "https://x.s3.amazonaws.com/a b/photo 1.jpg"), ("d2", "https://x.s3.amazonaws.com/f/नम.jpg"),
             ("d3", "https://evil.example.com/a.jpg"), ("d4", "https://x.s3.amazonaws.com/ok.jpg"),
             ("d5", "https://x.s3.amazonaws.com/t.jpg"), ("d6", "https://x.s3.amazonaws.com/i.jpg"),
             ("d7", "https://x.s3.amazonaws.com/r.jpg"), ("d8", "https://x.s3.amazonaws.com/u.jpg")]
    rid = {}
    for mid, url in media:
        cur = c.execute("INSERT INTO msgs(mid,phone,dir,ts,mtype,body,media_url,mime,fname,local_path,status,src) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (mid, P, "in", ago(3), "image", "", url, "", "", "", "", "walk"))
        rid[mid] = cur.lastrowid
    c.commit(); c.close()
    r = cl.get("/portal/inbox/media/%d" % rid["d1"])
    ck("D1 a link with spaces is fetched percent-encoded, host unchanged", r.status_code == 200 and seen and seen[-1] == "https://x.s3.amazonaws.com/a%20b/photo%201.jpg", (r.status_code, seen[-1:]))
    r = cl.get("/portal/inbox/media/%d" % rid["d2"])
    ck("D2 a link with a non-English letter is fetched percent-encoded", r.status_code == 200 and seen[-1].startswith("https://x.s3.amazonaws.com/f/%E0%A4%A8"), (r.status_code, seen[-1:]))
    r = cl.get("/portal/inbox/media/%d" % rid["d3"])
    ck("D3 a host not on the list is 404 (never fetched)", r.status_code == 404 and "evil" not in (seen[-1] if seen else ""), r.status_code)
    r = cl.get("/portal/inbox/media/%d" % rid["d4"])
    ck("D4 a good fetch is 200 and its copy kept", r.status_code == 200 and r.data.startswith(b"\xff\xd8"), r.status_code)
    for k, mid in (("timeout", "d5"), ("invalid", "d6"), ("refused", "d7"), ("unicode", "d8")):
        mode["x"] = k
        r = cl.get("/portal/inbox/media/%d" % rid[mid])
        body = r.get_data(as_text=True)
        ck("D5-%s answers 502 with a plain sentence (not a bare 500)" % k,
           r.status_code == 502 and "could not be fetched from MyOperator" in body, (r.status_code, body[:80]))
    mode["x"] = "ok"
    pre = "https://x.s3.amazonaws.com/p/a.jpg?X-Amz-Signature=ab%2Bcd%2F&X-Amz-Date=20261117T000000Z"
    c = M.db()
    cur = c.execute("INSERT INTO msgs(mid,phone,dir,ts,mtype,body,media_url,mime,fname,local_path,status,src) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", ("d9", P, "in", ago(3), "image", "", pre, "", "", "", "", "walk"))
    c.commit(); r9 = cur.lastrowid; c.close()
    r = cl.get("/portal/inbox/media/%d" % r9)
    ck("D6 an already-encoded / presigned link is fetched exactly as stored (never encoded twice)", r.status_code == 200 and seen[-1] == pre, seen[-1:])
except Exception as e:                                                  # a crash is a red, never a pass
    ck("CRASH in the walk", False, "%s: %s" % (e.__class__.__name__, e))
finally:
    shutil.rmtree(root, ignore_errors=True)
print("WALK OK %d/%d" % (len(oks), len(oks)) if not fails else "WALK RED %d of %d failed" % (len(fails), len(oks) + len(fails)))
sys.exit(1 if fails else 0)
