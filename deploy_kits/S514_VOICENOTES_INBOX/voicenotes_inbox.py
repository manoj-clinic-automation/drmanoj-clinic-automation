#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""voicenotes_inbox.py -- kit S514_VOICENOTES_INBOX (session 304, 10-Oct-2026; D689 pick 2).

THE OWNER'S ASK: a to-do list he makes in Voicenotes reaches the task section of his staff-lists panel by itself
(until now he pasted it). Voicenotes sends a webhook on "To-Do List Creation"; this is the door it posts to, and the
small inbox the panel reads.

  POST /finance/api/voicenotes-push?key=<key>   the ONE public door (the front gate lets this path through; the key is
        checked HERE, against /root/finance/voicenotes.key, which the installer makes and which is never printed).
        A to-do list becomes one inbox row per line. Any other kind of Voicenotes event (a note created, updated or
        deleted, a summary, main points) is answered 200 and kept as nothing but its name -- the owner may tick more
        events than he meant to, and Voicenotes must not retry. A list sent twice is stored once.
  GET  /finance/aaj/api/vn                       the owner only: the waiting lines, the last few posts received (their
        event names and how many lines), and the address to paste into Voicenotes.
  POST /finance/aaj/api/vn  {op:'used'|'drop', ids:[...]}   the owner only: put into the task box, or removed.

