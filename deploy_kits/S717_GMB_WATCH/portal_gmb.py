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

S717 (D832 Part C, the owner's "build" 11:05 IST 06-Nov on the mock-up he narrowed at 10:18-10:20 IST: "the comparison
should be as percent of reviewers who complained" · "don't chase others' fake or real reviews, narrow down on what is
useful for us only"): the section "What patients say -- for our clinic" under the drafts reads the readings kept here.
  snapshot -- one row per reading (every two weeks, read-only, by the assistant in the browser): our reviewers counted,
              each complaint as a percent of OUR reviewers and of the other listings' reviewers, the words patients use
              elsewhere that ours do not, the listings it was read from. No review text, no reviewer, no star average.
  watch    -- the listings to read, the owner's own additions included.
  GET  /portal/gmb/api/watch                     -> {ok, latest, previous, listings}
  POST /portal/gmb/api/snapshot  {taken_on, data} -> {ok, id}        (the reading; checked field by field)
  POST /portal/gmb/api/watch     {name}           -> {ok, listings}  (the owner adds a listing to read)

A failure here costs only the keeping: the page is served by portal.py's own /portal/gmb and Copy / WhatsApp work
whether or not the save answers.
"""
import datetime
import io
import json
import os
import re
import sqlite3

KIT = "S717"
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
CREATE TABLE IF NOT EXISTS snapshot(
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  at        TEXT NOT NULL,              -- IST, when it was saved
  who       TEXT NOT NULL,
  taken_on  TEXT NOT NULL,              -- the day the listings were read, YYYY-MM-DD
  data      TEXT NOT NULL,              -- the reading (JSON, see check_reading)
  kit       TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS watch(
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  name      TEXT NOT NULL UNIQUE,
  added_at  TEXT NOT NULL,
  who       TEXT NOT NULL,
  active    INTEGER NOT NULL DEFAULT 1
);
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


def _num(v, lo=0.0, hi=100.0):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    try:
        v = float(v)
    except (OverflowError, ValueError):
        return None
    return round(v, 1) if lo <= v <= hi else None


def _name(v, cap):
    if not isinstance(v, str):
        return None
    v = re.sub(r"\s+", " ", v).strip()
    return no_numbers(v) if 0 < len(v) <= cap else None


def check_reading(taken_on, d):
    """(clean dict, None) or (None, why). Only counts, percents, short names and words -- never a review's text."""
    try:
        day = datetime.date.fromisoformat(taken_on) if isinstance(taken_on, str) and len(taken_on) == 10 else None
    except ValueError:
        day = None
    if day is None or day < datetime.date(2026, 1, 1) or day > datetime.datetime.now(IST).date():
        return None, "taken_on is a real date (YYYY-MM-DD), not in the future"
    if not isinstance(d, dict):
        return None, "the reading is an object"
    out = {}
    for k in ("ours_n", "else_n"):
        v = d.get(k)
        if isinstance(v, bool) or not isinstance(v, int) or not 0 < v < 100000:
            return None, "%s is a count of reviewers" % k
        out[k] = v
    out["ours_low_pct"] = _num(d.get("ours_low_pct"))
    if out["ours_low_pct"] is None:
        return None, "ours_low_pct is a percent"
    th = d.get("themes")
    if not isinstance(th, list) or not 0 < len(th) <= 12:
        return None, "themes: 1 to 12"
    out["themes"] = []
    for t in th:
        if not isinstance(t, dict):
            return None, "a theme is an object"
        n, o, e = _name(t.get("name"), 40), _num(t.get("ours")), _num(t.get("else"))
        if n is None or o is None or e is None:
            return None, "a theme has a name (up to 40) and two percents"
        if any(x["name"] == n for x in out["themes"]):
            return None, "each complaint once"
        out["themes"].append({"name": n, "ours": o, "else": e})
    ws = d.get("words", [])
    if not isinstance(ws, list) or len(ws) > 40:
        return None, "words: up to 40"
    out["words"] = []
    for w in ws:
        w = _name(w, 30)
        if w is None:
            return None, "a word is short text (up to 30)"
        out["words"].append(w)
    src = d.get("sources")
    if not isinstance(src, list) or not 0 < len(src) <= 20:
        return None, "sources: 1 to 20 listings"
    out["sources"] = []
    for x in src:
        x = _name(x, 60)
        if x is None:
            return None, "a source is a listing's name (up to 60)"
        out["sources"].append(x)
    note = d.get("note", "")
    if note and _name(note, 300) is None:
        return None, "the note is short text (up to 300)"
    out["note"] = _name(note, 300) if note else ""
    return out, None


def save_reading(c, taken_on, clean, who):
    cur = c.execute("INSERT INTO snapshot(at,who,taken_on,data,kit) VALUES(?,?,?,?,?)",
                    (now_ist(), (who or "doctor")[:40], taken_on, json.dumps(clean, ensure_ascii=False), KIT))
    return cur.lastrowid


def add_watch(c, name, who):
    c.execute("INSERT OR IGNORE INTO watch(name,added_at,who,active) VALUES(?,?,?,1)", (name, now_ist(), (who or "doctor")[:40]))
    c.execute("UPDATE watch SET active=1 WHERE name=?", (name,))


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

    def watch_list(c):
        return [r["name"] for r in c.execute("SELECT name FROM watch WHERE active=1 ORDER BY id")]

    def reading(r):
        return None if r is None else {"taken_on": r["taken_on"], "data": json.loads(r["data"])}

    @app.route("/portal/gmb/api/watch", methods=["GET"], endpoint="gmb_watch_get")
    @guard
    def gmb_watch_get():
        c = connect(db_path)
        try:
            rows = c.execute("SELECT taken_on,data FROM snapshot ORDER BY taken_on DESC, id DESC LIMIT 2").fetchall()
            return jsonify({"ok": True, "latest": reading(rows[0] if rows else None),
                            "previous": reading(rows[1] if len(rows) > 1 else None), "listings": watch_list(c)})
        finally:
            c.close()

    @app.route("/portal/gmb/api/snapshot", methods=["POST"], endpoint="gmb_watch_snapshot")
    @guard
    def gmb_watch_snapshot():
        b, err = body()
        if err:
            return err
        clean, why = check_reading(b.get("taken_on"), b.get("data"))
        if clean is None:
            return fail(why)
        c = connect(db_path)
        try:
            sid = save_reading(c, b["taken_on"], clean, get_user())
            c.commit()
            return jsonify({"ok": True, "id": sid})
        finally:
            c.close()

    @app.route("/portal/gmb/api/watch", methods=["POST"], endpoint="gmb_watch_add")
    @guard
    def gmb_watch_add():
        b, err = body()
        if err:
            return err
        n = _name(b.get("name"), 60)
        if n is None:
            return fail("a listing's name, up to 60 letters")
        c = connect(db_path)
        try:
            if n not in watch_list(c) and len(watch_list(c)) >= 20:
                return fail("20 listings at most")
            add_watch(c, n, get_user())
            c.commit()
            return jsonify({"ok": True, "listings": watch_list(c)})
        finally:
            c.close()

    return True


def seed(path, seed_file):
    """The installer's step: the 5-Nov reading and the listings, once, only when the store has no reading yet.
    Returns 'seeded', 'already' or raises."""
    with io.open(seed_file, encoding="utf-8") as fh:
        s = json.load(fh)
    clean, why = check_reading(s["taken_on"], s["data"])
    if clean is None:
        raise ValueError("the seed is not a valid reading: " + why)
    c = connect(path)
    try:
        if c.execute("SELECT COUNT(*) FROM snapshot").fetchone()[0]:
            return "already"
        save_reading(c, s["taken_on"], clean, "S717 seed")
        for n in clean["sources"]:
            if n != "Our own listing":
                add_watch(c, n, "S717 seed")
        c.commit()
        return "seeded"
    finally:
        c.close()
