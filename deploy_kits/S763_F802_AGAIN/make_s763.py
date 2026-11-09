#!/usr/bin/env python3
"""make_s763.py -- kit S763_F802_AGAIN (S417, 09-Nov-2026). F-802's permanent fix (D867 / D868 / D879).

Builds the four changed files from the LIVE bytes (asserted by full md5 -- F-472) with anchored edits, each anchor found exactly once:
  medical PC  D:\\SendToClinic\\marg_watch.py   df7736e9 -> (out)   a repeat export is told to the server as "received again"
  server      /root/finance/marg_door.py        565ad9c8 -> (out)   X-Marg-Note: again -> one mi_receipt row, answer AGAIN, same as <stamp>
  server      /root/finance/amir_day.py         c86bb8e5 -> (out)   the salt duty reads the newest receipt, first or again
  server      /root/finance/reports_tile.py     f44fe768 -> (out)   the salt row reads the same
  repository  claude_code_briefs/DUTY_MAP.json  78b5f07e -> (out)   amir.salt_list due_sql = amir_day's, byte for byte; v21
Not changed: /root/marg_ingest/marg_take.py (5cad2d24), D:\\SendToClinic\\marg_push.py (3f5ed144) -- read only.

usage: python make_s763.py <src_dir> <out_dir>
"""
import hashlib
import json
import os
import sys

FROM = {
    "marg_watch.py": "df7736e99abfd13f480d61ab4b5320d0",
    "marg_door.py": "565ad9c811ecb74a29340abd73c26f12",
    "amir_day.py": "c86bb8e533a1084c62bd2a2dfc8f7aef",
    "reports_tile.py": "f44fe768beed07069968113a3e55259d",
    "DUTY_MAP.json": "78b5f07ef7cdd48b1a76d78db52107fc",
}