Nothing here makes a task. A line waits in the inbox until he puts it into the "Give a task" box, picks who gets it
and presses Give -- the panel's own, unchanged way of giving a task. The words of a line are kept as sent (one line,
no control characters, 300 characters at most -- aaj_kaam's own limit); nothing else from the post is kept.
"""
import datetime as dt
import hmac
import html
import json
import os
import re
import time

KEY_FILE = os.environ.get("VOICENOTES_KEY_FILE", "/root/finance/voicenotes.key")
PUBLIC_URL = "https://followup.dr-manoj.in/finance/api/voicenotes-push"
TEXT_MAX, LINES_MAX, TITLE_MAX, WAITING_MAX, RATE_PER_HOUR = 300, 40, 120, 300, 60
OTHER_EVENT = re.compile(r"recording|summary|main.?point|delet|updat|transcri|note\.(?:created|updated|deleted)", re.I)
MARK = re.compile(r"^\s*(?:[-*•‣◦▪]\s+|\d{1,2}[.)]\s+)")
BOX = re.compile(r"^\s*(?:\[[ xX]?\]|☐|☑|✅)\s*")
INBOX_SQL = ("CREATE TABLE IF NOT EXISTS vn_inbox (id INTEGER PRIMARY KEY, at TEXT NOT NULL, note_id TEXT NOT NULL DEFAULT '', "
             "title TEXT NOT NULL DEFAULT '', text TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'new', state_at TEXT NOT NULL DEFAULT '', "
             "state_by TEXT NOT NULL DEFAULT '')")
SEEN_SQL = ("CREATE TABLE IF NOT EXISTS vn_seen (id INTEGER PRIMARY KEY, at TEXT NOT NULL, event TEXT NOT NULL DEFAULT '', "
            "kind TEXT NOT NULL DEFAULT '', lines INTEGER NOT NULL DEFAULT 0, kept INTEGER NOT NULL DEFAULT 0, why TEXT NOT NULL DEFAULT '')")
_hits = []


def clean(text, limit):
    """One line, no control characters, cut to a length (aaj_kaam.clean, the same rule)."""
    t = "".join(ch if (ch >= " " and ch != "\x7f") else " " for ch in str(text or ""))
    return " ".join(t.split())[:limit]


def _key():
    try:
        with open(KEY_FILE, "r", encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def _rate_ok():
    now = time.time()
    while _hits and now - _hits[0] > 3600:
        _hits.pop(0)
    if len(_hits) >= RATE_PER_HOUR:
        return False
    _hits.append(now)
    return True


def _texts(v):
    """Every piece of text in a to-do payload's content, in order: a string, a list of strings, or a list of objects that
    carry 'text' / 'content' / 'title' / 'task' / 'description'."""
    out = []
    if isinstance(v, str):
        out.append(v)
    elif isinstance(v, list):
        for x in v[:200]:
            out.extend(_texts(x))
    elif isinstance(v, dict):
        for k in ("text", "content", "title", "task", "description", "body"):
            if isinstance(v.get(k), (str, list)):
                out.extend(_texts(v[k]))
                break
    return out


def lines_of(content):
    """The to-do lines: HTML and Markdown taken apart into lines; a list mark or a tick-box at the very start taken off
    (the panel's own rule: '10.30 baje' and '2.5 kg' stay as written); a heading line ('To-do list:', '# Tasks') and
    an empty one dropped; the same line twice kept once."""
    raw = []
    for t in _texts(content):
        t = re.sub(r"(?i)<\s*(?:br|/li|/p|/div|/h\d|li|p|div|h\d)\b[^>]*>", "\n", t)
        t = html.unescape(re.sub(r"<[^>]+>", "", t))
        raw.extend(t.splitlines())
    out, seen = [], set()
    for s in raw:
        s = BOX.sub("", MARK.sub("", s)).strip()
        s = re.sub(r"^#{1,6}\s+", "", s).strip()
        s = s.strip("*_ ").strip()
        if not s or re.match(r"(?i)^(?:to[- ]?do(?:s| list)?|tasks?|action items?)\s*:?$", s):
            continue
        s = clean(s, TEXT_MAX)
        if s and s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return out[:LINES_MAX]


def ensure(con):
    con.execute(INBOX_SQL)
    con.execute(SEEN_SQL)


def take(con, body, now):
    """Store one post. Returns (answer dict, http status). Pure apart from the two tables, so the walk holds it."""
    ensure(con)
    if not isinstance(body, dict):
        con.execute("INSERT INTO vn_seen (at, event, kind, lines, kept, why) VALUES (?,?,?,?,?,?)", (now, "", "", 0, 0, "not JSON"))
        con.commit()
        return dict(ok=False, error="bad_payload"), 400
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    event = clean(body.get("event") or body.get("type") or "", 60)
    kind = clean(data.get("type") or "", 40)
    if OTHER_EVENT.search(event) and not re.search(r"(?i)to.?do", event + " " + kind):
        con.execute("INSERT INTO vn_seen (at, event, kind, lines, kept, why) VALUES (?,?,?,?,?,?)", (now, event, kind, 0, 0, "not a to-do list"))
        con.commit()
        return dict(ok=True, kept=0, ignored="not a to-do list"), 200
    content = data.get("content") if "content" in data else (data.get("todos") or data.get("items") or data.get("tasks") or "")
    lines = lines_of(content)
    note_id = clean(data.get("id") or data.get("recording_id") or "", 80)
    title = clean(data.get("title") or "", TITLE_MAX)
    waiting = con.execute("SELECT COUNT(*) FROM vn_inbox WHERE state='new'").fetchone()[0]
    kept = 0
    for s in lines:
        if waiting + kept >= WAITING_MAX:
            break
        if con.execute("SELECT 1 FROM vn_inbox WHERE note_id=? AND text=? AND ?<>''", (note_id, s, note_id)).fetchone():
            continue                                               # the same list sent again (a retry): stored once
        con.execute("INSERT INTO vn_inbox (at, note_id, title, text, state) VALUES (?,?,?,?, 'new')", (now, note_id, title, s))
        kept += 1
    con.execute("INSERT INTO vn_seen (at, event, kind, lines, kept, why) VALUES (?,?,?,?,?,?)",
                (now, event, kind, len(lines), kept, "" if lines else "no lines found"))
    con.execute("DELETE FROM vn_seen WHERE id NOT IN (SELECT id FROM vn_seen ORDER BY id DESC LIMIT 50)")
    con.commit()
    return dict(ok=True, kept=kept, lines=len(lines)), 200


def inbox(con, key):
    ensure(con)
    con.commit()
    items = [dict(id=r[0], at=r[1], title=r[2], text=r[3]) for r in
             con.execute("SELECT id, at, title, text FROM vn_inbox WHERE state='new' ORDER BY id LIMIT ?", (WAITING_MAX,))]
    seen = [dict(at=r[0], event=r[1], kind=r[2], lines=r[3], kept=r[4], why=r[5]) for r in
            con.execute("SELECT at, event, kind, lines, kept, why FROM vn_seen ORDER BY id DESC LIMIT 5")]
    return dict(ok=True, items=items, seen=seen, url=("%s?key=%s" % (PUBLIC_URL, key)) if key else "")


def mark(con, op, ids, login, now):
    ensure(con)
    if op not in ("used", "drop") or not isinstance(ids, list):
        return "bad_request"
    ids = [i for i in ids if isinstance(i, int) and not isinstance(i, bool)][:WAITING_MAX]
    for i in ids:
        con.execute("UPDATE vn_inbox SET state=?, state_at=?, state_by=? WHERE id=? AND state='new'", (op, now, login, i))
    con.commit()
    return None


def init(app, db_getter, require_fn, current_user_fn):
    from flask import Blueprint, jsonify, request                      # noqa: PLC0415
    bp = Blueprint("voicenotes_inbox", __name__)

    def _now():
        return dt.datetime.now().replace(microsecond=0).isoformat(sep=" ")

    def _nostore(r):
        r.headers["Cache-Control"] = "no-store"
        return r

    @bp.route("/finance/api/voicenotes-push", methods=["POST"])
    def vn_push():
        """Voicenotes' door. The front gate lets this one path through; the key is checked HERE."""
        key = _key()
        given = request.args.get("key", "")
        if not key or not given or not hmac.compare_digest(str(given), key):
            return jsonify(ok=False, error="bad_key"), 401
        if not _rate_ok():
            return jsonify(ok=False, error="too_many"), 429
        body = request.get_json(silent=True, force=True)
        out, code = take(db_getter(), body, _now())
        return jsonify(**out), code

    @bp.route("/finance/aaj/api/vn", methods=["GET", "POST"])
    def vn_owner():
        u = current_user_fn() or {}
        login = str(u.get("user") or "").strip().lower()
        if not login:
            return jsonify(ok=False, error="not_signed_in"), 401
        owner, _err = require_fn("checker", unit="packs")            # the owner: the console's own gate (aaj_kaam's too)
        if not owner:
            return jsonify(ok=False, error="owner_only"), 403
        con = db_getter()
        if request.method == "POST":
            b = request.get_json(silent=True) if request.is_json else None
            if not isinstance(b, dict):
                return jsonify(ok=False, error="bad_request"), 400
            why = mark(con, b.get("op"), b.get("ids"), login, _now())
            if why:
                return jsonify(ok=False, error=why), 400
        return _nostore(jsonify(**inbox(con, _key())))

    app.register_blueprint(bp)


if __name__ == "__main__":
    raise SystemExit("voicenotes_inbox.py is mounted by finance_app.py")
