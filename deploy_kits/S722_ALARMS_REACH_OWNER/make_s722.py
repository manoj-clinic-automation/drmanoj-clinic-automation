#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_s722.py -- S722_ALARMS_REACH_OWNER (Sanjeevni session 393, 06-Nov-2026; F-1134, the owner's word 14:22 IST "alarms first").

Builds the five changed files from the live bytes by anchored edits: every anchor must stand EXACTLY ONCE and every FROM pin must be
exact, else REFUSED and nothing is written.

    python3 -B make_s722.py <dir holding the FROM files> <out dir>

The dir may hold any subset; each file present is built (the server's installer gives it the three server files, the medical PC's
delivery the two medical files).
"""
import hashlib
import os
import sys

FROM = {
    "owner_notice.py": "ca5cd4436dd85d797d7f923ee0eac163",    # /root/finance (S706)
    "reports_watch.py": "adbb21bef64c6dec63d9a603e5214cad",   # /root/finance (S702)
    "marg_door.py": "dc5c1e36d2c8bee2cd556de5c5e4f018",       # /root/finance (S480)
    "marg_push.py": "566e189e986128fa2ebb341a78b9ab65",       # medical PC D:\SendToClinic (S259)
    "marg_watch.py": "a009d2fda60aac3d0b3462f50ddec6f6",      # medical PC D:\SendToClinic (S679)
}

# ---------------------------------------------------------------------------------------------------------------- owner_notice.py
E_OWNER = [
('''Nothing that happened before the install (owner_notice.since) is announced.
''',
'''  medical_off:<last>     S722 (F-1134): nothing from the medical PC for owner_notice.medical_quiet_min minutes inside its working window
                         (09:00-20:00; Sunday 09:00-14:00) after it was heard that day -- its pusher's beat every 5 minutes, as the
                         Marg door records it in /root/marg_ingest/medical_seen.json; a PC not heard at all today is said at
                         owner_notice.medical_first_by (11:00: it is usually switched on 09:15-10:50).  Once per silence.  Nothing is
                         said before its first beat (the door writes the note for a beat only).
  medical_back:<last>    ... and when it is heard again: once nothing is waiting on it, or owner_notice.medical_back_wait_min after its
                         first beat back, with the reports it pushed since the silence began.
Nothing that happened before the install (owner_notice.since) is announced.
''', 1),
('''KIT = "S702_OWNER_REPORT_NOTICES"
''',
'''KIT = "S702_OWNER_REPORT_NOTICES"           # S722_ALARMS_REACH_OWNER adds the medical PC's silence and return (F-1134)
''', 1),
('''HAND_URL = "/finance/sanjeevni/expiry"                           # S706: a hand-change message opens the Expiry watch (its top section)
''',
'''HAND_URL = "/finance/sanjeevni/expiry"                           # S706: a hand-change message opens the Expiry watch (its top section)
SEEN_FILE = os.environ.get("S722_SEEN_FILE", "/root/marg_ingest/medical_seen.json")   # S722: written by the Marg door only
REPORT_NAMES = {"SALE_BILLWISE": "Sale report", "STOCK_CLOSING": "Closing stock", "PURCHASE_ITEMWISE": "Purchase item-wise",
                "PURCHASE_BILLWISE": "Purchase bill-wise", "STOCK_VALUATION": "Stock Valuation", "STOCK_EXPIRY": "Batch Stock",
                "ORDER_PENDING": "Order sheet", "SALE_RETURN": "Sale return", "SALT_WISE_ITEM_LIST": "Salt list",
                "CATEGORY_WISE_ITEM_LIST": "Category list", "ITEM_MASTER": "Item list", "DOCUMENT_PDF": "a PDF"}
''', 1),
('''    ("owner_notice.hand_to", "21:00", "S706 (D828): ... until this time; one found later waits for the next morning"),
)
''',
'''    ("owner_notice.hand_to", "21:00", "S706 (D828): ... until this time; one found later waits for the next morning"),
    ("owner_notice.medical_quiet_min", "20", "S722 (F-1134): nothing from the medical PC this long inside its window -- the owner is told once"),
    ("owner_notice.medical_from", "09:00", "S722 (F-1134): the medical PC's working window opens (for a PC already heard that day)"),
    ("owner_notice.medical_first_by", "11:00", "S722 (F-1134): a medical PC not heard at all today is said at this time"),
    ("owner_notice.medical_to", "20:00", "S722 (F-1134): ... and closes, Monday to Saturday"),
    ("owner_notice.medical_to_sunday", "14:00", "S722 (F-1134): ... and closes on a Sunday (the half day)"),
    ("owner_notice.medical_back_wait_min", "15", "S722 (F-1134): 'Medical PC back' waits until nothing is waiting on it, or this long after "
     "its first beat back"),
)
''', 1),
('''def collect(con, now):
    """-> (messages, errors).  Reads only.  Each part is fail-soft: one part's fault never stops the others."""
