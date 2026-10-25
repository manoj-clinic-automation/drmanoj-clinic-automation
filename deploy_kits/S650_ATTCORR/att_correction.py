#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""att_correction.py -- kit S650_ATTCORR (the parent, session 354, 25-Oct-2026) -- D786, THE MONTH-END ATTENDANCE
CORRECTION FLOW, as the owner ruled it on the mock-up (claude.ai artifact 8gg5NKJThNmSMJXPgeUNHM, rev 2 + the fallback).

  1  From the 1st, reception prints the Attendance correction sheet (A4): one block per staff member listing every day
     of the month just ended with NO machine punch (Sundays included), columns Date . Day . Present . Leave . Absent,
     a signature line under each block and the three signatures (reception, Shavez, Dr Manoj) at the foot.
  2  Each staff member ticks and signs on the paper.
  3  Reception enters the ticks on screen and Saves. Shavez and the owner have the same screen as a fallback.
  4  Shavez makes the final corrections against the signed sheet and Saves. Nothing is sent back. His own days are
     the owner's ("Shavez ke apne din Sir dekhte hain").
  5  The owner's page: any day editable, Shavez's step his too; Approve & save puts the month in.
  Every screen has a Save button and shows 'Saved' on screen (the owner's rule 45, D786).

NOTHING COUNTS UNTIL APPROVE & SAVE. The staging tables attcorr_* hold the ticks and are read by nobody else.
Approve & save turns each tick into a record the register ALREADY has, so no salary reader changes:
  Present -> an already-approved present_request in the D338 shape (correct_present): req_ts = the day + the person's
             duty start, so no late mark; reason 'Attendance correction sheet <Month YYYY>'; decide_note DECIDE_NOTE.
             A leave or an absent entry the day grid holds for that staff-day is cleared.
  Leave   -> the day grid's own leave row, exactly as save_maker writes a leave the doctor sanctioned (daily_register:
             absence_type 'leave_sanctioned', leave_kind 'discretionary' -- 'festival' on a listed festival, D278 --
             leave_approved_by the approver). On a rostered-OFF Sunday nothing is written: an off day is not a leave.
  Absent  -> no new row (the machine already says absent). A leave the day grid holds for that day becomes 'absent'.
Every write keeps what it replaced (attcorr_day.applied_prior); a tick changed after approval is undone and written
again at the next Approve & save. Every write goes to audit_log.

THE SALARY LOCK WAITS (the mock-up): from FROM_YM, the Lock refuses while the month has listed days and its corrections
are not approved, or were changed after approval. The lock's view is WRAPPED here, not edited.

THE LINES. GET /register/attcorr/api/line answers the staff's 'Aaj ka kaam' (aaj_duties.json, kind 'fetch') about the
month just ended: reception's two lines from the 1st until she saves, Shavez's after she saves; the owner's console
reads the tables itself.

THE MANUAL WAY STAYS. The owner's Step 0 sheet (/register/salary/flow/verify), the fix-absents desk and the day page's
past-day correction (D338/D339) are untouched; a day already corrected there is not listed here.

Hooked into staff_register.py by install(app, module) just before its __main__ block (one counted edit); a fault here
leaves the register running without these pages (the hook catches it).
"""
import calendar
import datetime
import functools
import json

from flask import make_response, redirect, render_template_string, request

VERSION = "S650 1"
FROM_YM = "2026-10"                                   # the first month the flow (and the lock's wait) applies to
DECIDE_NOTE = "attendance correction sheet (D786)"
MARKS = ("P", "L", "A")
WORD_EN = {"P": "Present", "L": "Leave", "A": "Absent", "": "not marked"}
DAY_HI = {"Monday": "Monday", "Tuesday": "Tuesday", "Wednesday": "Wednesday", "Thursday": "Thursday",
          "Friday": "Friday", "Saturday": "Saturday", "Sunday": "Sunday"}
SR = None                                             # the staff_register module, set by install()

SCHEMA = """
CREATE TABLE IF NOT EXISTS attcorr_day (          -- S650 (D786): one tick per staff-day; counts for NOTHING until approved
    reg_date      TEXT NOT NULL,
    staff_id      INTEGER NOT NULL,
    ym            TEXT NOT NULL,
    mark          TEXT,                            -- P | L | A | NULL: the tick as it stands now
    entered_mark  TEXT, entered_by TEXT, entered_ts TEXT,    -- reception's Save (or the fallback's)
    checked_mark  TEXT, checked_by TEXT, checked_ts TEXT,    -- Shavez's change, when he changed it
    owner_mark    TEXT, owner_by TEXT, owner_ts TEXT,        -- the owner's change, when he changed it
    applied_mark  TEXT, applied_by TEXT, applied_ts TEXT,    -- what Approve & save last wrote
    applied_prior TEXT,                            -- JSON: the day-grid row that write replaced (for an undo)
    PRIMARY KEY (reg_date, staff_id)
);
CREATE INDEX IF NOT EXISTS ix_attcorr_day_ym ON attcorr_day(ym);
CREATE TABLE IF NOT EXISTS attcorr_sign (         -- 'Sheet par <name> ka sign hai'
    ym TEXT NOT NULL, staff_id INTEGER NOT NULL,
    signed INTEGER NOT NULL DEFAULT 0, by_user TEXT, ts TEXT,
    PRIMARY KEY (ym, staff_id)
);
CREATE TABLE IF NOT EXISTS attcorr_month (        -- who saved each step of a month, and when
    ym TEXT PRIMARY KEY,
    entered_by TEXT, entered_ts TEXT,
    checked_by TEXT, checked_ts TEXT,
    approved_by TEXT, approved_ts TEXT, n_applied INTEGER
);
"""


# --------------------------------------------------------------------------------------------- small helpers ---
def _db():
    con = SR.get_db()
    con.executescript(SCHEMA)
    return con


def _prev_ym(today):
    y, m = int(today[:4]), int(today[5:7])
    return "%04d-12" % (y - 1) if m == 1 else "%04d-%02d" % (y, m - 1)


def _ym_arg():
    ym = (request.values.get("ym") or "").strip()
    return ym if SR._valid_ym(ym) else _prev_ym(SR._today())


def _month_name(ym):
    try:
        return datetime.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%B %Y")
    except (ValueError, TypeError):
        return ym


def _mon(ym):
    try:
        return datetime.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%B")
    except (ValueError, TypeError):
        return ym


def _dmy(d):
    return "%s-%s-%s" % (d[8:10], d[5:7], d[:4]) if d and len(d) >= 10 else (d or "")


def _dm(ts):
    return "%s-%s" % (ts[8:10], ts[5:7]) if ts and len(ts) >= 10 else ""


def _hm(ts):
    return ts[11:16] if ts and len(ts) >= 16 else ""


def _dates_only():
    """The policy's part-time staff (dates_only_staff): their days are not absences, so they are never listed."""
    try:
        P, _e = SR._policy_module()
        return P.dates_only_names(P.load_settings()) if P else set()
    except Exception:
        return set()