# ======================================================================================================================================
# marg_door.py
# ======================================================================================================================================
DOOR = [
    (
        '''    if str(request.headers.get("X-Marg-Note") or "").strip().lower() == "refused":   # S454 P4 (10.2): the PC's note, before take()
        return _s454_pc_note(MT)
''',
        '''    if str(request.headers.get("X-Marg-Note") or "").strip().lower() == "refused":   # S454 P4 (10.2): the PC's note, before take()
        return _s454_pc_note(MT)
    if str(request.headers.get("X-Marg-Note") or "").strip().lower() == "again":     # S763 (F-802): the same export, received again
        return _s763_again(MT)
'''),
    (
        '''# ---- S454 part 4 end -------------------------------------------------------------------------------------------------------------------
''',
        '''# ---- S454 part 4 end -------------------------------------------------------------------------------------------------------------------


# ==========================================================================================================================================
# S763_F802_AGAIN (09-Nov-2026, S417; F-802, D867 / D868 / D879): THE SAME EXPORT, RECEIVED AGAIN. When the staff export a Marg report whose
# bytes are the same as one this door already holds, take() answers ALREADY and writes nothing, and until S763 the medical PC did not even
# send it. An export made after a salt tick when Marg's list had not changed therefore never moved the salt duty, and the duty stayed open for
# ever. The medical PC's watcher now sends a re-receipt -- {name, md5, at, from}, no content -- with header X-Marg-Note: again, ONLY when
# the file was exported after the capture it repeats. This door:
#   * writes ONE row in mi_receipt (the record: md5, received_at, name, exported_at, source) -- nothing reads it to decide anything;
#   * when the report it repeats is VERIFIED, moves the setting 'mi_again:<TYPE>' forward to the moment the PC says it was EXPORTED (never
#     later than now, never backwards) -- the salt duty reads this (amir_day._SALT_LAST, reports_tile._salt_row, DUTY_MAP amir.salt_list).
#     The setting table is there on every copy of finance.db, so the duty map can arrive before or after this file without a missing table;
#   * never touches mi_file (its received_at stays the FIRST receipt, which three hundred readers mean);
#   * answers AGAIN "received again, same as <stamp>"; an md5 it does not hold is UNKNOWN, nothing written (the PC tries again later);
#     a locked database is BUSY (503; the PC tries again). A second re-receipt of one md5 within a minute adds no second record row.
# ==========================================================================================================================================
S763_DDL = ("CREATE TABLE IF NOT EXISTS mi_receipt (id INTEGER PRIMARY KEY, md5 TEXT NOT NULL, received_at TEXT NOT NULL, "
            "name TEXT NOT NULL DEFAULT '', exported_at TEXT NOT NULL DEFAULT '', source TEXT NOT NULL DEFAULT '')")
S763_IDX = "CREATE INDEX IF NOT EXISTS mi_receipt_md5 ON mi_receipt (md5)"
S763_KEY = "mi_again:"                                                 # + the report's type, e.g. mi_again:SALT_WISE_ITEM_LIST
_S763_KEYS = ("name", "md5", "at", "from")
S763_SAME_S = 60
S763_AHEAD_S = 600                                                     # a PC export time further ahead of this server's clock is not believed


def _s763_again(MT):
    n = request.content_length
    if n is None or n > 4096:
        return jsonify(ok=False, status="REFUSED", message="a re-receipt is a small JSON with its length -- nothing written"), 400
    if request.files:
        return jsonify(ok=False, status="REFUSED", message="a re-receipt carries no file content -- nothing written"), 400
    b = request.get_json(silent=True)
    if not isinstance(b, dict) or [k for k in b if k not in _S763_KEYS]:
        return jsonify(ok=False, status="REFUSED", message="a re-receipt is {name, md5, at, from} and nothing else -- nothing written"), 400
    md5 = str(b.get("md5") or "").strip().lower()
    if len(md5) != 32 or any(c not in "0123456789abcdef" for c in md5):
        return jsonify(ok=False, status="REFUSED", message="a re-receipt needs the report's md5 -- nothing written"), 400
    name = MT.safe_name(str(b.get("name") or ""))[:120]
    at = " ".join(str(b.get("at") or "").split())[:19]
    import re as _re                                                    # noqa: PLC0415
    import sqlite3 as _sq                                               # noqa: PLC0415
    from datetime import timedelta                                      # noqa: PLC0415
    MI = MT.MI
    now = MI.now_ist()
    now_s = now.strftime("%Y-%m-%d %H:%M:%S")
    at_s = at.replace("T", " ") if _re.match(r"^\\d{4}-\\d\\d-\\d\\d[T ]\\d\\d:\\d\\d:\\d\\d$", at) else ""
    ahead_s = (now + timedelta(seconds=S763_AHEAD_S)).strftime("%Y-%m-%d %H:%M:%S")
    eff = min(at_s, now_s) if (at_s and at_s <= ahead_s) else ""         # the export's own moment; no moment, or a PC clock running
    try:
        con = MT._connect(MI.DB_DEFAULT)
        try:
            f = con.execute("SELECT type, verdict, stamp, received_at FROM mi_file WHERE md5=?", (md5,)).fetchone()
            if not f:
                return jsonify(ok=True, status="UNKNOWN", md5=md5,
                               message="the server holds no report with this md5 -- nothing written; send the report itself"), 200
            typ, verdict, stamp, first = (f[0] or ""), (f[1] or ""), (f[2] or ""), (f[3] or "")
            con.execute(S763_DDL)
            con.execute(S763_IDX)
            cut = (now - timedelta(seconds=S763_SAME_S)).isoformat()
            dup = con.execute("SELECT 1 FROM mi_receipt WHERE md5=? AND received_at >= ?", (md5, cut)).fetchone()
            if not dup:
                con.execute("INSERT INTO mi_receipt (md5, received_at, name, exported_at, source) VALUES (?,?,?,?,?)",
                            (md5, now.isoformat(), name, at, "push"))
            counted = bool(verdict == "VERIFIED" and typ and eff)          # ahead of ours by more than 10 min: recorded, never counted
            if counted:
                con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
                con.execute("INSERT OR IGNORE INTO setting (key, value) VALUES (?, '')", (S763_KEY + typ,))
                con.execute("UPDATE setting SET value=? WHERE key=? AND (value IS NULL OR value < ?)", (eff, S763_KEY + typ, eff))
            con.commit()
        finally:
            con.close()
    except _sq.OperationalError as e:
        return jsonify(ok=False, status="BUSY", md5=md5, message="the database is busy (%s) -- try again" % str(e)[:60]), 503
    return jsonify(ok=True, status="AGAIN", md5=md5, type=typ, verdict=verdict, stamp=stamp, first=first, recorded=not dup,
                   counted=counted, exported=eff,
                   message="received again, same as %s" % (stamp or first[:19] or "an earlier export")), 200
# ---- S763 end -------------------------------------------------------------------------------------------------------------------------
'''),
]