''',
'''def _s722_seen():
    """The Marg door's note of the medical PC's beat: (last beat, waiting or None, first beat after a gap) as naive IST datetimes, or None."""
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        at = dt.datetime.strptime(norm_ts(d.get("at")), "%Y-%m-%d %H:%M:%S")
    except (OSError, ValueError, TypeError, AttributeError):
        return None
    try:
        first = dt.datetime.strptime(norm_ts(d.get("first_at")), "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        first = at
    w = d.get("waiting")
    return at, (int(w) if isinstance(w, int) and w >= 0 else None), min(first, at)


def _s722_when(t, n):
    return t.strftime("%H:%M") if t.date() == n.date() else t.strftime("%d-%m %H:%M")


def _s722_span(a, b):
    m = max(0, int((b - a).total_seconds() // 60))
    return ("%d h %d min" % (m // 60, m % 60)) if m >= 60 else "%d min" % m


def _part_medical(con, now):
    """S722 (F-1134): the medical PC silent inside its working window -> 'Medical PC offline', once per silence; heard again ->
    'Medical PC back' with the reports it pushed since.  Reads the Marg door's note, owner_notice and mi_file only."""
    seen = _s722_seen()
    if seen is None:
        return []                                                 # no beat has ever come: the medical half is not installed yet
    last, waiting, first = seen
    n = now.replace(tzinfo=None)
    out = []
    off = None
    if _table(con, "owner_notice"):
        off = con.execute("SELECT key FROM owner_notice WHERE kind='medical_off' ORDER BY id DESC LIMIT 1").fetchone()
    if off is not None:
        stamp_off = str(off[0]).split(":", 1)[1]
        try:
            went = dt.datetime.strptime(stamp_off, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            went = None
        if went is not None and last > went and not con.execute("SELECT 1 FROM owner_notice WHERE key=?",
                                                                ("medical_back:%s" % stamp_off,)).fetchone():
            back = first if first > went else last                # the first beat after the silence (the door keeps it)
            wait_min = int(setting(con, "owner_notice.medical_back_wait_min") or 15)
            if waiting == 0 or n - back >= dt.timedelta(minutes=wait_min):
                rows = []
                if _table(con, "mi_file"):
                    rows = [(norm_ts(r[0]), str(r[1] or "")) for r in con.execute(
                        "SELECT received_at, type FROM mi_file WHERE source='push' AND verdict != 'REFUSED' AND received_at >= ? "
                        "ORDER BY received_at", (went.strftime("%Y-%m-%d"),)).fetchall()]
                    rows = [(t, k) for t, k in rows if t and t > stamp(went) and t <= stamp(n)]
                names = []
                for _t, k in rows:
                    nm = REPORT_NAMES.get(k, (k or "a report not recognised").replace("_", " ").lower().capitalize())
                    if nm not in names:
                        names.append(nm)
                body = "Back at %s after %s. " % (back.strftime("%H:%M"), _s722_span(went, back))
                body += ("%s delivered since: %s." % (plural(len(rows), "report"), ", ".join(names))) if rows else (
                    "No report delivered yet." if waiting else "No report was waiting on it.")
                if waiting:
                    body += " %s still waiting to be sent." % plural(waiting, "report")
                out.append(dict(key="medical_back:%s" % stamp_off, kind="medical_back", title="Medical PC back ✓", body=body))
    start = mins(setting(con, "owner_notice.medical_from"), 540)
    end = mins(setting(con, "owner_notice.medical_to_sunday" if n.weekday() == 6 else "owner_notice.medical_to"), 1200)
    m = n.hour * 60 + n.minute
    if start <= m < end:
        if last.date() == n.date() and last.hour * 60 + last.minute >= start:   # heard inside today's window
            due = n - last >= dt.timedelta(minutes=int(setting(con, "owner_notice.medical_quiet_min") or 20))
        else:                                                     # not heard today (a beat at night or before 09:00 is not "today"):
                                                                  # it is usually switched on 09:15-10:50
            due = m >= mins(setting(con, "owner_notice.medical_first_by"), 660)
        if due:
            out.append(dict(key="medical_off:%s" % stamp(last), kind="medical_off", title="Medical PC offline",
                            body="Nothing from the medical PC since %s. Reports made on it now wait there until it is back. Check that it is "
                                 "switched on and its internet works." % _s722_when(last, n)))
    return out


def collect(con, now):
    """-> (messages, errors).  Reads only.  Each part is fail-soft: one part's fault never stops the others."""
''', 1),
('''              ("phone", lambda: _part_phone(con, now)), ("hand", lambda: _part_hand(con, now, since))]
''',
'''              ("phone", lambda: _part_phone(con, now)), ("hand", lambda: _part_hand(con, now, since)),
              ("medical", lambda: _part_medical(con, now))]                     # S722 (F-1134)
''', 1),
]

# ---------------------------------------------------------------------------------------------------------------- reports_watch.py
E_WATCH = [
('''KIT = "S500_REPORT_CHECK"
''',
'''KIT = "S500_REPORT_CHECK"          # S722 (F-1134): the message goes by owner_notice's road -- the clinic app first, ntfy when no device
''', 1),
('''    url = _conf_url()
    if not url:
        return False, "NTFY_URL not set -- nothing sent"
    try:                                                         # the Request is built inside: a malformed address names no URL anywhere
''',
'''    try:                                                         # S722 (F-1134): the clinic app (Web Push) first, ntfy only when no device
        import owner_notice                                      # noqa: PLC0415
        return owner_notice.deliver(con, "reports:" + title, title, body)
    except Exception:                                            # noqa: BLE001 -- the old road below stays the fallback
        pass
    url = _conf_url()
    if not url:
        return False, "NTFY_URL not set -- nothing sent"
    try:                                                         # the Request is built inside: a malformed address names no URL anywhere
''', 1),
('''        title = "Sanjeevni morning reports %s" % _ddmm(s.get("due_day"))
''',
'''        title = "Morning reports %s" % _ddmm(s.get("due_day"))   # S722: owner_notice puts "Sanjeevni" in front
''', 1),
('''            ok, how = _send(con, "Sanjeevni morning reports - test",
                            "A test from the install of S500. This is where you will be told when a morning Marg report is wrong "
                            "twice or has not come by the hour. Nothing is wrong now.")
''',
'''            ok, how = _send(con, "Morning reports - test",
                            "A test from the install of S722. From now the morning-report alarms (a report wrong twice, or not in by "
                            "10:00) come here, to the clinic app, and you are told when the medical PC goes offline and comes back. "
                            "Nothing is wrong now.")
''', 1),
]

# ---------------------------------------------------------------------------------------------------------------- marg_door.py
E_DOOR = [
('''bp = Blueprint("marg_door", __name__)
''',
'''bp = Blueprint("marg_door", __name__)
# S722 (F-1134): the medical PC's beat -- its pusher's GET carrying X-Marg-Beat, every 5 minutes -- noted with its waiting count and the
# first beat after a gap.  owner_notice reads it to say "Medical PC offline / back".  ONLY a beat writes it (a pushed file never does: the
# old pusher must not start the messages).  Written atomically; never fails a request.
SEEN_FILE = os.environ.get("S722_SEEN_FILE", "/root/marg_ingest/medical_seen.json")
S722_GAP_S = 600                                               # a beat after this long a silence starts a new "first"


def _s722_beat(h):
    """'MEDICAL waiting=3' -> 3; a beat with no readable count -> None (still a beat)."""
    for part in str(h or "").split():
        if part.startswith("waiting="):
            v = part[8:]
            return int(v) if v.isascii() and v.isdigit() and len(v) < 7 else None
    return None


def _s722_seen(header):
    try:
        import datetime as _dt                                 # noqa: PLC0415
        import json as _json                                   # noqa: PLC0415
        now = _dt.datetime.utcnow() + _dt.timedelta(hours=5, minutes=30)
        at = now.strftime("%Y-%m-%dT%H:%M:%S+05:30")
        first = at
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as fh:
                old = _json.load(fh)
            prev = _dt.datetime.strptime(str(old.get("at"))[:19], "%Y-%m-%dT%H:%M:%S")
            if (now - prev).total_seconds() < S722_GAP_S and old.get("first_at"):
                first = str(old.get("first_at"))
        except Exception:                                      # noqa: BLE001 -- no note yet, or a spoiled one: this beat is the first
            pass
        tmp = "%s.%d.part" % (SEEN_FILE, os.getpid())
        with open(tmp, "w", encoding="utf-8") as fh:
            _json.dump({"at": at, "first_at": first, "waiting": _s722_beat(header), "how": "beat"}, fh)
        os.replace(tmp, SEEN_FILE)
    except Exception:                                          # noqa: BLE001
        pass
''', 1),
('''    if request.method == "GET":
        c = MT.counts()
''',
'''    if request.method == "GET":
        if str(request.headers.get("X-Marg-Beat") or "").startswith("MEDICAL"):   # S722: the medical PC's beat
            _s722_seen(request.headers.get("X-Marg-Beat"))
        c = MT.counts()
''', 1),
]

# ---------------------------------------------------------------------------------------------------------------- marg_push.py (medical PC)
E_PUSH = [
('''OFF SWITCH (S259) -- D:\\SendToClinic\\_off\\ALL_OFF.txt  or  MARG_PUSH_OFF.txt. Read at the top of
    every pass, so switching off or back on needs no restart. Capture is NOT stopped by it.
"""
''',
'''OFF SWITCH (S259) -- D:\\SendToClinic\\_off\\ALL_OFF.txt  or  MARG_PUSH_OFF.txt. Read at the top of
    every pass, so switching off or back on needs no restart. Capture is NOT stopped by it.

THE BEAT (S722, F-1134) -- every BEAT_EVERY seconds the thread asks the server "are you there?" (the --probe GET) with the header
    X-Marg-Beat: MEDICAL waiting=<n>, so the server knows this PC can reach it even when there is nothing to send, and tells the owner
    "Medical PC offline" after 20 minutes of silence in the working day and "Medical PC back" when it is heard again. No file, no
    content, no new key. The switch stops the beat too. A beat that cannot go is logged only when the state changes.
"""
''', 1),
('''MAX_BYTES = 25 * 1024 * 1024
''',
'''MAX_BYTES = 25 * 1024 * 1024
BEAT_EVERY = 300             # S722: seconds between beats
''', 1),
('''def probe(tok=None):
    tok = tok if tok is not None else token()
    if not tok:
        return 0, {"status": "NO_KEY", "message": "token.txt is missing or empty"}
    req = urllib.request.Request(URL, method="GET")
    req.add_header("X-Finance-Marg", tok)
''',
'''def beat_text(waiting):
    """S722: the beat header's value -- the PC's name and how many captures wait to be sent; nothing else."""
    try:
        n = max(0, int(waiting or 0))
    except (TypeError, ValueError):
        n = 0
    return "MEDICAL waiting=%d" % n


def probe(tok=None, beat=None):
    tok = tok if tok is not None else token()
    if not tok:
        return 0, {"status": "NO_KEY", "message": "token.txt is missing or empty"}
    req = urllib.request.Request(URL, method="GET")
    req.add_header("X-Finance-Marg", tok)
    if beat:
        req.add_header("X-Marg-Beat", beat)
''', 1),
('''    time.sleep(5)                        # let capture settle after a restart before any network
    was_off = False
    while True:
''',
'''    time.sleep(5)                        # let capture settle after a restart before any network
    was_off = False
    last_beat = 0.0                      # S722: the first beat goes on the first pass
    beat_ok = None
    while True:
''', 1),
('''        except Exception as e:           # noqa: BLE001  -- a pusher fault is never a capture fault
            log("pass failed: %s: %s" % (e.__class__.__name__, str(e)[:160]))
        if wake is not None:
''',
'''        except Exception as e:           # noqa: BLE001  -- a pusher fault is never a capture fault
            log("pass failed: %s: %s" % (e.__class__.__name__, str(e)[:160]))
        try:                             # S722 (F-1134): the beat -- after the pass, so a report never waits for it
            if not off and time.time() - last_beat >= BEAT_EVERY:
                last_beat = time.time()
                code, _ans = probe(beat=beat_text((state_read().get("last") or {}).get("waiting")))
                if (code == 200) != beat_ok:
                    beat_ok = code == 200
                    log("beat: %s" % ("the server answers" if beat_ok else "the server does not answer (%s)" % (code or "no reach")))
        except Exception as e:           # noqa: BLE001  -- a beat fault is never a push or capture fault
            log("beat failed: %s" % e.__class__.__name__)
        if wake is not None:
''', 1),
('''    ck("ALL_OFF switches the pusher off too", off_marker(od) is not None)
''',
'''    ck("ALL_OFF switches the pusher off too", off_marker(od) is not None)
    ck("S722: the beat carries the PC's name and the waiting count, nothing else",
       beat_text(3) == "MEDICAL waiting=3" and beat_text(None) == "MEDICAL waiting=0" and beat_text("x") == "MEDICAL waiting=0")
    ck("S722: one beat every five minutes", BEAT_EVERY == 300)
''', 1),
]

# ---------------------------------------------------------------------------------------------------------------- marg_watch.py (medical PC)
# Only the start line: the agent restarts the watcher for a marg_watch.py change only (RESTART_FOR), which loads the new marg_push.
E_MWATCH = [
('''    out("marg_watch S679 starting -- text reader %s, text route %s, refusal notes on (a note that cannot go waits and is tried again), "
''',
'''    out("marg_watch S679+S722 starting -- the pusher beats every 5 min (S722) -- text reader %s, text route %s, refusal notes on (a note that cannot go waits and is tried again), "
''', 1),
]

EDITS = {"owner_notice.py": E_OWNER, "reports_watch.py": E_WATCH, "marg_door.py": E_DOOR, "marg_push.py": E_PUSH,
         "marg_watch.py": E_MWATCH}


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(name, raw):
    if md5(raw) != FROM[name]:
        raise SystemExit("make_s722: REFUSED -- %s is %s, not the FROM %s (nothing written)" % (name, md5(raw)[:8], FROM[name][:8]))
    s = raw.decode("utf-8")
    for i, (old, new, want) in enumerate(EDITS[name], 1):
        n = s.count(old)
        if n != want:
            raise SystemExit("make_s722: REFUSED -- %s edit %d: the anchor stands %d time(s), not %d (nothing written)" % (name, i, n, want))
        s = s.replace(old, new)
    return s.encode("utf-8")


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    src, out = argv
    built = {}
    for name in FROM:
        p = os.path.join(src, name)
        if os.path.isfile(p):
            with open(p, "rb") as fh:
                built[name] = build(name, fh.read())
    if not built:
        raise SystemExit("make_s722: REFUSED -- none of the five FROM files is in %s" % src)
    os.makedirs(out, exist_ok=True)
    for name, b in built.items():
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(b)
        print("make_s722: %s %s -> %s (%d edits)" % (name, FROM[name][:8], md5(b)[:8], len(EDITS[name])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