def _locked(con, ym):
    try:
        r = con.execute("SELECT status FROM locked_run WHERE ym=?", (ym,)).fetchone()
    except Exception:
        return False
    return bool(r and r["status"] == "locked")


# ------------------------------------------------------------------------------------------------ the days ---
def _salary_start(date, ym, sh):
    """The duty start the SALARY reads for that day, or None when the salary treats the day as off.

    The salary's roster is att_month_report.duty_shift (its ROSTER_FROM, the ATT_ROSTER_FROM switch), NOT the register's
    own duty_shift_for (ROSTER_FROM 2026-09): the two can disagree on Sundays, and a leave written on a day the salary
    reads as off would ADD a charged day. So 'off' is decided where the money is decided. Fallback: the register's."""
    try:
        SR._policy_module()                                   # puts /root on the path, as the salary does
        import att_month_report as amr                        # noqa: PLC0415
        start, _end = amr.duty_shift(date, ym, sh, {"sunday_group": sh.get("sunday_group") or ""})
        return start
    except Exception:
        try:
            start, _end = SR.duty_shift_for(date, sh)
            return start
        except Exception:
            return None


def day_list(con, ym):
    """Every staff-day of ym with NO machine punch, per staff: (blocks, feed_ok).

    Listed when all hold: the day is before today (the running day is never read as absent); it is not a clinic
    holiday; the person is active that day and not part-time (dates_only_staff); the machine has no punch; no
    present_request exists for that staff-day other than one this flow wrote; and the salary reads the person as on duty
    that day -- or the day is a Sunday (D786: 'include sundays'; an off-duty Sunday is marked off, and nothing on it is
    ever charged).
    feed_ok False = the punch feed cannot be read: the caller must say so and never show a clean list."""
    if not SR._valid_ym(ym):
        return [], True
    idx = SR.punch_month_index(ym)
    if idx is None:
        return [], False
    y, m = int(ym[:4]), int(ym[5:7])
    nd = calendar.monthrange(y, m)[1]
    today = SR._today()
    shifts = SR.load_staff_shifts() or {}
    donly = _dates_only()
    reqs = {}
    try:
        for r in con.execute("SELECT reg_date, staff_id, decide_note FROM present_request WHERE reg_date LIKE ?",
                             (ym + "-%",)):
            reqs[(r["reg_date"], r["staff_id"])] = r["decide_note"] or ""
    except Exception:
        pass
    acc = {}
    for day in range(1, nd + 1):
        d = "%s-%02d" % (ym, day)
        if d >= today:
            break
        if SR.is_holiday(con, d):
            continue
        date = datetime.date(y, m, day)
        sun = date.weekday() == 6
        fest = SR.festival_on(con, d) is not None
        punched = idx.get(d, set())
        for s in SR.staff_for_date(con, d):
            sid = s["staff_id"]
            name = s["name"] or ""
            if sid in punched or name.strip().lower() in donly:
                continue
            note = reqs.get((d, sid))
            if note is not None and DECIDE_NOTE not in note:
                continue                                   # asked for, or corrected, on the register's own doors
            sh = shifts.get(sid)
            start, off = None, False
            if sh is not None:
                start = _salary_start(date, ym, sh)
                if start is None:
                    if not sun:
                        continue                           # an off day the salary never reads
                    off = True                             # an off-duty Sunday: listed (D786), never charged
                    start = sh.get("wd_start") or sh.get("sun_start")
            b = acc.setdefault(sid, {"sid": sid, "name": name, "rows": []})
            b["rows"].append({"d": d, "dow": date.strftime("%A"), "sun": sun, "off": off, "fest": fest,
                              "in": start.strftime("%H:%M") if start else "09:00"})
    return sorted(acc.values(), key=lambda b: b["name"].lower()), True


def _state(con, ym):
    rows = {(r["reg_date"], r["staff_id"]): dict(r)
            for r in con.execute("SELECT * FROM attcorr_day WHERE ym=?", (ym,))}
    signs = {r["staff_id"]: dict(r) for r in con.execute("SELECT * FROM attcorr_sign WHERE ym=?", (ym,))}
    mon = con.execute("SELECT * FROM attcorr_month WHERE ym=?", (ym,)).fetchone()
    return rows, signs, (dict(mon) if mon else {})


def summary(con, ym, blocks=None, feed_ok=True):
    """The month's standing. approved = the owner approved AND no tick differs from what was written."""
    if blocks is None:
        blocks, feed_ok = day_list(con, ym)
    rows, signs, mon = _state(con, ym)
    n_days = unmarked = pending = 0
    for b in blocks:
        for r in b["rows"]:
            n_days += 1
            x = rows.get((r["d"], b["sid"])) or {}
            mk = x.get("mark") or ""
            if not mk:
                unmarked += 1
            if mk != (x.get("applied_mark") or ""):
                pending += 1
    entered = bool(mon.get("entered_ts"))
    checked = bool(mon.get("checked_ts"))
    return dict(ym=ym, feed_ok=feed_ok, n_days=n_days, n_staff=len(blocks), unmarked=unmarked, pending=pending,
                entered=entered, checked=checked, approved=bool(mon.get("approved_ts")) and pending == 0,
                ever_approved=bool(mon.get("approved_ts")), locked=_locked(con, ym), mon=mon,
                rows=rows, signs=signs, applies=ym >= FROM_YM)


def _view(blocks, st, own_sid=None):
    """blocks + each day's current tick and the notes the pages show."""
    out = []
    for b in blocks:
        days = []
        for r in b["rows"]:
            x = st["rows"].get((r["d"], b["sid"])) or {}
            mk = x.get("mark") or ""
            em = x.get("entered_mark") or ""
            days.append(dict(r, mark=mk, entered=em, checked=x.get("checked_mark") or "",
                             changed_by_check=bool(x.get("checked_ts")), changed_by_owner=bool(x.get("owner_ts")),
                             applied=x.get("applied_mark") or ""))
        sg = st["signs"].get(b["sid"]) or {}
        out.append(dict(sid=b["sid"], name=b["name"], days=days, signed=bool(sg.get("signed")),
                        own=(own_sid is not None and b["sid"] == own_sid),
                        unmarked=sum(1 for x in days if not x["mark"])))
    return out