# ======================================================================================================================================
# amir_day.py
# ======================================================================================================================================
SALT_LAST_OLD = ('''_SALT_LAST = ("SELECT MAX(substr(replace(received_at,'T',' '),1,19)) FROM mi_file "
              "WHERE type='SALT_WISE_ITEM_LIST' AND verdict='VERIFIED'")
''')
AMIR = [
    (
        SALT_LAST_OLD,
        '''_SALT_LAST_S444 = ("SELECT MAX(substr(replace(received_at,'T',' '),1,19)) FROM mi_file "
                   "WHERE type='SALT_WISE_ITEM_LIST' AND verdict='VERIFIED'")
# S763 (F-802, D879): the newest moment the server has a verified salt list for -- its first receipt (mi_file), or the moment the very same
# bytes were EXPORTED AGAIN (setting 'mi_again:SALT_WISE_ITEM_LIST', moved forward only by marg_door._s763_again). mi_file is never moved.
_SALT_LAST = ("SELECT MAX(t) FROM (SELECT substr(replace(received_at,'T',' '),1,19) AS t FROM mi_file "
              "WHERE type='SALT_WISE_ITEM_LIST' AND verdict='VERIFIED' UNION ALL "
              "SELECT substr(replace(value,'T',' '),1,19) AS t FROM setting WHERE key='mi_again:SALT_WISE_ITEM_LIST' AND value <> '')")


def _salt_due(last):
    return ("WITH l(t) AS (" + last + ") SELECT COUNT(*) AS n, MIN(substr(replace(s.done_at,'T',' '),1,19)) AS since "
            "FROM purchase_salt_task s, l WHERE COALESCE(s.done,0) = 1 AND s.done_at IS NOT NULL AND s.done_at <> '' "
            "AND (l.t IS NULL OR substr(replace(s.done_at,'T',' '),1,19) > l.t)")


_SALT_DUE_S444 = _salt_due(_SALT_LAST_S444)                              # S763: a copy with no setting table is read as before
'''),
    (
        '''    "amir.salt_list": ("WITH l(t) AS (" + _SALT_LAST + ") SELECT COUNT(*) AS n, MIN(substr(replace(s.done_at,'T',' '),1,19)) AS since "
                       "FROM purchase_salt_task s, l WHERE COALESCE(s.done,0) = 1 AND s.done_at IS NOT NULL AND s.done_at <> '' "
                       "AND (l.t IS NULL OR substr(replace(s.done_at,'T',' '),1,19) > l.t)"),
''',
        '''    "amir.salt_list": _salt_due(_SALT_LAST),                            # S763 (F-802): the same list exported again counts
'''),
    (
        '''    try:
        r = cx.execute(_SALT_LAST).fetchone()
        out["last_list"] = r[0] if r else None
        r = cx.execute(DUTY_SQL["amir.salt_list"]).fetchone()
''',
        '''    try:
        again = _table_exists(cx, "setting")                                # S763: every real copy has it; a bare test db may not
        r = cx.execute(_SALT_LAST if again else _SALT_LAST_S444).fetchone()
        out["last_list"] = r[0] if r else None
        r = cx.execute(DUTY_SQL["amir.salt_list"] if again else _SALT_DUE_S444).fetchone()
'''),
]

