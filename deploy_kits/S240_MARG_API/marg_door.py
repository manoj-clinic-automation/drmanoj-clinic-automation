#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marg_door.py  --  S240 (D467 Phase 2a).  "Send a Marg export to the server, from anything."

THE OWNER, 12-Sep-2026: "...in worst scenario, a fallback for manual upload to vps works."

This is that fallback, and it is the floor the whole design stands on.  If the medical PC's push
is broken, if Google Drive is signed out, if his own PC is switched off -- a person opens this
page on a phone or any browser, picks the export file, and the server takes it.  Nothing else is
needed: no Tailscale, no token, no scheduled task, no other machine.

It is also, deliberately, the SAME door everything else uses: it calls marg_take.take(), so a file
sent by hand is classified, verified, counted and de-duplicated exactly like one that arrived by
itself.  Sending a report that the server already has is harmless and says so -- that is what
makes it safe to use when nobody is sure whether a report got through.

  GET  /finance/clinic/marg/upload     the page: what to do, and the last 20 files taken
  POST /finance/clinic/marg/upload     up to 10 files at once; one line of verdict each

Login: maker or checker on the clinic desk, like the Day Revenue page.  The path sits under
/finance/clinic/ because the app resolves the unit from the path.
No JavaScript.  No table is created here.  Nothing is sent anywhere.

S240 phase 2b ALSO adds the machine door, so the medical PC can push each capture the moment it
is taken -- the same take(), the same de-duplication, the same PHI rule, no person involved:

  GET  /finance/api/marg-file          "are you there?"  -> READY, and how much is held
  POST /finance/api/marg-file          one export; answers TAKEN / ALREADY / REFUSED / BUSY

  It carries NO NEW SECRET.  It uses FINANCE_MARG_TOKEN, the scoped stage-only key the medical
  PC already holds -- which is why a rebuilt machine needs one file and not a new credential.
  The key opens this path and nothing else, grants no identity and no role, and this handler
  re-checks it even though the app's front gate already did (defence in depth, S187_M1a).
  A sender may declare the md5 it believes it sent; if the bytes disagree, nothing is taken.