# ----------------------------------------------------------------------------------------------- the saves ---
def _ensure(con, d, sid, ym):
    con.execute("INSERT INTO attcorr_day(reg_date, staff_id, ym) VALUES(?,?,?) "
                "ON CONFLICT(reg_date, staff_id) DO NOTHING", (d, sid, ym))


def _marks_from(form, blocks, skip_sid=None):
    out = {}
    for b in blocks:
        if skip_sid is not None and b["sid"] == skip_sid:
            continue
        for r in b["rows"]:
            v = (form.get("m_%d_%s" % (b["sid"], r["d"])) or "").strip().upper()
            out[(r["d"], b["sid"])] = v if v in MARKS else ""
    return out


def _save_signs(con, form, blocks, ym, actor, now, skip_sid=None):
    for b in blocks:
        if skip_sid is not None and b["sid"] == skip_sid:
            continue
        v = 1 if form.get("sign_%d" % b["sid"]) in ("1", "on", "yes") else 0
        con.execute("INSERT INTO attcorr_sign(ym, staff_id, signed, by_user, ts) VALUES(?,?,?,?,?) "
                    "ON CONFLICT(ym, staff_id) DO UPDATE SET signed=excluded.signed, by_user=excluded.by_user, "
                    "ts=excluded.ts", (ym, b["sid"], v, actor, now))


def _month_set(con, ym, **kw):
    con.execute("INSERT INTO attcorr_month(ym) VALUES(?) ON CONFLICT(ym) DO NOTHING", (ym,))
    for k, v in kw.items():
        con.execute("UPDATE attcorr_month SET %s=? WHERE ym=?" % k, (v, ym))


def _guard(st, step):
    if not st["applies"]:
        raise PermissionError("this flow starts with %s" % _month_name(FROM_YM))
    if not st["feed_ok"]:
        raise PermissionError("machine ka data abhi padha nahi ja raha -- thodi der baad dobara kijiye"
                              if step != "owner" else "the punch feed cannot be read just now -- try again shortly")
    if st["locked"]:
        raise PermissionError("is mahine ki salary lock ho chuki hai" if step != "owner"
                              else "this month's salary is locked -- unlock it first to change attendance")
    if step != "owner" and st["ever_approved"]:
        raise PermissionError("Sir approve kar chuke hain -- ab badlaav Sir ke page par hoga")
    if step == "enter" and st["checked"]:
        raise PermissionError("Shavez check kar chuke hain -- ab badlaav Shavez ke page par hoga")


def save_enter(actor, ym, form):
    """Step 3: reception (or the fallback) enters the ticks from the signed sheet."""
    con = _db()
    try:
        blocks, ok = day_list(con, ym)
        st = summary(con, ym, blocks, ok)
        _guard(st, "enter")
        now = SR._now()
        marks = _marks_from(form, blocks)
        n = 0
        for (d, sid), v in marks.items():
            _ensure(con, d, sid, ym)
            con.execute("UPDATE attcorr_day SET mark=?, entered_mark=?, entered_by=?, entered_ts=? "
                        "WHERE reg_date=? AND staff_id=?", (v or None, v or None, actor, now, d, sid))
            n += 1 if v else 0
        _save_signs(con, form, blocks, ym, actor, now)
        _month_set(con, ym, entered_by=actor, entered_ts=now)
        SR._audit(con, "attcorr", ym, "enter_save", "", "%d of %d days ticked" % (n, len(marks)), actor)
        con.commit()
        return n, len(marks)
    finally:
        con.close()


def save_check(actor, ym, form):
    """Step 4: Shavez corrects against the signed sheet. His own block is the owner's."""
    con = _db()
    try:
        blocks, ok = day_list(con, ym)
        st = summary(con, ym, blocks, ok)
        _guard(st, "check")
        own = SR.staff_for_user(con, actor)
        now = SR._now()
        marks = _marks_from(form, blocks, skip_sid=own)
        changed = 0
        for (d, sid), v in marks.items():
            old = (st["rows"].get((d, sid)) or {}).get("mark") or ""
            if v == old:
                continue
            _ensure(con, d, sid, ym)
            con.execute("UPDATE attcorr_day SET mark=?, checked_mark=?, checked_by=?, checked_ts=? "
                        "WHERE reg_date=? AND staff_id=?", (v or None, v or None, actor, now, d, sid))
            changed += 1
        _save_signs(con, form, blocks, ym, actor, now, skip_sid=own)
        _month_set(con, ym, checked_by=actor, checked_ts=now)
        SR._audit(con, "attcorr", ym, "check_save", "", "%d day(s) changed" % changed, actor)
        con.commit()
        return changed, len(marks)
    finally:
        con.close()


def save_owner(actor, ym, form):
    """Step 5: the owner changes any day and Approve & save writes the month."""
    con = _db()
    try:
        blocks, ok = day_list(con, ym)
        st = summary(con, ym, blocks, ok)
        _guard(st, "owner")
        now = SR._now()
        marks = _marks_from(form, blocks)
        changed = 0
        for (d, sid), v in marks.items():
            old = (st["rows"].get((d, sid)) or {}).get("mark") or ""
            if v == old:
                continue
            _ensure(con, d, sid, ym)
            con.execute("UPDATE attcorr_day SET mark=?, owner_mark=?, owner_by=?, owner_ts=? "
                        "WHERE reg_date=? AND staff_id=?", (v or None, v or None, actor, now, d, sid))
            changed += 1
        _save_signs(con, form, blocks, ym, actor, now)
        written = _apply_month(con, actor, ym, blocks)
        _month_set(con, ym, approved_by=actor, approved_ts=now, n_applied=written)
        SR._audit(con, "attcorr", ym, "approve_save", "", "%d changed, %d written" % (changed, written), actor)
        con.commit()
        return changed, written
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


# ------------------------------------------------------------------------------- approve: the real records ---
def _dr(con, d, sid):
    r = con.execute("SELECT * FROM daily_register WHERE reg_date=? AND staff_id=?", (d, sid)).fetchone()
    return dict(r) if r else None