# ======================================================================================================================================
# reports_tile.py
# ======================================================================================================================================
TILE = [
    (
        '''    if oks:
        last_ok = max(_norm_ts(r.get("received_at")) for r in oks)
    newest_tick = ""
''',
        '''    if oks:
        last_ok = max(_norm_ts(r.get("received_at")) for r in oks)
    last_seen = last_ok                                       # S763 (F-802): the same list exported again counts as received
    if last_ok and _table_exists(cx, "setting"):
        r = cx.execute("SELECT value AS t FROM setting WHERE key='mi_again:SALT_WISE_ITEM_LIST' AND value <> ''").fetchone()
        if r and r["t"]:
            last_seen = max(last_seen, _norm_ts(r["t"]))
    newest_tick = ""
'''),
    (
        '''    due = bool(newest_tick) and (not last_ok or newest_tick > last_ok)
''',
        '''    due = bool(newest_tick) and (not last_seen or newest_tick > last_seen)
'''),
    (
        '''            since = (last_ok or newest_tick)[:10]
''',
        '''            since = (last_seen or newest_tick)[:10]
'''),
]

# ======================================================================================================================================
# marg_watch.py (the medical PC)
# ======================================================================================================================================
WATCH = [
    (
        '''TXT_SEEN = set()        # md5s of text already judged this run -- converted, or not ours
''',
        '''TXT_SEEN = set()        # md5s of text already judged this run -- converted, or not ours
TXT_DIGEST = {}         # S763 (F-802): md5 of a text -> md5 of the report it made, once that report is captured
XLS_STAT = {}           # S763 (F-802): an Excel export already captured -> (size, mtime) when last judged; judged again only when it changes
'''),
    (
        '''    if tmd5 in TXT_SEEN:
        if stat_key:
            TXT_STAT[path] = stat_key
        return False
''',
        '''    if tmd5 in TXT_SEEN:
        if stat_key:
            TXT_STAT[path] = stat_key
        if tmd5 in TXT_DIGEST:                  # S763 (F-802): the same report again -- said; the server told if it was exported again
            TXT_VERDICT[path] = (time.time(), _again_or_hold(path, TXT_DIGEST[tmd5], spool, out))
        elif path not in TXT_VERDICT:
            TXT_VERDICT[path] = (time.time(), "the same bytes as a text judged earlier -- nothing sent")
        return False
'''),
    (
        '''    if digest in captured:
        TXT_VERDICT.setdefault(path, (time.time(), "already taken earlier (the same report, byte for byte)"))
        if not TXT_VERDICT[path][1].startswith("TAKEN"):
            TXT_VERDICT[path] = (time.time(), "already taken earlier (the same report, byte for byte)")
        return False
''',
        '''    if digest in captured:                      # S763 (F-802): said; the server told if it was exported after the capture it repeats
        TXT_DIGEST[tmd5] = digest
        TXT_VERDICT[path] = (time.time(), _again_or_hold(path, digest, spool, out))
        return False
'''),
    (
        '''    captured.add(digest)
    TXT_VERDICT[path] = (time.time(), "TAKEN -> %s" % os.path.basename(dest))
''',
        '''    captured.add(digest)
    TXT_DIGEST[tmd5] = digest                   # S763: the report these bytes made, for when they come again
    TXT_VERDICT[path] = (time.time(), "TAKEN -> %s" % os.path.basename(dest))
'''),
    (
        '''CENSUS_EVERY_S = 600
CENSUS_DAYS = 3
''',
        '''# ------------------------------------------------------------------ S763 (F-802): the same export, received again
# Until S763 a text whose bytes this run had judged already returned without a word (TXT_SEEN), and one whose report was already in the
# spool said "already taken earlier" and sent nothing. An export made after a salt tick when Marg's list had not changed never reached the
# server, and its duty stayed open for ever. Now an export made AFTER the capture it repeats is told to the server as a re-receipt --
# {name, md5, at, from}, no content, header X-Marg-Note: again -- kept first as _captured_txt\\again\\<stamp>__<md5>.json and sent by a
# thread (a waiting one is tried again at every start and every census). A file that is only SEEN again -- a restart reading what was
# already taken -- was not exported again: its own time is not after the capture, and nothing is sent. The first receipt's time on the
# server is never moved. Rule (F-802): a capture that decides not to send says so, where the sender will look -- the log and the census.
AGAIN_SINK = None       # the selftest / walk sets a list here: re-receipts are collected there and never sent
AGAIN_DIR = "again"
AGAIN_SLACK_S = 2       # an export's own time must be this much after its capture to count as exported again
AGAIN_LOCK = threading.Lock()
AGAIN_BUSY = []         # one sender at a time
AGAIN_SAID = {}         # stem -> the last reason it waits, said once


def _again_dir(spool):
    return os.path.join(os.path.dirname(os.path.abspath(spool)), "_captured_txt", AGAIN_DIR)


def _spool_of(spool, digest):
    """(name, mtime) of the newest capture in the spool whose bytes are DIGEST, or (None, None). A text's capture is written fresh
    (its time is the capture's); an Excel capture is a copy2 (its time is the export's own) -- either way not after the export it is."""
    found = (None, None)
    try:
        names = sorted(os.listdir(spool))
    except OSError:
        return found
    tail = ("__%s" % digest[:8]).lower()
    for n in names:
        stem, ext = os.path.splitext(n)
        if not stem.lower().endswith(tail) or ext.lower() not in (".xls", ".xlsx", ".pdf"):
            continue
        p = os.path.join(spool, n)
        try:
            with open(p, "rb") as fh:
                if hashlib.md5(fh.read()).hexdigest() != digest:
                    continue
            found = (n, os.path.getmtime(p))
        except OSError:
            continue
    return found


def _again_or_hold(path, digest, spool, out):
    """S763: a TEXT that made a report already captured -- while the text reader is on hold nothing is told on its strength."""
    if not txt_live():
        return "same as an earlier export -- the text reader is on hold; nothing sent"
    return again_note(path, digest, spool, out)


def again_note(path, digest, spool, out):
    """S763: PATH made a report already captured (DIGEST). Says so; keeps a re-receipt for the server when PATH was exported after
    that capture. Returns the census verdict. Never raises: capture never fails for a re-receipt."""
    base = os.path.basename(path)
    try:
        parts = [x.lower() for x in re.split(r"[\\\\/]", os.path.abspath(path))]
        if "_captured_txt" in parts:                            # a copy this PC KEPT (a refused text offered again) is no export
            return "same as an earlier export -- a copy kept on this PC, not an export; nothing sent"
        name, cap_t = _spool_of(spool, digest)
        if not name:
            out("  = SAME %s (text) -- the same report as an earlier export, but that capture is not in the spool; nothing sent" % base)
            return "same as an earlier export (that capture is not in the spool) -- nothing sent"
        try:
            exp_t = os.path.getmtime(path)
        except OSError:
            return "same as an earlier export (%s)" % name
        if exp_t <= cap_t + AGAIN_SLACK_S:
            return "same as an earlier export (%s) -- the file it was taken from; nothing to send" % name
        at = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(exp_t))
        d = _again_dir(spool)
        os.makedirs(d, exist_ok=True)
        stem = "%s__%s" % (time.strftime("%Y%m%d-%H%M%S", time.localtime(exp_t)), digest)
        if not any(os.path.exists(os.path.join(d, stem + e)) for e in (".json", ".sent", ".gone")):
            p = os.path.join(d, stem + ".json")
            with open(p + ".part", "w", encoding="utf-8") as fh:
                json.dump({"name": name if name.startswith("MEDICAL__") else "MEDICAL__" + name, "md5": digest, "at": at,
                           "from": base[:120]}, fh)
            os.replace(p + ".part", p)
            out("  = AGAIN %s (text) -- exported again %s, the same report as %s; the server is told (received again)"
                % (base, at.replace("T", " ")[:16], name))
        again_try(spool, out)
        return "same as an earlier export (%s) -- exported again %s; re-receipt for the server (see the log)" \\
            % (name, at.replace("T", " ")[:16])
    except Exception as ex:                                     # noqa: BLE001
        out("  ! AGAIN %s: %s -- the re-receipt was not kept" % (base, ex.__class__.__name__))
        return "same as an earlier export -- the re-receipt could not be kept (%s)" % ex.__class__.__name__


def _again_send(note):
    """ONE attempt. ("sent", answer-dict) | ("refused", why) | ("wait", why)."""
    try:
        import marg_push as MP
    except Exception as ex:                                     # noqa: BLE001
        return "wait", "marg_push.py is not here (%s)" % ex.__class__.__name__
    try:
        off = MP.off_marker()
        if off:
            return "wait", "sending is OFF (%s)" % os.path.basename(off)
        tok = MP.token()
        if not tok:
            return "wait", "no key in token.txt"
        req = urllib.request.Request(MP.URL, data=json.dumps(note).encode("utf-8"), method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("X-Finance-Marg", tok)
        req.add_header("X-Marg-Note", "again")
        try:
            with urllib.request.urlopen(req, timeout=30, context=MP._ctx()) as r:
                js = json.loads(r.read().decode("utf-8", "replace") or "{}")
        except urllib.error.HTTPError as e:
            if e.code in NOTE_FINAL:
                return "refused", "HTTP %s" % e.code
            return "wait", "the server answered HTTP %s" % e.code
        except ValueError:
            return "wait", "the answer was not the server's own (not JSON)"
        except Exception:                                       # noqa: BLE001 -- a dead line: tried again at the next census
            return "wait", "the server could not be reached"
        if not isinstance(js, dict):
            return "wait", "the answer was not the server's own"
        return "sent", js
    except Exception as ex:                                     # noqa: BLE001
        return "wait", ex.__class__.__name__


def _again_mark(p, ext, why):
    stem = p[:-len(".json")]
    try:
        with open(p, encoding="utf-8") as fh:
            body = fh.read()
    except OSError:
        body = ""
    with open(stem + ext + ".part", "w", encoding="utf-8") as fh:
        fh.write("%s\\n%s\\n%s\\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), why, body))
    os.replace(stem + ext + ".part", stem + ext)
    try:
        os.remove(p)
    except OSError:
        pass


def _again_run(spool, out):
    d = _again_dir(spool)
    tried = set()
    try:
        while True:
            try:
                todo = [n for n in sorted(os.listdir(d)) if n.endswith(".json") and n not in tried]
            except OSError:
                return
            if not todo:
                return
            for n in todo:
                tried.add(n)
                p = os.path.join(d, n)
                stem = n[:-len(".json")]
                try:
                    age = time.time() - os.path.getmtime(p)
                except OSError:
                    continue
                try:
                    with open(p, encoding="utf-8") as fh:
                        note = json.load(fh)
                    if not isinstance(note, dict):
                        raise ValueError("not a re-receipt")
                except (OSError, ValueError):
                    if age > CENSUS_DAYS * 86400:
                        _again_mark(p, ".gone", "unreadable and older than %d days" % CENSUS_DAYS)
                    continue
                if AGAIN_SINK is not None:
                    AGAIN_SINK.append(dict(note))
                    _again_mark(p, ".sent", "collected by the selftest -- nothing left the PC")
                    continue
                what, ans = _again_send(note)
                st = str(ans.get("status")) if what == "sent" else ""
                if st == "AGAIN":
                    _again_mark(p, ".sent", "the server answered AGAIN -- %s" % ans.get("message", ""))
                    out("  again: the server has it -- %s (%s)" % (ans.get("message", ""), note.get("from", "")))
                    AGAIN_SAID.pop(stem, None)
                    continue
                if what == "refused" or (what == "sent" and st != "UNKNOWN"):
                    why = ans if what == "refused" else st
                    _again_mark(p, ".gone", "the server would not take it (%s) -- not tried again" % why)
                    out("  again: the server would not take the re-receipt of %s (%s) -- not tried again" % (note.get("from", ""), why))
                    AGAIN_SAID.pop(stem, None)
                    continue
                why = "the server does not hold that report yet" if st == "UNKNOWN" else ans
                if age > CENSUS_DAYS * 86400:
                    _again_mark(p, ".gone", "expired -- older than %d days and never taken (%s)" % (CENSUS_DAYS, why))
                    out("  again: EXPIRED, never taken -- the re-receipt of %s (%s)" % (note.get("from", ""), why))
                    AGAIN_SAID.pop(stem, None)
                    continue
                if AGAIN_SAID.get(stem) != why:
                    AGAIN_SAID[stem] = why
                    out("  again: %s -- the re-receipt of %s waits; tried again at every census" % (why, note.get("from", "")))
                if what == "wait":
                    return                                      # the line, the switch or the key said: not now
    except Exception as ex:                                     # noqa: BLE001 -- capture never fails for a re-receipt
        out("  again: %s -- the re-receipts wait" % ex.__class__.__name__)
    finally:
        with AGAIN_LOCK:
            del AGAIN_BUSY[:]


def again_try(spool, out):
    """Send the waiting re-receipts -- on a thread, one sender at a time (inline in the selftest)."""
    try:
        if not os.path.isdir(_again_dir(spool)):
            return 0
        with AGAIN_LOCK:
            if AGAIN_BUSY:
                return 0
            AGAIN_BUSY.append(1)
        if AGAIN_SINK is not None:
            _again_run(spool, out)
            return 1
        threading.Thread(target=_again_run, args=(spool, out), daemon=True, name="again_note").start()
        return 1
    except Exception as ex:                                     # noqa: BLE001
        with AGAIN_LOCK:
            del AGAIN_BUSY[:]
        out("  again: could not start (%s) -- the re-receipts wait" % ex.__class__.__name__)
        return 0


CENSUS_EVERY_S = 600
CENSUS_DAYS = 3
'''),
    (
        '''    notes_try(spool, out)               # S454 P4C: every waiting note, at every start, after the retry
''',
        '''    notes_try(spool, out)               # S454 P4C: every waiting note, at every start, after the retry
    again_try(spool, out)               # S763 (F-802): every waiting re-receipt, at every start
'''),
    (
        '''            notes_try(spool, out)                                 # S454 P4C: every waiting note, at every census
''',
        '''            notes_try(spool, out)                                 # S454 P4C: every waiting note, at every census
            again_try(spool, out)                                 # S763 (F-802): every waiting re-receipt, at every census
'''),
    (
        '''    out("marg_watch S679+S722 starting -- the pusher beats every 5 min (S722) -- text reader %s, text route %s, refusal notes on (a note that cannot go waits and is tried again), "
        "a reader change offers the refused texts again"
''',
        '''    out("marg_watch S679+S722+S763 starting -- the pusher beats every 5 min (S722) -- text reader %s, text route %s, refusal notes on (a note that cannot go waits and is tried again), "
        "a reader change offers the refused texts again, a repeat export is told to the server as received again (S763)"
'''),
    (
        '''        if got or str(TXT_VERDICT.get(p, (0, ""))[1]).startswith(("TAKEN", "already taken", "HELD")):
''',
        '''        if got or str(TXT_VERDICT.get(p, (0, ""))[1]).startswith(("TAKEN", "already taken", "HELD", "same as an earlier export")):
'''),
    (
        '''    if digest in captured:
        return False
    try:
        os.makedirs(spool, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        slot = os.path.splitext(os.path.basename(path))[0]
''',
        '''    if digest in captured:                      # S763 (F-802): an Excel export already captured -- judged once per change of the file;
        try:                                    # a re-receipt is kept when it was exported after its capture
            st = os.stat(path)
            key = (st.st_size, st.st_mtime)
        except OSError:
            key = None
        if key and XLS_STAT.get(path) != key:
            XLS_STAT[path] = key
            again_note(path, digest, spool, out)
        return False
    try:
        os.makedirs(spool, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        slot = os.path.splitext(os.path.basename(path))[0]
'''),
    (
        '''    global NOTE_SINK, _from_medical
    NOTE_SINK = []                                              # S454: notes are collected, never sent, in the selftest
''',
        '''    global NOTE_SINK, _from_medical, AGAIN_SINK
    NOTE_SINK = []                                              # S454: notes are collected, never sent, in the selftest
    AGAIN_SINK = []                                             # S763: re-receipts too
'''),
    (
        '''    NOTE_SINK = None
    _from_medical = _from_medical_was
''',
        '''    NOTE_SINK = None
    AGAIN_SINK = None
    _from_medical = _from_medical_was
'''),
]

