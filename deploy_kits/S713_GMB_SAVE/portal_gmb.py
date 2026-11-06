"""portal_gmb.py -- the GMB Review Assist's saved presses (kit S713, the parent, session 389, 06-Nov-2026).

THE OWNER'S PLAN (D832, Part B, his OK 14:58 IST 05-Nov; his "Yes" 08:45 IST 06-Nov):
  "Each press is kept on the server behind your login (never in the repository): the ticks, language, size, the three
   drafts as generated, and -- when you change the text before sharing it -- the text as shared. A 'Shared' button
   beside Copy records that moment. Your edits are the only real signal of what sounds right; today they are lost the
   moment you copy."

WHAT IT KEEPS (one SQLite file, GMB_STORE_DB, default /root/portal/gmb_store.db -- data, never in the repository and
never in the nightly code bundle, which carries no .db):
  press  -- one row per Generate / Fresh variation: when (IST), who, language, relation, the ticks as the page held them,
            the three drafts exactly as generated.
  share  -- one row per Shared / Copy / WhatsApp press on a draft: which draft, how, the text in the box at that moment,
            and whether it differed from the draft as generated.
  No phone number is kept: any run of 7 or more digits in a stored text is replaced by "[number]" before it is written.
  The page never sends a phone number (WhatsApp opens with no number).

DOORS (all behind the portal's doctor gate; writes also need the page's own X-Gmb: 1 header, which a page on any
other site cannot send without being refused first):
  POST /portal/gmb/api/press   {state:{...}, drafts:[short, medium, long]}                       -> {ok, id}
  POST /portal/gmb/api/share   {id, which:0|1|2, how:"shared"|"copied"|"whatsapp", text}         -> {ok, edited}
  GET  /portal/gmb/api/health                                                                     -> {ok, kit, presses, shares}

A failure here costs only the keeping: the page is served by portal.py's own /portal/gmb and Copy / WhatsApp work
whether or not the save answers.
"""
import datetime
import json
import os
import re
import sqlite3

KIT = "S713"
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
HOWS = ("shared", "copied", "whatsapp")
MAX_TEXT = 4000           # a long draft is under 90 words; 4,000 characters is generous for an edited one
MAX_STATE = 8000
MAX_BODY = 64 * 1024
_DIGITS = re.compile(r"\+?\(?\d[\d\s\-\u2013\u2014.()/]{5,}\d")

SCHEMA = """
CREATE TABLE IF NOT EXISTS press(
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  at        TEXT NOT NULL,              -- IST, ISO
  who       TEXT NOT NULL,
  lang      TEXT, relation TEXT,
  state     TEXT NOT NULL,              -- the ticks as the page held them (JSON)
  d0 TEXT, d1 TEXT, d2 TEXT,            -- short, medium, long, exactly as generated
  kit       TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS share(
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  press_id  INTEGER NOT NULL REFERENCES press(id),
  at        TEXT NOT NULL,
  who       TEXT NOT NULL,
  which     INTEGER NOT NULL,           -- 0 short, 1 medium, 2 long
  how       TEXT NOT NULL,              -- shared | copied | whatsapp
  text      TEXT NOT NULL,
  edited    INTEGER NOT NULL            -- 1 when the text differs from the draft as generated
);
CREATE INDEX IF NOT EXISTS share_press ON share(press_id);
"""


def now_ist():
    return datetime.datetime.now(IST).isoformat(timespec="seconds")


def no_numbers(s):
    """Any run of 7+ digits becomes [number] -- spaces, hyphens, dashes, dots, brackets and slashes allowed between them,
    so a mobile number typed with spaces, a hyphen, a dash, dots, brackets or a +91 in front is caught."""
    def rep(m):
        return "[number]" if len(re.sub(r"\D", "", m.group(0))) >= 7 else m.group(0)
    return _DIGITS.sub(rep, s or "")


def mask_tree(v):
    """no_numbers() on every string inside the ticks, BEFORE they become JSON (so the stored JSON stays valid);
    a bare number of 7+ digits is dropped to None."""
    if isinstance(v, str):
        return no_numbers(v)
    if isinstance(v, bool) or v is None:
        return v
    if isinstance(v, (int, float)):
        return None if len(re.sub(r"\D", "", str(v))) >= 7 else v
    if isinstance(v, list):
        return [mask_tree(x) for x in v]
    if isinstance(v, dict):
        return {str(k)[:40]: mask_tree(x) for k, x in v.items()}
    return None


