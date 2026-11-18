#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""off_days.py -- kit S868_DOCTOR_OFF_DAY (the parent, S480, 18-Nov-2026). NEW.

THE OWNER, 18-Nov-2026 12:08-12:11 IST: on the days he does not sit (16, 17 and 18-Nov), reception still exported the
reports; the empty consultation report was set aside ("no date in the file") and his pages called the day's export missing.
"proceed": a day he is NOT SITTING is known to the server, and then
  * the consultation report of that day counts as done -- "no consultations, Dr Manoj not sitting" -- on every page and
    alert that asks for it (docterz_pickup.owner_lines, docterz_missing_alert, Aaj ka kaam's evening line, his console):
    they all read finance.db's docterz_export for a CURRENT consultation row of the day, so a not-sitting day writes ONE such
    row (rows 0, nothing stored, drive_id 'offday:<who>'), and every reader is satisfied without being changed;
  * reception's evening job then waits for the follow-up log alone (it is what tomorrow's calls are built from);
  * a real consultation report of that day, with patients in it, still wins: docterz_pickup replaces a current row that
    has fewer rows (0) by its own rule, and the day stops being 'not sitting' (the export proves he sat).
A day is marked
  * by him: /finance/console/off-days -- "Not sitting today", or a date ahead (his leave), and taken back the same way;
  * by the server: docterz_pickup.take() finds a consultation report with NO patients and no OPD slip that day (S868).