# ======================================================================================================================================
# DUTY_MAP.json -- text edits so the file keeps its own layout
# ======================================================================================================================================
OLD_SALT_DUE = ("WITH l(t) AS (SELECT MAX(substr(replace(received_at,'T',' '),1,19)) FROM mi_file WHERE type='SALT_WISE_ITEM_LIST' AND "
                "verdict='VERIFIED') SELECT COUNT(*) AS n, MIN(substr(replace(s.done_at,'T',' '),1,19)) AS since FROM purchase_salt_task s, l "
                "WHERE COALESCE(s.done,0) = 1 AND s.done_at IS NOT NULL AND s.done_at <> '' AND (l.t IS NULL OR "
                "substr(replace(s.done_at,'T',' '),1,19) > l.t)")


def new_salt_due():
    last = ("SELECT MAX(t) FROM (SELECT substr(replace(received_at,'T',' '),1,19) AS t FROM mi_file "
            "WHERE type='SALT_WISE_ITEM_LIST' AND verdict='VERIFIED' UNION ALL "
            "SELECT substr(replace(value,'T',' '),1,19) AS t FROM setting WHERE key='mi_again:SALT_WISE_ITEM_LIST' AND value <> '')")
    return ("WITH l(t) AS (" + last + ") SELECT COUNT(*) AS n, MIN(substr(replace(s.done_at,'T',' '),1,19)) AS since "
            "FROM purchase_salt_task s, l WHERE COALESCE(s.done,0) = 1 AND s.done_at IS NOT NULL AND s.done_at <> '' "
            "AND (l.t IS NULL OR substr(replace(s.done_at,'T',' '),1,19) > l.t)")