def _has_exception(r):
    return bool(r and (r.get("leave_kind") or r.get("late_flag") or r.get("dress_improper") or r.get("icard_missing")
                       or r.get("extra_duty") or r.get("outstation_nights")
                       or r.get("absence_type") in ("absent", "outstation", "leave_sanctioned")))


def _restore_dr(con, d, sid, old):
    cur = _dr(con, d, sid)
    if old is None:
        if cur:
            con.execute("DELETE FROM daily_register WHERE id=?", (cur["id"],))
        return
    cols = [c for c in old if c != "id"]
    if cur:
        con.execute("UPDATE daily_register SET %s WHERE id=?" % ", ".join("%s=?" % c for c in cols),
                    [old[c] for c in cols] + [cur["id"]])
    else:
        con.execute("INSERT INTO daily_register(%s) VALUES(%s)" % (", ".join(cols), ", ".join("?" for _ in cols)),
                    [old[c] for c in cols])


def _undo(con, actor, d, sid, applied, prior):
    if applied == "P":
        con.execute("DELETE FROM present_request WHERE reg_date=? AND staff_id=? AND decide_note=?",
                    (d, sid, DECIDE_NOTE))
    if prior and prior.get("touched"):
        _restore_dr(con, d, sid, prior.get("dr"))
    SR._audit(con, "attcorr", "%s/%s" % (d, sid), "undo", applied, "", actor)


def _write(con, actor, ym, r, sid, mark, punches):
    """One tick into the register's own records. Returns what it replaced (kept for an undo)."""
    d = r["d"]
    if punches.get(d, set()) and sid in punches.get(d, set()):
        raise PermissionError("the machine now has a punch for staff %s on %s -- open the page again" % (sid, _dmy(d)))
    dr = _dr(con, d, sid)
    now = SR._now()
    if mark == "P":
        ex = con.execute("SELECT status FROM present_request WHERE reg_date=? AND staff_id=?", (d, sid)).fetchone()
        if ex:
            raise PermissionError("a present request already exists for staff %s on %s (%s)" % (sid, _dmy(d), ex["status"]))
        con.execute("INSERT INTO present_request(reg_date, staff_id, req_user, req_ts, reason, status, decide_user, "
                    "decide_ts, decide_note) VALUES(?,?,?,?,?,'approved',?,?,?)",
                    (d, sid, actor, "%s %s:00" % (d, r["in"]), "Attendance correction sheet " + _month_name(ym),
                     actor, now, DECIDE_NOTE))
        SR._audit(con, "present_request", "%s/%s" % (d, sid), "attcorr_present", "", "in_time=%s" % r["in"], actor)
        if dr and (dr.get("leave_kind") or dr.get("absence_type") in ("absent", "leave_sanctioned")):
            con.execute("UPDATE daily_register SET absence_type=NULL, leave_kind=NULL, leave_approved_by=NULL "
                        "WHERE id=?", (dr["id"],))
            if not _has_exception(_dr(con, d, sid)):
                con.execute("DELETE FROM daily_register WHERE id=?", (dr["id"],))
            return {"dr": dr, "touched": True}
        return {"dr": dr, "touched": False}
    if mark == "L":
        if r["off"]:
            return {"dr": dr, "touched": False}            # a rostered-off Sunday: not a leave, nothing to write
        kind = "festival" if r["fest"] else "discretionary"
        by = actor if actor in ("bhawna", "manoj") else "manoj"
        if dr:
            con.execute("UPDATE daily_register SET absence_type='leave_sanctioned', leave_kind=?, leave_approved_by=?, "
                        "late_flag=NULL, late_approved_by=NULL, dress_improper=0, icard_missing=0, extra_duty=0, "
                        "outstation_nights=0 WHERE id=?", (kind, by, dr["id"]))
        else:
            con.execute("INSERT INTO daily_register(reg_date, staff_id, absence_type, leave_kind, leave_approved_by, "
                        "maker_user, maker_ts) VALUES(?,?,'leave_sanctioned',?,?,?,?)",
                        (d, sid, kind, by, "attcorr:" + actor, now))
        SR._audit(con, "day", "%s/%s" % (d, sid), "attcorr_leave", "", kind, actor)
        return {"dr": dr, "touched": True}
    if mark == "A":
        if dr and (dr.get("leave_kind") or dr.get("absence_type") == "leave_sanctioned"):
            con.execute("UPDATE daily_register SET absence_type='absent', leave_kind=NULL, leave_approved_by=NULL "
                        "WHERE id=?", (dr["id"],))
            SR._audit(con, "day", "%s/%s" % (d, sid), "attcorr_absent", "leave", "absent", actor)
            return {"dr": dr, "touched": True}
        return {"dr": dr, "touched": False}
    return None


def _apply_month(con, actor, ym, blocks):
    punches = SR.punch_month_index(ym)
    if punches is None:
        raise PermissionError("the punch feed cannot be read just now -- try again shortly")
    rows, _s, _m = _state(con, ym)
    written = 0
    for b in blocks:
        sid = b["sid"]
        for r in b["rows"]:
            x = rows.get((r["d"], sid)) or {}
            mark, applied = x.get("mark") or "", x.get("applied_mark") or ""
            if mark == applied:
                continue
            if applied:
                prior = json.loads(x["applied_prior"]) if x.get("applied_prior") else None
                _undo(con, actor, r["d"], sid, applied, prior)
            newp = _write(con, actor, ym, r, sid, mark, punches) if mark else None
            _ensure(con, r["d"], sid, ym)
            con.execute("UPDATE attcorr_day SET applied_mark=?, applied_by=?, applied_ts=?, applied_prior=? "
                        "WHERE reg_date=? AND staff_id=?",
                        (mark or None, actor, SR._now(), json.dumps(newp) if newp is not None else None, r["d"], sid))
            written += 1
    return written


# ---------------------------------------------------------------------------------------- the salary lock ---
def lock_blocker(ym):
    """'' when the lock may go ahead, else the sentence the Lock desk shows."""
    if not SR._valid_ym(ym) or ym < FROM_YM:
        return ""
    con = _db()
    try:
        blocks, ok = day_list(con, ym)
        url = "https://followup.dr-manoj.in%s/attcorr?ym=%s" % (SR.APP_PREFIX, ym)
        if not ok:
            return ("The punch feed cannot be read, so %s's attendance corrections cannot be checked -- the lock waits. "
                    "Try again shortly." % _mon(ym))
        if not blocks:
            return ""
        st = summary(con, ym, blocks, ok)
        if st["approved"]:
            return ""
        if st["ever_approved"]:
            return ("%s's attendance corrections were changed after you approved them -- open %s and press "
                    "Approve & save again, then lock." % (_mon(ym), url))
        return ("%s's attendance corrections are not approved yet (%d day(s) with no punch) -- open %s, check them "
                "and press Approve & save, then lock." % (_mon(ym), st["n_days"], url))
    finally:
        con.close()