Table clinic_off_day (finance.db): day PK, how ('owner' | 'auto'), by, at, note. Only this file and docterz_pickup write it.
No patient data anywhere here.
"""
import datetime as dt
import html
import sqlite3

VERSION = "S868 1"
PAGE_URL = "/finance/console/off-days"
DDL = ("CREATE TABLE IF NOT EXISTS clinic_off_day (day TEXT PRIMARY KEY, how TEXT NOT NULL, by TEXT NOT NULL DEFAULT '', "
       "at TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '')")
MARK_PREFIX = "offday:"                     # drive_id of the row a not-sitting day writes in docterz_export
AHEAD_DAYS = 60                             # how far ahead a day may be marked
BACK_DAYS = 7                               # and how far back
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def now_ist():
    return dt.datetime.now(IST).replace(tzinfo=None)


def ensure(con):
    con.execute(DDL)


def _good_day(s):
    try:
        return dt.date.fromisoformat(str(s or "")[:10])
    except ValueError:
        return None


def is_off(con, day_iso):
    try:
        return bool(con.execute("SELECT 1 FROM clinic_off_day WHERE day=?", (day_iso,)).fetchone())
    except sqlite3.Error:
        return False


def days(con, lo_iso, hi_iso):
    try:
        return [dict(day=r[0], how=r[1], by=r[2], at=r[3], note=r[4]) for r in con.execute(
            "SELECT day, how, by, at, note FROM clinic_off_day WHERE day BETWEEN ? AND ? ORDER BY day", (lo_iso, hi_iso))]
    except sqlite3.Error:
        return []


def _has_real_consultation(con, day_iso):
    """A current consultation export of the day WITH patients (he sat that day)."""
    r = con.execute("SELECT 1 FROM docterz_export WHERE kind='consultation' AND business_date=? AND status='current' "
                    "AND rows>0 LIMIT 1", (day_iso,)).fetchone()
    return bool(r)


def _write_export_row(con, day_iso, who, at):
    """The one CURRENT consultation row of a not-sitting day (rows 0, nothing stored). Nothing when the day already has a
    current consultation row of any kind (a real export, or an empty report already taken). Its drive_mtime sorts BEFORE any
    real Drive time, so docterz_pickup never takes a real export of the day for 'older' than this row."""
    if con.execute("SELECT 1 FROM docterz_export WHERE kind='consultation' AND business_date=? AND status='current' LIMIT 1",
                   (day_iso,)).fetchone():
        return False
    con.execute("INSERT INTO docterz_export (drive_id, drive_name, drive_mtime, md5, kind, business_date, rows, stored, status, "
                "note, taken_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (MARK_PREFIX + who, "not sitting", "0000-offday-" + day_iso, "offday-" + day_iso, "consultation", day_iso, 0, "", "current",
                 "no consultations: Dr Manoj not sitting (marked by %s)" % who, at))
    return True


def mark(con, day_iso, who, how="owner", note=""):
    """Mark a day not sitting. Refused (False, why) for a day with a real consultation export, or out of range."""
    d = _good_day(day_iso)
    if d is None:
        return False, "not a date"
    today = now_ist().date()
    if not (today - dt.timedelta(days=BACK_DAYS) <= d <= today + dt.timedelta(days=AHEAD_DAYS)):
        return False, "only from %d days back to %d days ahead" % (BACK_DAYS, AHEAD_DAYS)
    if d.weekday() == 6:
        return False, "Sunday is closed anyway"
    ensure(con)
    iso = d.isoformat()
    if _has_real_consultation(con, iso):
        return False, "the consultation report of %s has patients in it -- you sat that day" % d.strftime("%d-%b")
    at = now_ist().strftime("%Y-%m-%d %H:%M:%S")
    con.execute("INSERT OR REPLACE INTO clinic_off_day (day, how, by, at, note) VALUES (?,?,?,?,?)",
                (iso, how, who, at, note[:200]))
    _write_export_row(con, iso, who, at)
    con.commit()
    return True, ""


def unmark(con, day_iso, who):
    """Take a day back: its mark and the row the mark wrote (never a real export's row)."""
    d = _good_day(day_iso)
    if d is None:
        return False, "not a date"
    ensure(con)
    iso = d.isoformat()
    con.execute("DELETE FROM clinic_off_day WHERE day=?", (iso,))
    con.execute("DELETE FROM docterz_export WHERE kind='consultation' AND business_date=? AND drive_id LIKE ? AND rows=0 "
                "AND stored='' AND drive_mtime=?", (iso, MARK_PREFIX + "%", "0000-offday-" + iso))
    con.commit()
    return True, ""


def forget_if_sat(con, day_iso):
    """docterz_pickup: a real consultation report (patients in it) arrived for the day -- he sat; the mark goes."""
    try:
        con.execute("DELETE FROM clinic_off_day WHERE day=?", (day_iso,))
    except sqlite3.Error:
        pass


# ---------------------------------------------------------------------------------------------------------------- the page
_CSS = ("body{font:15px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f6f7f9;color:#1d2433}"
        ".w{max-width:720px;margin:0 auto;padding:16px}h1{font-size:20px;margin:6px 0 4px}.sub{color:#5b6475;margin:0 0 14px}"
        ".box{background:#fff;border:1px solid #dfe3ea;border-radius:10px;padding:14px;margin:0 0 12px}"
        "button{font:inherit;padding:8px 14px;border-radius:8px;border:1px solid #2b5cd6;background:#2b5cd6;color:#fff;cursor:pointer}"
        "button.ghost{background:#fff;color:#2b5cd6}input[type=date]{font:inherit;padding:6px 8px;border:1px solid #c9cfd9;border-radius:8px}"
        "table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:7px 6px;border-bottom:1px solid #eef0f4}"
        ".mut{color:#6b7385;font-size:13px}.ok{color:#137333}.bad{color:#b3261e}a{color:#2b5cd6}")


def page_html(con, who):
    today = now_ist().date()
    rows = days(con, (today - dt.timedelta(days=BACK_DAYS)).isoformat(), (today + dt.timedelta(days=AHEAD_DAYS)).isoformat())
    marked_today = any(r["day"] == today.isoformat() for r in rows)
    lis = "".join(
        "<tr><td><b>%s</b></td><td class=mut>%s</td><td>%s</td></tr>" % (
            html.escape(dt.date.fromisoformat(r["day"]).strftime("%a %d-%b-%Y")),
            html.escape(("marked by %s" % r["by"]) if r["how"] == "owner" else "the server saw an empty consultation report"),
            ("<button class=ghost onclick=\"go('unmark','%s')\">Take back</button>" % r["day"]))
        for r in rows) or "<tr><td class=mut colspan=3>No day marked.</td></tr>"
    return ("<!doctype html><html><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>Days not sitting</title><style>%s</style></head><body><div class=w>"
            "<p class=mut><a href='/finance/console'>&larr; Command console</a></p>"
            "<h1>Days you are not sitting</h1>"
            "<p class=sub>On a day marked here, no page or alert asks for that day's consultation report or calls it missing; "
            "reception's evening job waits for the follow-up log only. If you do sit after all, the day's real consultation "
            "report clears the mark by itself.</p>"
            "<div class=box>%s</div>"
            "<div class=box><b>A day ahead</b> (leave, a conference): <input type=date id=d min='%s' max='%s'> "
            "<button onclick=\"go('mark',document.getElementById('d').value)\">Mark not sitting</button></div>"
            "<div class=box><table><tr><th>Day</th><th></th><th></th></tr>%s</table></div>"
            "<p id=msg></p></div><script>"
            "function go(a,d){if(!d){return}fetch('%s',{method:'POST',credentials:'same-origin',headers:{'Content-Type':"
            "'application/json'},body:JSON.stringify({action:a,day:d})}).then(function(r){return r.json()}).then(function(j){"
            "if(j.ok){location.reload()}else{document.getElementById('msg').innerHTML='<span class=bad>'+(j.why||'not done')"
            ".replace(/</g,'&lt;')+'</span>'}})}</script></body></html>") % (
        _CSS,
        ("<span class=ok>Today (%s) is marked: you are not sitting.</span>" % today.strftime("%a %d-%b") if marked_today else
         "<button onclick=\"go('mark','%s')\">I am not sitting today (%s)</button>" % (today.isoformat(), today.strftime("%a %d-%b"))),
        (today - dt.timedelta(days=BACK_DAYS)).isoformat(), (today + dt.timedelta(days=AHEAD_DAYS)).isoformat(), lis, PAGE_URL)


def init(app, db_getter, require_fn, unit="packs"):
    """Mount only; touches no database at mount (F-303). Called by owner_console.init, beside the Patients page."""
    from flask import Blueprint, Response, jsonify, request            # noqa: PLC0415
    bp = Blueprint("off_days", __name__)

    def _gate():
        return require_fn("checker", unit=unit)

    def _who(u):
        return str((u or {}).get("user") or (u or {}).get("username") or "owner")[:40]

    @bp.route(PAGE_URL, methods=["GET"])
    def off_days_page():
        u, err = _gate()
        if err:
            return Response("This page is for Dr Manoj's login.", status=403, mimetype="text/plain")
        con = db_getter()
        ensure(con)
        r = Response(page_html(con, _who(u)), mimetype="text/html")
        r.headers["Cache-Control"] = "no-store"
        return r

    @bp.route(PAGE_URL, methods=["POST"])
    def off_days_post():
        u, err = _gate()
        if err:
            return err
        j = request.get_json(silent=True) or {}
        act, day = str(j.get("action") or ""), str(j.get("day") or "")[:10]
        con = db_getter()
        if act == "mark":
            ok, why = mark(con, day, _who(u), "owner")
        elif act == "unmark":
            ok, why = unmark(con, day, _who(u))
        else:
            ok, why = False, "unknown action"
        return jsonify(ok=ok, why=why, version=VERSION)

    app.register_blueprint(bp)