MAP = [
    ('"due_sql": "%s"' % OLD_SALT_DUE, '"due_sql": "%s"' % new_salt_due()),
    ('"version": 20,', '"version": 21,'),
    ('"kit": "S638_EXPIRY_WATCH",', '"kit": "S763_F802_AGAIN",'),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(name, text, edits):
    for i, (old, new) in enumerate(edits, 1):
        n = text.count(old)
        if n != 1:
            sys.exit("STOP: %s edit %d: the anchor is found %d times (must be exactly once) -- nothing written" % (name, i, n))
        text = text.replace(old, new)
    return text


def main(argv):
    if len(argv) != 3:
        sys.exit(__doc__)
    src, out = argv[1], argv[2]
    data = {}
    for n, want in FROM.items():                             # the box builds its three; the chat builds all five
        if not os.path.isfile(os.path.join(src, n)):
            print("%-16s not in %s -- not built here" % (n, src))
            continue
        with open(os.path.join(src, n), "rb") as fh:
            b = fh.read()
        if md5(b) != want:
            sys.exit("STOP: %s is %s, not the live %s -- nothing written" % (n, md5(b), want))
        data[n] = b.decode("utf-8")
    if not data:
        sys.exit("STOP: none of the five files is in %s -- nothing written" % src)
    edits = {"marg_door.py": DOOR, "amir_day.py": AMIR, "reports_tile.py": TILE, "marg_watch.py": WATCH, "DUTY_MAP.json": MAP}
    res = {n: apply(n, t, edits[n]) for n, t in data.items()}
    if "DUTY_MAP.json" in res:
        json.loads(res["DUTY_MAP.json"])                     # still JSON
    os.makedirs(out, exist_ok=True)
    for n, t in res.items():
        b = t.encode("utf-8")
        with open(os.path.join(out, n), "wb") as fh:
            fh.write(b)
        print("%-16s %s -> %s  (%d B)" % (n, FROM[n][:8], md5(b), len(b)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
