#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""presence.py -- kit S957_PUNCH_DOOR (the parent, S523, 26-Nov-2026; roadmap E0). NEW. READ-ONLY; it need not be run by hand.

WHO IS AT THE CLINIC NOW, from the biometric machine's punches, with the duty roster as the fallback.
One reader, so the call-back clock today (callback_clock.on_duty moved here) and the notification engine later (E1) agree.

  * PUNCHED IN TODAY: the person's first punch of today (punches.csv, written by /root/attlistener_v2.py).
  * PUNCHED OUT: the last punch of today, when the day holds an even number of punches (two or more) and the last is at
    least OUT_MIN_GAP (120) minutes after the first -- a double tap or a re-tap on arrival is not a punch-out. (The
    attendance pages read in/out the same way: an odd count means still in.)
  * ON DUTY NOW: punched in, not punched out, and inside the shift of the day in staff_master.csv (it starts at the shift
    start, or at the punch when that is later; a Sunday follows the Sunday columns; empty = off) -- calls_console's own
    duty_window, unchanged.
  * THE ROSTER FALLBACK: when NO punch at all (by anyone) has come by 09:30 today, or the machine is silent now
    (att_silence_watch.py's state: a failure in the last SILENT_FRESH_MIN minutes, newer than its newest all-clear), a person
    with no punch today who is inside the roster's shift counts as on duty "by roster" -- a punch, when there is one, always
    wins. NEVER on a day the staff register marks the clinic closed (festival_day.clinic_closed, read-only). Setting PORTAL_PRESENCE_ROSTER = "0"
    (or off / no / false) turns the fallback off. The roster time is PORTAL_PRESENCE_ROSTER_AFTER (default 09:30).
  * Unreadable files: ok False -- the caller decides (the clock then treats every phone staff member as on duty).

It reads staff_master.csv (through calls_console.load_duty: names, user ids and the four shift columns only -- never a pay
column), punches.csv and the silence watch's state file. It writes nothing. No name, number or id is in this file.
"""
import csv
import datetime as _dt
import json
import os

VERSION = "S957 1.0"
PUNCH_CSV_DEFAULT = "/root/punches.csv"
STAFF_MASTER_DEFAULT = "/root/staff_master.csv"
SILENCE_STATE_DEFAULT = "/root/att_silence_watch.state.json"
SR_DB_DEFAULT = "/root/staff_register/staff_register.db"
SILENT_FRESH_MIN = 30                              # a silence failure older than this is not "silent now" (the watch may be off)
ROSTER_AFTER_DEFAULT = "09:30"
OUT_MIN_GAP = 120                                  # minutes between the first and the last punch before the last is an "out"


def _cfg(CC, key, default):
    """A setting as the caller reads it (the clock sets calls_console's reader: portal_config.py, then the environment);
    with no reader set, the environment, then the default."""
    try:
        f = getattr(CC, "_cfg_path", None)
        v = f(key, default) if (f and getattr(CC, "_CFG", None)) else (os.environ.get(key) or default)
    except Exception:                                    # noqa: BLE001
        v = default
    return str(v if v is not None else default).strip()


def roster_on(CC=None):
    return _cfg(CC, "PORTAL_PRESENCE_ROSTER", "1").lower() not in ("0", "off", "no", "false")


def roster_after(CC=None):
    v = _cfg(CC, "PORTAL_PRESENCE_ROSTER_AFTER", ROSTER_AFTER_DEFAULT)
    try:
        return _dt.datetime.strptime(v, "%H:%M").time()
    except Exception:                                    # noqa: BLE001
        return _dt.time(9, 30)


def machine_silent(path=None, now=None):
    """True when the silence watch's newest failure is newer than its newest all-clear AND at most SILENT_FRESH_MIN minutes
    old (the watch runs every 5 minutes; an old failure means the watch stopped, not that the machine is silent). A missing
    or unreadable state is NOT silence (never guessed)."""
    path = path or os.environ.get("PRESENCE_SILENCE_STATE") or SILENCE_STATE_DEFAULT
    try:
        with open(path, encoding="utf-8") as fh:
            st = json.load(fh)
    except Exception:                                    # noqa: BLE001
        return False
    ok = str(st.get("last_ok_iso") or "").replace("T", " ")[:19]      # the watch writes "YYYY-MM-DD HH:MM:SS"; "T" read too
    bad = str(st.get("last_failure_iso") or "").replace("T", " ")[:19]
    if not bad or (ok and bad <= ok):
        return False
    try:
        age = ((now or _dt.datetime.now()) - _dt.datetime.strptime(bad, "%Y-%m-%d %H:%M:%S")).total_seconds()
    except ValueError:
        return False
    return -300 <= age <= SILENT_FRESH_MIN * 60


def clinic_closed(CC, day):
    """True when the staff register marks the clinic closed that day (festival_day.clinic_closed = 1). Read-only; an
    unreadable register is not a holiday."""
    import sqlite3
    path = _cfg(CC, "SR_DB_PATH", SR_DB_DEFAULT)
    try:
        con = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=5)
        try:
            return con.execute("SELECT 1 FROM festival_day WHERE fest_date=? AND clinic_closed=1", (day,)).fetchone() is not None
        finally:
            con.close()
    except Exception:                                    # noqa: BLE001
        return False


def _uid(v):
    v = str(v or "").strip()
    try:
        return str(int(v))
    except ValueError:
        return ""


def _ts(s):
    s = (s or "").strip().replace("T", " ")[:19]
    for f in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return _dt.datetime.strptime(s, f)
        except ValueError:
            pass
    return None


def punches_of(punch_path, uid_key, day):
    """({key: [sorted datetimes of that day]}, punches of that day by anyone) -- every punch, not only the first. Raises when
    the file cannot be read."""
    out, n_all = {}, 0
    with open(punch_path, newline="", encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh)
        if not {"user_id", "datetime"} <= set(rd.fieldnames or []):
            raise ValueError("the punch log's columns")
        for row in rd:
            ds = (row.get("datetime") or "").strip().replace("T", " ")
            if ds[:10] != day:
                continue
            n_all += 1                                   # any punch at all: the machine is working today
            key = uid_key.get(_uid(row.get("user_id")))
            t = _ts(ds)
            if key and t is not None:
                out.setdefault(key, set()).add(t)
    return {k: sorted(v) for k, v in out.items()}, n_all


def today(CC, now, master=None, punch=None, silence=None):
    """{"ok", "basis" ("punch" | "roster"), "why", "silent", "any_punch", "people": {first-name key: {...}}}.
    CC = the calls_console module (its load_duty / duty_window / roster_window are used as they are)."""
    master = master or _cfg(CC, "SR_STAFF_MASTER", getattr(CC, "STAFF_MASTER_DEFAULT", STAFF_MASTER_DEFAULT))
    punch = punch or _cfg(CC, "SR_PUNCH_CSV", getattr(CC, "PUNCH_CSV_DEFAULT", PUNCH_CSV_DEFAULT))
    d = now.date().isoformat()
    res = {"ok": False, "basis": "punch", "why": "", "silent": False, "any_punch": False, "people": {}, "version": VERSION}
    try:
        staff, _first, ok = CC.load_duty(master, punch, [d])
    except Exception:                                    # noqa: BLE001
        staff, ok = {}, False
    if not ok or not staff:
        res["why"] = "duty not known"
        return res
    try:
        times, n_all = punches_of(punch, {e["uid"]: k for k, e in staff.items()}, d)
    except Exception:                                    # noqa: BLE001
        res["why"] = "duty not known"
        return res
    silent = machine_silent(silence, now)
    any_punch = n_all > 0
    late = now >= _dt.datetime.combine(now.date(), roster_after(CC))
    closed = clinic_closed(CC, d)
    roster = roster_on(CC) and not closed and (silent or (not any_punch and late))
    res.update({"ok": True, "silent": silent, "any_punch": any_punch, "closed": closed, "basis": "roster" if roster else "punch",
                "why": ("the machine is silent" if silent else "no punch by %s" % roster_after(CC).strftime("%H:%M"))
                if roster else "punches"})
    for k, ent in staff.items():
        ts = times.get(k, [])
        p_in = ts[0] if ts else None
        p_out = None
        if len(ts) >= 2 and len(ts) % 2 == 0 and (ts[-1] - ts[0]) >= _dt.timedelta(minutes=OUT_MIN_GAP):
            p_out = ts[-1]
        w = CC.duty_window(ent, d, p_in) if p_in else None
        if w and p_out:
            w = (w[0], min(w[1], p_out)) if min(w[1], p_out) > w[0] else None
        rw = CC.roster_window(ent, d)
        on, by = False, "off"
        if w and w[0] <= now <= w[1]:
            on, by = True, "punch"
        elif roster and not ts and rw and rw[0] <= now <= rw[1]:
            on, by = True, "roster"
        res["people"][k] = {"name": ent.get("name"), "in": p_in, "out": p_out, "punches": len(ts),
                            "present": bool(p_in) and not p_out, "rostered": rw, "on_duty": on, "by": by}
    return res


def on_duty(CC, now, keys, master=None, punch=None, silence=None):
    """(the keys on duty now, today's picture). Unknown duty -> ([], picture with ok False)."""
    t = today(CC, now, master, punch, silence)
    if not t["ok"]:
        return [], t
    return [k for k in keys if (t["people"].get(k) or {}).get("on_duty")], t


def clock_on_duty(CC, now, phone, rec, backup):
    """callback_clock.on_duty (S953) as it was, read through presence: (logins, why). The phone staff on duty now + the
    reception mobile; nobody on duty -> the reception mobile + the backup; the duty files unreadable -> every phone staff
    login + the reception mobile. New (S957): a punch-out ends the duty; the roster fallback; why says "by roster"."""
    on, t = on_duty(CC, now, phone)
    if not t["ok"]:
        return list(phone) + [rec], "duty not known"
    if on:
        by_roster = any((t["people"].get(k) or {}).get("by") == "roster" for k in on)
        return on + [rec], ("on duty by roster (%s)" % t["why"]) if by_roster else "on duty"
    return [rec] + [b for b in backup if b not in phone], "no phone staff on duty"


if __name__ == "__main__":                               # a read-only look, counts only (no names): python3 presence.py
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import calls_console as _CC                          # noqa: E402
    _now = _dt.datetime.now()
    _t = today(_CC, _now)
    _p = _t["people"].values()
    print("PRESENCE %s %s: ok %s, basis %s (%s), people %d, punched in %d, punched out %d, on duty %d (by roster %d)"
          % (VERSION, _now.strftime("%Y-%m-%d %H:%M"), _t["ok"], _t["basis"], _t["why"], len(_t["people"]),
             sum(1 for x in _p if x["in"]), sum(1 for x in _p if x["out"]), sum(1 for x in _p if x["on_duty"]),
             sum(1 for x in _p if x["by"] == "roster")))