"""
import hashlib
import hmac
import html
import os
import sys
import time

from flask import Blueprint, jsonify, request

DOOR_DIR = "/root/marg_ingest"
if DOOR_DIR not in sys.path:
    sys.path.insert(0, DOOR_DIR)

bp = Blueprint("marg_door", __name__)
_db = None
_require = None
_unit = "clinic"
MAX_FILES = 10
RATE_PER_MIN = 240          # the medical PC sends a handful a day; this is a runaway guard
_hits = []


def init(app, db_getter, require_fn, unit="clinic", url_prefix=""):
    """Mounted at import time from finance_app.py, like every other module here."""
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


# ------------------------------------------------------------------ the page frame
_CSS = """
:root{--ink:#1b1b1b;--soft:#6b6b6b;--line:#e3e3e3;--ok:#137333;--warn:#8a6d00;--bad:#a50e0e;--bg:#fafafa}
*{box-sizing:border-box}
body{margin:0;padding:16px;background:var(--bg);color:var(--ink);
     font:15px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:820px;margin:0 auto}
h1{font-size:20px;margin:0 0 4px}
.sub{color:var(--soft);font-size:13px;margin:0 0 16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px;margin:0 0 14px}
.card h2{font-size:15px;margin:0 0 8px}
input[type=file]{display:block;width:100%;padding:10px;border:1px dashed #bbb;border-radius:8px;
                 background:#fcfcfc;margin:0 0 10px}
button{appearance:none;border:0;border-radius:8px;background:#1a73e8;color:#fff;
       font:600 15px/1 inherit;padding:12px 18px;width:100%}
.tscroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);white-space:nowrap}
th{color:var(--soft);font-weight:600}
td.wrap0{white-space:normal}
.ok{color:var(--ok);font-weight:600}.warn{color:var(--warn);font-weight:600}.bad{color:var(--bad);font-weight:600}
.note{color:var(--soft);font-size:13px;margin:8px 0 0}
ul{margin:6px 0 0 18px;padding:0}li{margin:2px 0}
"""


def _shell(title, body):
    return ("<!doctype html><html lang=en><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>%s</title><style>%s</style></head><body><div class=wrap>"
            "<h1>%s</h1>%s</div></body></html>" % (html.escape(title), _CSS, html.escape(title), body))


def _denied():
    return _shell("Send a Marg export", """
      <div class="card"><h2>Not permitted</h2>
      <p>This page loads pharmacy reports into the clinic's books. Your login is not on the
      clinic desk, so it is not open to you. If that is wrong, ask Dr Manoj.</p></div>""")


def _cls(status, verdict):
    if status == "TAKEN" and verdict == "VERIFIED":
        return "ok"
    if status in ("ALREADY", "BUSY") or (status == "TAKEN" and verdict):
        return "warn"
    return "bad"


def _say(r):
    if r["status"] == "TAKEN":
        what = r["type"] or "not recognised"
        span = (" %s" % r["date_from"]) if r["date_from"] else ""
        if r["date_to"] and r["date_to"] != r["date_from"]:
            span += " to %s" % r["date_to"]
        tail = ""
        if r["lines"]:
            tail = " · %d item lines kept, the file itself deleted (it carries patient numbers)" % r["lines"]
        elif r["kept"]:
            tail = " · file kept"
        return "taken — %s%s · %s%s" % (what, span, r["verdict"] or "no verdict", tail)
    if r["status"] == "ALREADY":
        return "already here — %s%s, taken %s. Nothing was counted twice." % (
            r["type"] or "?", (" " + r["date_from"]) if r["date_from"] else "", (r["when"] or "")[:16].replace("T", " "))
    if r["status"] == "BUSY":
        return "busy — %s" % r["reason"]
    return "not taken — %s" % (r["reason"] or "refused")


def _recent_table(rows):
    if not rows:
        return "<p class=note>Nothing has been taken yet.</p>"
    out = ["<div class=tscroll><table><tr><th>when</th><th>report</th><th>for</th>"
           "<th>verdict</th><th>lines</th><th>came by</th></tr>"]
    by = {"manual": "by hand", "push": "medical PC", "drive": "Drive", "pc": "Dr Manoj's PC", "": "Drive"}
    for r in rows:
        span = r["date_from"] or ""
        if r["date_to"] and r["date_to"] != r["date_from"]:
            span += " – " + r["date_to"]
        out.append("<tr><td>%s</td><td class=wrap0>%s</td><td>%s</td><td class=%s>%s</td>"
                   "<td>%s</td><td>%s</td></tr>" % (
                       html.escape((r["when"] or "")[:16].replace("T", " ")),
                       html.escape(r["type"] or "?"), html.escape(span),
                       "ok" if r["verdict"] == "VERIFIED" else "bad", html.escape(r["verdict"] or "—"),
                       r["lines"] or "", html.escape(by.get(r["source"], r["source"]))))
    out.append("</table></div>")
    return "".join(out)


# ------------------------------------------------------------------ routes
@bp.route("/finance/clinic/marg/upload", methods=["GET", "POST"])
def marg_upload():
    u, err = _require("maker", "checker", unit=_unit)
    if err:
        return _denied()
    try:
        import marg_take as MT
    except Exception as e:                                     # noqa: BLE001
        return _shell("Send a Marg export", "<div class=card><h2>Not ready</h2><p class=note>"
                      "The server's Marg reader is not installed here (%s). Nothing was lost — "
                      "keep the file and try again once it is.</p></div>" % html.escape(str(e)[:120]))

    done = ""
    if request.method == "POST":
        files = [f for f in request.files.getlist("f") if f and f.filename]
        if not files:
            done = "<div class=card><h2>Nothing chosen</h2><p class=note>Pick the export file first.</p></div>"
        else:
            lines = []
            for f in files[:MAX_FILES]:
                raw = f.read()
                r = MT.take(raw, name=f.filename, source="manual")
                lines.append("<li><b>%s</b><br><span class=%s>%s</span></li>" % (
                    html.escape(f.filename[:80]), _cls(r["status"], r["verdict"]), html.escape(_say(r))))
            extra = ("<p class=note>Only the first %d files were taken; send the rest in another "
                     "go.</p>" % MAX_FILES) if len(files) > MAX_FILES else ""
            done = "<div class=card><h2>What happened</h2><ul>%s</ul>%s</div>" % ("".join(lines), extra)

    c = MT.counts()
    body = done + """
      <div class="card">
        <h2>Send an export</h2>
        <form method=post enctype="multipart/form-data">
          <input type=file name=f multiple accept=".xls,.xlsx,.pdf">
          <button type=submit>Send to the server</button>
        </form>
        <p class=note>The file Marg wrote, exactly as it is — <b>.xls</b>, <b>.xlsx</b> or <b>.pdf</b>,
        up to 10 at a time. Sending the same report again is safe: the server knows it by its own
        contents and will say it already has it. A sale report is read into item lines and the file
        is then deleted here, because it carries patients' numbers.</p>
      </div>
      <div class="card">
        <h2>Last taken</h2>
        %s
        <p class=note>%d reports held in all, %d of them verified, %d today.</p>
      </div>""" % (_recent_table(MT.recent(20)), c["total"], c["verified"], c["today"])
    return _shell("Send a Marg export", body)


# ------------------------------------------------------------------ the machine door
def _rate_ok():
    """A crude, honest guard: a sender gone mad cannot spend this box's day."""
    now = time.time()
    while _hits and now - _hits[0] > 60:
        _hits.pop(0)
    if len(_hits) >= RATE_PER_MIN:
        return False
    _hits.append(now)
    return True