def _wrap_lock(orig):
    @functools.wraps(orig)
    def wrapped(*a, **k):
        u = SR.current_user(request)
        if u and u["caps"].get("lock") and request.method == "POST":
            ym = (request.form.get("ym") or "").strip()
            try:
                msg = lock_blocker(ym)
            except Exception as e:                                   # noqa: BLE001
                msg = "The attendance corrections could not be read (%s) -- the lock waits." % type(e).__name__
            if msg:
                return SR._render_salary(ym, u, msg)
        return orig(*a, **k)
    wrapped._attcorr_wrapped = True
    return wrapped


# ---------------------------------------------------------------------------------------------- the pages ---
CSS = """
 *{box-sizing:border-box}
 body{margin:0;background:#f3f5f8;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:#1d2433}
 .top{background:var(--c);color:#fff;padding:16px 16px 14px}
 .top h1{margin:0;font-size:20px} .top .s{font-size:14px;margin-top:4px}
 .top a{color:#fff;font-size:13px;text-decoration:underline}
 .wrap{max-width:560px;margin:0 auto;padding:14px 14px 48px;display:flex;flex-direction:column;gap:14px}
 .card{background:#fff;border:1px solid #d6dbe3;border-radius:12px;padding:14px;display:flex;flex-direction:column;gap:10px}
 .k{font-size:13px;font-weight:700;color:var(--c);letter-spacing:.03em}
 .p{font-size:15px;line-height:1.45;margin:0}
 .muted{font-size:13px;color:#4a5263;line-height:1.45}
 details.st{background:#fff;border:1px solid #d6dbe3;border-radius:12px}
 details.st.hl{border:2px solid #b45309}
 details.st>summary{padding:14px;font-weight:700;font-size:16px;display:flex;justify-content:space-between;
   align-items:center;cursor:pointer;list-style:none;min-height:44px}
 details.st>summary::-webkit-details-marker{display:none}
 summary .c{font-size:13px;font-weight:400;color:#4a5263}
 .day{padding:10px 14px;border-top:1px solid #eef1f5}
 .dl{font-size:14px;display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}
 .dl .sun{font-weight:700;color:#3b0f8a}
 .seg{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin-top:6px}
 .seg label{position:relative;display:block}
 .seg input{position:absolute;opacity:0;width:1px;height:1px}
 .seg span{display:block;text-align:center;padding:12px 4px;border-radius:8px;border:1px solid #b8c0cc;
   background:#fff;font-size:15px;min-height:44px}
 .seg input:checked+span{background:var(--c);border-color:var(--c);color:#fff;font-weight:600}
 .seg input:focus-visible+span{outline:3px solid #f0a020;outline-offset:1px}
 .note{font-size:12px;color:#8a3f06;font-weight:600}
 .ro{font-weight:600}
 .sign{display:flex;gap:10px;align-items:center;background:#fff7ec;padding:10px;border-radius:8px;margin:4px 14px 14px;
   font-size:14px;min-height:44px}
 .sign input{width:22px;height:22px}
 .btn{display:block;width:100%;padding:15px;border:0;border-radius:10px;background:var(--c);color:#fff;font-size:17px;
   font-weight:700;cursor:pointer;min-height:48px}
 .btn[disabled]{opacity:.6}
 .link{display:block;text-align:center;border:2px solid var(--c);color:var(--c);text-decoration:none;padding:12px;
   border-radius:10px;font-size:15px;font-weight:600}
 .solid{display:block;text-align:center;background:var(--c);color:#fff;text-decoration:none;padding:13px;border-radius:10px;
   font-size:16px;font-weight:600}
 .ok{background:#e7f5ee;border:1px solid #8fd0ad;color:#145c37;border-radius:10px;padding:12px;font-size:15px;
   font-weight:600;text-align:center}
 .err{background:#fdecec;border:1px solid #e3a0a0;color:#7a1414;border-radius:10px;padding:12px;font-size:15px;font-weight:600}
 .warn{background:#fff7ec;border:1px solid #f0c48a;color:#6b3a0a;border-radius:12px;padding:12px 14px;font-size:14px;line-height:1.45}
"""

