#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""callback_clock.py -- kit S796_CALLBACK_CLOCK (session S435, 12-Nov-2026, the parent). NEW.
                       S953_STAFF_NOTIFY (session S520, 25-Nov-2026, the parent; D1067 "notifications first").

THE OWNER, 12-Nov-2026 07:47 / 07:52 IST, on the plan "so that no caller is lost": "a clock on the callback, this is fine. And the backup
phone should be Shavez." -- "Both" (build it).

WHY. 14-Oct .. 11-Nov, callers counted once a day: 15 in 100 never spoke to anyone, and 57 of those 66 had no call-back on record --
although the missed-call notification goes to the staff phones at once (ring_hook.py) and MyOperator sends the caller its template.
The first notification is easy to lose in a busy hour; nothing asked again.

WHAT IT DOES. Run by cron every 5 minutes. It reads /root/wa/console.db READ-ONLY (the Call Console's own store, rebuilt every 10
minutes) and finds every caller with a MISSED incoming call since yesterday's closing time who has not SPOKEN to the clinic since (no
answered call after it, either way -- the Call Console's own rule for a missed call). The clock counts DUTY minutes only (Mon-Sat
09:00-20:30, Sunday 09:00-14:30), and is judged as of the store's own build time, so a call-back the store has not seen yet is never
chased early:
  * 30 duty minutes  -> ONE notification to the phone staff (shivani, alisha, the reception mobile): how many, and who;
  * 60 duty minutes  -> ONE notification to Shavez, the backup (the owner's word);
  * at closing time  -> the count still open goes to the owner (English), only when it is above zero.
Each caller's missed call is notified once per stage (its own small store, STORE); a number the owner marked Spam is left out; a stale
console.db (older than STALE_MIN) is not judged at all. Nothing here changes console.db, the portal, or any page.

S953_STAFF_NOTIFY -- the staff now work the new staff Call Console (/portal/console/staff, S948), so:
  1. Every tap opens THAT page on the right tab (?tab=missed / ?tab=again / ?tab=wa), no longer the old Tracker.
  2. The 30 / 60 minute stages follow the page's own Incoming missed tab (calls_staff.build_lists -- the same rule, never a second
     one): today's misses AND yesterday's carried misses (S951: no connected call, no WhatsApp from him, no Docterz visit since).
     A caller already tried once has left that tab for Call again and is chased there instead. A carried miss starts its clock at
     today's opening and is notified once a day.
  3. Two new notifications, each once per item per stage, to the phone staff ON DUTY now (punched in and inside the shift, read from
     staff_master.csv + punches.csv as calls_console reads them; the reception mobile always; no phone staff on duty -> the reception
     mobile and Shavez; the duty files unreadable -> every phone staff login):
       * "Call again due"   -- a Call again row that is due (2 h after one unanswered try, PORTAL_STAFF_CALL_AGAIN_H, the page's rule);
       * "WhatsApp waiting" -- a chat awaiting a reply (calls_console.wa_awaiting, the owner's rule) past PORTAL_CLOCK_WA_MIN duty minutes.
  4. Every time is a setting (portal_config.py, then the environment -- as the portal reads them): PORTAL_CLOCK_T1_MIN (30),
     PORTAL_CLOCK_T2_MIN (60), PORTAL_CLOCK_WA_MIN (30), PORTAL_CLOCK_AGAIN_ON (1), PORTAL_CLOCK_WA_ON (1), PORTAL_CLOCK_LISTS (1;
     0 = the S796 rule for the stages). ntfy is the fallback only for a login with no subscribed device, and only when
     PORTAL_STAFF_NTFY_URL is set (no staff topic exists yet: unset = Web Push only, as before).
  If the staff lists cannot be built (any fault), the run says so in its log line and works exactly as S796 did, the taps opening the
  new page -- a notification is never lost to a fault here. One run at a time (a lock beside STORE).

CLI:  callback_clock.py          the run (what cron calls)
      callback_clock.py --dry    counts only; pushes nothing, writes nothing
Stdlib (+ ring_common from /root/portal for the push: absent = counted, nothing sent; + calls_console / calls_staff for the lists).
"""
import datetime as dt
import json
import os
import re
import sqlite3
import sys
import time
import urllib.request

VERSION = "S953 1"
CONSOLE_DB = os.environ.get("CC_CONSOLE_DB", "/root/wa/console.db")
REVIEWS_DB = os.environ.get("CC_REVIEWS_DB", "/root/wa/console_reviews.db")
STORE = os.environ.get("CC_STORE", "/root/portal/callback_clock.db")
PORTAL_DIR = os.environ.get("RING_PORTAL_DIR", "/root/portal")
STAFF = ("shivani", "alisha", "reception")
BACKUP = ("shavez",)                               # the owner, 12-Nov 07:47 IST
OWNER = ("manoj",)
T1, T2 = 30, 60                                    # duty minutes (S953: settings PORTAL_CLOCK_T1_MIN / _T2_MIN)
WA_MIN = 30                                        # S953: a chat awaiting a reply this many duty minutes (PORTAL_CLOCK_WA_MIN)
OPEN_HM = (9, 0)
CLOSE_HM = (20, 30)
SUN_CLOSE_HM = (14, 30)
STALE_MIN = 25                                     # console.db is rebuilt every 10 minutes
STAFF_URL = "/portal/console/staff?tab=missed"     # S953: the staff Call Console (was /portal/go/call-tracker, the old Tracker)
AGAIN_URL = "/portal/console/staff?tab=again"
OLD_URL = "/portal/go/call-tracker"               # S796's landing: kept for a login the staff page does not admit (second look, S953)
WA_URL = "/portal/console/staff?tab=wa"
OWNER_URL = "/portal/console"
PUBLIC_BASE = "https://followup.dr-manoj.in"       # for an ntfy tap only (PORTAL_PUBLIC_BASE)
RECEPTION = "reception"
SPAM_OUTCOME = "Spam / marketing"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
_JK = re.compile(r"^(\d{10})_(\d{9,12})$")
_TZ = re.compile(r"([+-]\d{2}:?\d{2}|Z)\s*$")
SUBS_OF = None                                     # the walk hands in a stub (login -> its subscribed devices)
NTFY_POST = None                                   # the walk hands in a stub (url, title, body, click) -> bool


def now_ist():
    return dt.datetime.now(IST).replace(tzinfo=None)


def parse_ts(s):
    s = _TZ.sub("", (s or "").strip()).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------------------------- S953: the settings
_PC = [None, False]


def _pc():
    if not _PC[1]:
        _PC[1] = True
        try:
            if PORTAL_DIR not in sys.path:
                sys.path.insert(0, PORTAL_DIR)
            import portal_config as pc                   # noqa: PLC0415  (VPS-only, 0600; absent on a walk)
            _PC[0] = pc
        except Exception:                                # noqa: BLE001
            _PC[0] = None
    return _PC[0]


def cfg(name, default=""):
    """As the portal reads a setting: portal_config.py, then the environment, then the default."""
    pc = _pc()
    v = getattr(pc, name, None) if pc is not None else None
    if v is None or str(v).strip() == "":                # 0 / False in portal_config.py is a value (cold review, S953)
        v = os.environ.get(name, "")
    v = str(v if v is not None else "").strip()
    return v or (default if default is not None else "")


def cfg_min(name, default):
    try:
        n = int(float(cfg(name, str(default))))
        return n if n > 0 else default
    except Exception:                                    # noqa: BLE001
        return default


def cfg_on(name):
    return cfg(name, "1").lower() not in ("0", "off", "no", "false")


# ---------------------------------------------------------------------------------------------- S796 (unchanged)
def window(day):
    """(start, end) of the duty window of one date."""
    close = SUN_CLOSE_HM if day.weekday() == 6 else CLOSE_HM
    return (dt.datetime.combine(day, dt.time(*OPEN_HM)), dt.datetime.combine(day, dt.time(*close)))


def duty_minutes(t0, t1):
    """Whole duty minutes between two moments (0 when t1 <= t0)."""
    if t1 <= t0:
        return 0
    total = 0.0
    day = t0.date()
    while day <= t1.date():
        a, b = window(day)
        lo, hi = max(a, t0), min(b, t1)
        if hi > lo:
            total += (hi - lo).total_seconds()
        day += dt.timedelta(days=1)
    return int(total // 60)


def phone_of(p10, jk, ref):
    """The Call Console's own rule (calls_console.phone_of)."""
    p = (p10 or "").strip()
    if len(p) == 10 and p.isdigit():
        return p
    m = _JK.match(jk or "")
    if m:
        return m.group(1)
    cr = (ref or "").strip()
    m2 = re.match(r"^(\d{10})\D", cr + " ")
    if m2 and not cr.startswith("IN-"):
        return m2.group(1)
    return ""


def spam_phones(path=None):
    out = set()
    try:
        con = sqlite3.connect("file:%s?mode=ro" % (path or REVIEWS_DB), uri=True, timeout=5)
        try:
            for (jk,) in con.execute("SELECT join_key FROM dispositions WHERE final_outcome=?", (SPAM_OUTCOME,)):
                if "_" in (jk or ""):
                    out.add(jk.split("_", 1)[0])
        finally:
            con.close()
    except Exception:                                    # noqa: BLE001
        pass
    return out


def read_console(path, d_from, d_to):
    """(built_at or None, {phone: [(t, direction, answered)]}, {phone: (name, clinic_id)})."""
    con = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=10)
    try:
        built = None
        try:
            r = con.execute("SELECT v FROM meta WHERE k='built_at'").fetchone()
            built = parse_ts(r[0]) if r else None
        except sqlite3.Error:
            built = None
        by = {}
        for p10, jk, ref, direction, answered, ended in con.execute(
                "SELECT c.phone10, c.join_key, c.client_ref_id, c.direction, c.answered, c.ended_at_ist FROM calls c "
                "WHERE substr(c.ended_at_ist,1,10)>=? AND substr(c.ended_at_ist,1,10)<=? ORDER BY c.ended_at_ist ASC, c.id ASC",
                (d_from, d_to)):
            ph, t = phone_of(p10, jk, ref), parse_ts(ended)
            if ph and t:
                by.setdefault(ph, []).append((t, (direction or "").strip(), answered == 1))
        pats = {}
        try:
            for ph, name, cid in con.execute("SELECT phone10, name, clinic_id FROM patients WHERE phone10<>'' ORDER BY rowid"):
                pats[ph] = ((name or "").strip(), (cid or "").strip())
        except sqlite3.Error:
            pats = {}
        return built, by, pats
    finally:
        con.close()


def open_callers(by, pats, spam, cutoff):
    """Callers whose missed call at or after `cutoff` has not been followed by an answered call (either way)."""
    out = []
    for ph, its in by.items():
        if ph in spam:
            continue
        its = sorted(its)
        last_ok = max([t for t, _d, ok in its if ok], default=None)
        opens = [t for t, d, ok in its if d == "In" and not ok and t >= cutoff and (last_ok is None or t > last_ok)]
        if not opens:
            continue
        t0 = opens[0]
        name, cid = pats.get(ph, ("", ""))
        out.append({"phone": ph, "t0": t0, "missed": len(opens), "name": name, "cid": cid, "unknown": not name,
                    "tried": sum(1 for t, d, ok in its if d == "Out" and not ok and t > t0)})
    out.sort(key=lambda c: c["t0"])
    return out


def label(c):
    if c["name"]:
        return c["name"] + ((" (ID %s)" % c["cid"]) if c["cid"] else "")
    return "नया नंबर " + c["phone"]


def names(cs, n=3):
    s = " · ".join(label(c) for c in cs[:n])
    return s + ((" +%d" % (len(cs) - n)) if len(cs) > n else "")


def store_open(path):
    con = sqlite3.connect(path, timeout=10)
    con.execute("CREATE TABLE IF NOT EXISTS sent(phone TEXT NOT NULL, t0 TEXT NOT NULL, stage INTEGER NOT NULL, at TEXT NOT NULL, "
                "PRIMARY KEY(phone, t0, stage))")
    con.execute("CREATE TABLE IF NOT EXISTS runs(at TEXT NOT NULL, open INTEGER, unknown INTEGER, s1 INTEGER, s2 INTEGER, closing INTEGER, "
                "sent TEXT)")
    return con


def get_pusher(pusher=None):
    if pusher is not None:
        return pusher
    try:
        if PORTAL_DIR not in sys.path:
            sys.path.insert(0, PORTAL_DIR)
        import ring_common as rc                         # noqa: PLC0415
        return rc.push_user
    except Exception:                                    # noqa: BLE001
        return None


def push(pusher, who, title, body, url, tag):
    s = f = 0
    for w in who:
        u = url(w) if callable(url) else url             # S953: the landing can differ per login
        try:
            a, b = pusher(w, {"title": title, "body": body, "url": u, "tag": tag, "ttl": 1800, "requireInteraction": True, "renotify": True})
        except Exception:                                # noqa: BLE001
            a, b = 0, 1
        s, f = s + a, f + b
    return s, f


# ---------------------------------------------------------------------------------------------- S953: lists, duty, ntfy
def _subs_of():
    if SUBS_OF is not None:
        return SUBS_OF
    try:
        if PORTAL_DIR not in sys.path:
            sys.path.insert(0, PORTAL_DIR)
        import ring_common as rc                         # noqa: PLC0415
        return lambda u: rc.subs_for(u)
    except Exception:                                    # noqa: BLE001
        return None


def _ntfy_post(url, title, body, click):
    if NTFY_POST is not None:
        return NTFY_POST(url, title, body, click)
    try:
        req = urllib.request.Request(url, data=(title + "\n" + body).encode("utf-8"), method="POST",
                                     headers={"Title": "Clinic", "Click": click, "Tags": "telephone_receiver"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return 200 <= r.status < 300
    except Exception:                                    # noqa: BLE001
        return False


def send(pusher, who, title, body, url, tag):
    """Web Push to each login; ntfy once for the logins with no subscribed device, only when a staff topic is set."""
    s, f = push(pusher, who, title, body, url, tag) if pusher else (0, 0)
    nt = cfg("PORTAL_STAFF_NTFY_URL", "")
    if nt:
        so = _subs_of()
        bare = []
        for w in who:
            try:
                if so is not None and not so(w):
                    bare.append(w)
            except Exception:                            # noqa: BLE001
                pass
        masked = mask_nums(body)                         # ntfy is an outside server: numbers to the last four only
        if bare and _ntfy_post(nt, title, masked + " (" + ", ".join(bare) + ")",
                               cfg("PORTAL_PUBLIC_BASE", PUBLIC_BASE) + (url(bare[0]) if callable(url) else url)):
            return s, f, len(bare)
    return s, f, 0


def mask_nums(text):
    """Every run of 10+ digits (spaces and dashes inside allowed, as '50000 14075') -> '......' + its last four digits."""
    def m(mo):
        d = re.sub(r"\D", "", mo.group(0))
        return ("......" + d[-4:]) if len(d) >= 10 else mo.group(0)
    return re.sub(r"\+?\d[\d \-]{8,}\d", m, text or "")


def _meta_fn(console):
    def m():
        try:
            con = sqlite3.connect("file:%s?mode=ro" % console, uri=True, timeout=5)
            try:
                r = con.execute("SELECT v FROM meta WHERE k='built_at'").fetchone()
            finally:
                con.close()
            return {"ok": True, "built_at": (r[0] if r else "")}
        except Exception:                                # noqa: BLE001
            return {"ok": False, "built_at": ""}
    return m


def staff_view(console, now, reviews=None):
    """The staff page's own lists (calls_staff.build_lists) and the owner's WhatsApp-awaiting rule, read-only. Raises on a fault."""
    if PORTAL_DIR not in sys.path:
        sys.path.insert(0, PORTAL_DIR)
    import calls_console as CC                           # noqa: PLC0415
    import calls_staff as CS                             # noqa: PLC0415
    if CC._CFG is None:                                  # a separate process from the portal: its settings, its way
        CC._CFG = cfg
    CC._H.setdefault("spam_phones", lambda: spam_phones(reviews))
    CC._H.setdefault("console_meta", _meta_fn(console))
    CS.CC = CC
    import contextlib                                    # noqa: PLC0415
    import io                                            # noqa: PLC0415
    conn = sqlite3.connect("file:%s?mode=ro" % console, uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):            # the builder's own failure lines can carry a number: masked below
            inbox = CC._cfg_path("PORTAL_INBOX_DB", CC.INBOX_DB_DEFAULT)
            lists = CS.build_lists(conn, RECEPTION, now=now, inbox_path=inbox, fin_db=CC._cfg_path("FINANCE_DB_PATH", None))
            if not isinstance(lists, dict) or not isinstance(lists.get("tabs"), dict):
                raise ValueError("no lists")
            d = now.date().isoformat()
            aw = CC.wa_awaiting(conn, CC.wa_load(conn, d, d, now, inbox), now)
    finally:
        conn.close()
        if err.getvalue():
            sys.stderr.write(mask_nums(err.getvalue()))
    return lists, aw, CC


def on_duty(CC, now):
    """(logins, why): the phone staff on duty now + the reception mobile; nobody on duty -> the reception mobile + the backup;
    the duty files unreadable -> every phone staff login + the reception mobile."""
    phone = []
    for part in str(CC._cfg_path("PORTAL_PHONE_STAFF", CC.PHONE_STAFF_DEFAULT) or "").split(","):
        k = re.sub(r"[^a-z]", "", part.strip().lower().split()[0]) if part.strip() else ""
        if k and k not in phone:
            phone.append(k)
    rec = re.sub(r"[^a-z]", "", str(CC._cfg_path("PORTAL_RECEPTION_AGENT", RECEPTION) or RECEPTION).lower().split()[0]) or RECEPTION
    d = now.date().isoformat()
    try:
        staff, punches, ok = CC.load_duty(CC._cfg_path("SR_STAFF_MASTER", CC.STAFF_MASTER_DEFAULT),
                                          CC._cfg_path("SR_PUNCH_CSV", CC.PUNCH_CSV_DEFAULT), [d])
    except Exception:                                    # noqa: BLE001
        staff, punches, ok = {}, {}, False
    if not ok or not staff:
        return phone + [rec], "duty not known"
    on = []
    for k in phone:
        ent = staff.get(k)
        w = CC.duty_window(ent, d, punches.get(k, {}).get(d)) if ent else None
        if w and w[0] <= now <= w[1]:
            on.append(k)
    if on:
        return on + [rec], "on duty"
    return [rec] + [b for b in BACKUP if b not in phone], "no phone staff on duty"


def admitted():
    """The logins the staff page admits (calls_staff.allowed_keys() with the live settings, as the page reads them) -- a
    function login -> bool; None when it cannot be read (then every tap keeps S796's landing)."""
    try:
        if PORTAL_DIR not in sys.path:
            sys.path.insert(0, PORTAL_DIR)
        import calls_console as CC                       # noqa: PLC0415
        import calls_staff as CS                         # noqa: PLC0415
        if CC._CFG is None:
            CC._CFG = cfg
        CS.CC = CC
        keys = set(CS.allowed_keys())
        return lambda w: bool(w) and CC.login_key(w) in keys
    except Exception:                                    # noqa: BLE001
        return None


def landing(adm, new_url):
    """login -> the tap's address: the staff page's tab for a login it admits, else S796's landing."""
    return lambda w: new_url if (adm is not None and adm(w)) else OLD_URL


def row_label(r):
    nm = (r.get("name") or "").strip()
    if not nm or nm in ("New number", "Patient"):
        return (nm or "New number") + " " + (r.get("phone_h") or r.get("phone") or "")
    return nm


def row_names(rows, n=3):
    s = " · ".join(row_label(r) for r in rows[:n])
    return s + ((" +%d" % (len(rows) - n)) if len(rows) > n else "")


def _lock(store):
    try:
        import fcntl                                     # noqa: PLC0415
        fh = open(store + ".lock", "w")
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fh
    except BlockingIOError:
        return None
    except Exception:                                    # noqa: BLE001
        return True                                      # no lock to be had (not Linux): run as S796 did


def run(dry=False, pusher=None, now=None, console=None, store=None, reviews=None):
    t_start = time.time()
    now = now or now_ist()
    console = console or CONSOLE_DB
    store = store or STORE
    today = now.date()
    yday = today - dt.timedelta(days=1)
    t1, t2, wa_min = cfg_min("PORTAL_CLOCK_T1_MIN", T1), cfg_min("PORTAL_CLOCK_T2_MIN", T2), cfg_min("PORTAL_CLOCK_WA_MIN", WA_MIN)
    staff_url = cfg("PORTAL_CLOCK_STAFF_URL", STAFF_URL)
    try:
        built, by, pats = read_console(console, yday.isoformat(), today.isoformat())
    except Exception as e:                               # noqa: BLE001
        print("%s console.db could not be read (%s) -- nothing judged" % (now.strftime("%Y-%m-%d %H:%M"), type(e).__name__))
        return {"ok": False, "why": "unreadable"}
    age = int((now - built).total_seconds() // 60) if built else None
    if built is None or age > STALE_MIN:
        print("%s console.db is stale (built %s) -- nothing judged" % (now.strftime("%Y-%m-%d %H:%M"), built.strftime("%H:%M") if built else "never"))
        return {"ok": False, "why": "stale", "age": age}
    asof = min(now, built)
    cutoff = window(yday)[1]
    spam = spam_phones(reviews)
    cs = open_callers(by, pats, spam, cutoff)            # S796's own reading: the owner's closing count, and the fallback
    for c in cs:
        c["mins"] = duty_minutes(c["t0"], asof)
    a, b = window(today)
    in_duty = a <= now <= b
    closing = now >= b

    # S953: the stages follow the staff page's Incoming missed tab (today's misses + yesterday's carried), when it can be built
    lists_ok, lists_why, aw, CC, again_due, wa_due, res_skip, part = False, "", {}, None, [], [], 0, []
    stage = [dict(c, k=c["t0"].strftime("%Y-%m-%d %H:%M:%S")) for c in cs]
    if cfg_on("PORTAL_CLOCK_LISTS"):
        try:
            lists, aw, CC = staff_view(console, now, reviews)
            if lists.get("fu_ok") is False:
                part.append("follow-up list failed")
            if aw.get("failed") or lists.get("wa_ok") is False:
                part.append("WhatsApp list failed")
            again_due = [r for r in lists["tabs"].get("again") or [] if r.get("hi") and r.get("phone")]
            for ch in (aw.get("chats") or []) if not aw.get("failed") else []:
                since = ch.get("since")
                if ch.get("phone") and isinstance(since, dt.datetime) and duty_minutes(since, asof) >= wa_min:
                    wa_due.append(dict(ch, k=since.strftime("%Y-%m-%d %H:%M:%S")))
            if lists.get("carry_ok") is False:          # a part failed inside the page's builder: the stages may miss callers
                raise RuntimeError("the yesterday carry failed")
            wide = {c["phone"]: c for c in open_callers(by, pats, spam, dt.datetime.combine(yday, dt.time(0, 0)))}
            stage = []
            for r in lists["tabs"].get("missed") or []:
                c = wide.get(r.get("phone") or "")
                if c is None:
                    res_skip += 1                        # the store cannot time it: not chased here (the tab still shows it)
                    continue
                c = dict(c)
                if c["t0"] < a:                          # carried (yesterday, or before opening): today's clock, once a day --
                    last_ok = max([t for t, _d, ok_ in by.get(c["phone"], ()) if ok_], default=None)
                    again_t = [t for t, d_, ok_ in sorted(by.get(c["phone"], ())) if d_ == "In" and not ok_ and t >= a
                               and (last_ok is None or t > last_ok)]
                    if again_t:                          # -- unless he was missed again today: that miss has its own clock
                        c["mins"], c["k"] = duty_minutes(again_t[0], asof), again_t[0].strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        c["mins"], c["k"] = duty_minutes(a, asof), "C" + today.isoformat()
                else:
                    c["mins"], c["k"] = duty_minutes(c["t0"], asof), c["t0"].strftime("%Y-%m-%d %H:%M:%S")
                stage.append(c)
            stage.sort(key=lambda c: c["t0"])
            lists_ok = True
        except Exception as e:                           # noqa: BLE001
            carry_only = str(e).startswith("the yesterday carry") and CC is not None
            lists_why = "the yesterday carry" if carry_only else type(e).__name__
            stage = [dict(c, k=c["t0"].strftime("%Y-%m-%d %H:%M:%S")) for c in cs]
            res_skip = 0
            if not carry_only:                           # only the carry failed: today's Call again / WhatsApp lists still stand
                again_due, wa_due, CC = [], [], None
    res = {"ok": True, "open": len(cs), "unknown": sum(1 for c in cs if c["unknown"]), "due1": sum(1 for c in stage if c["mins"] >= t1),
           "due2": sum(1 for c in stage if c["mins"] >= t2), "asof": asof.strftime("%H:%M"), "new1": 0, "new2": 0, "closing": 0, "sent": {},
           "lists": lists_ok, "skipped": res_skip, "again_due": len(again_due), "wa_due": len(wa_due), "new_again": 0, "new_wa": 0, "to": [], "version": VERSION}
    lists_h = (("lists ok" + (" (%d untimed)" % res_skip if res_skip else "")) if lists_ok else ("lists FAILED (%s) -- S796 rule" % lists_why if lists_why else "lists off -- S796 rule"))
    if part:
        lists_h += " (" + ", ".join(part) + ")"
    if dry:
        print("DRY %s: callers not spoken to %d (unknown numbers %d); waiting 30+ duty minutes %d, 60+ %d; call again due %d; "
              "WhatsApp waiting %d; %s; judged as of %s; nothing sent, nothing written"
              % (now.strftime("%Y-%m-%d %H:%M"), res["open"], res["unknown"], res["due1"], res["due2"], res["again_due"], res["wa_due"],
                 lists_h, res["asof"]))
        return res
    lk = _lock(store)
    if lk is None:
        print("%s another run holds the clock -- this run skipped" % now.strftime("%Y-%m-%d %H:%M"))
        return {"ok": False, "why": "locked"}
    con = store_open(store)
    try:
        done = {(r[0], r[1], r[2]) for r in con.execute("SELECT phone, t0, stage FROM sent")}
        key = lambda c, st: (c["phone"], c["k"], st)     # noqa: E731
        new1 = [c for c in stage if c["mins"] >= t1 and key(c, 1) not in done] if in_duty else []
        new2 = [c for c in stage if c["mins"] >= t2 and key(c, 2) not in done] if in_duty else []
        akey = lambda r: (r["phone"], "A" + today.isoformat(), 3)       # noqa: E731  one Call again per number per day
        wkey = lambda r: (r["phone"], r["k"], 4)                        # noqa: E731  one per waiting chat
        new_a = [r for r in again_due if akey(r) not in done] if (in_duty and cfg_on("PORTAL_CLOCK_AGAIN_ON")) else []
        new_w = [r for r in wa_due if wkey(r) not in done] if (in_duty and cfg_on("PORTAL_CLOCK_WA_ON")) else []
        close_key = ("*", today.isoformat(), 9)
        do_close = closing and close_key not in done and len(cs) > 0
        p = get_pusher(pusher) if (new1 or new2 or do_close or new_a or new_w) else None
        adm = admitted() if (new1 or new2 or new_a or new_w) else None
        stamp = now.strftime("%Y-%m-%d %H:%M:%S")
        who, why = (list(STAFF), "")
        if (new_a or new_w) and CC is not None:
            try:
                who, why = on_duty(CC, now)
            except Exception:                            # noqa: BLE001  never stops the run (cold review, S953)
                who, why = list(STAFF), "duty failed"
            res["to"], res["duty"] = who, why
        nt = 0
        if new1:
            if p:
                s_, f_, n_ = send(p, STAFF, "⏰ %d call back बाकी — %d मिनट से ज़्यादा" % (len(new1), t1),
                                  names(new1) + " — अभी call back करें", landing(adm, staff_url), "cb-clock-1")
                res["sent"]["staff"], nt = (s_, f_), nt + n_
            con.executemany("INSERT OR IGNORE INTO sent(phone, t0, stage, at) VALUES(?,?,?,?)", [key(c, 1) + (stamp,) for c in new1])
        if new2:
            if p:
                s_, f_, n_ = send(p, BACKUP, ("⏰ 1 घंटा हो गया — %d call back अभी भी बाकी" % len(new2)) if t2 == 60 else
                                  ("⏰ %d मिनट हो गए — %d call back अभी भी बाकी" % (t2, len(new2))),
                                  names(new2) + " — Shavez ji, aap call karein", landing(adm, staff_url), "cb-clock-2")
                res["sent"]["backup"], nt = (s_, f_), nt + n_
            con.executemany("INSERT OR IGNORE INTO sent(phone, t0, stage, at) VALUES(?,?,?,?)", [key(c, 2) + (stamp,) for c in new2])
        if new_a:
            if p:
                s_, f_, n_ = send(p, who, "Call again due: %d" % len(new_a), row_names(new_a) + " — tap to open Call again",
                                  landing(adm, cfg("PORTAL_CLOCK_AGAIN_URL", AGAIN_URL)), "cb-clock-3")
                res["sent"]["again"], nt = (s_, f_), nt + n_
            con.executemany("INSERT OR IGNORE INTO sent(phone, t0, stage, at) VALUES(?,?,?,?)", [akey(r) + (stamp,) for r in new_a])
        if new_w:
            if p:
                s_, f_, n_ = send(p, who, "WhatsApp waiting: %d" % len(new_w),
                                  row_names(new_w) + " — waiting over %d min, tap to reply" % wa_min, landing(adm, cfg("PORTAL_CLOCK_WA_URL", WA_URL)),
                                  "cb-clock-4")
                res["sent"]["wa"], nt = (s_, f_), nt + n_
            con.executemany("INSERT OR IGNORE INTO sent(phone, t0, stage, at) VALUES(?,?,?,?)", [wkey(r) + (stamp,) for r in new_w])
        if do_close:
            if p:
                res["sent"]["owner"] = push(p, OWNER, "Callers not called back today: %d" % len(cs),
                                            "%d from unknown numbers · %d waited over an hour. Tap for the Call Console."
                                            % (res["unknown"], sum(1 for c in cs if c["mins"] >= T2)), OWNER_URL, "cb-clock-9")
            con.execute("INSERT OR IGNORE INTO sent(phone, t0, stage, at) VALUES(?,?,?,?)", close_key + (stamp,))
        if nt:
            res["sent"]["ntfy"] = nt
        res["new1"], res["new2"], res["closing"] = len(new1), len(new2), int(do_close)
        res["new_again"], res["new_wa"] = len(new_a), len(new_w)
        con.execute("INSERT INTO runs(at, open, unknown, s1, s2, closing, sent) VALUES(?,?,?,?,?,?,?)",
                    (stamp, res["open"], res["unknown"], len(new1), len(new2), int(do_close),
                     json.dumps({"sent": res["sent"], "again": len(new_a), "wa": len(new_w), "lists": lists_ok, "v": VERSION})))
        con.execute("DELETE FROM runs WHERE at < ?", ((today - dt.timedelta(days=45)).isoformat(),))
        con.execute("DELETE FROM sent WHERE at < ?", ((today - dt.timedelta(days=45)).isoformat(),))
        con.commit()
    finally:
        con.close()
        try:
            lk.close()
        except Exception:                                # noqa: BLE001
            pass
    print("%s not spoken to %d (unknown %d) · new at 30 min %d · new at 60 min %d · call again %d · WhatsApp %d · closing %d · "
          "sent %s · %s · as of %s · %.1f s"
          % (stamp, res["open"], res["unknown"], res["new1"], res["new2"], res["new_again"], res["new_wa"], res["closing"],
             res["sent"] or "-", lists_h, res["asof"], time.time() - t_start))
    return res


if __name__ == "__main__":
    run(dry="--dry" in sys.argv[1:])
