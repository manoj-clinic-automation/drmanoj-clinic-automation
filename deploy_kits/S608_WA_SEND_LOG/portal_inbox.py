#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
portal_inbox.py -- the owner's WhatsApp Inbox (kit S597, session S329, 19-Oct-2026 · D744)
==========================================================================================
THE OWNER, 19-Oct-2026 (01:56-06:10 IST): "I need interactive whatsapp communication from the waba incoming messages ...
images etc can't be opened" · "Only me, and add a call button inline" · "Need to send photo and pdf back from beginning,
so that the build is completed once only" · "Need full mobile numbers, clinic id" · "Also I want to send voice messages"
· "Mockups are ok".

WHAT IT IS: one page at /portal/inbox, behind the portal's own WhatsApp gate (wa_required: the doctor login AND a name in
PORTAL_WA_USERS -- today "manoj" alone). It lists every WhatsApp conversation on the clinic number, shows photos, PDFs,
voice notes and videos inside the chat, replies by text / photo / PDF / voice note inside WhatsApp's 24-hour window,
sends an approved template after it (portal_wa's own registry and sender), and places a click-to-call through the live
call service (his mobile rings first; the patient sees the clinic number).

WHERE THE MESSAGES COME FROM -- NOTHING LIVE IS CHANGED TO GET THEM: the receiver (wa_receiver.py) writes every push it
gets, first and raw, to /root/wa/wa_logs/YYYY-MM-DD.jsonl. This module reads those files forward from where it last
stopped (an offset per file) into its own store /root/wa/wa_inbox/inbox.db, using the receiver's OWN field paths
(build_row / is_inbound_message, copied verbatim below). The receiver, its sheet and its alert are untouched.

MEDIA: an incoming photo/PDF/voice carries MyOperator's public S3 copy (payload.data.context.link). It is fetched once,
when first opened, into /root/wa/wa_inbox/media/ (root, 700) and served only through the guarded route. An outgoing
file is kept in /root/wa/wa_inbox/out/ and given to MyOperator as a link under /portal/inbox/f/<token>/<name> -- a
random 32-hex token, valid for INBOX_LINK_HOURS (6) hours, the only route here without the login (MyOperator must fetch
it). The send shape is the one kit S595 proved on 19-Oct 08:17 IST: data.type image|document|audio, data.context
{link, filename, mime_type, caption}. A voice note is recorded in the browser and encoded there as MP3 (S595: OGG was
refused by MyOperator, MP3 delivered) with lame.min.js (LGPL, LAME project, lame.sourceforge.net), served from this
module.

S599 (19-Oct-2026, the owner 08:52 IST: "I want to send templates" · "see the replies which are sent by my staff members
in the chat also"): (1) the WhatsApp key is the one the installer PROVED against MyOperator, named (never copied) in
/root/wa/wa_inbox/config.json -- the S597 test text had been refused with HTTP 500 by the key it guessed; (2) templates
use that same key; (3) each chat also shows the clinic's replies sent from the other pages: the portal's template log
(/root/wa/wa_portal/wa_portal_sends.csv -- Send WhatsApp and the follow-up batch) and the 'out' rows of the WA_Inbox sheet
(the call tracker's replies), each with the name of who sent it. Replies typed in MyOperator's own app reach the server
only when MyOperator's "message sent" webhook is switched on; the raw-log reader already takes them when they come.

SAFETY: every POST needs the X-Inbox header (a page on another site cannot set it); phones are logged by last 4 only;
no token is ever printed; any failure inside a route answers in JSON, never a crash of the portal.
"""

import os, re, json, time, uuid, sqlite3, secrets, hashlib, threading, mimetypes, datetime, urllib.request, urllib.error
from urllib.parse import urlparse

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
RAW_DIR = os.environ.get("INBOX_RAW_DIR", "/root/wa/wa_logs")
STORE = os.environ.get("INBOX_STORE", "/root/wa/wa_inbox")
DB_PATH = os.path.join(STORE, "inbox.db")
MEDIA_DIR = os.path.join(STORE, "media")
OUT_DIR = os.path.join(STORE, "out")
WA_ENV = os.environ.get("INBOX_WA_ENV", "/root/wa/.env")
HERE = os.path.dirname(os.path.abspath(__file__))
LAME_JS = os.path.join(HERE, "static_inbox", "lame.min.js")
API_URL = os.environ.get("INBOX_API_URL", "https://publicapi.myoperator.co/chat/messages")
CALL_URL = os.environ.get("INBOX_CALL_URL", "http://127.0.0.1:8097/call")
COMPANY_ID = "68384350414b9847"          # the same constants portal_wa / wa_send carry
PHONE_NUMBER_ID = "1090067637530949"
WINDOW_H = 24
MEDIA_TYPES = ("image", "document", "video", "audio", "sticker", "voice")
MEDIA_HOSTS = ("amazonaws.com", "myoperator.co", "myoperator.com")
SEND_RULES = {   # kind -> (allowed mimes, max bytes)
    "image": (("image/jpeg", "image/png"), 5 * 1024 * 1024),
    "document": (("application/pdf",), 20 * 1024 * 1024),
    "audio": (("audio/mpeg",), 16 * 1024 * 1024),
}
_ING_LOCK = threading.Lock()
_ING_LAST = {"t": 0.0}
_PAT = {"mtime": None, "map": {}}


# --------------------------------------------------------------------------- helpers
def now_ist():
    return datetime.datetime.now(IST)


def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%S") + "+05:30"


def last10(s):
    d = re.sub(r"\D", "", str(s or ""))
    return d[-10:] if len(d) >= 10 else ""


def tail4(s):
    return "••••" + (re.sub(r"\D", "", str(s or ""))[-4:] or "?")


def read_env(path=WA_ENV):
    vals = {}
    try:
        for raw in open(path, encoding="utf-8"):
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return vals


def dig(d, *paths, default=""):
    """The receiver's own dig(): the first non-empty value at any dotted path."""
    for path in paths:
        cur = d
        ok = True
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur not in (None, "", [], {}):
            return cur
    return default


def to_ist_iso(ts):
    """The receiver's own to_ist_iso(): any MyOperator timestamp -> an IST ISO string."""
    try:
        s = str(ts).strip()
        if s.isdigit():
            v = int(s)
            if v > 10 ** 12:
                v //= 1000
            return iso(datetime.datetime.fromtimestamp(v, IST))
        if s:
            t = s.replace("Z", "+00:00")
            m = re.match(r"^(.*?)(\.\d+)?([+-]\d{2}:?\d{2})?$", t)
            if m:
                t = m.group(1) + ((m.group(2) or "")[:7]) + (m.group(3) or "")
            try:
                d = datetime.datetime.fromisoformat(t)
            except ValueError:
                return ""
            if d.tzinfo is None:
                d = d.replace(tzinfo=datetime.timezone.utc)
            return iso(d.astimezone(IST))
    except Exception:                                                   # noqa: BLE001
        pass
    return ""


def parse_ts(s):
    try:
        return datetime.datetime.fromisoformat(str(s))
    except Exception:                                                   # noqa: BLE001
        return None


def is_inbound_message(et, direction, mtype, message):
    """The receiver's own filter, verbatim: inbound patient messages only, no status pings."""
    et = str(et).lower()
    direction = str(direction).lower()
    mtype = str(mtype).lower()
    status_only = ("received" not in et) and any(
        k in et for k in ("delivered", "read", "sent", "status", "failed"))
    if status_only:
        return False
    inbound = "out" not in direction
    looks_message = ("received" in et) or bool(message) or (mtype and mtype != "status")
    return inbound and looks_message


def read_push(payload):
    """One raw push -> a dict of what it says. Paths are the receiver's build_row paths, plus the media details."""
    g = lambda *p, **k: dig(payload, *p, **k)                           # noqa: E731
    return {
        "ts": g("timestamp", "payload.timestamp", "data.timestamp", "payload.data.timestamp"),
        "phone": g("customer_identifier", "payload.customer_identifier", "data.customer_identifier", "customer_number",
                   "payload.customer_number", "payload.data.context.from", "contact.wa_id"),
        "direction": g("direction", "payload.direction", "data.direction", default="incoming"),
        "mtype": g("payload.data.type", "data.type", "payload.type", "type", default="text"),
        "body": g("payload.data.context.body", "data.context.body", "payload.data.body", "data.body", "message", "text",
                  default=""),
        "id": g("payload.id", "payload.message_id", "data.id", "id", "message_id"),
        "status": g("payload.status", "data.status", "status", default=""),
        "event": g("event_type", "event", "payload.event_type", default=""),
        "link": g("payload.data.context.link", "data.context.link"),
        "mime": g("payload.data.context.mime_type", "data.context.mime_type", "payload.data.context.mimetype",
                  "data.context.mimetype"),
        "fname": g("payload.data.context.filename", "data.context.filename", "payload.data.context.file_name"),
        "caption": g("payload.data.context.caption", "data.context.caption"),
        "template": g("payload.data.context.template_name", "data.context.template_name"),
    }


# --------------------------------------------------------------------------- store
def db():
    os.makedirs(STORE, mode=0o700, exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=20)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript("""
    CREATE TABLE IF NOT EXISTS msgs(
        rid INTEGER PRIMARY KEY AUTOINCREMENT, mid TEXT UNIQUE, phone TEXT NOT NULL, dir TEXT NOT NULL,
        ts TEXT NOT NULL, mtype TEXT, body TEXT, media_url TEXT, mime TEXT, fname TEXT, local_path TEXT,
        status TEXT, sent_by TEXT, src TEXT);
    CREATE INDEX IF NOT EXISTS msgs_phone_ts ON msgs(phone, ts);
    CREATE TABLE IF NOT EXISTS offsets(fname TEXT PRIMARY KEY, pos INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS pending_status(mid TEXT PRIMARY KEY, status TEXT, ts TEXT);
    CREATE TABLE IF NOT EXISTS reads(phone TEXT PRIMARY KEY, ts TEXT);
    CREATE TABLE IF NOT EXISTS replies(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, body TEXT NOT NULL,
        sort INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS links(token TEXT PRIMARY KEY, path TEXT NOT NULL, name TEXT NOT NULL, mime TEXT,
        expires TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS shapes(sig TEXT PRIMARY KEY, n INTEGER NOT NULL);
    """)
    return c


STATUS_RANK = {"": 0, "pending": 1, "sent": 2, "delivered": 3, "read": 4, "failed": 5}


def _status_word(p):
    for s in (str(p["status"]).lower(), str(p["event"]).lower()):
        for w in ("failed", "read", "delivered", "sent"):
            if w in s:
                return w
    return ""


def _shape(obj, prefix="", out=None):
    out = out if out is not None else []
    if isinstance(obj, dict):
        for k in sorted(obj)[:40]:
            _shape(obj[k], prefix + "." + str(k) if prefix else str(k), out)
    else:
        out.append(prefix)
    return out


def ingest_line(c, payload):
    """Apply one raw push. Returns 'in', 'out', 'status', 'skip' or 'unread'."""
    if not isinstance(payload, dict):
        return "skip"
    p = read_push(payload)
    phone = last10(p["phone"])
    mid = str(p["id"] or "").strip()
    mtype = str(p["mtype"] or "text").lower()
    word = _status_word(p)
    ts = to_ist_iso(p["ts"]) or iso(now_ist())
    if is_inbound_message(p["event"], p["direction"], mtype, p["body"]):
        if not phone or not mid:
            sig = "in:" + ",".join(_shape(payload))[:400]
            c.execute("INSERT INTO shapes(sig,n) VALUES(?,1) ON CONFLICT(sig) DO UPDATE SET n=n+1", (sig,))
            return "unread"
        body = str(p["body"] or "")
        link = str(p["link"] or "")
        if mtype in MEDIA_TYPES:
            if body.startswith("http") and not link:            # the receiver's convention: media link in 'message'
                link, body = body, ""
            body = str(p["caption"] or body or "")
        row = c.execute("SELECT rid, media_url FROM msgs WHERE mid=?", (mid,)).fetchone()
        if row:
            if link and not row["media_url"]:                      # a late push brings the link the first lacked
                c.execute("UPDATE msgs SET media_url=?, mime=COALESCE(NULLIF(mime,''),?), fname=COALESCE(NULLIF(fname,''),?)"
                          " WHERE rid=?", (link, str(p["mime"] or ""), str(p["fname"] or ""), row["rid"]))
            return "in"
        c.execute("INSERT INTO msgs(mid,phone,dir,ts,mtype,body,media_url,mime,fname,status,src) "
                  "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                  (mid, phone, "in", ts, mtype, body, link, str(p["mime"] or ""), str(p["fname"] or ""), "received", "log"))
        return "in"
    # not an inbound message: a status ping, or an echo of something the clinic sent
    if mid and word:
        row = c.execute("SELECT rid, status FROM msgs WHERE mid=?", (mid,)).fetchone()
        if row:
            if STATUS_RANK.get(word, 0) > STATUS_RANK.get(row["status"] or "", 0):
                c.execute("UPDATE msgs SET status=? WHERE rid=?", (word, row["rid"]))
        else:
            old = c.execute("SELECT status FROM pending_status WHERE mid=?", (mid,)).fetchone()
            if not old or STATUS_RANK.get(word, 0) > STATUS_RANK.get(old["status"] or "", 0):
                c.execute("INSERT OR REPLACE INTO pending_status(mid,status,ts) VALUES(?,?,?)", (mid, word, ts))
    if "out" in str(p["direction"]).lower() and phone and mid and (p["body"] or p["template"] or p["link"]):
        if not c.execute("SELECT 1 FROM msgs WHERE mid=?", (mid,)).fetchone():
            body = str(p["body"] or (("Template: " + str(p["template"])) if p["template"] else "") or p["caption"] or "")
            c.execute("INSERT INTO msgs(mid,phone,dir,ts,mtype,body,media_url,mime,fname,status,src) "
                      "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                      (mid, phone, "out", ts, mtype, body, str(p["link"] or ""), str(p["mime"] or ""),
                       str(p["fname"] or ""), word or "sent", "log"))
            _apply_pending(c, mid)
        return "out"
    return "status" if word else "skip"


def _apply_pending(c, mid):
    ps = c.execute("SELECT status FROM pending_status WHERE mid=?", (mid,)).fetchone()
    if ps:
        c.execute("UPDATE msgs SET status=? WHERE mid=?", (ps["status"], mid))
        c.execute("DELETE FROM pending_status WHERE mid=?", (mid,))


def _tpl_text(name, values):
    try:
        import portal_wa
        t = portal_wa.TEMPLATES.get(name) or {}
        body = t.get("preview") or ""
        for k, v in (values or {}).items():
            body = body.replace("{%s}" % k, str(v))
        return "Template: %s\n%s" % (t.get("title") or name, body) if body else "Template: " + (t.get("title") or name)
    except Exception:                                                   # noqa: BLE001
        return "Template: " + str(name)


def ingest_portal_log(c, report=None):
    """The portal's own template log (Send WhatsApp, follow-up batch, the inbox): every LIVE send that went, with who sent it."""
    import csv, io
    try:
        size = os.path.getsize(PORTAL_LOG)
    except OSError:
        return
    row = c.execute("SELECT pos FROM offsets WHERE fname='csv:portal'").fetchone()
    pos = row["pos"] if row else 0
    if size < pos:                                                      # the log was replaced: read it again from the top
        pos = 0
    if size == pos:
        return
    with open(PORTAL_LOG, "rb") as fh:
        head = fh.readline().decode("utf-8", "replace")
        if pos == 0:
            pos = len(head.encode("utf-8"))
        fh.seek(pos)
        chunk = fh.read(size - pos)
    end = chunk.rfind(b"\n")
    if end < 0:
        return
    cols = next(csv.reader([head.strip()]))
    for rec in csv.reader(io.StringIO(chunk[:end + 1].decode("utf-8", "replace"))):
        if not rec:
            continue
        r = dict(zip(cols, rec))
        if r.get("mode") != "LIVE" or r.get("ok") != "1":
            continue
        ph = last10(r.get("phone"))
        mid = (r.get("message_id") or "").strip()
        if not ph:
            continue
        mid = mid or "csv-" + hashlib.sha1(("%s|%s|%s" % (r.get("ts_ist"), ph, r.get("template"))).encode()).hexdigest()[:20]
        if c.execute("SELECT 1 FROM msgs WHERE mid=?", (mid,)).fetchone():
            continue
        try:
            vals = json.loads(r.get("values_json") or "{}")
        except ValueError:
            vals = {}
        c.execute("INSERT INTO msgs(mid,phone,dir,ts,mtype,body,status,sent_by,src) VALUES(?,?,?,?,?,?,?,?,?)",
                  (mid, ph, "out", r.get("ts_ist") or iso(now_ist()), "template", _tpl_text(r.get("template"), vals), "sent",
                   (r.get("sent_by") or "")[:40], "portal"))
        _apply_pending(c, mid)
        if report is not None:
            report["portal_log"] = report.get("portal_log", 0) + 1
    c.execute("INSERT OR REPLACE INTO offsets(fname,pos) VALUES('csv:portal',?)", (pos + end + 1,))


_SHEET = {"t": 0.0, "running": False, "last": "", "rows": 0}


def sheet_rows():
    """The 'out' rows of the WA_Inbox sheet (the call tracker's replies via wa_send_api): read-only, through the receiver's
    own sheet settings in /root/wa/.env. Returns a list of dicts; raises on any failure (the caller keeps it quiet)."""
    env = read_env()
    import gspread
    from google.oauth2.service_account import Credentials
    creds = Credentials.from_service_account_file(env["WA_SA_KEY"], scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    ws = gspread.authorize(creds).open_by_key(env["WA_SHEET_ID"]).worksheet(env.get("WA_TAB") or "WA_Inbox")
    values = ws.get_all_values()
    if not values:
        return []
    head = [h.strip().lower() for h in values[0]]
    out = []
    for v in values[1:]:
        r = {head[i]: (v[i] if i < len(v) else "") for i in range(len(head))}
        if str(r.get("direction", "")).strip().lower().startswith("out"):
            out.append(r)
    return out


def ingest_sheet(rows, report=None):
    c = db()
    try:
        c.execute("BEGIN IMMEDIATE")
        n = 0
        for r in rows:
            ph = last10(r.get("phone"))
            if not ph:
                continue
            body = str(r.get("message") or "")
            ts = to_ist_iso(r.get("timestamp")) or str(r.get("timestamp") or "")
            mid = str(r.get("message id") or "").strip() or \
                "sheet-" + hashlib.sha1(("%s|%s|%s" % (ts, ph, body)).encode()).hexdigest()[:20]
            if c.execute("SELECT 1 FROM msgs WHERE mid=?", (mid,)).fetchone():
                continue
            c.execute("INSERT INTO msgs(mid,phone,dir,ts,mtype,body,status,sent_by,src) VALUES(?,?,?,?,?,?,?,?,?)",
                      (mid, ph, "out", ts or iso(now_ist()), (r.get("type") or "text").lower(), body,
                       (r.get("status") or "sent").lower(), str(r.get("sent by") or "")[:40], "sheet"))
            _apply_pending(c, mid)
            n += 1
        c.execute("COMMIT")
        if report is not None:
            report["sheet"] = report.get("sheet", 0) + n
        return n
    except Exception:                                                   # noqa: BLE001
        try:
            c.execute("ROLLBACK")
        except Exception:                                               # noqa: BLE001
            pass
        raise
    finally:
        c.close()


def sheet_sync(force=False):
    """At most every 3 minutes, in the background: the page never waits for Google."""
    if _SHEET["running"] or (not force and time.time() - _SHEET["t"] < 180):
        return
    _SHEET["running"] = True
    _SHEET["t"] = time.time()

    def run():
        try:
            n = ingest_sheet(sheet_rows())
            _SHEET["last"], _SHEET["rows"] = iso(now_ist()), n
        except Exception as e:                                          # noqa: BLE001
            _SHEET["last"] = "failed: %s" % type(e).__name__
        finally:
            _SHEET["running"] = False
    threading.Thread(target=run, name="inbox_sheet_sync", daemon=True).start()


def ingest(force=False, report=None):
    """Read every raw-log file forward from its saved offset. Cheap when nothing is new. Never raises."""
    if not force and time.time() - _ING_LAST["t"] < 3:
        return
    with _ING_LOCK:
        _ING_LAST["t"] = time.time()
        try:
            names = sorted(n for n in os.listdir(RAW_DIR) if re.match(r"^\d{4}-\d{2}-\d{2}\.jsonl$", n))
        except OSError:
            return
        c = db()
        try:
            c.execute("BEGIN IMMEDIATE")
            for n in names:
                fp = os.path.join(RAW_DIR, n)
                row = c.execute("SELECT pos FROM offsets WHERE fname=?", (n,)).fetchone()
                pos = row["pos"] if row else 0
                try:
                    size = os.path.getsize(fp)
                except OSError:
                    continue
                if size <= pos:
                    continue
                with open(fp, "rb") as fh:
                    fh.seek(pos)
                    chunk = fh.read(size - pos)
                end = chunk.rfind(b"\n")
                if end < 0:
                    continue
                for line in chunk[:end].split(b"\n"):
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line.decode("utf-8", "replace"))
                    except ValueError:
                        res = "bad"
                    else:
                        res = ingest_line(c, rec.get("body") if isinstance(rec, dict) else None)
                    if report is not None:
                        report[res] = report.get(res, 0) + 1
                c.execute("INSERT OR REPLACE INTO offsets(fname,pos) VALUES(?,?)", (n, pos + end + 1))
            ingest_portal_log(c, report)
            c.execute("COMMIT")
        except Exception:                                               # noqa: BLE001
            try:
                c.execute("ROLLBACK")
            except Exception:                                           # noqa: BLE001
                pass
            if report is not None:
                raise
        finally:
            c.close()


def patients():
    """phone10 -> (name, clinic_id), from the portal's console.db mirror (read-only), cached on its file time."""
    try:
        import portal_wa
        path = portal_wa.CONSOLE_DB
    except Exception:                                                   # noqa: BLE001
        path = "/root/wa/console.db"
    try:
        mt = os.path.getmtime(path)
    except OSError:
        return {}
    if _PAT["mtime"] == mt:
        return _PAT["map"]
    m = {}
    try:
        cc = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=10)
        try:
            for r in cc.execute("SELECT phone10, name, clinic_id FROM patients"):
                k = last10(r[0])
                if k and k not in m:
                    m[k] = ((r[1] or "").strip(), (r[2] or "").strip())
        finally:
            cc.close()
    except Exception:                                                   # noqa: BLE001
        return _PAT["map"]
    _PAT["mtime"], _PAT["map"] = mt, m
    return m


def window(c, phone):
    r = c.execute("SELECT MAX(ts) FROM msgs WHERE phone=? AND dir='in'", (phone,)).fetchone()
    last = parse_ts(r[0]) if r and r[0] else None
    if not last:
        return {"open": False, "last_in": "", "hours_left": 0}
    left = WINDOW_H - (now_ist() - last).total_seconds() / 3600.0
    return {"open": left > 0, "last_in": r[0], "hours_left": round(max(left, 0), 1)}


def preview(row):
    t = (row["mtype"] or "text").lower()
    label = {"image": "Photo", "document": "PDF / file", "audio": "Voice note", "voice": "Voice note",
             "video": "Video", "sticker": "Sticker"}.get(t)
    b = (row["body"] or "").strip()
    if label:
        return label + (" · " + b if b else "")
    return b or "(%s)" % t


def row_out(r):
    return {"rid": r["rid"], "dir": r["dir"], "ts": r["ts"], "type": (r["mtype"] or "text").lower(), "body": r["body"] or "",
            "has_media": bool(r["media_url"] or r["local_path"]), "mime": r["mime"] or "", "fname": r["fname"] or "",
            "status": r["status"] or "", "sent_by": r["sent_by"] or ""}


# --------------------------------------------------------------------------- MyOperator
CONFIG = os.path.join(STORE, "config.json")
PORTAL_LOG = os.environ.get("INBOX_PORTAL_LOG", "/root/wa/wa_portal/wa_portal_sends.csv")


def token_from(source, cfg_get=None):
    """A key named by its SOURCE -- 'env:<file>:<NAME>', 'portal:<NAME>' or 'wa_send' -- never stored itself."""
    try:
        kind, _, rest = str(source or "").partition(":")
        if kind == "env":
            path, _, name = rest.rpartition(":")
            return read_env(path).get(name, "")
        if kind == "portal" and cfg_get is not None:
            return cfg_get(rest, "") or ""
        if kind == "wa_send":
            import sys as _sys
            if "/root/wa" not in _sys.path:
                _sys.path.append("/root/wa")
            import wa_send
            return wa_send.load_config().get("token") or ""
    except Exception:                                                   # noqa: BLE001
        return ""
    return ""


def config():
    try:
        with open(CONFIG, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:                                                   # noqa: BLE001
        return {}


def _token(cfg_get):
    """The key the installer proved against MyOperator (config.json names its source); the old order only without one."""
    src = config().get("token_source")
    if src:
        t = token_from(src, cfg_get)
        if t:
            return t
    return read_env().get("MYOP_AUTH_TOKEN") or cfg_get("MYOP_AUTH_TOKEN", "") or os.environ.get("MYOP_AUTH_TOKEN", "")


def myop_send(token, phone, data, timeout=30, trace=None):
    """POST one session message. Returns (ok, message_id, error). Never raises.

    S608: when `trace` (a dict) is passed it is filled with what was sent (never the key) and everything MyOperator
    answered -- status, body, headers (x-amzn-requestid is the id their tech team asks for), time taken."""
    payload = {"phone_number_id": PHONE_NUMBER_ID, "customer_country_code": "91", "customer_number": phone,
               "data": data, "reply_to": None, "myop_ref_id": None}
    req = urllib.request.Request(API_URL, data=json.dumps(payload).encode("utf-8"), method="POST")
    req.add_header("Authorization", "Bearer " + token)                 # capital B required
    req.add_header("X-MYOP-COMPANY-ID", COMPANY_ID)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    t0 = time.time()
    hdrs = {}
    if trace is not None:
        trace.update({"endpoint": API_URL, "request_json": json.dumps(payload), "status": 0, "raw": "", "headers": {},
                      "ms": 0})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            status = resp.status
            hdrs = dict(resp.headers.items())
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8", "replace")
        except Exception:                                               # noqa: BLE001
            raw = ""
        status = e.code
        try:
            hdrs = dict(e.headers.items()) if e.headers else {}
        except Exception:                                               # noqa: BLE001
            hdrs = {}
    except Exception as e:                                              # noqa: BLE001
        if trace is not None:
            trace.update({"ms": int((time.time() - t0) * 1000), "raw": "no answer: %s" % type(e).__name__})
        return False, "", "could not reach MyOperator (%s)" % type(e).__name__
    if trace is not None:
        trace.update({"status": status, "raw": raw[:4000], "ms": int((time.time() - t0) * 1000),
                      "headers": {k: v for k, v in hdrs.items() if k.lower() not in ("set-cookie", "authorization")}})
    try:
        j = json.loads(raw) if raw else {}
    except ValueError:
        j = {}
    d = j.get("data") if isinstance(j.get("data"), dict) else {}
    mid = str(d.get("message_id") or d.get("id") or "")
    ok = status in (200, 201) and (str(j.get("status", "")).lower() == "success" or bool(mid))
    if ok:
        return True, mid, ""
    why = j.get("message") or j.get("error") or j.get("errors") or raw[:200] or "refused"
    why = re.sub(r"\d{7,}", lambda m: "••••" + m.group(0)[-4:], why if isinstance(why, str) else json.dumps(why))
    return False, "", "MyOperator refused (HTTP %s): %s" % (status, why[:200])


# --------------------------------------------------------------------------- S608: the send log
# Every send the inbox makes is written here, one JSON line each, whatever the answer. Full numbers and texts: it is
# the clinic's own record, on the clinic's own server, shown only on the owner's page, and it is what MyOperator's
# team needs to find a request in their logs. It never holds the key.
SEND_LOG = os.path.join(STORE, "send_log.jsonl")
SMTP_CLASS = None                       # the walk puts a stand-in here; None = smtplib.SMTP
MYOP_TICKET_DEFAULT = "691386"
MYOP_MAIL_TO_DEFAULT = "support@myoperator.com,khushi.jain@myoperator.co"
_NOTE_LOCK = threading.Lock()
_NOTE = {"last": 0.0, "pending": [], "busy": False}
NOTE_GAP_S = 120


def _reqid(headers):
    for k, v in (headers or {}).items():
        if k.lower() in ("x-amzn-requestid", "x-request-id", "x-amz-apigw-id", "x-amzn-trace-id"):
            return str(v)
    return ""


def log_send(entry):
    """Append one attempt. Never raises -- a log must not stop a message."""
    try:
        os.makedirs(STORE, mode=0o700, exist_ok=True)
        entry = dict(entry)
        entry.setdefault("ts", iso(now_ist()))
        entry.setdefault("id", uuid.uuid4().hex[:12])
        old = os.umask(0o077)
        try:
            with open(SEND_LOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        finally:
            os.umask(old)
        if not entry.get("ok") and entry.get("kind") != "log-mail":
            _note_refused(entry)
    except Exception:                                                   # noqa: BLE001
        pass


def attempt_entry(user, phone, kind, text, trace, ok, mid, err, fname="", mime="", route="inbox"):
    tr = trace or {}
    return {"by": user or "doctor", "customer": phone, "kind": kind, "text": (text or "")[:1000],
            "file": fname or "", "mime": mime or "", "route": route, "ok": bool(ok), "message_id": mid or "",
            "error": err or "", "http_status": tr.get("status", ""), "myoperator_reply": tr.get("raw", ""),
            "request_id": _reqid(tr.get("headers")), "response_headers": tr.get("headers") or {},
            "ms": tr.get("ms", ""), "endpoint": tr.get("endpoint", ""), "request_json": tr.get("request_json", "")}


def read_log(days=7, only_refused=False, limit=2000):
    floor = iso(now_ist() - datetime.timedelta(days=days)) if days else ""
    out = []
    try:
        with open(SEND_LOG, encoding="utf-8") as fh:
            for line in fh:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if floor and str(e.get("ts", "")) < floor:
                    continue
                if only_refused and e.get("ok"):
                    continue
                out.append(e)
    except OSError:
        pass
    out.sort(key=lambda e: e.get("ts", ""), reverse=True)
    return out[:limit]


CSV_COLS = ("ts", "by", "customer", "kind", "text", "file", "route", "ok", "http_status", "message_id", "error",
            "myoperator_reply", "request_id", "ms", "endpoint", "request_json", "response_headers")


def log_csv(rows):
    import csv as _csv
    import io as _io
    buf = _io.StringIO()
    w = _csv.writer(buf)
    w.writerow(["time_ist", "sent_by", "customer_number", "kind", "text", "file", "route", "result", "http_status",
                "message_id", "error", "myoperator_reply", "x_amzn_requestid", "elapsed_ms", "endpoint",
                "request_json_without_key", "response_headers"])
    for e in rows:
        w.writerow([e.get("ts", ""), e.get("by", ""), ("91" + e["customer"]) if e.get("customer") else "",
                    e.get("kind", ""), e.get("text", ""), e.get("file", ""), e.get("route", ""),
                    "sent" if e.get("ok") else "REFUSED", e.get("http_status", ""), e.get("message_id", ""),
                    e.get("error", ""), e.get("myoperator_reply", ""), e.get("request_id", ""), e.get("ms", ""),
                    e.get("endpoint", ""), e.get("request_json", ""), json.dumps(e.get("response_headers") or {})])
    return buf.getvalue()


def entry_text(e):
    return ("Time (IST): %s\nSent by: %s\nCustomer: +91 %s\nKind: %s\nText: %s\nResult: %s\nHTTP status: %s\n"
            "MyOperator reply: %s\nx-amzn-requestid: %s\nTime taken: %s ms\nEndpoint: %s\n"
            "Request (key not shown): %s\nResponse headers: %s\n"
            % (e.get("ts", ""), e.get("by", ""), e.get("customer", ""), e.get("kind", ""), e.get("text", "") or e.get("file", ""),
               "sent" if e.get("ok") else "REFUSED", e.get("http_status", ""), e.get("myoperator_reply", ""),
               e.get("request_id", "") or "(none in the answer)", e.get("ms", ""), e.get("endpoint", ""),
               e.get("request_json", ""), json.dumps(e.get("response_headers") or {})))


def smtp_send(to_list, subject, body, cc_list=(), attach_csv=None, attach_name="whatsapp_send_log.csv"):
    """Send from the clinic Gmail (the watchdog's own SMTP settings in /root/wa/.env). Returns (ok, why)."""
    import smtplib
    from email.message import EmailMessage
    env = read_env()
    host = env.get("WATCHDOG_SMTP_HOST", "smtp.gmail.com")
    port = int(env.get("WATCHDOG_SMTP_PORT", "587") or 587)
    user = env.get("WATCHDOG_SMTP_USER", "")
    pw = env.get("WATCHDOG_SMTP_PASS", "")
    if not user or not pw:
        return False, "the clinic mail settings are not on the server"
    m = EmailMessage()
    m["From"] = user
    m["To"] = ", ".join([t for t in to_list if t] or [user])
    if cc_list:
        m["Cc"] = ", ".join(cc_list)
    m["Subject"] = subject
    m.set_content(body)
    if attach_csv is not None:
        m.add_attachment(attach_csv.encode("utf-8"), maintype="text", subtype="csv", filename=attach_name)
    try:
        cls = SMTP_CLASS or smtplib.SMTP
        s = cls(host, port, timeout=30)
        try:
            s.starttls()
            s.login(user, pw)
            s.send_message(m)
        finally:
            try:
                s.quit()
            except Exception:                                           # noqa: BLE001
                pass
        return True, user
    except Exception as ex:                                             # noqa: BLE001
        return False, "the mail did not go (%s)" % type(ex).__name__


def _note_refused(entry):
    """A refused send is mailed to the clinic Gmail itself, at most one mail every two minutes (batched), so the
    record is in the mailbox, ready to forward, without anyone opening the server."""
    with _NOTE_LOCK:
        _NOTE["pending"].append(entry)
        if _NOTE["busy"]:
            return
        _NOTE["busy"] = True
    threading.Thread(target=_note_worker, daemon=True).start()


def _note_worker():
    try:
        while True:
            with _NOTE_LOCK:
                wait = _NOTE["last"] + NOTE_GAP_S - time.time()
            if wait > 0:
                time.sleep(min(wait, NOTE_GAP_S))
                continue
            with _NOTE_LOCK:
                batch, _NOTE["pending"] = _NOTE["pending"], []
                if not batch:
                    _NOTE["busy"] = False
                    return
                _NOTE["last"] = time.time()
            env = read_env()
            first = batch[0]
            subj = "[WA send refused] %s · ••••%s · HTTP %s%s" % (
                str(first.get("ts", ""))[:16].replace("T", " "), str(first.get("customer", ""))[-4:],
                first.get("http_status", "") or "no answer", (" (+%d more)" % (len(batch) - 1)) if len(batch) > 1 else "")
            body = ("MyOperator refused %d WhatsApp message(s) sent from the clinic inbox.\n"
                    "This is the server's own record, for MyOperator's team if they ask (ticket %s).\n"
                    "The full log: https://followup.dr-manoj.in/portal/inbox/sendlog\n\n" % (len(batch), MYOP_TICKET_DEFAULT)
                    + "\n".join(entry_text(e) for e in batch))
            smtp_send([env.get("WATCHDOG_SMTP_USER", "")], subj, body)
    except Exception:                                                   # noqa: BLE001
        with _NOTE_LOCK:
            _NOTE["busy"] = False


def safe_name(name, fallback):
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", os.path.basename(str(name or "")))[:60].strip("._")
    return base or fallback


# --------------------------------------------------------------------------- routes
def register(app, guard, get_user, cfg_get, base_url=None):
    from flask import request, jsonify, Response, abort, send_file

    public_base = (base_url or cfg_get("INBOX_PUBLIC_BASE", "") or "https://followup.dr-manoj.in").rstrip("/")
    link_hours = float(cfg_get("INBOX_LINK_HOURS", "") or 6)
    call_agent = str(cfg_get("INBOX_CALL_AGENT", "") or "10")

    def xhr_ok():
        return request.headers.get("X-Inbox") == "1"

    def fail(msg, code=400):
        return jsonify({"ok": False, "error": msg}), code

    def out_row(c, phone, kind, body, mid, status, local_path="", mime="", fname="", src="inbox"):
        c.execute("INSERT OR IGNORE INTO msgs(mid,phone,dir,ts,mtype,body,local_path,mime,fname,status,sent_by,src) "
                  "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                  (mid or ("local-" + uuid.uuid4().hex), phone, "out", iso(now_ist()), kind, body, local_path, mime,
                   fname, status, (get_user() or "doctor"), src))
        if mid:
            _apply_pending(c, mid)

    @app.route("/portal/inbox/health")
    def inbox_health():                                                 # the installer's proof the module is in; carries nothing
        return jsonify({"inbox": "ok", "kit": "S608"})

    # ---- S608: the send log -- the owner's page, its CSV, and the mail to MyOperator ----------------------------
    def _log_args():
        try:
            days = int(request.args.get("days") or (request.get_json(silent=True) or {}).get("days") or 7)
        except (TypeError, ValueError):
            days = 7
        only = str(request.args.get("only") or (request.get_json(silent=True) or {}).get("only") or "") == "refused"
        return max(1, min(days, 365)), only

    @app.route("/portal/inbox/sendlog")
    @guard
    def inbox_sendlog_page():
        return Response(LOG_PAGE, mimetype="text/html; charset=utf-8")

    @app.route("/portal/inbox/api/sendlog")
    @guard
    def inbox_sendlog_api():
        days, only = _log_args()
        rows = read_log(days, only)
        allr = read_log(days, False)
        pats = {}
        try:
            pats = patients()
        except Exception:                                               # noqa: BLE001
            pass
        for e in rows:
            e["name"] = (pats.get(e.get("customer", ""), ("", ""))[0] or "")
        sends = [e for e in allr if e.get("kind") != "log-mail"]
        return jsonify({"ok": True, "rows": rows, "total": len(sends), "refused": sum(1 for e in sends if not e.get("ok")),
                        "ticket": cfg_get("INBOX_MYOP_TICKET", "") or MYOP_TICKET_DEFAULT,
                        "mail_to": cfg_get("INBOX_MYOP_MAIL_TO", "") or MYOP_MAIL_TO_DEFAULT})

    @app.route("/portal/inbox/sendlog.csv")
    @guard
    def inbox_sendlog_csv():
        days, only = _log_args()
        name = "whatsapp_send_log_%s_%dd%s.csv" % (now_ist().strftime("%Y%m%d"), days, "_refused" if only else "")
        return Response(log_csv(read_log(days, only, limit=100000)), mimetype="text/csv; charset=utf-8",
                        headers={"Content-Disposition": "attachment; filename=%s" % name})

    @app.route("/portal/inbox/api/sendlog/email", methods=["POST"])
    @guard
    def inbox_sendlog_email():
        if not xhr_ok():
            abort(403)
        b = request.get_json(silent=True) or {}
        days, only = _log_args()
        rows = [e for e in read_log(days, only, limit=100000) if e.get("kind") != "log-mail"]
        if not rows:
            return fail("nothing in the log for that choice")
        ticket = cfg_get("INBOX_MYOP_TICKET", "") or MYOP_TICKET_DEFAULT
        to = [t.strip() for t in (cfg_get("INBOX_MYOP_MAIL_TO", "") or MYOP_MAIL_TO_DEFAULT).split(",") if t.strip()]
        cc = [t.strip() for t in (cfg_get("INBOX_MYOP_MAIL_CC", "") or "").split(",") if t.strip()]
        note = str(b.get("note") or "").strip()[:2000]
        refused = [e for e in rows if not e.get("ok")]
        body = ("Hi MyOperator team,\n\n"
                + ((note + "\n\n") if note else "")
                + "Attached is our server's log of WhatsApp sends through your public API for the last %d day(s)%s: "
                  "%d attempt(s), %d refused.\n"
                  "Company ID %s · phone_number_id %s · endpoint %s.\n"
                  "Each row has the time (IST), the customer, what we sent (the key is never logged), your HTTP "
                  "status, your full reply and the x-amzn-requestid header from your answer.\n\n"
                  % (days, " (refused only)" if only else "", len(rows), len(refused), COMPANY_ID, PHONE_NUMBER_ID, API_URL)
                + ("The refused ones:\n\n" + "\n".join(entry_text(e) for e in refused[:50]) if refused else "")
                + "\nRegards,\nDr Manoj Agarwal Clinic, Bareilly\n")
        subj = "Re:[## %s ##] WhatsApp send log from our server -- %s" % (ticket, now_ist().strftime("%d-%b-%Y %H:%M IST"))
        ok, why = smtp_send(to, subj, body, cc_list=cc, attach_csv=log_csv(rows),
                            attach_name="whatsapp_send_log_%s.csv" % now_ist().strftime("%Y%m%d_%H%M"))
        log_send({"by": get_user() or "doctor", "customer": "", "kind": "log-mail", "text": "%d rows to %s" % (len(rows), ", ".join(to)),
                  "route": "sendlog-email", "ok": ok, "message_id": "", "error": "" if ok else why, "http_status": "",
                  "myoperator_reply": "", "request_id": "", "response_headers": {}, "ms": "", "endpoint": "smtp",
                  "request_json": ""})
        if not ok:
            return fail(why, 502)
        return jsonify({"ok": True, "to": to, "rows": len(rows)})

    @app.route("/portal/inbox")
    @guard
    def inbox_page():
        return Response(PAGE, mimetype="text/html; charset=utf-8")

    @app.route("/portal/inbox/lame.min.js")
    @guard
    def inbox_lame():
        try:
            return send_file(LAME_JS, mimetype="application/javascript", max_age=86400)
        except Exception:                                               # noqa: BLE001
            return Response("/* lame.min.js missing */", mimetype="application/javascript", status=404)

    @app.route("/portal/inbox/api/chats")
    @guard
    def inbox_chats():
        try:
            ingest()
            sheet_sync()
            q = (request.args.get("q") or "").strip().lower()
            pats = patients()
            c = db()
            try:
                rows = [c.execute("SELECT * FROM msgs WHERE phone=? ORDER BY ts DESC, rid DESC LIMIT 1", (p[0],)).fetchone()
                        for p in c.execute("SELECT phone, MAX(ts) AS mt FROM msgs GROUP BY phone ORDER BY mt DESC LIMIT 400")]
                reads = {r["phone"]: r["ts"] for r in c.execute("SELECT phone, ts FROM reads")}
                out = []
                for r in rows:
                    ph = r["phone"]
                    name, cid = pats.get(ph, ("", ""))
                    if q:
                        qd = re.sub(r"\D", "", q)
                        if not (q in name.lower() or q == cid.lower() or (len(qd) >= 3 and (qd in ph or qd == cid))):
                            continue
                    unread = c.execute("SELECT COUNT(*) FROM msgs WHERE phone=? AND dir='in' AND ts>?",
                                       (ph, reads.get(ph, ""))).fetchone()[0]
                    w = window(c, ph)
                    out.append({"phone": ph, "name": name, "clinic_id": cid, "ts": r["ts"], "last": preview(r),
                                "last_dir": r["dir"], "last_by": r["sent_by"] or "", "unread": unread, "open": w["open"]})
                    if len(out) >= 200:
                        break
            finally:
                c.close()
            return jsonify({"ok": True, "chats": out})
        except Exception as e:                                          # noqa: BLE001
            return fail("the chat list could not be read (%s)" % type(e).__name__, 500)

    @app.route("/portal/inbox/api/resolve")
    @guard
    def inbox_resolve():
        mid = (request.args.get("m") or "").strip()
        try:
            ingest(force=True)
            c = db()
            try:
                r = c.execute("SELECT phone FROM msgs WHERE mid=?", (mid,)).fetchone()
            finally:
                c.close()
            return jsonify({"ok": bool(r), "phone": r["phone"] if r else ""})
        except Exception as e:                                          # noqa: BLE001
            return fail("not found (%s)" % type(e).__name__, 404)

    @app.route("/portal/inbox/api/chat")
    @guard
    def inbox_chat():
        ph = last10(request.args.get("phone"))
        if not ph:
            return fail("no such chat")
        try:
            ingest()
            name, cid = patients().get(ph, ("", ""))
            c = db()
            try:
                rows = c.execute("SELECT * FROM (SELECT * FROM msgs WHERE phone=? ORDER BY ts DESC, rid DESC LIMIT 300) "
                                 "ORDER BY ts, rid", (ph,)).fetchall()
                w = window(c, ph)
            finally:
                c.close()
            try:
                import portal_wa
                tpls = portal_wa.registry_public()
                dry = (cfg_get("PORTAL_WA_DRYRUN", "1") or "1") != "0"
            except Exception:                                           # noqa: BLE001
                tpls, dry = [], True
            return jsonify({"ok": True, "me": (get_user() or ""), "phone": ph, "name": name, "clinic_id": cid, "window": w,
                            "msgs": [row_out(r) for r in rows], "templates": tpls, "templates_test_mode": dry})
        except Exception as e:                                          # noqa: BLE001
            return fail("the chat could not be read (%s)" % type(e).__name__, 500)

    @app.route("/portal/inbox/api/read", methods=["POST"])
    @guard
    def inbox_read():
        if not xhr_ok():
            abort(403)
        ph = last10((request.get_json(silent=True) or {}).get("phone"))
        if not ph:
            return fail("no such chat")
        c = db()
        try:
            c.execute("INSERT OR REPLACE INTO reads(phone, ts) VALUES(?,?)", (ph, iso(now_ist())))
            c.commit()
        finally:
            c.close()
        return jsonify({"ok": True})

    @app.route("/portal/inbox/media/<int:rid>")
    @guard
    def inbox_media(rid):
        c = db()
        try:
            r = c.execute("SELECT * FROM msgs WHERE rid=?", (rid,)).fetchone()
            if not r:
                abort(404)
            path = r["local_path"] or ""
            mime = r["mime"] or ""
            if not (path and os.path.exists(path)):
                url = r["media_url"] or ""
                u = urlparse(url)
                if u.scheme != "https" or not any((u.hostname or "").endswith(h) for h in MEDIA_HOSTS):
                    abort(404)
                os.makedirs(MEDIA_DIR, mode=0o700, exist_ok=True)
                req = urllib.request.Request(url, headers={"User-Agent": "clinic-inbox"})
                with urllib.request.urlopen(req, timeout=25) as resp:
                    data = resp.read(30 * 1024 * 1024 + 1)
                    ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip()
                if len(data) > 30 * 1024 * 1024:
                    abort(413)
                mime = mime or ctype or mimetypes.guess_type(u.path)[0] or "application/octet-stream"
                ext = mimetypes.guess_extension(mime) or ""
                path = os.path.join(MEDIA_DIR, hashlib.sha1((r["mid"] or str(rid)).encode()).hexdigest() + ext)
                old = os.umask(0o077)
                try:
                    with open(path, "wb") as fh:
                        fh.write(data)
                finally:
                    os.umask(old)
                c.execute("UPDATE msgs SET local_path=?, mime=? WHERE rid=?", (path, mime, rid))
                c.commit()
        except urllib.error.URLError:
            abort(502)
        finally:
            c.close()
        name = r["fname"] or os.path.basename(urlparse(r["media_url"] or "").path) or os.path.basename(path)
        dl = request.args.get("dl") == "1"
        return send_file(path, mimetype=mime or "application/octet-stream", as_attachment=dl,
                         download_name=safe_name(name, "file"), max_age=3600)

    @app.route("/portal/inbox/f/<token>/<name>")
    def inbox_public_file(token, name):                                 # MyOperator fetches this: no login, a token
        if not re.match(r"^[0-9a-f]{32}$", token or ""):
            abort(404)
        c = db()
        try:
            r = c.execute("SELECT * FROM links WHERE token=?", (token,)).fetchone()
        finally:
            c.close()
        if not r or r["name"] != name or (parse_ts(r["expires"]) or now_ist()) < now_ist() or not os.path.exists(r["path"]):
            abort(404)
        return send_file(r["path"], mimetype=r["mime"] or "application/octet-stream", max_age=0)

    @app.route("/portal/inbox/api/send", methods=["POST"])
    @guard
    def inbox_send():
        if not xhr_ok():
            abort(403)
        f = request.files.get("file")
        form = request.form if (request.form or f) else (request.get_json(silent=True) or {})
        ph = last10(form.get("phone"))
        kind = (form.get("kind") or "text").strip().lower()
        text = (form.get("text") or "").strip()
        if not ph:
            return fail("no number for this chat")
        if kind not in ("text", "image", "document", "audio"):
            return fail("unknown message kind")
        token = _token(cfg_get)
        if not token:
            return fail("the WhatsApp send key is not set on the server", 500)
        ingest(force=True)
        c = db()
        try:
            w = window(c, ph)
            if not w["open"]:
                return fail("More than 24 hours since this patient last wrote. WhatsApp allows only an approved template now.")
            if kind == "text":
                if not text:
                    return fail("type a message first")
                tr = {}
                ok, mid, err = myop_send(token, ph, {"type": "text", "context": {"body": text[:4000], "preview_url": False}},
                                         trace=tr)
                log_send(attempt_entry(get_user(), ph, "text", text[:4000], tr, ok, mid, err))
                if not ok:
                    return fail(err, 502)
                out_row(c, ph, "text", text[:4000], mid, "sent")
                c.commit()
                return jsonify({"ok": True})
            if not f:
                return fail("no file came with the message")
            mimes, cap = SEND_RULES[kind]
            mime = (f.mimetype or "").split(";")[0].strip().lower()
            if mime not in mimes:
                return fail("this file type cannot be sent as %s (%s)" % (kind, mime or "unknown"))
            data = f.read(cap + 1)
            if len(data) > cap:
                return fail("the file is too large (limit %d MB)" % (cap // (1024 * 1024)))
            if not data:
                return fail("the file is empty")
            ext = {"image/jpeg": ".jpg", "image/png": ".png", "application/pdf": ".pdf", "audio/mpeg": ".mp3"}[mime]
            fname = safe_name(f.filename, "file")
            if not fname.lower().endswith(ext):
                fname = (fname.rsplit(".", 1)[0] if "." in fname else fname) + ext
            if kind == "audio":
                fname = "voice-note-%s.mp3" % now_ist().strftime("%Y%m%d-%H%M%S")
            os.makedirs(OUT_DIR, mode=0o700, exist_ok=True)
            tok = secrets.token_hex(16)
            path = os.path.join(OUT_DIR, tok + "-" + fname)
            old = os.umask(0o077)
            try:
                with open(path, "wb") as fh:
                    fh.write(data)
            finally:
                os.umask(old)
            exp = now_ist() + datetime.timedelta(hours=link_hours)
            c.execute("INSERT INTO links(token,path,name,mime,expires) VALUES(?,?,?,?,?)", (tok, path, fname, mime, iso(exp)))
            c.commit()
            link = "%s/portal/inbox/f/%s/%s" % (public_base, tok, fname)
            ctx = {"link": link, "filename": fname, "mime_type": mime}
            if text and kind != "audio":
                ctx["caption"] = text[:1000]
            tr = {}
            ok, mid, err = myop_send(token, ph, {"type": kind, "context": ctx}, trace=tr)
            log_send(attempt_entry(get_user(), ph, kind, text if kind != "audio" else "", tr, ok, mid, err,
                                   fname=fname, mime=mime))
            if not ok:
                return fail(err, 502)
            out_row(c, ph, kind, text if kind != "audio" else "", mid, "sent", local_path=path, mime=mime, fname=fname)
            c.commit()
            return jsonify({"ok": True})
        except Exception as e:                                          # noqa: BLE001
            return fail("not sent (%s)" % type(e).__name__, 500)
        finally:
            c.close()

    @app.route("/portal/inbox/api/template", methods=["POST"])
    @guard
    def inbox_template():
        if not xhr_ok():
            abort(403)
        b = request.get_json(silent=True) or {}
        ph = last10(b.get("phone"))
        if not ph:
            return fail("no number for this chat")
        try:
            import portal_wa
            dry = (cfg_get("PORTAL_WA_DRYRUN", "1") or "1") != "0"
            tok = _token(cfg_get)
            r = portal_wa.send(ph, b.get("template", ""), b.get("values") or {}, (get_user() or "doctor"), tok, dry_run=dry)
        except Exception as e:                                          # noqa: BLE001
            return fail("the template sender could not run (%s)" % type(e).__name__, 500)
        if r.get("mode") != "DRY":
            log_send({"by": get_user() or "doctor", "customer": ph, "kind": "template", "text": b.get("template", ""),
                      "route": "inbox-template", "ok": bool(r.get("ok")), "message_id": r.get("message_id", ""),
                      "error": r.get("error", ""), "http_status": r.get("http_status", r.get("status", "")),
                      "myoperator_reply": str(r.get("raw") or r.get("response") or "")[:4000], "request_id": "",
                      "response_headers": {}, "ms": "", "endpoint": "portal_wa.send", "request_json": ""})
        if not r.get("ok"):
            return fail(r.get("error") or "not sent", 502)
        title = b.get("template", "")
        try:
            t = portal_wa.TEMPLATES.get(b.get("template", "")) or {}
            title = t.get("title") or title
        except Exception:                                               # noqa: BLE001
            pass
        c = db()
        try:
            out_row(c, ph, "template", ("[TEST MODE — not sent] " if r.get("mode") == "DRY" else "") + "Template: " + title,
                    "" if r.get("mode") == "DRY" else r.get("message_id", ""), "pending" if r.get("mode") == "DRY" else "sent")
            c.commit()
        finally:
            c.close()
        return jsonify({"ok": True, "mode": r.get("mode")})

    @app.route("/portal/inbox/api/call", methods=["POST"])
    @guard
    def inbox_call():
        if not xhr_ok():
            abort(403)
        ph = last10((request.get_json(silent=True) or {}).get("phone"))
        if not ph:
            return fail("no number for this chat")
        key = read_env().get("CALL_API_SECRET", "")
        if not key:
            return fail("calling is not set up on the server", 500)
        body = json.dumps({"agent": call_agent, "patient_number": ph, "reference_id": "inbox"}).encode()
        req = urllib.request.Request(CALL_URL, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("X-Call-Key", key)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                j = json.loads(resp.read().decode("utf-8", "replace") or "{}")
        except Exception as e:                                          # noqa: BLE001
            return fail("the call service did not answer (%s)" % type(e).__name__, 502)
        if not j.get("ok"):
            return fail(str(j.get("reason") or "the call was not placed")[:200], 502)
        return jsonify({"ok": True})

    @app.route("/portal/inbox/api/replies", methods=["GET", "POST"])
    @guard
    def inbox_replies():
        c = db()
        try:
            if request.method == "POST":
                if not xhr_ok():
                    abort(403)
                b = request.get_json(silent=True) or {}
                if b.get("delete") and b.get("id"):
                    c.execute("DELETE FROM replies WHERE id=?", (int(b["id"]),))
                else:
                    title = (b.get("title") or "").strip()[:60]
                    body = (b.get("body") or "").strip()[:2000]
                    if not title or not body:
                        return fail("a saved reply needs a short name and its text")
                    if b.get("id"):
                        c.execute("UPDATE replies SET title=?, body=? WHERE id=?", (title, body, int(b["id"])))
                    else:
                        c.execute("INSERT INTO replies(title, body, sort) VALUES(?,?,?)", (title, body, int(time.time())))
                c.commit()
            rows = c.execute("SELECT id, title, body FROM replies ORDER BY sort, id").fetchall()
            return jsonify({"ok": True, "replies": [dict(r) for r in rows]})
        finally:
            c.close()

    return True


# --------------------------------------------------------------------------- the page (one file; no outside script)
LOG_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WhatsApp send log</title>
<style>
:root{--ink:#16211D;--muted:#5B6B66;--line:#DDE2DE;--bg:#ECEEE9;--card:#fff;--head:#0F4F45;--acc:#0F6B5C;--bad:#9B2C1F;--badbg:#FCEDEA}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
header{background:var(--head);color:#fff;padding:14px 16px}header h1{margin:0;font-size:19px}header .sub{font-size:13px;color:#CFE5DF}
header a{color:#CFE5DF}.wrap{max-width:1000px;margin:0 auto;padding:12px 16px 60px}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:8px 0}
select,button,textarea{font:inherit}select{padding:8px;border-radius:8px;border:1px solid #bbb;background:#fff}
.btn{padding:9px 14px;border-radius:9px;border:1px solid #bbb;background:#fff;cursor:pointer;color:var(--ink);text-decoration:none;display:inline-block}
.btn.p{background:var(--acc);border-color:var(--acc);color:#fff}
.sum{font-size:14px;color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:8px 0}
.card.bad{border-color:#E8B4AC;background:var(--badbg)}
.r1{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}.r1 b{font-size:15px}
.k{color:var(--muted);font-size:13px}.ok{color:var(--acc);font-weight:600}.no{color:var(--bad);font-weight:600}
pre{white-space:pre-wrap;word-break:break-word;background:#F6F7F5;border-radius:6px;padding:6px 8px;font-size:12px;margin:6px 0 0}
details summary{cursor:pointer;color:var(--muted);font-size:13px;margin-top:4px}
#mailbox{display:none}textarea{width:100%;min-height:70px;border:1px solid #bbb;border-radius:8px;padding:8px}
#toast{position:fixed;left:0;right:0;bottom:0;background:#16211D;color:#fff;padding:12px 16px;display:none;white-space:pre-wrap}
</style></head><body>
<header><h1>WhatsApp send log</h1><div class="sub">Every message the inbox sent, and what MyOperator answered · <a href="/portal/inbox">back to the inbox</a></div></header>
<div class="wrap">
 <div class="bar">
  <select id="days"><option value="1">Today and yesterday</option><option value="7" selected>Last 7 days</option><option value="30">Last 30 days</option><option value="365">Last year</option></select>
  <select id="only"><option value="">All sends</option><option value="refused">Refused only</option></select>
  <a class="btn" id="csv" href="#">Download CSV</a>
  <button class="btn p" onclick="mailOpen()">Email to MyOperator</button>
 </div>
 <div class="sum" id="sum">Loading…</div>
 <div class="card" id="mailbox">
  <div><b>Email this log to MyOperator</b> <span class="k" id="mailto"></span></div>
  <div class="k">Goes from the clinic Gmail on ticket <span id="tk"></span>, with the log attached as a spreadsheet (CSV). Add a line if you like:</div>
  <textarea id="note" placeholder="e.g. Please check the refused messages to this customer."></textarea>
  <div class="bar"><button class="btn p" onclick="mailSend()">Send now</button><button class="btn" onclick="mailClose()">Cancel</button></div>
 </div>
 <div id="rows"></div>
</div>
<div id="toast"></div>
<script>
var $=function(i){return document.getElementById(i)};
function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})}
function toast(t){var m=$("toast");m.textContent=t;m.style.display="block";clearTimeout(toast.t);toast.t=setTimeout(function(){m.style.display="none"},5000)}
function q(){return "days="+$("days").value+"&only="+$("only").value}
function fmt(ts){ts=String(ts||"");return ts.slice(8,10)+"-"+ts.slice(5,7)+"-"+ts.slice(0,4)+" "+ts.slice(11,16)}
function load(){
 $("csv").href="/portal/inbox/sendlog.csv?"+q();
 fetch("/portal/inbox/api/sendlog?"+q(),{headers:{"X-Inbox":"1"}}).then(function(r){return r.json()}).then(function(j){
  if(!j.ok){$("sum").textContent=j.error||"could not read the log";return}
  $("tk").textContent=j.ticket;$("mailto").textContent="· to "+j.mail_to;
  $("sum").textContent=j.total+" send(s) in this period · "+j.refused+" refused by MyOperator";
  var h="";
  j.rows.forEach(function(e){
   var who=(e.name?e.name+" · ":"")+(e.customer?"+91 "+e.customer:"");
   h+='<div class="card'+(e.ok?'':' bad')+'"><div class="r1"><b>'+esc(fmt(e.ts))+' · '+esc(who||e.kind)+'</b>'+
    (e.ok?'<span class="ok">✓ sent</span>':'<span class="no">✗ refused · HTTP '+esc(e.http_status||"no answer")+'</span>')+'</div>'+
    '<div class="k">'+esc(e.kind)+' · by '+esc(e.by)+(e.ms!==""?' · '+esc(e.ms)+' ms':'')+(e.request_id?' · request id '+esc(e.request_id):'')+'</div>'+
    (e.text||e.file?'<div>'+esc(e.text||e.file)+'</div>':'')+
    (e.ok?'':'<div class="no" style="font-weight:400">'+esc(e.error)+'</div>')+
    '<details><summary>Technical details for MyOperator</summary><pre>Their reply: '+esc(e.myoperator_reply)+'\nRequest (key not shown): '+esc(e.request_json)+'\nResponse headers: '+esc(JSON.stringify(e.response_headers||{}))+'</pre></details></div>';
  });
  $("rows").innerHTML=h||'<div class="card">Nothing logged in this period yet. Every send from now on is recorded here.</div>';
 }).catch(function(){$("sum").textContent="could not read the log"});
}
function mailOpen(){$("mailbox").style.display="block";$("note").focus()}
function mailClose(){$("mailbox").style.display="none"}
function mailSend(){
 fetch("/portal/inbox/api/sendlog/email?"+q(),{method:"POST",headers:{"X-Inbox":"1","Content-Type":"application/json"},
  body:JSON.stringify({days:$("days").value,only:$("only").value,note:$("note").value})})
 .then(function(r){return r.json()}).then(function(j){ if(j.ok){toast("Sent to "+j.to.join(", ")+" ("+j.rows+" rows).");mailClose();$("note").value=""}else toast(j.error||"not sent")})
 .catch(function(){toast("not sent")});
}
$("days").onchange=load;$("only").onchange=load;load();
</script></body></html>"""


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>WhatsApp Inbox</title>
<style>
:root{--ink:#16211D;--muted:#5B6B66;--line:#DDE2DE;--bg:#ECEEE9;--card:#FFFFFF;--head:#0F4F45;--acc:#0F6B5C;--out:#D7ECE5;--warn:#FFF6E0;--warnink:#5A4300}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:var(--bg);color:var(--ink);font-family:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif}
button,input,textarea,select{font:inherit}
.app{display:flex;height:100vh;height:100dvh;max-width:1200px;margin:0 auto;background:var(--card)}
.list{width:380px;border-right:1px solid var(--line);display:flex;flex-direction:column;min-width:0;min-height:0}
.chat{flex:1;display:flex;flex-direction:column;min-width:0;min-height:0;overflow:hidden;background:var(--bg)}
@media (max-width:820px){.list{width:100%;border-right:0}.chat{display:none}.app.open .list{display:none}.app.open .chat{display:flex}}
@media (min-width:821px){.back{display:none!important}}
.lhead{background:var(--head);color:#fff;padding:14px 14px 12px;display:flex;flex-direction:column;gap:10px}
.lhead .t{display:flex;justify-content:space-between;align-items:center}
.lhead h1{font-size:19px;margin:0}
.lhead .sub{font-size:12px;color:#CFE5DF}
.lhead a{color:#CFE5DF;font-size:13px}
.search{display:flex;align-items:center;gap:8px;background:#fff;border-radius:10px;padding:0 12px;height:44px}
.search input{border:0;outline:0;flex:1;font-size:15px;background:transparent;color:var(--ink)}
.rows{flex:1;overflow:auto;min-height:0}
.row{display:flex;gap:12px;padding:12px 14px;border:0;border-bottom:1px solid #E2E6E2;background:#fff;width:100%;text-align:left;cursor:pointer;color:var(--ink)}
.row:hover,.row.sel{background:#F3F8F6}
.av{width:44px;height:44px;border-radius:22px;background:#DCEBE6;color:var(--head);display:flex;align-items:center;justify-content:center;font-weight:600;flex-shrink:0}
.rb{flex:1;min-width:0;display:flex;flex-direction:column;gap:3px}
.r1,.r2{display:flex;justify-content:space-between;gap:8px;align-items:center}
.nm{font-weight:600;font-size:15px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tm{font-size:12px;color:var(--muted);flex-shrink:0}
.tm.new{color:var(--acc);font-weight:600}
.pv{font-size:14px;color:#3E4C47;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.badge{background:var(--acc);color:#fff;font-size:12px;font-weight:600;border-radius:10px;min-width:20px;height:20px;padding:0 6px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.tag{font-size:11px;color:#8A5A00;font-weight:600;flex-shrink:0}
.empty{padding:30px 16px;color:var(--muted);text-align:center}
.chead{background:var(--head);color:#fff;padding:10px 12px;display:flex;align-items:center;gap:10px}
.chead .who{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}
.chead .n{font-size:17px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.chead .num{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.chead .w{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
@media (max-width:440px){.callbtn .lbl{display:none}.callbtn{padding:0 12px}}
.chead .w{font-size:12px;color:#CFE5DF}
.chead .w.closed{color:#FFD98A}
.iconbtn{width:44px;height:44px;border-radius:22px;border:0;background:transparent;display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0}
.callbtn{height:44px;border:0;border-radius:22px;background:#fff;color:var(--head);font-weight:600;font-size:15px;padding:0 16px;display:flex;align-items:center;gap:8px;cursor:pointer;flex-shrink:0}
.note{background:var(--warn);color:var(--warnink);font-size:12px;padding:8px 14px;border-bottom:1px solid #F0E2B8}
.msgs{flex:1;overflow:auto;min-height:0;padding:14px 12px;display:flex;flex-direction:column;gap:8px}
.day{align-self:center;font-size:12px;color:var(--muted);background:#fff;border-radius:8px;padding:3px 10px;margin:4px 0}
.b{max-width:78%;border-radius:4px 14px 14px 14px;background:#fff;padding:8px 10px;display:flex;flex-direction:column;gap:6px;align-self:flex-start;word-wrap:break-word;overflow-wrap:anywhere}
.b.o{align-self:flex-end;background:var(--out);border-radius:14px 4px 14px 14px}
.b .tx{font-size:15px;white-space:pre-wrap}
.b .mt{font-size:11px;color:var(--muted);align-self:flex-end}
.b img{max-width:260px;width:100%;border-radius:10px;cursor:zoom-in;display:block;background:#2B3431;min-height:60px}
.b video{max-width:260px;width:100%;border-radius:10px}
.b audio{width:240px;max-width:100%}
.doc{display:flex;align-items:center;gap:10px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:10px;color:var(--ink);text-decoration:none}
.comp{background:#fff;border-top:1px solid var(--line);padding:10px 12px 12px;display:flex;flex-direction:column;gap:8px;max-height:58%;overflow:auto;flex-shrink:0}
.chips{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.chip{min-height:36px;border:1px solid #B9CFC8;background:#F3F8F6;color:var(--head);border-radius:18px;font-size:13px;padding:0 12px;cursor:pointer}
.lnk{font-size:13px;color:var(--acc);background:none;border:0;cursor:pointer;padding:6px}
.bar{display:flex;align-items:flex-end;gap:8px}
.cb{width:44px;height:44px;border-radius:22px;border:1px solid var(--line);background:#fff;display:flex;align-items:center;justify-content:center;flex-shrink:0;cursor:pointer}
.cb.rec{background:#B3261E;border-color:#B3261E}
.send{width:44px;height:44px;border-radius:22px;border:0;background:var(--acc);display:flex;align-items:center;justify-content:center;flex-shrink:0;cursor:pointer}
.send:disabled{opacity:.5}
textarea.in{flex:1;min-width:0;border:0;outline:0;background:#F3F5F2;border-radius:22px;min-height:44px;max-height:120px;padding:11px 14px;font-size:15px;resize:none;color:var(--ink)}
.pending{display:flex;align-items:center;gap:8px;background:#F3F8F6;border:1px solid #B9CFC8;border-radius:12px;padding:8px 10px;font-size:13px}
.pending .x{margin-left:auto}
.tpl{display:flex;flex-direction:column;gap:8px}
.tpl label.t{display:flex;gap:10px;align-items:flex-start;border:1px solid var(--line);border-radius:12px;padding:10px 12px;cursor:pointer}
.tpl label.t.on{border:2px solid var(--acc);background:#F3F8F6}
.tpl .pvw{font-size:13px;color:#3E4C47;white-space:pre-wrap}
.tpl .f{display:flex;flex-direction:column;gap:4px;font-size:13px}
.tpl .f input{border:1px solid var(--line);border-radius:8px;height:40px;padding:0 10px}
.big{height:48px;min-height:48px;flex-shrink:0;border:0;border-radius:24px;background:var(--acc);color:#fff;font-weight:600;font-size:16px;cursor:pointer}
.big:disabled{background:#C9D6D2;color:#3E4C47;cursor:default}
.toast{position:fixed;left:50%;top:88px;transform:translateX(-50%);background:#16211D;color:#fff;padding:10px 16px;border-radius:10px;font-size:14px;max-width:90vw;z-index:9;display:none}
.ov{position:fixed;inset:0;background:rgba(0,0,0,.85);display:none;align-items:center;justify-content:center;z-index:8}
.ov img{max-width:96vw;max-height:92vh}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.4);display:none;align-items:center;justify-content:center;z-index:8;padding:16px}
.mbox{background:#fff;border-radius:14px;padding:16px;width:100%;max-width:440px;display:flex;flex-direction:column;gap:10px;max-height:90vh;overflow:auto}
.mbox input,.mbox textarea{border:1px solid var(--line);border-radius:8px;padding:8px 10px;font-size:15px;width:100%}
.mbox .r{display:flex;justify-content:space-between;gap:8px;align-items:flex-start;border-bottom:1px solid #EEF0EE;padding:6px 0}
.mrow{display:flex;gap:8px;justify-content:flex-end}
.ghost{height:40px;border:1px solid var(--line);background:#fff;border-radius:20px;padding:0 14px;cursor:pointer}
.placeholder{flex:1;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:15px;padding:20px;text-align:center}
</style></head><body>
<div class="app" id="app">
  <section class="list" aria-label="All chats">
    <div class="lhead">
      <div class="t"><div><h1>WhatsApp Inbox</h1><div class="sub">Clinic number · only you can see this</div></div>
      <span><a href="/portal/inbox/sendlog">Send log</a> · <a href="/portal">Portal</a></span></div>
      <label class="search"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5B6B66" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"></circle><path d="M20 20l-4-4"></path></svg>
      <input id="q" type="search" placeholder="Search name, mobile or clinic ID" aria-label="Search chats"></label>
    </div>
    <div class="rows" id="rows"><div class="empty">Loading…</div></div>
  </section>
  <section class="chat" id="chat" aria-label="Chat">
    <div class="placeholder" id="ph">Choose a chat on the left.</div>
  </section>
</div>
<div class="ov" id="ov" role="dialog" aria-label="Photo"><img id="ovimg" alt="Photo, enlarged"></div>
<div class="modal" id="modal" role="dialog" aria-modal="true"><div class="mbox" id="mbox"></div></div>
<div class="toast" id="toast" role="status"></div>
<input type="file" id="fimg" accept="image/jpeg,image/png" hidden>
<input type="file" id="fpdf" accept="application/pdf" hidden>
<script>
(function(){
"use strict";
var S={phone:"",chat:null,chats:[],pending:null,rec:null,replies:[],tpl:null,timer:null,lastSig:""};
var $=function(id){return document.getElementById(id);};
function el(tag,attrs,kids){var e=document.createElement(tag);if(attrs){for(var k in attrs){if(k==="text")e.textContent=attrs[k];else if(k==="cls")e.className=attrs[k];else if(k.slice(0,2)==="on")e.addEventListener(k.slice(2),attrs[k]);else e.setAttribute(k,attrs[k]);}}(kids||[]).forEach(function(c){if(c)e.appendChild(typeof c==="string"?document.createTextNode(c):c);});return e;}
function svg(path,stroke,fill){var s=document.createElementNS("http://www.w3.org/2000/svg","svg");s.setAttribute("width","20");s.setAttribute("height","20");s.setAttribute("viewBox","0 0 24 24");s.setAttribute("fill",fill||"none");s.setAttribute("stroke",stroke||"#0F4F45");s.setAttribute("stroke-width","2");s.setAttribute("aria-hidden","true");s.innerHTML=path;return s;}
var IC={back:'<path d="M15 18l-6-6 6-6"></path>',call:'<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"></path>',img:'<rect x="3" y="5" width="18" height="14" rx="2"></rect><circle cx="9" cy="11" r="2"></circle><path d="M21 17l-5-5-8 8"></path>',pdf:'<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"></path><path d="M14 3v5h5"></path>',mic:'<rect x="9" y="3" width="6" height="11" rx="3"></rect><path d="M5 11a7 7 0 0 0 14 0"></path><path d="M12 18v3"></path>',stop:'<rect x="7" y="7" width="10" height="10" rx="1"></rect>',send:'<path d="M22 2L11 13"></path><path d="M22 2l-7 20-4-9-9-4z"></path>'};
function toast(t,ms){var e=$("toast");e.textContent=t;e.style.display="block";clearTimeout(toast.h);toast.h=setTimeout(function(){e.style.display="none";},ms||3500);}
function api(url,opt){opt=opt||{};opt.headers=opt.headers||{};opt.headers["X-Inbox"]="1";opt.credentials="same-origin";return fetch(url,opt).then(function(r){return r.json().catch(function(){return {ok:false,error:"the server answered "+r.status};});});}
function post(url,obj){return api(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(obj)});}
function fmtNum(p){return "+91 "+p.slice(0,5)+" "+p.slice(5);}
function initials(n,p){if(!n)return p.slice(-2);var w=n.trim().split(/\s+/);return ((w[0]||"")[0]||"").toUpperCase()+((w[1]||"")[0]||"").toUpperCase();}
function dt(s){var d=new Date(s);return isNaN(d)?null:d;}
function hhmm(s){var d=dt(s);if(!d)return "";return d.toLocaleTimeString("en-IN",{hour:"2-digit",minute:"2-digit",hour12:false,timeZone:"Asia/Kolkata"});}
function dayLabel(s){var d=dt(s);if(!d)return "";var k=function(x){return x.toLocaleDateString("en-IN",{timeZone:"Asia/Kolkata"});};var n=new Date();var y=new Date(Date.now()-864e5);if(k(d)===k(n))return "Today";if(k(d)===k(y))return "Yesterday";return d.toLocaleDateString("en-IN",{day:"numeric",month:"short",year:"numeric",timeZone:"Asia/Kolkata"});}
function when(s){var l=dayLabel(s);return l==="Today"?hhmm(s):l;}
function tick(st){return {sent:"Sent",delivered:"Delivered",read:"Read",failed:"NOT delivered",pending:"Test mode — not sent",received:""}[st]||"";}

function loadChats(){
  var q=$("q").value.trim();
  return api("/portal/inbox/api/chats"+(q?"?q="+encodeURIComponent(q):"")).then(function(j){
    if(!j.ok){$("rows").replaceChildren(el("div",{cls:"empty",text:j.error||"Could not load."}));return;}
    S.chats=j.chats;drawRows();
  });
}
function drawRows(){
  var box=$("rows");var kids=[];
  if(!S.chats.length){kids.push(el("div",{cls:"empty",text:$("q").value?"No chat matches.":"No WhatsApp messages yet."}));}
  S.chats.forEach(function(c){
    var title=c.name?(c.name+(c.clinic_id?" · ID "+c.clinic_id:"")):fmtNum(c.phone);
    var right=c.unread?el("span",{cls:"badge",text:String(c.unread)}):(!c.open&&c.last_dir==="in"?el("span",{cls:"tag",text:"Template only"}):null);
    var b=el("button",{cls:"row"+(c.phone===S.phone?" sel":""),type:"button",onclick:function(){openChat(c.phone);}},[
      el("div",{cls:"av",text:initials(c.name,c.phone)}),
      el("div",{cls:"rb"},[el("div",{cls:"r1"},[el("span",{cls:"nm",text:title}),el("span",{cls:"tm"+(c.unread?" new":""),text:when(c.ts)})]),
        el("div",{cls:"r2"},[el("span",{cls:"pv",text:(c.last_dir==="out"?((c.last_by&&c.last_by!=="manoj"&&c.last_by!=="doctor")?c.last_by+": ":"You: "):"")+c.last}),right])])]);
    kids.push(b);
  });
  box.replaceChildren.apply(box,kids);
}
function openChat(phone){
  S.phone=phone;S.pending=null;S.tpl=null;S.lastSig="";$("app").classList.add("open");drawRows();
  loadChat(true);post("/portal/inbox/api/read",{phone:phone}).then(function(){loadChats();});
}
function loadChat(scroll){
  if(!S.phone)return Promise.resolve();
  return api("/portal/inbox/api/chat?phone="+encodeURIComponent(S.phone)).then(function(j){
    if(!j.ok){toast(j.error||"Could not load the chat.");return;}
    var sig=JSON.stringify([j.msgs.length,j.msgs.length?j.msgs[j.msgs.length-1].rid:0,j.msgs.map(function(m){return m.status;}).join(""),j.window.open]);
    var first=!S.chat||S.chat.phone!==j.phone;S.chat=j;
    if(first){drawChat();}
    else if(sig!==S.lastSig){drawHead();drawMsgs(true);drawComposer();}
    S.lastSig=sig;
  });
}
function drawChat(){
  var c=$("chat");c.replaceChildren(el("div",{id:"chead",cls:"chead"}),el("div",{id:"note",cls:"note",text:"Call rings your mobile first, then connects the patient. The patient sees the clinic number."}),el("div",{id:"msgs",cls:"msgs"}),el("div",{id:"comp",cls:"comp"}));
  drawHead();drawMsgs(true);drawComposer();
}
function drawHead(){
  var j=S.chat,h=$("chead");if(!h)return;
  var w=j.window;var wt=w.open?("Free reply open · "+(w.hours_left>=1?Math.floor(w.hours_left)+" h left":"under 1 h left")):("Free reply closed"+(w.last_in?" · last message "+when(w.last_in):""));
  var back=el("button",{cls:"iconbtn back",type:"button","aria-label":"Back to all chats",onclick:function(){$("app").classList.remove("open");S.phone="";S.chat=null;drawRows();$("chat").replaceChildren(el("div",{cls:"placeholder",text:"Choose a chat on the left."}));}},[svg(IC.back,"#fff")]);
  h.replaceChildren(back,el("div",{cls:"who"},[el("div",{cls:"n",text:j.name||"Not in patient records"}),el("div",{cls:"num",text:fmtNum(j.phone)+(j.clinic_id?" · ID "+j.clinic_id:"")}),el("div",{cls:"w"+(w.open?"":" closed"),text:wt})]),
    el("button",{cls:"callbtn",type:"button","aria-label":"Call from the clinic number",onclick:doCall},[svg(IC.call),el("span",{cls:"lbl",text:"Call"})]));
}
function mediaNode(m){
  var src="/portal/inbox/media/"+m.rid;
  if(m.type==="image"||m.type==="sticker"){var i=el("img",{src:src,alt:m.body||"Photo",loading:"lazy"});i.addEventListener("click",function(){$("ovimg").src=src;$("ov").style.display="flex";});return i;}
  if(m.type==="audio"||m.type==="voice"){return el("audio",{src:src,controls:"",preload:"none"});}
  if(m.type==="video"){return el("video",{src:src,controls:"",preload:"none"});}
  var name=m.fname||"Document";
  return el("a",{cls:"doc",href:src,target:"_blank",rel:"noopener"},[svg(IC.pdf,"#9A2B1F"),el("div",{},[el("div",{text:name,style:"font-size:14px;font-weight:500"}),el("div",{text:"Tap to open",style:"font-size:12px;color:#5B6B66"})])]);
}
function drawMsgs(scroll){
  var box=$("msgs");if(!box)return;var atEnd=box.scrollHeight-box.scrollTop-box.clientHeight<80;var kids=[];var lastDay="";
  S.chat.msgs.forEach(function(m){
    var d=dayLabel(m.ts);if(d!==lastDay){kids.push(el("div",{cls:"day",text:d}));lastDay=d;}
    var parts=[];if(m.has_media)parts.push(mediaNode(m));
    else if(["image","document","audio","voice","video","sticker"].indexOf(m.type)>=0)parts.push(el("div",{cls:"tx",text:"("+m.type+" — the file has not arrived yet)",style:"color:#5B6B66"}));
    if(m.body)parts.push(el("div",{cls:"tx",text:m.body}));
    if(!m.has_media&&!m.body)parts.push(el("div",{cls:"tx",text:"("+m.type+")",style:"color:#5B6B66"}));
    var by=(m.dir==="out"&&m.sent_by&&m.sent_by!==S.chat.me)?" · by "+m.sent_by:"";
    var meta=hhmm(m.ts)+(m.dir==="out"&&tick(m.status)?" · "+tick(m.status):"")+by;
    parts.push(el("div",{cls:"mt",text:meta,style:m.status==="failed"?"color:#B3261E;font-weight:600":""}));
    kids.push(el("div",{cls:"b"+(m.dir==="out"?" o":"")},parts));
  });
  if(!kids.length)kids.push(el("div",{cls:"day",text:"No messages"}));
  box.replaceChildren.apply(box,kids);if(scroll||atEnd)box.scrollTop=box.scrollHeight;
}
function drawComposer(){
  var c=$("comp");if(!c)return;var j=S.chat;
  if(S.rec){return;}
  if(!j.window.open){drawTemplates(c);return;}
  var chips=el("div",{cls:"chips"});
  chips.appendChild(el("span",{text:"Saved replies",style:"font-size:13px;font-weight:600;color:#3E4C47"}));
  S.replies.forEach(function(r){chips.appendChild(el("button",{cls:"chip",type:"button",onclick:function(){var t=$("txt");t.value=r.body;t.focus();grow(t);}},[r.title]));});
  chips.appendChild(el("button",{cls:"lnk",type:"button",onclick:editReplies},[S.replies.length?"Edit list":"Add a saved reply"]));
  var kids=[chips];
  if(S.pending){kids.push(el("div",{cls:"pending"},[svg(S.pending.kind==="image"?IC.img:S.pending.kind==="audio"?IC.mic:IC.pdf),el("span",{text:S.pending.label}),S.pending.kind==="audio"?el("audio",{src:S.pending.url,controls:""}):null,el("button",{cls:"lnk x",type:"button",onclick:function(){S.pending=null;drawComposer();}},["Remove"])]));}
  var ta=el("textarea",{id:"txt",cls:"in",rows:"1",placeholder:S.pending?(S.pending.kind==="audio"?"Voice note ready — tap Send":"Add a caption (optional)"):"Type a reply","aria-label":"Reply"});
  ta.addEventListener("input",function(){grow(ta);});
  ta.addEventListener("keydown",function(e){if(e.key==="Enter"&&!e.shiftKey&&window.matchMedia("(min-width:821px)").matches){e.preventDefault();doSend();}});
  if(S.pending&&S.pending.kind==="audio")ta.disabled=true;
  var bar=el("div",{cls:"bar"},[
    el("button",{cls:"cb",type:"button","aria-label":"Send a photo",onclick:function(){$("fimg").click();}},[svg(IC.img)]),
    el("button",{cls:"cb",type:"button","aria-label":"Send a PDF",onclick:function(){$("fpdf").click();}},[svg(IC.pdf)]),
    ta,
    el("button",{cls:"cb",type:"button","aria-label":"Record a voice note",onclick:startRec},[svg(IC.mic)]),
    el("button",{id:"sendbtn",cls:"send",type:"button","aria-label":"Send",onclick:doSend},[svg(IC.send,"#fff")])]);
  kids.push(bar);c.replaceChildren.apply(c,kids);
}
function grow(t){t.style.height="auto";t.style.height=Math.min(t.scrollHeight,120)+"px";}
function drawTemplates(c){
  var j=S.chat;var kids=[el("div",{cls:"note",style:"border-radius:8px;border:0",text:"More than 24 hours since this patient wrote. WhatsApp allows only your approved messages now — or tap Call."+(j.templates_test_mode?" (Templates are in TEST MODE on this server: nothing will really be sent.)":"")})];
  var list=el("div",{cls:"tpl"});
  if(!j.templates.length)list.appendChild(el("div",{cls:"empty",text:"No approved templates are listed."}));
  j.templates.forEach(function(t){
    var on=S.tpl&&S.tpl.name===t.name;
    var lab=el("label",{cls:"t"+(on?" on":"")},[el("input",{type:"radio",name:"tpl"}),el("div",{style:"display:flex;flex-direction:column;gap:4px"},[el("span",{text:t.title,style:"font-size:14px;font-weight:600"}),el("span",{cls:"pvw",text:t.preview||""})])]);
    if(on)lab.querySelector("input").checked=true;
    lab.addEventListener("click",function(){S.tpl={name:t.name,t:t,values:{}};drawComposer();});
    list.appendChild(lab);
    if(on){t.fields.forEach(function(f){var v=f.prefill_name?(j.name||""):"";S.tpl.values[f.key]=S.tpl.values[f.key]||v;var inp=el("input",{type:"text",value:S.tpl.values[f.key]});inp.addEventListener("input",function(){S.tpl.values[f.key]=inp.value;});list.appendChild(el("label",{cls:"f"},[f.label,inp]));});}
  });
  kids.push(el("div",{text:"Your approved messages (from MyOperator)",style:"font-size:13px;font-weight:600;color:#3E4C47"}),list);
  var b=el("button",{cls:"big",type:"button",onclick:sendTemplate},["Send approved message"]);if(!S.tpl)b.disabled=true;kids.push(b);
  c.replaceChildren.apply(c,kids);
}
function sendTemplate(){
  if(!S.tpl)return;var b=this;b.disabled=true;
  post("/portal/inbox/api/template",{phone:S.phone,template:S.tpl.name,values:S.tpl.values}).then(function(j){b.disabled=false;
    if(!j.ok){toast(j.error||"Not sent.",6000);return;}toast(j.mode==="DRY"?"TEST MODE: recorded, not sent.":"Sent.");S.tpl=null;S.lastSig="";loadChat(true);});
}
function doSend(){
  var t=$("txt");var text=t?t.value.trim():"";var btn=$("sendbtn");
  if(!S.pending&&!text)return;btn.disabled=true;
  var p;
  if(S.pending){var fd=new FormData();fd.append("phone",S.phone);fd.append("kind",S.pending.kind);fd.append("text",S.pending.kind==="audio"?"":text);fd.append("file",S.pending.blob,S.pending.name);
    p=api("/portal/inbox/api/send",{method:"POST",body:fd});}
  else p=post("/portal/inbox/api/send",{phone:S.phone,kind:"text",text:text});
  toast("Sending…",20000);
  p.then(function(j){btn.disabled=false;if(!j.ok){toast(j.error||"Not sent.",7000);return;}
    toast("Sent.");S.pending=null;S.lastSig="";if(t)t.value="";drawComposer();loadChat(true);loadChats();});
}
function doCall(){
  var j=S.chat;var who=j.name||fmtNum(j.phone);
  modal([el("div",{text:"Call "+who+"?",style:"font-size:17px;font-weight:600"}),el("div",{text:"Your mobile rings first. When you pick up, the patient is dialled and sees the clinic number.",style:"font-size:14px;color:#3E4C47"}),
    el("div",{cls:"mrow"},[el("button",{cls:"ghost",type:"button",onclick:closeModal},["Cancel"]),el("button",{cls:"big",type:"button",style:"padding:0 18px",onclick:function(){closeModal();toast("Placing the call…",8000);post("/portal/inbox/api/call",{phone:j.phone}).then(function(r){toast(r.ok?"Your mobile will ring now.":(r.error||"The call was not placed."),7000);});}},["Call now"])])]);
}
function modal(kids){var b=$("mbox");b.replaceChildren.apply(b,kids);$("modal").style.display="flex";}
function closeModal(){$("modal").style.display="none";}
$("modal").addEventListener("click",function(e){if(e.target===$("modal"))closeModal();});
$("ov").addEventListener("click",function(){$("ov").style.display="none";$("ovimg").removeAttribute("src");});
function loadReplies(){return api("/portal/inbox/api/replies").then(function(j){if(j.ok){S.replies=j.replies;if(S.chat)drawComposer();}});}
function editReplies(){
  function draw(){
    var rows=S.replies.map(function(r){return el("div",{cls:"r"},[el("div",{},[el("div",{text:r.title,style:"font-weight:600"}),el("div",{text:r.body,style:"font-size:13px;color:#3E4C47;white-space:pre-wrap"})]),
      el("button",{cls:"lnk",type:"button",onclick:function(){post("/portal/inbox/api/replies",{id:r.id,"delete":1}).then(function(j){if(j.ok){S.replies=j.replies;draw();drawComposer();}});}},["Delete"])]);});
    var ti=el("input",{type:"text",placeholder:"Short name, e.g. Clinic timings",maxlength:"60"});var bo=el("textarea",{rows:"4",placeholder:"The message text"});
    modal([el("div",{text:"Saved replies",style:"font-size:17px;font-weight:600"})].concat(rows).concat([el("div",{text:"Add one",style:"font-weight:600;margin-top:6px"}),ti,bo,
      el("div",{cls:"mrow"},[el("button",{cls:"ghost",type:"button",onclick:closeModal},["Close"]),el("button",{cls:"big",type:"button",style:"padding:0 18px",onclick:function(){post("/portal/inbox/api/replies",{title:ti.value,body:bo.value}).then(function(j){if(!j.ok){toast(j.error);return;}S.replies=j.replies;draw();drawComposer();});}},["Save"])])]));
  }
  draw();
}
function pickImage(file){
  if(!file)return;if(!/^image\/(jpeg|png)$/.test(file.type)){toast("Only JPG or PNG photos.");return;}
  var img=new Image();var u=URL.createObjectURL(file);
  img.onload=function(){var max=1600,w=img.naturalWidth,h=img.naturalHeight;
    if(file.size<=1500000&&Math.max(w,h)<=max){S.pending={kind:"image",blob:file,name:file.name||"photo.jpg",label:"Photo · "+Math.round(file.size/1024)+" KB"};drawComposer();URL.revokeObjectURL(u);return;}
    var s=Math.min(1,max/Math.max(w,h));var cv=document.createElement("canvas");cv.width=Math.round(w*s);cv.height=Math.round(h*s);cv.getContext("2d").drawImage(img,0,0,cv.width,cv.height);
    cv.toBlob(function(b){URL.revokeObjectURL(u);if(!b){toast("This photo could not be prepared.");return;}S.pending={kind:"image",blob:b,name:"photo.jpg",label:"Photo · "+Math.round(b.size/1024)+" KB"};drawComposer();},"image/jpeg",0.85);};
  img.onerror=function(){toast("This photo could not be opened.");};img.src=u;
}
$("fimg").addEventListener("change",function(){pickImage(this.files[0]);this.value="";});
$("fpdf").addEventListener("change",function(){var f=this.files[0];this.value="";if(!f)return;if(f.type!=="application/pdf"){toast("Only PDF files.");return;}if(f.size>20*1048576){toast("The PDF is larger than 20 MB.");return;}S.pending={kind:"document",blob:f,name:f.name||"document.pdf",label:(f.name||"PDF")+" · "+Math.round(f.size/1024)+" KB"};drawComposer();});
// ---- voice: record -> decode -> MP3 in the browser (lame.min.js) ----
var lameLoaded=null;
function loadLame(){if(window.lamejs)return Promise.resolve();if(lameLoaded)return lameLoaded;lameLoaded=new Promise(function(ok,no){var s=document.createElement("script");s.src="/portal/inbox/lame.min.js";s.onload=function(){window.lamejs?ok():no(new Error("encoder"));};s.onerror=function(){no(new Error("encoder"));};document.head.appendChild(s);});return lameLoaded;}
function startRec(){
  if(!navigator.mediaDevices||!window.MediaRecorder){toast("This browser cannot record. Use Chrome on your phone or PC.");return;}
  loadLame().catch(function(){});
  navigator.mediaDevices.getUserMedia({audio:true}).then(function(stream){
    var chunks=[];var mr=new MediaRecorder(stream);var t0=Date.now();
    mr.ondataavailable=function(e){if(e.data&&e.data.size)chunks.push(e.data);};
    mr.onstop=function(){stream.getTracks().forEach(function(t){t.stop();});clearInterval(S.rec.iv);var secs=(Date.now()-t0)/1000;S.rec=null;
      if(secs<1){toast("Too short — hold on a little longer.");drawComposer();return;}
      toast("Preparing the voice note…",15000);
      toMp3(new Blob(chunks,{type:mr.mimeType||"audio/webm"})).then(function(mp3){toast("Voice note ready.");S.pending={kind:"audio",blob:mp3,name:"voice-note.mp3",url:URL.createObjectURL(mp3),label:"Voice note · "+Math.round(secs)+" s"};drawComposer();})
      .catch(function(){toast("The voice note could not be prepared on this browser.",6000);drawComposer();});};
    mr.start();S.rec={mr:mr,iv:null};
    var c=$("comp");var lab=el("span",{text:"Recording… 0 s",style:"font-size:15px;font-weight:600;color:#B3261E"});
    c.replaceChildren(el("div",{cls:"bar",style:"align-items:center;justify-content:space-between"},[lab,
      el("button",{cls:"ghost",type:"button",onclick:function(){chunks=[];t0=Date.now();mr.stop();}},["Cancel"]),
      el("button",{cls:"cb rec",type:"button","aria-label":"Stop recording",onclick:function(){mr.stop();}},[svg(IC.stop,"#fff","#fff")])]));
    S.rec.iv=setInterval(function(){lab.textContent="Recording… "+Math.round((Date.now()-t0)/1000)+" s";if(Date.now()-t0>300000)mr.stop();},500);
  }).catch(function(){toast("The microphone was not allowed. Allow it in the browser and try again.",6000);});
}
function toMp3(blob){
  return Promise.all([loadLame(),blob.arrayBuffer()]).then(function(r){
    var AC=window.AudioContext||window.webkitAudioContext;var ac=new AC();
    return new Promise(function(ok,no){ac.decodeAudioData(r[1],ok,no);}).then(function(buf){
      var rate=buf.sampleRate;var n=buf.length;var mono=new Float32Array(n);
      for(var ch=0;ch<buf.numberOfChannels;ch++){var d=buf.getChannelData(ch);for(var i=0;i<n;i++)mono[i]+=d[i]/buf.numberOfChannels;}
      try{ac.close();}catch(e){}
      return encodeMp3(mono,rate);
    });
  });
}
function encodeMp3(f32,rate){
  var enc=new lamejs.Mp3Encoder(1,rate,64);var pcm=new Int16Array(f32.length);
  for(var i=0;i<f32.length;i++){var s=Math.max(-1,Math.min(1,f32[i]));pcm[i]=s<0?s*0x8000:s*0x7FFF;}
  var out=[];for(var j=0;j<pcm.length;j+=1152){var b=enc.encodeBuffer(pcm.subarray(j,j+1152));if(b.length)out.push(new Uint8Array(b));}
  var e=enc.flush();if(e.length)out.push(new Uint8Array(e));
  return new Blob(out,{type:"audio/mpeg"});
}
window.__inboxEncodeMp3=encodeMp3;
var qt=null;$("q").addEventListener("input",function(){clearTimeout(qt);qt=setTimeout(loadChats,250);});
function poll(){loadChats();if(S.phone&&!S.rec)loadChat(false);}
var mid=new URLSearchParams(location.search).get("m");
loadReplies();
loadChats().then(function(){if(mid){api("/portal/inbox/api/resolve?m="+encodeURIComponent(mid)).then(function(j){if(j.ok&&j.phone)openChat(j.phone);});history.replaceState(null,"","/portal/inbox");}});
setInterval(function(){if(!document.hidden)poll();},10000);
document.addEventListener("visibilitychange",function(){if(!document.hidden)poll();});
})();
</script></body></html>"""