FORM_HTML = """<!doctype html><html lang="{{ 'en' if mode == 'owner' else 'hi' }}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }}</title><style>:root{--c:{{ colour }}}{{ css|safe }}</style></head><body>
<div class="top"><h1>{{ title }}</h1><div class="s">{{ sub }}</div></div>
<div class="wrap">
{% if saved %}<div class="ok" role="status">&#10003; Saved &mdash; {{ saved }}</div>{% endif %}
{% if err %}<div class="err" role="alert">{{ err }}</div>{% endif %}
{% if not st.applies %}
 <div class="card"><p class="p">{{ 'This flow starts with ' if mode == 'owner' else 'Yeh kaam shuru hota hai ' }}{{ from_month }}.</p></div>
{% elif not st.feed_ok %}
 <div class="err">{{ 'The punch feed cannot be read just now, so the days with no punch cannot be listed. This page will not guess -- try again shortly.' if mode == 'owner' else 'Machine ka data abhi padha nahi ja raha, isliye din nahi dikh rahe. Thodi der baad page dobara kholiye.' }}</div>
{% elif not blocks %}
 <div class="card"><p class="p">{{ 'Nobody has a day without a punch in ' ~ month ~ ' -- nothing to correct.' if mode == 'owner' else month ~ ' mein sabka har din machine par hai. Kuch bharna nahi hai.' }}</p></div>
 {% if mode == 'owner' and not st.approved %}<form method="post" action="{{ action }}" onsubmit="this.querySelector('button').disabled=true">
  <input type="hidden" name="ym" value="{{ ym }}"><button class="btn" type="submit">Approve &amp; save</button></form>{% endif %}
{% else %}
 {% if mode == 'enter' %}
 <div class="card"><div class="k">1 &middot; SHEET PRINT KIJIYE</div>
  <p class="p">{{ st.n_staff }} staff ke {{ st.n_days }} din machine par punch ke bina hain.</p>
  <a class="solid" href="{{ prefix }}/attcorr/sheet?ym={{ ym }}" target="_blank" rel="noopener">Attendance correction sheet (A4)</a></div>
 {% elif mode == 'check' %}
 <p class="muted">Sign wali sheet saamne rakhiye. Jo tick sheet se alag hai, use yahin theek kijiye, phir Save.</p>
 {% if not st.entered and not frozen %}<a class="link" href="{{ prefix }}/attcorr/enter?ym={{ ym }}">Reception nahi hai? Sheet se khud bhariye</a>{% endif %}
 {% else %}
 <div class="warn">{% if st.locked %}<b>{{ mon }}'s salary is locked.</b> Unlock it first to change attendance.
  {% elif st.approved %}<b>Approved</b> by {{ st.mon.approved_by }} on {{ dm(st.mon.approved_ts) }} at {{ hm(st.mon.approved_ts) }} &mdash; {{ mon }}'s attendance is updated. You can still change a day and approve again.
  {% else %}<b>{{ mon }}'s salary lock waits</b> for your Approve &amp; save. Tap any day to change it.{% endif %}</div>
 <a class="link" href="{{ prefix }}/attcorr/enter?ym={{ ym }}">Enter from the signed sheet yourself (reception's screen)</a>
 <a class="link" href="{{ prefix }}/attcorr/sheet?ym={{ ym }}" target="_blank" rel="noopener">The printed sheet (A4)</a>
 {% endif %}
 {% if frozen %}<div class="warn">{{ frozen }}</div>{% endif %}
 <form method="post" action="{{ action }}" onsubmit="var b=this.querySelector('button[type=submit]');if(b){b.disabled=true;b.textContent='Saving...';}">
 <input type="hidden" name="ym" value="{{ ym }}">
 {% if mode == 'enter' %}<div class="k" style="margin-top:4px">2 &middot; SIGN WALI SHEET SE TICK BHARIYE</div>{% endif %}
 {% for b in view %}
 <details class="st{{ ' hl' if b.hl }}"{% if b.open %} open{% endif %} style="margin-bottom:12px">
  <summary><span>{{ b.name }}</span><span class="c">{{ b.days|length }} {{ 'day(s)' if mode == 'owner' else 'din' }}{% if b.signed %} &middot; sign &#10003;{% endif %}{% if b.unmarked and not frozen %} &middot; {{ b.unmarked }} {{ 'not marked' if mode == 'owner' else 'baaki' }}{% endif %}</span></summary>
  {% for x in b.days %}<div class="day">
   <div class="dl"><span class="{{ 'sun' if x.sun else '' }}">{% if mode == 'owner' %}{{ x.dow[:3] }} {{ x.d[8:10] }}-{{ x.mon3 }}{% else %}{{ x.d[8:10] }}-{{ x.d[5:7] }} {{ x.dow }}{% endif %}{% if x.off %} <small>({{ 'off-duty Sunday' if mode == 'owner' else 'chhutti ka Sunday' }})</small>{% endif %}{% if x.fest %} <small>(festival)</small>{% endif %}</span>
   {% if b.ro or frozen %}<span class="ro">{{ words[x.mark] if x.mark else '&mdash;'|safe }}</span>{% endif %}</div>
   {% if x.notes %}<div class="note">{{ x.notes }}</div>{% endif %}
   {% if not (b.ro or frozen) %}<div class="seg" role="radiogroup" aria-label="{{ b.name }} {{ x.d }}">
    {% for k in ['P','L','A'] %}<label><input type="radio" name="m_{{ b.sid }}_{{ x.d }}" value="{{ k }}"{% if x.mark == k %} checked{% endif %}><span>{{ words[k] }}</span></label>{% endfor %}
   </div>{% endif %}
  </div>{% endfor %}
  {% if b.ro %}<div class="muted" style="padding:6px 14px 14px">{{ b.ro }}</div>
  {% elif not frozen %}<label class="sign"><input type="checkbox" name="sign_{{ b.sid }}" value="1"{% if b.signed %} checked{% endif %}>{{ ('Signed on the sheet by ' ~ b.name) if mode == 'owner' else ('Sheet par ' ~ b.name ~ ' ka sign hai') }}</label>{% endif %}
 </details>
 {% endfor %}
 {% if not frozen %}<button class="btn" type="submit">{{ 'Approve &amp; save'|safe if mode == 'owner' else 'Save' }}</button>{% endif %}
 </form>
 <div class="muted" style="text-align:center">{{ foot }}</div>
{% endif %}
</div></body></html>"""