def _answer(r, code):
    return jsonify(ok=r["status"] in ("TAKEN", "ALREADY"), status=r["status"], md5=r["md5"],
                   type=r["type"], variant=r["variant"], verdict=r["verdict"], lines=r["lines"],
                   kept=r["kept"], stamp=r["stamp"], date_from=r["date_from"], date_to=r["date_to"],
                   message=_say(r)), code


@bp.route("/finance/api/marg-file", methods=["GET", "POST"])
def api_marg_file():
    tok = os.environ.get("FINANCE_MARG_TOKEN", "")
    if not tok:
        return jsonify(ok=False, status="NO_TOKEN",
                       message="FINANCE_MARG_TOKEN is not set on this server"), 503
    if not hmac.compare_digest(str(request.headers.get("X-Finance-Marg", "")), str(tok)):
        return jsonify(ok=False, status="NOT_YOU", message="bad or missing key"), 401
    try:
        import marg_take as MT
    except Exception as e:                                     # noqa: BLE001
        return jsonify(ok=False, status="NOT_READY",
                       message="the Marg reader is not installed here: %s" % str(e)[:120]), 503
    if request.method == "GET":
        c = MT.counts()
        return jsonify(ok=True, status="READY", held=c["total"], verified=c["verified"],
                       today=c["today"], max_bytes=MT.MAX_BYTES), 200
    if not _rate_ok():
        return jsonify(ok=False, status="SLOW_DOWN",
                       message="more than %d files in a minute; nothing was taken" % RATE_PER_MIN), 429
    if (request.content_length or 0) > MT.MAX_BYTES + 65536:
        return jsonify(ok=False, status="REFUSED",
                       message="too big; a Marg export is a few hundred KB"), 413
    f = request.files.get("f")
    if f is not None:
        raw = f.read()
        name = (request.form.get("name") or f.filename or "").strip()
    else:
        raw = request.get_data(cache=False) or b""
        name = (request.headers.get("X-Marg-Name") or "").strip()
    want = (request.form.get("md5") or request.headers.get("X-Marg-MD5") or "").strip().lower()
    if want:
        if len(want) != 32 or hashlib.md5(raw).hexdigest() != want:
            return jsonify(ok=False, status="REFUSED", md5="",
                           message="the bytes do not match the md5 you declared -- nothing taken"), 400
    src = (request.form.get("source") or request.headers.get("X-Marg-Source") or "push").strip()
    r = MT.take(raw, name=name, source=src)
    return _answer(r, {"TAKEN": 200, "ALREADY": 200, "BUSY": 503}.get(r["status"], 400))