def connect(path):
    c = sqlite3.connect(path, timeout=20)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=20000")
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(SCHEMA)
    return c


def register(app, guard, get_user, cfg_get):
    from flask import request, jsonify

    db_path = cfg_get("GMB_STORE_DB", "") or "/root/portal/gmb_store.db"

    def fail(msg, code=400):
        return jsonify({"ok": False, "error": msg}), code

    def body():
        if request.headers.get("X-Gmb") != "1":
            return None, fail("not from the page", 403)
        if (request.content_length or 0) > MAX_BODY:
            return None, fail("too large", 413)
        b = request.get_json(silent=True)
        if not isinstance(b, dict):
            return None, fail("not JSON")
        return b, None

    def text(v, cap=MAX_TEXT):
        if not isinstance(v, str):
            return None
        v = v.replace("\r\n", "\n")
        return no_numbers(v) if len(v) <= cap else None

    @app.route("/portal/gmb/api/press", methods=["POST"], endpoint="gmb_save_press")
    @guard
    def gmb_save_press():
        b, err = body()
        if err:
            return err
        st = b.get("state")
        drafts = b.get("drafts")
        if not isinstance(st, dict) or not isinstance(drafts, list) or len(drafts) != 3:
            return fail("state and three drafts are needed")
        ds = [text(d) for d in drafts]
        if any(d is None for d in ds):
            return fail("a draft is not text or is too long")
        st = mask_tree(st)
        sj = json.dumps(st, ensure_ascii=False, sort_keys=True)
        if len(sj) > MAX_STATE:
            return fail("the ticks are too long")
        lang = str(st.get("language") or "")[:20]
        rel = str(st.get("relation") or "")[:20]
        c = connect(db_path)
        try:
            cur = c.execute("INSERT INTO press(at,who,lang,relation,state,d0,d1,d2,kit) VALUES(?,?,?,?,?,?,?,?,?)",
                            (now_ist(), (get_user() or "doctor")[:40], lang, rel, sj, ds[0], ds[1], ds[2], KIT))
            c.commit()
            return jsonify({"ok": True, "id": cur.lastrowid})
        finally:
            c.close()

    @app.route("/portal/gmb/api/share", methods=["POST"], endpoint="gmb_save_share")
    @guard
    def gmb_save_share():
        b, err = body()
        if err:
            return err
        try:
            pid = int(b.get("id"))
            which = int(b.get("which"))
        except (TypeError, ValueError):
            return fail("id and which are numbers")
        how = b.get("how")
        if which not in (0, 1, 2) or how not in HOWS:
            return fail("which is 0, 1 or 2; how is shared, copied or whatsapp")
        t = text(b.get("text"))
        if t is None:
            return fail("the text is not text or is too long")
        c = connect(db_path)
        try:
            p = c.execute("SELECT d0,d1,d2 FROM press WHERE id=?", (pid,)).fetchone()
            if p is None:
                return fail("no such press", 404)
            orig = p["d%d" % which] or ""
            edited = 0 if t.strip() == orig.strip() else 1
            c.execute("INSERT INTO share(press_id,at,who,which,how,text,edited) VALUES(?,?,?,?,?,?,?)",
                      (pid, now_ist(), (get_user() or "doctor")[:40], which, how, t, edited))
            c.commit()
            return jsonify({"ok": True, "edited": bool(edited)})
        finally:
            c.close()

    @app.route("/portal/gmb/api/health", endpoint="gmb_save_health")
    @guard
    def gmb_save_health():
        c = connect(db_path)
        try:
            n = c.execute("SELECT COUNT(*) FROM press").fetchone()[0]
            s = c.execute("SELECT COUNT(*) FROM share").fetchone()[0]
            e = c.execute("SELECT COUNT(*) FROM share WHERE edited=1").fetchone()[0]
            return jsonify({"ok": True, "kit": KIT, "presses": n, "shares": s, "edited": e})
        finally:
            c.close()

    return True