SHEET_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Attendance correction sheet - {{ month }}</title>
<style>
 body{font-family:"Segoe UI",Arial,sans-serif;margin:16px auto;max-width:800px;color:#111;background:#fff;font-size:13px;
   -webkit-print-color-adjust:exact;print-color-adjust:exact;padding:0 12px}
 .bar{margin:0 0 12px;display:flex;gap:16px;flex-wrap:wrap} .bar a{color:#05c;font-weight:bold;text-decoration:none;font-size:15px}
 .hdr{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:2px solid #111;padding-bottom:8px;margin-bottom:14px;gap:12px}
 .hdr h1{font-size:21px;margin:0} .hdr .m{font-size:12.5px;margin-top:3px} .hdr .r{font-size:12px;text-align:right;white-space:nowrap}
 .blk{break-inside:avoid;page-break-inside:avoid;margin-bottom:16px}
 .blk h2{font-size:15px;margin:0 0 5px}
 table{width:100%;border-collapse:collapse;font-size:13.5px}
 th{background:#eee;border:1px solid #555;padding:6px;text-align:left}
 th.c{text-align:center;width:16%}
 td{border:1px solid #555;padding:8px 6px}
 td.c{text-align:center;font-size:18px}
 tr.sun td.d,tr.sun td.w{font-weight:700}
 .sig{font-size:13.5px;padding-top:7px}
 .nb{font-size:12.5px;color:#333;border:1px dashed #777;padding:9px 11px;line-height:1.5;margin:6px 0 18px}
 .foot{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px;font-size:13px;border-top:2px solid #111;padding-top:12px;
   break-inside:avoid;page-break-inside:avoid}
 .err{border:2px solid #b00;padding:10px;border-radius:6px;font-size:15px}
 @page{size:A4 portrait;margin:12mm}
 @media print{.noprint{display:none!important} body{margin:0;max-width:none;padding:0}}
</style></head><body>
<div class="bar noprint"><a href="#" onclick="window.print();return false">&#128424; Print</a>
 <a href="{{ prefix }}/attcorr/enter?ym={{ ym }}">Ticks bhariye &rarr;</a></div>
<div class="hdr"><div><h1>Attendance correction sheet &mdash; {{ month }}</h1>
 <div class="m">Dr Manoj Agarwal Clinic &middot; In dinon machine par punch nahi hai. Har din par ek tick lagaiye, phir apna sign kijiye.</div></div>
 <div class="r">Printed {{ printed }}</div></div>
{% if not feed_ok %}<div class="err">Machine ka data abhi padha nahi ja raha, isliye sheet nahi bani. Thodi der baad dobara kholiye.</div>
{% elif not blocks %}<div class="nb">{{ month }} mein sabka har din machine par hai. Kuch bharna nahi hai.</div>
{% else %}
{% for b in blocks %}<div class="blk"><h2>{{ b.name }}</h2>
<table><thead><tr><th style="width:22%">Date</th><th>Day</th><th class="c">Present</th><th class="c">Leave</th><th class="c">Absent</th></tr></thead>
<tbody>{% for r in b.rows %}<tr class="{{ 'sun' if r.sun else '' }}"><td class="d">{{ r.d[8:10] }}-{{ r.d[5:7] }}-{{ r.d[:4] }}</td><td class="w">{{ r.dow }}</td><td class="c">&#9744;</td><td class="c">&#9744;</td><td class="c">&#9744;</td></tr>{% endfor %}</tbody></table>
<div class="sig">{{ b.name }}'s signature: ______________________</div></div>
{% endfor %}
<div class="nb">Jis din machine par punch hai, woh din is sheet par nahi hai. Jiska naam yahan nahi hai, uska poora mahina machine par hai.</div>
{% endif %}
<div class="foot"><div>Reception (entered):<br><br>______________________</div><div>Shavez (checked):<br><br>______________________</div><div>Dr Manoj:<br><br>______________________</div></div>
</body></html>"""

NOACCESS_HTML = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Attendance correction</title><div style="font-family:system-ui,sans-serif;max-width:480px;margin:40px auto;padding:0 16px">
<h2>Attendance correction</h2><p>{{ text }}</p></div>"""

WORDS = {"P": "Present", "L": "Leave", "A": "Absent"}


def _arg_msgs():
    saved, err = "", (request.args.get("err") or "").strip()[:300]
    if request.args.get("ok"):
        bits = [x for x in ((request.args.get("at") or "").strip()[:16], (request.args.get("what") or "").strip()[:60]) if x]
        saved = " · ".join(bits) or "done"
    return saved, err


def _back(path, ym, ok=None, err=None, what=""):
    if err is not None:
        return redirect("%s?ym=%s&err=%s" % (path, ym, SR._msg_safe(err)))
    now = SR._now()
    return redirect("%s?ym=%s&ok=1&at=%s&what=%s" % (path, ym, SR._msg_safe("%s · %s" % (_dm(now), _hm(now))),
                                                    SR._msg_safe(what)))


def _render(mode, ym, u):
    con = _db()
    try:
        blocks, ok = day_list(con, ym)
        st = summary(con, ym, blocks, ok)
        own = SR.staff_for_user(con, u["user"]) if mode == "check" else None
    finally:
        con.close()
    view = _view(blocks, st, own_sid=own)
    for b in view:
        b["ro"] = ""
        if mode == "check" and b["own"]:
            b["ro"] = "Aapke apne din Sir dekhenge."
        b["hl"] = False
        for x in b["days"]:
            x["mon3"] = datetime.date.fromisoformat(x["d"]).strftime("%b")
            notes = ""
            if mode == "check" and x["changed_by_check"] and x["entered"] != x["mark"]:
                notes = "Shavez ne badla · reception ne %s bhara tha" % (WORDS.get(x["entered"]) or "kuch nahi")
                b["hl"] = True
            elif mode == "owner":
                parts = []
                if x["changed_by_check"] and x["entered"] != x["checked"]:
                    parts.append("Shavez corrected %s to %s" % (WORDS.get(x["entered"]) or "blank",
                                                                WORDS.get(x["checked"]) or "blank"))
                    b["hl"] = True
                if x["applied"] and x["applied"] != x["mark"]:
                    parts.append("approved as %s -- approve again to change" % WORDS.get(x["applied"]))
                    b["hl"] = True
                notes = " · ".join(parts)
            x["notes"] = notes
        b["open"] = bool(b["unmarked"]) or b["hl"] or mode == "owner"
    frozen = ""
    if st["applies"] and st["feed_ok"]:
        if st["locked"]:
            frozen = ("This month's salary is locked." if mode == "owner" else "Is mahine ki salary lock ho chuki hai.")
        elif mode != "owner" and st["ever_approved"]:
            frozen = "Sir approve kar chuke hain. Ab koi badlaav Sir ke page par hoga."
        elif mode == "enter" and st["checked"]:
            frozen = "Shavez check kar chuke hain. Ab koi badlaav Shavez ke page par hoga."
    saved, err = _arg_msgs()
    mon, month = _mon(ym), _month_name(ym)
    P = SR.APP_PREFIX
    mm = st["mon"]
    if mode == "enter":
        title, colour = "Attendance correction — %s" % mon, "#0f6e66"
        sub = "%s · %s" % ("Reception" if u["role"] == "maker" else u["user"], _dmy(SR._today()))
        foot = "Save ke baad Shavez dekh lenge. Sign wali sheet Shavez ko dijiye."
        action = P + "/attcorr/enter"
    elif mode == "check":
        title, colour = "Attendance correction — check", "#1f3a5f"
        sub = "Shavez · %s · %s" % (mon, ("reception ne %s ko bhara" % _dm(mm.get("entered_ts")))
                                              if st["entered"] else "reception ne abhi nahi bhara")
        foot = "Kisi bhi din par tap karke badal sakte hain. Shavez ke apne din Sir dekhte hain."
        action = P + "/attcorr/check"
    else:
        title, colour = "Attendance correction — %s" % mon, "#1d2433"
        bits = ["%d day(s) with no punch" % st["n_days"]]
        if st["entered"]:
            bits.append("entered by %s %s" % (mm.get("entered_by"), _dm(mm.get("entered_ts"))))
        if st["checked"]:
            bits.append("checked by %s %s" % (mm.get("checked_by"), _dm(mm.get("checked_ts"))))
        sub = " · ".join(bits)
        foot = ("If Shavez has not checked yet, this same page does his step: change any day and Approve & save. "
                "A day marked Present counts from the duty start, with no late mark. On an off-duty Sunday nothing is "
                "charged or paid: the salary does not read off days.")
        action = P + "/attcorr"
    return render_template_string(
        FORM_HTML, mode=mode, title=title, sub=sub, colour=colour, css=CSS, saved=saved, err=err, st=st, view=view,
        blocks=blocks, ym=ym, mon=mon, month=month, from_month=_month_name(FROM_YM), prefix=P, action=action,
        frozen=frozen, foot=foot, words=WORDS, dm=_dm, hm=_hm)


def view_enter():
    return _render("enter", _ym_arg(), SR.current_user(request))


def view_check():
    return _render("check", _ym_arg(), SR.current_user(request))


def view_owner():
    u = SR.current_user(request)
    if u["user"] not in SR.PRESENT_APPROVERS:
        return render_template_string(NOACCESS_HTML, text="Only Dr Manoj approves the attendance corrections."), 403
    return _render("owner", _ym_arg(), u)


def post_enter():
    u = SR.current_user(request)
    ym = _ym_arg()
    try:
        n, total = save_enter(u["user"], ym, request.form)
    except PermissionError as e:
        return _back(SR.APP_PREFIX + "/attcorr/enter", ym, err=str(e))
    return _back(SR.APP_PREFIX + "/attcorr/enter", ym, ok=True, what="%d din" % n)


def post_check():
    u = SR.current_user(request)
    ym = _ym_arg()
    try:
        changed, _total = save_check(u["user"], ym, request.form)
    except PermissionError as e:
        return _back(SR.APP_PREFIX + "/attcorr/check", ym, err=str(e))
    return _back(SR.APP_PREFIX + "/attcorr/check", ym, ok=True,
                 what="check poora" + (" · %d badle" % changed if changed else ""))


def post_owner():
    u = SR.current_user(request)
    ym = _ym_arg()
    if u["user"] not in SR.PRESENT_APPROVERS:
        return render_template_string(NOACCESS_HTML, text="Only Dr Manoj approves the attendance corrections."), 403
    try:
        _changed, written = save_owner(u["user"], ym, request.form)
    except PermissionError as e:
        return _back(SR.APP_PREFIX + "/attcorr", ym, err=str(e))
    return _back(SR.APP_PREFIX + "/attcorr", ym, ok=True,
                 what="%s's attendance is updated (%d day(s) written)" % (_mon(ym), written))


def view_sheet():
    ym = _ym_arg()
    con = _db()
    try:
        blocks, ok = day_list(con, ym)
    finally:
        con.close()
    return render_template_string(SHEET_HTML, blocks=blocks, feed_ok=ok, ym=ym, month=_month_name(ym),
                                  printed=_dmy(SR._today()), prefix=SR.APP_PREFIX)


def line_payload(ym):
    """What the staff's lists and the owner's console need about ym (the month just ended)."""
    con = _db()
    try:
        blocks, ok = day_list(con, ym)
        st = summary(con, ym, blocks, ok)
    finally:
        con.close()
    mon = _mon(ym)
    live = st["applies"] and ok and st["n_days"] > 0 and not st["locked"] and not st["ever_approved"]
    p = dict(ok=True, ym=ym, month=mon, feed_ok=ok, days=st["n_days"], staff=st["n_staff"],
             entered=st["entered"], checked=st["checked"], approved=st["approved"], locked=st["locked"],
             print_open=0, enter_open=0, check_open=0, owner_open=0,
             print_text="", enter_text="", check_text="", owner_text="")
    if live and not st["entered"]:
        p["print_open"] = st["n_days"]
        p["print_text"] = "Attendance correction sheet print kijiye (%s) — %d staff, %d din" % (mon, st["n_staff"], st["n_days"])
    if live and not st["checked"] and (st["unmarked"] or not st["entered"]):
        p["enter_open"] = st["unmarked"] or st["n_days"]
        p["enter_text"] = "Sign wali sheet se tick bhariye aur Save kijiye (%s) — %d din" % (mon, p["enter_open"])
    if live and st["entered"] and not st["checked"]:
        p["check_open"] = st["n_days"]
        p["check_text"] = "Attendance correction check kijiye — %d din (%s)" % (st["n_days"], mon)
    if st["applies"] and ok and st["n_days"] and not st["locked"] and st["entered"] and not st["approved"]:
        p["owner_open"] = 1
        p["owner_text"] = "Attendance correction: %s ready — approve & save" % mon
    return p


def view_line():
    u = SR.current_user(request)
    if not u or not u["caps"].get("maker"):
        body, code = "{}", 403
    else:
        body, code = json.dumps(line_payload(_prev_ym(SR._today()))), 200
    resp = make_response(body, code)
    resp.headers["Content-Type"] = "application/json"
    resp.headers["Cache-Control"] = "no-store"
    return resp


# ------------------------------------------------------------------------------------------------- install ---
def install(app, sr):
    """Called once by staff_register.py, just before its __main__ block."""
    global SR
    SR = sr                                  # no database is touched here: --init and --selftest stay as they were
    P = SR.APP_PREFIX
    req = SR.require
    rules = [
        ("/attcorr", "attcorr_owner", req("present")(view_owner), ["GET"]),
        ("/attcorr", "attcorr_owner_save", req("present")(post_owner), ["POST"]),
        ("/attcorr/enter", "attcorr_enter", req("maker")(view_enter), ["GET"]),
        ("/attcorr/enter", "attcorr_enter_save", req("maker")(post_enter), ["POST"]),
        ("/attcorr/check", "attcorr_check", req("check")(view_check), ["GET"]),
        ("/attcorr/check", "attcorr_check_save", req("check")(post_check), ["POST"]),
        ("/attcorr/sheet", "attcorr_sheet", req("maker")(view_sheet), ["GET"]),
        ("/attcorr/api/line", "attcorr_line", view_line, ["GET"]),
    ]
    for path, ep, fn, methods in rules:
        app.add_url_rule(P + path, ep, fn, methods=methods)
    orig = app.view_functions.get("salary_lock")
    if orig is not None and not getattr(orig, "_attcorr_wrapped", False):
        app.view_functions["salary_lock"] = _wrap_lock(orig)
    return True
